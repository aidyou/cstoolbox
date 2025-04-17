import os
import asyncio
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

from logger import get_logger
from config import config

logger = get_logger(__name__)


class DynamicBrowserPool:
    """Dynamic browser pool, supports auto expansion/shrinkage and health check"""

    def __init__(self):
        logger.debug(f"Proxy: {config.proxy}")

        # min size pool
        self.min_size = int(config.browser_pool_min_size)
        self.max_size = int(config.browser_pool_max_size)
        self.idle_timeout = timedelta(seconds=300)  # Idle instance timeout

        # pool status
        self.pool = asyncio.Queue(maxsize=self.max_size)
        self._active_count = 0  # Total active instances (including in use and idle)
        self._last_used = {}  # Instance last used time {crawler: timestamp}
        self._initialized = False
        self._lock = asyncio.Lock()
        self._cleanup_task = None  # Background cleanup task

        # health check url
        self.health_check_url = "http://127.0.0.1:" + str(config.server_port) + "/ping"

        # browser config
        self.browser_config = BrowserConfig(
            browser_type="chromium",
            headless=config.headless == "true",
            user_agent=config.user_agent,
            user_agent_mode=config.user_agent_mode,
            proxy=config.proxy,
            user_data_dir=config.user_data_dir,
            text_mode=True,
            light_mode=True,
            viewport_width=1080,
            viewport_height=600,
            extra_args=[
                "--disable-extensions",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-software-rasterizer",
                "--disable-accelerated-2d-canvas",
                "--disable-accelerated-jpeg-decoding",
                "--disable-accelerated-video-decode",
                "--disable-background-networking",
                "--disable-sync",
                "--disable-default-apps",
                "--js-flags=--max-old-space-size=512",
                "--remote-debugging-port=0",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--no-sandbox",
                "--start-maximized",
                "--disable-web-security",
                "--disable-component-extensions-with-background-pages",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-background-timer-throttling",
                "--disable-ipc-flooding-protection",
                "--disable-hang-monitor",
                "--disable-popup-blocking",
                "--disable-prompt-on-repost",
                "--disable-client-side-phishing-detection",
                "--disable-crash-reporter",
                "--disable-ntp-popular-sites",
                "--disable-translate",
                "--disable-search-engine-choice-screen",
            ],
            verbose=True,
        )

    async def initialize(self):
        """Initialize browser pool"""
        async with self._lock:
            if self._initialized:
                return

            # Initialize minimum instances
            for _ in range(self.min_size):
                crawler = await self._create_crawler()
                await self._safe_put(crawler)

            # Start background cleanup task
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            self._initialized = True

    async def _create_crawler(self) -> AsyncWebCrawler:
        """Create and initialize browser instance"""
        crawler = AsyncWebCrawler(config=self.browser_config)
        await crawler.start()
        self._active_count += 1
        logger.debug(f"Created new browser instance. Total active: {self._active_count}")
        return crawler

    async def _destroy_crawler(self, crawler: AsyncWebCrawler):
        """Destroy browser instance"""
        try:
            await crawler.close()
            self._active_count -= 1
            logger.debug(f"Destroyed browser instance. Total active: {self._active_count}")
        except Exception as e:
            logger.error(f"Error destroying crawler: {e}")

    async def _safe_put(self, crawler: AsyncWebCrawler):
        """Safe return instance to pool"""
        if self.pool.full():
            await self._destroy_crawler(crawler)  # Exceed capacity, destroy
        else:
            self._last_used[crawler] = datetime.now()
            await self.pool.put(crawler)

    async def _background_cleanup(self):
        """Background cleanup idle timeout instances"""
        while self._initialized:
            await asyncio.sleep(60)  # Check every minute
            try:
                now = datetime.now()
                # Temporarily save current pool instances
                temp = []
                while not self.pool.empty():
                    crawler = self.pool.get_nowait()
                    temp.append(crawler)

                # Cleanup idle timeout instances
                for crawler in temp:
                    last_used = self._last_used.get(crawler, now)
                    if (now - last_used) > self.idle_timeout and self._active_count > self.min_size:
                        await self._destroy_crawler(crawler)
                    else:
                        await self.pool.put(crawler)  # Re-put back to pool
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")

    async def _get(self) -> AsyncWebCrawler:
        """Get browser instance (auto expand)"""
        try:
            # Try to get from pool first
            return self.pool.get_nowait()
        except asyncio.QueueEmpty:
            # Create new instance when pool is empty
            if self._active_count < self.max_size:
                return await self._create_crawler()
            # Wait when reached limit
            return await self.pool.get()

    async def _put(self, crawler: AsyncWebCrawler):
        """Return browser instance to pool (auto shrink)"""
        # Health check
        if not await self._is_healthy(crawler):
            await self._destroy_crawler(crawler)
            return

        # Return instance to pool
        await self._safe_put(crawler)

    async def _is_healthy(self, crawler: AsyncWebCrawler) -> bool:
        """Health check"""
        try:
            # 通过访问空白页验证实例健康状态
            result = await crawler.arun(
                url=self.health_check_url,
                config=CrawlerRunConfig(page_timeout=5000, verbose=False),
            )
            return result is not None
        except Exception as e:
            logger.warning(f"Browser instance unhealthy: {e}")
            return False

    def get_crawler(self):
        """Get browser instance context manager"""
        return BrowserContext(self)

    async def close(self):
        """Close all resources"""
        self._initialized = False
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # Empty the pool
        while not self.pool.empty():
            crawler = await self.pool.get()
            await self._destroy_crawler(crawler)


class BrowserContext:
    """Browser instance context manager"""

    def __init__(self, pool: DynamicBrowserPool):
        self.pool = pool
        self.crawler = None

    async def __aenter__(self) -> AsyncWebCrawler:
        """Get browser instance"""
        self.crawler = await self.pool._get()
        logger.debug("Acquired browser instance")
        return self.crawler

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Return browser instance to pool"""
        if self.crawler:
            await self.pool._put(self.crawler)
            logger.debug("Returned browser instance")


# Global browser pool instance
browser_pool = DynamicBrowserPool()
