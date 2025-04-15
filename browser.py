import os
import asyncio
import json
import logging
from datetime import datetime, timedelta
from crawl4ai import AsyncWebCrawler
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

logger = logging.getLogger(__name__)

from config import config


class DynamicBrowserPool:
    """动态浏览器池，支持自动扩容/缩容和健康检查"""

    def __init__(self):
        # 池配置
        self.min_size = int(
            os.getenv("BROWSER_POOL_MIN_SIZE", config.browser_pool_min_size)
        )
        self.max_size = int(
            os.getenv("BROWSER_POOL_MAX_SIZE", config.browser_pool_max_size)
        )
        self.idle_timeout = timedelta(seconds=300)  # 空闲实例超时时间

        # 池状态
        self.pool = asyncio.Queue(maxsize=self.max_size)
        self._active_count = 0  # 总活跃实例数（包括使用中和空闲）
        self._last_used = {}  # 实例最后使用时间 {crawler: timestamp}
        self._initialized = False
        self._lock = asyncio.Lock()
        self._cleanup_task = None  # 后台清理任务

        # 用来浏览器健康度检查地址
        self.health_check_url = os.getenv("HEALTH_CHECK_URL", config.health_check_url)
        # 浏览器配置
        proxy = os.getenv("PROXY", config.proxy)
        self.browser_config = BrowserConfig(
            browser_type=os.getenv("BROWSER_TYPE", config.browser_type),
            headless=os.getenv("HEADLESS", config.headless) == "true",
            user_agent=os.getenv("USER_AGENT", config.user_agent),
            proxy=proxy,
            proxy_config=config.proxy_config if not proxy else None,
            user_data_dir=os.getenv("USER_DATA_DIR", config.user_data_dir),
            verbose=True,
        )

    async def initialize(self):
        """初始化浏览器池"""
        async with self._lock:
            if self._initialized:
                return

            # 初始化最小实例
            for _ in range(self.min_size):
                crawler = await self._create_crawler()
                await self._safe_put(crawler)

            # 启动后台清理任务
            self._cleanup_task = asyncio.create_task(self._background_cleanup())
            self._initialized = True

    async def _create_crawler(self) -> AsyncWebCrawler:
        """创建并初始化浏览器实例"""
        crawler = AsyncWebCrawler(config=self.browser_config)
        await crawler.start()
        self._active_count += 1
        logger.debug(
            f"Created new browser instance. Total active: {self._active_count}"
        )
        return crawler

    async def _destroy_crawler(self, crawler: AsyncWebCrawler):
        """销毁浏览器实例"""
        try:
            await crawler.close()
            self._active_count -= 1
            logger.debug(
                f"Destroyed browser instance. Total active: {self._active_count}"
            )
        except Exception as e:
            logger.error(f"Error destroying crawler: {e}")

    async def _safe_put(self, crawler: AsyncWebCrawler):
        """安全归还实例到池中"""
        if self.pool.full():
            await self._destroy_crawler(crawler)  # 超过容量直接销毁
        else:
            self._last_used[crawler] = datetime.now()
            await self.pool.put(crawler)

    async def _background_cleanup(self):
        """后台清理空闲超时实例"""
        while self._initialized:
            await asyncio.sleep(60)  # 每分钟检查一次
            try:
                now = datetime.now()
                # 临时保存当前池中的实例
                temp = []
                while not self.pool.empty():
                    crawler = self.pool.get_nowait()
                    temp.append(crawler)

                # 清理超时实例
                for crawler in temp:
                    last_used = self._last_used.get(crawler, now)
                    if (
                        now - last_used
                    ) > self.idle_timeout and self._active_count > self.min_size:
                        await self._destroy_crawler(crawler)
                    else:
                        await self.pool.put(crawler)  # 重新放回池中
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")

    async def _get(self) -> AsyncWebCrawler:
        """获取浏览器实例（自动扩容）"""
        try:
            # 优先从池中获取
            return self.pool.get_nowait()
        except asyncio.QueueEmpty:
            # 池为空时动态创建新实例
            if self._active_count < self.max_size:
                return await self._create_crawler()
            # 达到上限则等待
            return await self.pool.get()

    async def _put(self, crawler: AsyncWebCrawler):
        """归还实例到池中（自动缩容）"""
        # 健康检查
        if not await self._is_healthy(crawler):
            await self._destroy_crawler(crawler)
            return

        # 归还实例
        await self._safe_put(crawler)

    async def _is_healthy(self, crawler: AsyncWebCrawler) -> bool:
        """健康检查"""
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
        """获取浏览器实例的上下文管理器"""
        return BrowserContext(self)

    async def close(self):
        """关闭所有资源"""
        self._initialized = False
        if self._cleanup_task:
            self._cleanup_task.cancel()

        # 清空池
        while not self.pool.empty():
            crawler = await self.pool.get()
            await self._destroy_crawler(crawler)


class BrowserContext:
    """浏览器实例的上下文管理器"""

    def __init__(self, pool: DynamicBrowserPool):
        self.pool = pool
        self.crawler = None

    async def __aenter__(self) -> AsyncWebCrawler:
        """获取浏览器实例"""
        self.crawler = await self.pool._get()
        logger.debug("Acquired browser instance")
        return self.crawler

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """归还浏览器实例"""
        if self.crawler:
            await self.pool._put(self.crawler)
            logger.debug("Returned browser instance")


# 全局浏览器池实例
browser_pool = DynamicBrowserPool()
