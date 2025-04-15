import asyncio
import base64
import json
import os
import random
import time

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.cache_context import CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional, List
from urllib.parse import quote, urljoin

from config import config as global_config
from core.browser import browser_pool
from logger import get_logger
from .schema import ExtractSchema


logger = get_logger(__name__)


@dataclass
class SearchResult:
    """Class representing a search result with support for multiple content types"""

    title: str
    url: str
    summary: Optional[str] = None
    site_name: Optional[str] = None
    publish_date: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    thumbnails: Optional[List[str]] = None
    duration: Optional[int] = None
    source_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class PaginationType(str, Enum):
    """pagination enum"""

    PAGE = "page"  # use page number, like page=1
    OFFSET = "offset"  # use offset, like first=10


class SearchProviderConfig(BaseModel):
    """search provider config"""

    name: str = ""
    url_template: str

    # pagination type, default is offset
    pagination_type: PaginationType = PaginationType.OFFSET
    # pagination param name, default is page or offset
    pagination_param: str = ""
    # max results per page
    max_results_per_page: Optional[int] = 10
    # pagination selector
    pages_selector: Optional[str] = None

    # A CSS selector or JS condition to wait for before extracting content.  Default: None.
    wait_for: str = ""

    # Timeout in ms for page operations like navigation. Default: 60000 (60 seconds).
    page_timeout: int = Field(default=60000, gt=0)

    # js_code
    js_code: Optional[str] = None

    click_config: Optional[List[dict]] = Field(
        default=None,
        description="Multi-step click configuration, example: [{'selector': '.more', 'wait': 1000}, {'selector': '.details', 'wait': 2000}]",
    )


class SearchConfiguration(BaseModel):
    """search configuration"""

    config: SearchProviderConfig
    schema: ExtractSchema


