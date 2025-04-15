import base64
import json
import re
import traceback

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.cache_context import CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator

from bs4 import BeautifulSoup
from dataclasses import dataclass
from markdownify import markdownify
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Optional
from urllib.parse import urlparse

from config import config as global_config
from core.browser import browser_pool
from logger import get_logger
from .schema import ExtractSchema, ExtractField

logger = get_logger(__name__)


@dataclass
class ContentExtractConfig:
    name: str
    page_timeout: int
    wait_for: str
    js_code: Optional[str] = None


class ContentConfiguration(BaseModel):
    """crawl configuration"""

    config: ContentExtractConfig
    schema: ExtractSchema


class DataExtractor:
    async def extract(self, url: str, format: str = "html") -> Dict[str, str]:
        """
        Extract content from specified URL using crawler pool

        Parameters:
            url (str): URL of the webpage to extract content from

        Returns:
            dict: Dictionary containing title and content
        """
        try:
            # 解析URL获取domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            config, schema = self._load_configs(domain)
            is_html_content = any(field.type == "html" and field.name == "content" for field in schema.fields)

            async with browser_pool.get_crawler() as crawler:
                extraction_strategy = JsonCssExtractionStrategy(
                    schema={
                        "name": config.name,
                        "baseSelector": schema.base_selector,
                        "fields": [
                            {
                                "name": field.name,
                                "selector": field.selector,
                                "type": field.type,
                                **({"attribute": field.attribute} if field.attribute else {}),
                            }
                            for field in schema.fields
                        ],
                    }
                )

                # Since the content is provided to AI, links and images are almost useless, so the information retrieved is directly removed
                crawler_config = CrawlerRunConfig(
                    wait_until="domcontentloaded",
                    wait_for=config.wait_for,  # Use merged selector list
                    # wait_until="networkidle",  # Wait for network requests to complete
                    page_timeout=(15000 if config.page_timeout == 0 else config.page_timeout),
                    cache_mode=CacheMode.DISABLED,
                    extraction_strategy=extraction_strategy,
                    markdown_generator=DefaultMarkdownGenerator(
                        options={
                            "ignore_links": True,  # Remove links
                            "ignore_images": True,  # Remove images
                        }
                    ),
                    verbose=False,
                    screenshot=global_config.log_level.lower() == "debug",
                    remove_forms=True,
                    process_iframes=False,
                    excluded_tags=[
                        "script",
                        "style",
                        "iframe",
                        "img",
                        "video",
                        "audio",
                        "form",
                        "input",
                        "select",
                        "textarea",
                        "button",
                        "option",
                        "nav",
                        "footer",
                        "header",
                        "aside",
                    ],
                )

                results = await crawler.arun(
                    url=url,
                    config=crawler_config,
                    render=True,
                    simulate_user=True,
                    js_code=self._get_js_code(config.js_code),
                )

                if not results:
                    logger.info("crawler result is None: %s", url)
                    raise Exception("crawler result is None")

                if not results.success:
                    logger.info("%s: %s", results.error_message, url)
                    raise Exception("Unavailable to crawl the url %s" % url)
                if not results.extracted_content and not results.cleaned_html:
                    raise Exception("No data extracted from the page, url: %s", url)

                if global_config.log_level.lower() == "debug":
                    if results.screenshot:
                        with open(f"{global_config.server_root}/logs/snapshot.png", "wb") as f:
                            f.write(base64.b64decode(results.screenshot))

                    if results.html:
                        with open(f"{global_config.server_root}/logs/snapshot.html", "w") as f:
                            f.write(self._clean_html(results.html))

                    if results.markdown:
                        with open(f"{global_config.server_root}/logs/snapshot.md", "w") as f:
                            f.write(results.markdown)

                data = {}
                if results.extracted_content:
                    data = json.loads(results.extracted_content)
                    if data:
                        data = data[0] if isinstance(data[0], dict) else {}
                    else:
                        data = {}

                if not data.get("title"):
                    # First use the title from metadata
                    if results.metadata and results.metadata.get("title"):
                        data["title"] = results.metadata.get("title").strip()
                    else:
                        soup = BeautifulSoup(results.html, "lxml")
                        # Try to get title from title tag
                        title_tag = soup.select_one("title")
                        if title_tag:
                            data["title"] = title_tag.text.strip()
                        else:
                            # If no title tag, try to get from h1
                            for tag in ["h1", "h2"]:
                                title_tag = soup.select_one(tag)
                                if title_tag:
                                    data["title"] = title_tag.text.strip()
                                    break
                            else:
                                data["title"] = ""
                    logger.debug(f"Extracted title: {data.get('title', 'No title')}")

                if data.get("content") is None:
                    if format == "markdown":
                        data["content"] = (
                            results.markdown.strip() if results.markdown else self._markdown(results.cleaned_html)
                        )
                    elif results.cleaned_html:
                        data["content"] = (
                            self._clean_html(results.cleaned_html.strip()).replace("\n", "").replace("\t", "")
                        )
                elif is_html_content:
                    if format == "markdown":
                        data["content"] = self._markdown(data["content"])
                    else:
                        data["content"] = (
                            self._clean_html(self._remove_block_html(data["content"]))
                            .replace("\n", "")
                            .replace("\t", "")
                        )
                data["url"] = url

                logger.info(f"content length: {len(data.get('content', ''))}, url: {url}")

                return data

        except Exception as e:
            error_details = {
                "error": str(e),
                "traceback": traceback.format_exc(),
                "url": url,
                "domain": domain,
            }
            logger.error(f"Error extracting content: {error_details}")
            raise Exception(e)

    def _load_configs(self, domain):
        """Load all content extraction configurations"""
        self.configs = {}
        config_path = self._find_domain_config(domain)
        if config_path:
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Use Pydantic model to validate the entire configuration
                cfg = ContentConfiguration(**data)

                return cfg.config, cfg.schema

            except (json.JSONDecodeError, ValidationError) as e:
                raise ValueError(f"Invalid configuration file for domain '{domain}': {e}")
        else:
            # Build a JS condition to wait for any of the selectors
            selectors = ["body", "article", "main", "#content", ".content", "#app"]
            wait_condition = " || ".join([f"document.querySelector('{sel}')" for sel in selectors])

            config = ContentExtractConfig(
                name=domain,
                wait_for=f"() => {wait_condition}",  # Return a function to check if any of the selectors exist
                page_timeout=10000,
            )
            schema = ExtractSchema(
                base_selector="html",
                fields=[
                    ExtractField(name="title", selector="title", type="text"),
                ],
            )
        return config, schema

    def _find_domain_config(self, domain: str) -> Path | None:
        """
        Find configuration file by domain.

        :param domain: Input domain, e.g., "a.b.c.d.com"
        :return: Return the first matching configuration file path, or None if not found
        """
        # Split the domain by '.' into multiple parts
        parts = domain.split(".")

        # Start from the most specific subdomain and check level by level
        for i in range(len(parts)):
            # Build the current subdomain
            subdomain = ".".join(parts[i:])

            # Build the configuration file path
            config_path = Path(global_config.server_root) / "schema" / "content" / f"{subdomain}.json"

            # Check if the file exists
            if config_path.exists():
                return config_path

        # If all level configuration files do not exist, return None
        return None

    def _markdown(self, text: str) -> str:
        """
        Convert text to Markdown format.

        :param text: Input text
        :return: Converted Markdown format text
        """
        text = self._clean_html(self._remove_block_html(text), remove_link=True, remove_img=True)
        return markdownify(text).strip()

    def _clean_html(self, text: str, remove_link: bool = True, remove_img: bool = True) -> str:
        # Remove the useless tags
        useless_tags = [
            r"<nav[^>]*>[\s\S]*?</nav>",
            r"<footer[^>]*>[\s\S]*?</footer>",
            r"<aside[^>]*>[\s\S]*?</aside>",
            r"<header[^>]*>[\s\S]*?</header>",
        ]
        for tag in useless_tags:
            text = re.sub(tag, "", text.strip())
        if remove_link:
            text = re.sub(r"<a[^>]*>([\s\S]*?)</a>", r"\1", text)
        else:
            text = re.sub(r"<a\s+([^>]*\s*href=['\"][^'\"]*['\"][^>]*)>", r"<a \1>", text)
        if remove_img:
            text = re.sub(r"<img[^>]*>", "", text)

        # remove multiple <span>
        text = re.sub(r"(<span[^>]*>)(\s*<span[^>]*>)+", r"\1", text)
        text = re.sub(r"(</span>)(\s*</span>)+", r"\1", text)

        # simplify li, td, th
        text = re.sub(r"<li[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</li>", r"<li>\1</li>", text)
        text = re.sub(r"<td[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</td>", r"<td>\1</td>", text)
        text = re.sub(r"<th[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</th>", r"<th>\1</th>", text)
        # remove tag attributes
        text = re.sub(r"<(?!a\b)([a-zA-Z]+)[^>]+>", r"<\1>", text)

        # remove comments
        text = re.sub(r"<!--.*?-->", "", text)
        # remove multiple \n
        text = re.sub(r"(\n\s*){2,}", r"\n\n", text)

        return text

    def _remove_block_html(self, text: str) -> str:
        # Remove block-level useless tags
        useless_tags = [
            r"<script[^>]*>[\s\S]*?</script>",
            r"<style[^>]*>[\s\S]*?</style>",
            r"<noscript[^>]*>[\s\S]*?</noscript>",
            r"<iframe[^>]*>[\s\S]*?</iframe>",
            r"<form[^>]*>[\s\S]*?</form>",
        ]
        for tag in useless_tags:
            text = re.sub(tag, "", text.strip())
        return text

    def _get_js_code(self, js_code: str | None) -> str:
        code = [
            # Simulate normal scrolling
            """
                    async function simulateScroll() {
                        const height = document.documentElement.scrollHeight;
                        for (let i = 0; i < height; i += 100) {
                            window.scrollTo(0, i);
                        await new Promise(r => setTimeout(r, 50));
                    }
                    window.scrollTo(0, 0);
                }
                await simulateScroll();
                """,
            # Handle lazy loading
            """
                function triggerLazyLoad() {
                    const images = document.getElementsByTagName('img');
                    for (let img of images) {
                        const rect = img.getBoundingClientRect();
                        if (rect.top >= 0 && rect.left >= 0) {
                            const event = new Event('lazyload', { bubbles: true });
                            img.dispatchEvent(event);
                        }
                    }
                }
                triggerLazyLoad();
                """,
        ]
        if js_code:
            code.append(js_code)

        return code
