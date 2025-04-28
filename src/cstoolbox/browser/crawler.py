"""
Playwright-based web crawler implementation with configuration support.
"""

import os
import re
import traceback
from pathlib import Path
from typing import Any, Union
from urllib.parse import urljoin
import functools
import time

from bs4 import BeautifulSoup, Comment, Tag
from markdownify import markdownify
from playwright.async_api import Page

from cstoolbox.logger import get_logger

from .config import CrawlerConfig, CrewlerResult, EventType, FieldType, PageConfig
from .pool import BrowserPool
from .block import block_domains

logger = get_logger(__name__)


class Crawler:
    """Playwright-based web crawler"""

    def __init__(self, browser_pool: BrowserPool):
        self.browser_pool = browser_pool

    async def crawl(self, url: str, config: CrawlerConfig) -> CrewlerResult:
        """
        Crawl webpage with given configuration

        Args:
            url: URL to crawl
            config: Crawler configuration
        """
        start_time = time.time()

        self.url = url
        page_config = PageConfig(
            wait_for=config.wait_for,
            wait_until=config.wait_until,
            wait_timeout=config.wait_timeout,
            page_timeout=config.page_timeout,
            init_js_code=config.init_js_code,
        )

        page = await self.browser_pool.new_page(page_config)

        # Block ad requests
        # await self._block_ad_requests(page)

        try:
            await page.goto(url, timeout=config.page_timeout)

            if config.events:
                for event in config.events:
                    if event.event == EventType.Click:
                        await page.click(event.selector, timeout=event.timeout)
                    elif event.event == EventType.Fill:
                        await page.fill(event.selector, event.value, timeout=event.timeout)
                    elif event.event == EventType.Enter:
                        await page.locator(event.selector).press("Enter", timeout=event.timeout)
                await page.wait_for_load_state('domcontentloaded', timeout=15000)

            if config.js_code:
                if isinstance(config.js_code, list):
                    for js in config.js_code:
                        await page.evaluate(js)
                elif isinstance(config.js_code, str):
                    await page.evaluate(config.js_code)

            if config.wait_for:
                if config.wait_for.startswith("js:"):
                    page.wait_for_function(config.wait_for[3:], timeout=(config.wait_timeout or 15000))
                else:
                    wait_for = config.wait_for[4:] if config.wait_for.startswith("css:") else config.wait_for
                    await page.wait_for_selector(wait_for, timeout=(config.wait_timeout or 15000))

            body_elm = await page.query_selector('body')
            if body_elm:
                body = await body_elm.inner_html()
            else:
                raise Exception("No body tag found in HTML, try to set wait_for to 'body'")
            html = await page.content()

            cleaned_html = self._clean_html_for_content(self._clean_html(body, config.remove_link))
            soup = BeautifulSoup(html, 'lxml')
            result = CrewlerResult(
                title=self._select_title(soup),
                url=url,
                html=html if config.return_full_html else "",
                cleaned_html=cleaned_html,
                markdown=self._mark_it_down(cleaned_html),
            )

            data = []
            if config.base_selector:
                elements = soup.select(config.base_selector)
                for element in elements:
                    item = {}
                    for field in config.fields:
                        value = self._select_one(
                            element, field.selector, field.type, field.attribute, field.remove_link, field.remove_img
                        )
                        item[field.name] = value.strip() if value else None
                    data.append(item)
            else:
                data = {}
                for field in config.fields:
                    value = self._select_one(
                        soup, field.selector, field.type, field.attribute, field.remove_link, field.remove_img
                    )
                    data[field.name] = value.strip() if value else None

            result.results = data
            result.success = True

            return result
        except Exception as e:
            logger.error(f"Error crawling {url}: {e}\n{traceback.format_exc()}")
            return CrewlerResult(
                error_message=str(e),
                success=False,
            )
        finally:
            logger.info(f"Crawl {url} finished in {time.time() - start_time:.2f} seconds")
            await page.close()

    def _select_title(self, soup: BeautifulSoup) -> str:
        """
        Select the title of the page.
        Args:
            soup: BeautifulSoup object
        Returns:
            Title of the page
        """
        for selector in ["title", "h1", "h2"]:
            title = self._select_one(soup, selector, FieldType.TEXT)
            if title:
                return title

    def _select_one(
        self,
        soup: Union[BeautifulSoup, Tag],
        selector: str,
        field_type: FieldType,
        attribute: str = "",
        remove_link: bool = False,
        remove_img: bool = True,
    ) -> Any:
        """
        Select the first element that matches the given CSS selector.
        Args:
            soup: BeautifulSoup object
            selector: CSS selector
        Returns:
            BeautifulSoup object of the first element that matches the selector
        """
        field_element = soup.select_one(selector)
        if not field_element:
            return None
        elif field_type == FieldType.TEXT:
            return field_element.get_text().strip()
        elif field_type == FieldType.HTML:
            return self._clean_html(str(field_element), remove_link, remove_img)
        elif field_type == FieldType.MARKDOWN:
            return self._mark_it_down(self._clean_html(str(field_element), remove_link, remove_img))
        elif field_type == FieldType.ATTRIBUTE and attribute:
            return field_element.get(attribute)
        else:
            return None

    def _mark_it_down(self, html: str) -> str | None:
        """
        Convert HTML to markdown.
        Args:
            html: HTML content
        Returns:
            Markdown content
        """
        try:
            return re.sub(r'\n{2,}', '\n', markdownify(html).strip())
        except Exception as e:
            logger.error(f"Error converting HTML to markdown: {e}")
            return ""

    async def _block_ad_requests(self, page: Page):
        """
        Block common ad requests using Playwright route interception with glob patterns.
        Args:
            page: Playwright page instance
        """

        # 1. Block specific domains/patterns
        async def block_domain_handler(route, pattern):
            # logging.debug(f"Blocking ad domain ({pattern}): {route.request.url}")
            logger.debug(f"Blocking ad domain ({pattern}): {route.request.url}")
            await route.abort()

        for pattern in block_domains:
            # Need to use lambda or functools.partial to capture the pattern correctly in the loop
            handler = functools.partial(block_domain_handler, pattern=pattern)
            await page.route(pattern, handler)

        # 2. Block specific resource types first (optional, but potentially cleaner)
        async def block_resource_types(route):
            if route.request.resource_type in ["image", "font", "media", "websocket"]:
                # logging.debug(f"Blocking resource type {route.request.resource_type}: {route.request.url}")
                # print(f"Blocking resource type {route.request.resource_type}: {route.request.url}")
                await route.abort()
            else:
                await route.continue_()

        await page.route('**/*', block_resource_types)

    def _remove_ads(self, html: str) -> str:
        """
        Remove common advertisement elements from HTML content.
        Args:
            html: HTML content to process
        Returns:
            HTML content with ads removed
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove elements with common ad-related class names
        for selector in [
            '[class*="ad-"]',
            '[class*="-ad"]',
            '[id*="ad-"]',
            '[id*="-ad"]',
            '[class*="banner"]',
            '[id*="banner"]',
            '.ad',
            '.ads',
            '.advertisement',
            '.ad-container',
            '.ad-wrapper',
        ]:
            for element in soup.select(selector):
                element.decompose()

        return str(soup)

    def _clean_html(self, html: str, remove_link: bool = False, remove_img: bool = True) -> str:
        """
        Clean HTML content by removing unnecessary tags and attributes.
        Args:
            html: HTML content to clean
        Returns:
            Cleaned HTML content
        """
        soup = BeautifulSoup(html, 'lxml')

        # Remove unwanted tags and comments
        for tag in soup(
            [
                "script",
                "style",
                "iframe",
                "frame",
                "frameset",
                "object",
                "embed",
                "noscript",
                "meta",
                "link",
                "form",
                "input",
                "button",
                "select",
                "textarea",
                "fieldset",
                "label",
                "datalist",
                "output",
                "option",
            ]
        ):
            tag.decompose()

        # Remove all comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()

        # Keep only structural and content tags but preserve essential attributes
        for tag in soup.find_all(True):
            if tag.name == "a":
                if remove_link:
                    tag.unwrap()
                else:
                    # Resolve relative URLs for <a> tags
                    href = tag.attrs.get("href")
                    if href:
                        if href.startswith("javascript:"):
                            tag.unwrap()
                            continue

                        try:
                            href = urljoin(self.url, href)
                        except:
                            pass
                    tag.attrs = {"href": href} if href else {}
            elif tag.name == "img":
                if remove_img:
                    tag.decompose()
                else:
                    # Resolve relative URLs for <img> tags
                    src = tag.attrs.get("src")
                    if src:
                        try:
                            src = urljoin(self.url, src)
                        except:
                            pass
                    tag.attrs = {"src": src} if src else {}
            elif tag.name in ["table", "td", "th", "tbody", "thead", "tfoot", "tr"]:
                # Keep rowspan and colspan for table elements
                attrs = {}
                if "rowspan" in tag.attrs:
                    attrs["rowspan"] = tag.attrs["rowspan"]
                if "colspan" in tag.attrs:
                    attrs["colspan"] = tag.attrs["colspan"]
                tag.attrs = attrs
            elif tag.name in [
                "div",
                "p",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ol",
                "ul",
                "li",
                "dl",
                "dd",
                "dt",
                "nav",
                "footer",
                "aside",
                "header",
                "article",
                "section",
                "main",
            ]:
                # Keep style for div and span elements
                tag.attrs = {}
            else:
                tag.unwrap()

        # Remove empty tags and whitespace-only tags
        for tag in soup.find_all(True):
            if (
                (not tag.contents or all(c.name in ['br', 'hr'] for c in tag.contents))
                and (not tag.string or tag.string.strip() == '')
                and tag.name not in ['br', 'hr', 'img', 'svg', 'figure']
            ):
                tag.decompose()
        # Check if a body tag exists (it almost always will with HTML parsers)
        if soup.body:
            # Use decode_contents() to get the inner HTML of the body tag
            data = soup.body.decode_contents()
        else:
            # Fallback in the unlikely case there's no body tag
            data = str(soup)

        return data.replace('\r', '\n').replace('\n\n', '\n').replace('    ', '  ').replace('\t', '  ').strip()

    def _clean_html_for_content(self, text: str) -> str:
        # Remove the useless tags
        useless_tags = [
            r"<nav[^>]*>[\s\S]*?</nav>",
            r"<footer[^>]*>[\s\S]*?</footer>",
            r"<aside[^>]*>[\s\S]*?</aside>",
            r"<header[^>]*>[\s\S]*?</header>",
        ]
        for tag in useless_tags:
            text = re.sub(tag, "", text.strip())

        # remove multiple <span>
        text = re.sub(r"(<span[^>]*>)(\s*<span[^>]*>)+", r"\1", text)
        text = re.sub(r"(</span>)(\s*</span>)+", r"\1", text)

        # simplify li, td, th
        text = re.sub(r"<li[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</li>", r"<li>\1</li>", text)
        text = re.sub(r"<td[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</td>", r"<td>\1</td>", text)
        text = re.sub(r"<th[^>]*>\s*<span[^>]*>([^<>]+?)</span>\s*</th>", r"<th>\1</th>", text)

        # remove comments
        text = re.sub(r"<!--.*?-->", "", text)
        # remove multiple \n
        text = re.sub(r"(\n\s*){2,}", r"\n\n", text)

        return text