class SearchExtractor:
    """Class for extracting search results based on configured schema"""

    provider: str
    page_urls: List[str]

    def __init__(self, provider: str):
        """Initialize SearchExtractor instance"""
        if not provider:
            raise ValueError("Provider cannot be empty")
        self.provider = provider

        self.config, self.schema = self._load_provider_data(provider)

    def _load_provider_data(
        self, provider: str
    ) -> tuple[SearchProviderConfig, ExtractSchema]:
        """Load provider configuration and schema from JSON file"""
        config_path = (
            Path(global_config.server_root) / "schema" / "search" / f"{provider}.json"
        )
        if not config_path.exists():
            logger.error(f"Configuration file not found: '{config_path}'")
            raise ValueError(f"Configuration file not found for provider '{provider}'")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # use Pydantic model to validate the entire configuration
            cfg = SearchConfiguration(**data)

            return cfg.config, cfg.schema

        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Invalid configuration file for provider '{provider}': {e}"
            )

    def _get_search_url(
        self, kw: str, page: int = 1, number: int = 10, time_period: str = ""
    ) -> str:
        """Generate search URL with given parameters"""
        encoded_kw = quote(kw)

        # calculate pagination parameter
        if self.config.pagination_type == PaginationType.PAGE:
            page_value = page
        else:  # OFFSET
            page_value = (page - 1) * number

        # get pagination parameter name, if not specified, use default value
        param_name = self.config.pagination_param or (
            "page" if self.config.pagination_type == PaginationType.PAGE else "offset"
        )

        # build parameter dictionary
        params = {
            "kw": encoded_kw,
            "number": number,
            "timestamp": int(time.time() * 1000),
            "rand": random.randint(10000, 99999),
            "time_period": time_period,
        }
        params[param_name] = page_value

        # get base URL
        region = os.getenv("REGION", global_config.region)
        base_url = global_config.region_urls.get(self.provider, {}).get(region)
        if not base_url:
            base_url = global_config.region_urls[self.provider]["com"]

        path = self.config.url_template.format(**params)
        return f"{base_url.rstrip('/')}{path}"

    async def extract_results(
        self, kw: str, page: int = 1, number: int = 10, time_period: str = ""
    ) -> Optional[str]:
        """Extract search results using crawl4ai"""
        # get max results per page
        max_per_page = min(number, getattr(self.config, "max_results_per_page", 10))
        total_needed = number
        # calculate number of requests needed
        request_times = (total_needed + max_per_page - 1) // max_per_page

        extraction_strategy = JsonCssExtractionStrategy(
            schema={
                "name": self.config.name,
                "baseSelector": self.schema.base_selector,
                "fields": [
                    {
                        "name": field.name,
                        "selector": field.selector,
                        "type": field.type,
                        **({"attribute": field.attribute} if field.attribute else {}),
                    }
                    for field in self.schema.fields
                ],
            }
        )

        crawler_config = CrawlerRunConfig(
            wait_until="domcontentloaded",
            wait_for_images=False,
            wait_for=self.config.wait_for,
            page_timeout=(
                30000 if self.config.page_timeout == 0 else self.config.page_timeout
            ),
            cache_mode=CacheMode.DISABLED,
            extraction_strategy=extraction_strategy,
            verbose=False,
            screenshot=False,  ## production environment must be disabled
            remove_forms=True,
            process_iframes=False,
            excluded_tags=["script", "style", "iframe", "img", "video", "audio"],
        )
        # TODO: duckduckgo temporarily can only get the first page

        async with browser_pool.get_crawler() as crawler:
            if self.config.click_config:
                return await self._extract_with_clicks(
                    crawler,
                    crawler_config,
                    self._get_search_url(kw, page, max_per_page, time_period),
                    request_times,
                )
            else:
                return await self._extract_normal(
                    crawler,
                    crawler_config,
                    page,
                    max_per_page,
                    kw,
                    time_period,
                    request_times,
                )

    async def _extract_normal(
        self,
        crawler: AsyncWebCrawler,
        crawler_config: CrawlerRunConfig,
        page: int = 1,
        max_per_page: int = 10,
        kw: str = "",
        time_period: str = "",
        request_times: int = 1,
    ):
        """
        Extract search results using crawl4ai
        """
        js_code = (
            [self.config.js_code.format(number=max_per_page)]
            if hasattr(self.config, "js_code") and self.config.js_code
            else None
        )

        all_results = []
        page_urls = []
        current_offset = (page - 1) * max_per_page
        for i in range(request_times):
            if page_urls:
                url = page_urls.pop(0)
            else:
                url = self._get_search_url(
                    kw, current_offset // max_per_page + 1, max_per_page, time_period
                )
            logger.info("search url: %s", url)

            results = await crawler.arun(
                url=url,
                config=crawler_config,
                render=True,
                simulate_user=True,
                js_code=js_code,
                wait_for=self.config.wait_for,
            )

            if not results:
                logger.info(
                    "No search results found for query: '%s' at offset %s",
                    kw,
                    current_offset,
                )
                raise Exception("crawler result is None")

            if not results.success:
                logger.info("%s: %s", results.error_message, url)
                raise Exception(results.error_message)

            if results.screenshot:
                with open(
                    f"{global_config.server_root}/logs/{self.provider}_{kw}_{i+1}.png",
                    "wb",
                ) as f:
                    f.write(base64.b64decode(results.screenshot))

            # if results.html:
            #     with open(f"{self.provider}_{kw}_{i+1}.html", "w") as f:
            #         f.write(results.html)

            if results.extracted_content:
                current_results = json.loads(results.extracted_content)
                if not current_results:
                    logger.info(
                        "No search results found for query: '%s' at offset %s",
                        kw,
                        current_offset,
                    )
                    break
                logger.info(
                    "Query: %s, offset: %s, found %s results",
                    kw,
                    current_offset,
                    len(current_results),
                )

                all_results.extend(current_results)
                current_offset += max_per_page

                # only extract page links on the first page
                if i == 0 and self.config.pages_selector and results.html:
                    soup = BeautifulSoup(results.html, "lxml")
                    page_links = soup.select(self.config.pages_selector)
                    page_urls = list(
                        dict.fromkeys(
                            urljoin(results.url, link["href"])  # 使用 urljoin 转换
                            for link in page_links
                            if link.has_attr("href") and link.text.strip() != "1"
                        )
                    )
                    logger.info(f"Found {len(page_urls)} page links")

                # add delay between requests, unless it's the last request
                if i < request_times - 1:
                    await asyncio.sleep(1)  # 300ms delay

        return all_results

    async def _extract_with_clicks(
        self,
        crawler: AsyncWebCrawler,
        crawler_config: CrawlerRunConfig,
        url: str,
        click_times: int = 1,
    ):
        """
        If schema file defines click_config, such as:
        {"click_config":[
            {'selector': '.more', 'wait': 1000},
            {'selector': '.details', 'wait': 2000}
            ]
        },
        then call this method to get data
        """
        all_results = []
        if self.config.click_config:
            for click_step in self.config.click_config:
                if not click_step["selector"]:
                    continue
                logger.debug("click url: %s, selector: %s", url, click_step["selector"])

                timeout = click_step.get("wait", 300)
                click_js = f"""(async () => {{
                        const element = document.querySelector('{click_step['selector']}');
                        if (element) {{
                            for (let i = 0; i < {click_times}; i++) {{
                                element.click();
                                await new Promise(r => setTimeout(r, {timeout}));
                            }}
                        }}
                    }})()"""

                results = await crawler.arun(
                    url=url,
                    config=crawler_config,
                    js_code=[click_js],
                    cache_mode=CacheMode.DISABLED,
                )

                if not results:
                    logger.info(
                        "No search results found for query: %s",
                        url,
                    )
                    raise Exception("search results object is None")

                if not results.success:
                    logger.info("%s: %s", results.error_message, url)
                    raise Exception(results.error_message)

                if results and results.screenshot:
                    with open(
                        f"{global_config.server_root}/logs/{self.provider}_new.png",
                        "wb",
                    ) as f:
                        f.write(base64.b64decode(results.screenshot))

                if results and results.extracted_content:
                    try:
                        results = json.loads(results.extracted_content)
                        all_results.extend(results)
                    except:
                        logger.error(
                            "Error parsing JSON: %s", results.extracted_content
                        )
                        continue

        return all_results

    async def search(
        self, kw: str, page: int = 1, number: int = 10, time_period: str = ""
    ) -> List[SearchResult]:
        """Convenience method to perform search and extract results"""
        return await self.extract_results(kw, page, number, time_period)
