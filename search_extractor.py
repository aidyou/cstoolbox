import asyncio
import json
import random
import time

from crawl4ai.async_configs import CrawlerRunConfig
from crawl4ai.cache_context import CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, field_validator, ValidationError
from typing import Dict, Any, Optional, List, Literal
from urllib.parse import quote

from browser import browser_pool
from config import config
from logger import get_logger


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
    """分页类型枚举"""

    PAGE = "page"  # 使用页码，如 page=1
    OFFSET = "offset"  # 使用偏移量，如 first=10


class SearchField(BaseModel):
    """搜索字段配置"""

    name: str
    selector: str
    type: str
    attribute: Optional[str] = None


class SearchSchema(BaseModel):
    """搜索模式配置"""

    base_selector: str
    fields: List[SearchField]
    error_selectors: Optional[List[str]] = None

    @field_validator("fields", "base_selector")
    def validate_fields(cls, v):
        if not v:
            raise ValueError("fields list cannot be empty")
        return v


class SearchProviderConfig(BaseModel):
    """搜索提供者配置"""

    name: str = ""
    url_template: str

    # 分页类型，默认为 offset
    pagination_type: PaginationType = PaginationType.OFFSET
    # 分页参数名称，默认为 page 或 offset
    pagination_param: str = ""

    # A CSS selector or JS condition to wait for before extracting content.  Default: None.
    wait_for: str = ""

    # The type of browser to launch. Supported values: "chromium", "firefox", "webkit".  Default: "chromium"
    browser_type: Optional[Literal["chromium", "webkit", "firefox"]] = "chromium"

    # Whether to run the browser in headless mode (no visible GUI). Default: True.
    headless: bool = True

    # Timeout in ms for page operations like navigation. Default: 60000 (60 seconds).
    page_timeout: int = Field(default=60000, gt=0)

    # Custom User-Agent string to use. Default: "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
    user_agent: Optional[str] = None

    # Path to a user data directory for persistent sessions. If None, a temporary directory may be used. Default: None.
    user_agent_mode: Optional[str] = None

    # Path to a user data directory for persistent sessions. If None, a temporary directory may be used. Default: None.
    user_data_dir: Optional[str] = None

    # Extra HTTP headers to apply to all requests in this context. Default: {}.
    headers: Optional[dict] = None

    # Proxy server URL (e.g., "http://username:password@proxy:port"). If None, no proxy is used.
    proxy: Optional[str] = None

    # proxy config: {"server": "...", "username": "..."}
    proxy_config: Optional[dict] = None

    # 点击加载更多配置
    click_load: Optional[dict] = None

    # js_code
    js_code: Optional[str] = None

    # 每页最大结果数限制
    max_results_per_page: Optional[int] = 10


class SearchConfiguration(BaseModel):
    """完整的搜索配置"""

    config: SearchProviderConfig
    schema: SearchSchema


class SearchExtractor:
    """Class for extracting search results based on configured schema"""

    provider: str

    def __init__(self, provider: str):
        """Initialize SearchExtractor instance"""
        if not provider:
            raise ValueError("Provider cannot be empty")
        self.provider = provider

        self.config, self.schema = self._load_provider_data(provider)

    def _load_provider_data(
        self, provider: str
    ) -> tuple[SearchProviderConfig, SearchSchema]:
        """Load provider configuration and schema from JSON file"""
        config_path = Path(__file__).parent / "schema" / f"{provider}.json"
        if not config_path.exists():
            raise ValueError(f"Configuration file not found for provider '{provider}'")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 使用 Pydantic 模型验证整个配置
            cfg = SearchConfiguration(**data)

            # 应用默认值
            if not cfg.config.user_agent:
                cfg.config.user_agent = config.user_agent
            if not cfg.config.user_agent_mode:
                cfg.config.user_agent_mode = config.user_agent_mode
            if not cfg.config.proxy:
                cfg.config.proxy = config.proxy
            if not cfg.config.proxy_config:
                cfg.config.proxy_config = config.proxy_config

            return cfg.config, cfg.schema

        except (json.JSONDecodeError, ValidationError) as e:
            raise ValueError(
                f"Invalid configuration file for provider '{provider}': {e}"
            )

    def _get_search_url(self, kw: str, page: int = 1, number: int = 10) -> str:
        """Generate search URL with given parameters"""
        encoded_kw = quote(kw)

        # 计算分页参数
        if self.config.pagination_type == PaginationType.PAGE:
            page_value = page
        else:  # OFFSET
            page_value = (page - 1) * number

        # 获取分页参数名称，如果未指定则使用默认值
        param_name = self.config.pagination_param or (
            "page" if self.config.pagination_type == PaginationType.PAGE else "offset"
        )

        # 构建参数字典
        params = {
            "kw": encoded_kw,
            "number": number,
            "timestamp": int(time.time() * 1000),
            "rand": random.randint(10000, 99999),
        }
        params[param_name] = page_value

        # 获取基础 URL
        base_url = config.region_urls.get(self.provider, {}).get(config.region)
        if not base_url:
            base_url = config.region_urls[self.provider]["com"]

        # 拼接完整 URL
        path = self.config.url_template.format(**params)
        return f"{base_url.rstrip('/')}{path}"

    async def extract_results(
        self, kw: str, page: int = 1, number: int = 10
    ) -> Optional[str]:
        """Extract search results using crawl4ai"""
        # 获取每页最大结果数限制
        max_per_page = min(number, getattr(self.config, "max_results_per_page", 10))
        total_needed = number
        all_results = []
        current_offset = (page - 1) * max_per_page

        # 计算需要请求的次数
        request_times = (total_needed + max_per_page - 1) // max_per_page

        # 准备 JS 代码
        js_code = None
        if hasattr(self.config, "js_code") and self.config.js_code:
            js_code = [self.config.js_code.format(number=max_per_page)]

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
            wait_for=self.config.wait_for,
            page_timeout=(
                30000 if self.config.page_timeout == 0 else self.config.page_timeout
            ),
            cache_mode=CacheMode.DISABLED,
            extraction_strategy=extraction_strategy,
            verbose=False,
            screenshot=False,  ## 生产环境务必关闭
        )
        # TODO: duckduckgo 暂时只能拿到第一页

        async with browser_pool.get_crawler() as crawler:
            for i in range(request_times):
                # 每次请求最大数量
                url = self._get_search_url(
                    kw, current_offset // max_per_page + 1, max_per_page
                )
                logger.info("search url: %s", url)

                results = await crawler.arun(
                    url=url,
                    config=crawler_config,
                    render=True,
                    simulate_user=True,
                    js_code=js_code,
                )

                if not results:
                    logger.info(
                        "No search results found for query: '%s' at offset %s",
                        kw,
                        current_offset,
                    )
                    break

                # if results.screenshot:
                #     with open(f"{self.provider}_{kw}_{i+1}.png", "wb") as f:
                #         f.write(base64.b64decode(results.screenshot))

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

                    # 在请求之间添加延迟，除非是最后一次请求
                    if i < request_times - 1:
                        await asyncio.sleep(0.3)  # 300ms 延迟

                # return json.dumps(all_results[:total_needed]) if all_results else "[]"
                return all_results if all_results else []

    async def search(
        self, kw: str, page: int = 1, number: int = 10
    ) -> List[SearchResult]:
        """Convenience method to perform search and extract results"""
        return await self.extract_results(kw, page, number)
