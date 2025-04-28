import json
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ValidationError

from cstoolbox.browser.crawler import CrawlerConfig
from cstoolbox.config import config as global_config
from cstoolbox.core import crawler_manager
from cstoolbox.logger import get_logger

from .schema import ExtractField, ExtractSchema

logger = get_logger(__name__)


@dataclass
class ContentExtractConfig:
    name: str
    page_timeout: int
    wait_for: str
    wait_until: Optional[str] = "domcontentloaded"
    wait_timeout: Optional[int] = 15000
    init_js_code: Optional[str] = None
    js_code: Optional[str] = None


class ContentConfiguration(BaseModel):
    """crawl configuration"""

    config: ContentExtractConfig
    selectors: ExtractSchema


class DataExtractor:
    async def extract(self, url: str, format: str = "html", remove_link: bool = True) -> Dict[str, str]:
        """
        Extract content from specified URL using crawler pool

        Parameters:
            url (str): URL of the webpage to extract content from
            format (str): Output format, markdown or html
            remove_link (bool): Whether to remove links from the content

        Returns:
            dict: Dictionary containing title and content
        """
        try:
            # 解析URL获取domain
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            config, schema = self._load_configs(domain)

            async with crawler_manager.get_crawler() as crawler:
                fields = [
                    {
                        "name": field.name,
                        "selector": field.selector,
                        "type": format if format != field.type and field.name == 'content' else field.type,
                        "attribute": field.attribute,
                        "remove_link": field.remove_link,
                        "remove_img": field.remove_img,
                    }
                    for field in schema.fields
                ]

                default_timeout = 15000
                crawler_config = CrawlerConfig(
                    wait_until=config.wait_until,
                    wait_for=config.wait_for,  # Use merged selector list
                    wait_timeout=(default_timeout if config.wait_timeout == 0 else config.wait_timeout),
                    page_timeout=(default_timeout if config.page_timeout == 0 else config.page_timeout),
                    init_js_code=config.init_js_code,
                    js_code=self._get_js_code(config.js_code),
                    base_selector=schema.base_selector or None,
                    fields=fields,
                    return_full_html=global_config.log_level.lower() == "debug",
                    remove_link=remove_link,
                )
                results = await crawler.crawl(
                    url=url,
                    config=crawler_config,
                )

                if not results:
                    logger.info("crawler result is None: %s", url)
                    raise Exception("crawler result is None")

                if not results.success:
                    raise Exception(f"Unavailable to crawl the url {url}")
                if not results.results and not results.markdown:
                    raise Exception(f"No data extracted from the page, url: {url}")

                if global_config.log_level.lower() == "debug":
                    if results.html:
                        with open(f"{global_config.log_dir}/crawl.html", "w") as f:
                            f.write(results.html)

                    if results.markdown:
                        with open(f"{global_config.log_dir}/crawl.md", "w") as f:
                            f.write(results.markdown)

                data = {}
                if isinstance(results.results, list):
                    data = results.results[0] if results.results else {}
                elif isinstance(results.results, dict):
                    data = results.results

                if not data.get("title"):
                    # First use the title from metadata
                    data["title"] = results.title if results.title else ""

                if not data.get("content"):
                    if format == "markdown":
                        data["content"] = results.markdown.strip() if results.markdown else ""
                    else:
                        data["content"] = results.cleaned_html
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

                return cfg.config, cfg.selectors

            except (json.JSONDecodeError, ValidationError) as e:
                raise ValueError(f"Invalid configuration file for domain '{domain}': {e}")
        else:
            # Build a JS condition to wait for any of the selectors
            selectors = ["body", "article", "main", "#content", ".content", "#app"]
            wait_condition = "||".join([f"document.querySelector('{sel}')" for sel in selectors])

            config = ContentExtractConfig(
                name=domain,
                wait_for=f"js:() => {wait_condition}",
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

    def _get_js_code(self, js_code: str | None) -> str:
        code = [
            # Simulate normal scrolling
            # """
            #     (async () => {
            #         async function simulateScroll() {
            #             const height = document.documentElement.scrollHeight;
            #             for (let i = 0; i < height; i += 100) {
            #                 window.scrollTo(0, i);
            #                 await new Promise(r => setTimeout(r, 50));
            #             }
            #             window.scrollTo(0, 0);
            #         }
            #         await simulateScroll();
            #     })()""",
            # # Handle lazy loading
            # """
            # (async () => {
            #     async function triggerLazyLoad() {
            #         const images = document.getElementsByTagName('img');
            #         for (let img of images) {
            #             const rect = img.getBoundingClientRect();
            #             if (rect.top >= 0 && rect.left >= 0) {
            #                 const event = new Event('lazyload', { bubbles: true });
            #                 img.dispatchEvent(event);
            #             }
            #         }
            #     }
            #     await triggerLazyLoad();
            # })();""",
        ]
        if js_code:
            code.append(js_code)

        return code
