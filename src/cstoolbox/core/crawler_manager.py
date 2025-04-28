import asyncio
import os
from datetime import datetime, timedelta

from cstoolbox.browser.config import BrowserConfig, BrowserType
from cstoolbox.browser.crawler import Crawler
from cstoolbox.browser.pool import BrowserPool
from cstoolbox.config import config
from cstoolbox.logger import get_logger

logger = get_logger(__name__)


class CrawlerManager:
    """Dynamic browser pool, supports auto expansion/shrinkage and health check"""

    def __init__(self):
        extra_args = []
        lang = config.browser_lang
        timezone = self._detect_timezone()

        if not config.executable_path:
            if not lang:
                lang = "en-US"
            if not config.browser_timezone:
                timezone = "Etc/UTC"

        if lang:
            extra_args.append(f"--lang={lang}")
        if timezone:
            extra_args.append(f"--timezone={timezone}")

        self.idle_timeout = timedelta(seconds=300)  # Idle instance timeout

        # pool status
        self._lock = asyncio.Lock()

        # browser config
        logger.info(f"Set Browser Env: proxy: {config.proxy}, lang: {lang}, timezone: {timezone}")
        self.browser_config = BrowserConfig(
            type=config.browser_type or BrowserType.CHROMIUM,
            headless=config.headless.lower() == "true",
            proxy=config.proxy,
            user_data_dir=config.user_data_dir,
            text_mode=True,
            executable_path=config.executable_path,
            extra_args=extra_args,
        )
        self.pool = BrowserPool(self.browser_config)
        self.crawler = Crawler(self.pool)

    def _detect_timezone(self) -> str:
        """
        Auto detect timezone
        """
        # Get timezone from environment variables
        if config.browser_timezone:
            return config.browser_timezone

        # Try to get timezone from /etc/timezone file
        try:
            with open('/etc/timezone') as f:
                return f.read().strip()
        except FileNotFoundError:
            pass

        # Get system current timezone
        return datetime.now().astimezone().tzinfo.tzname(None) or 'Etc/UTC'

    def initialize(self):
        """Initialize browser pool"""
        asyncio.run(self.pool.initialize())

    def get_crawler(self):
        """Get browser instance context manager"""
        return BrowserContext(self)

    async def close(self):
        """Close browser pool"""
        if self.pool:
            await self.pool.close()


class BrowserContext:
    """Browser instance context manager"""

    def __init__(self, manager: CrawlerManager):
        self.manager = manager

    async def __aenter__(self) -> Crawler:
        return self.manager.crawler

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Return browser instance to pool"""
        pass


# Global browser pool instance
crawler_manager = CrawlerManager()
# asyncio.run(crawler_manager.pool.initialize())
