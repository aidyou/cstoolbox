"""
Browser core implementation for Playwright-based web crawling.

Contains:
- BrowserPool class
"""

import asyncio
from typing import Optional

from playwright.async_api import Browser, BrowserContext, Page

from .config import BrowserConfig, PageConfig
from .playwright_manager import PlaywrightManager
from cstoolbox.config import server_root
from cstoolbox.logger import get_logger

logger = get_logger(__name__)


class BrowserPool:
    """Browser pool for managing browser instances"""

    def __init__(self, config: BrowserConfig):
        self.playwright_manager = PlaywrightManager(config)

        self._browser_context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()

    async def _get_context(self) -> BrowserContext:
        """Get or create context instance with health check"""
        async with self._lock:
            if self._browser_context is None or (
                self._browser_context.browser is not None and not self._browser_context.browser.is_connected()
            ):
                if self._browser_context:
                    await self._browser_context.close()
                    self._browser_context = None
                self._browser_context = await self.playwright_manager.launch_browser()
                await self._browser_context.add_init_script(
                    script='Object.defineProperty(navigator, "webdriver", {get: () => false,});'
                )
                logger.info(f"Browser context created: {self.playwright_manager.config.type}")
        return self._browser_context

    # async def initialize(self):
    #     """Initialize browser and context"""
    #     try:
    #         page = await self.new_page(PageConfig())
    #         page.goto(f"https://www.bing.com")
    #     except Exception as e:
    #         logger.warning(f"Error initializing browser: {e}")
    #     finally:
    #         if page:
    #             await page.close()

    async def new_page(self, config: PageConfig) -> Page:
        """Create new page with given configuration and health check"""
        context = await self._get_context()
        page = await context.new_page()

        await page.set_extra_http_headers(
            {'Cache-Control': 'no-cache, no-store, must-revalidate', 'Pragma': 'no-cache', 'Expires': '0'}
        )

        if not config.wait_until or not config.wait_until in ['domcontentloaded', 'load', 'networkidle']:
            config.wait_until = 'domcontentloaded'
        await page.wait_for_load_state(config.wait_until, timeout=config.wait_timeout)

        if config.page_timeout:
            page.set_default_timeout(config.page_timeout)

        if config.init_js_code:
            await page.add_init_script(script=config.init_js_code)

        return page

    async def close(self):
        """Close browser and context"""
        if self._browser_context:
            try:
                if self._browser_context.browser.is_connected():
                    await self._browser_context.browser.close()
                await self._browser_context.close()
            except Exception as e:
                logger.warning(f"Error closing browser context: {e}")
            finally:
                self._browser_context = None
