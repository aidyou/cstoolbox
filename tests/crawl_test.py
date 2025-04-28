import asyncio

from cstoolbox.browser.pool import BrowserPool
from cstoolbox.browser.config import BrowserConfig
from cstoolbox.browser.crawler import CrawlerConfig, Crawler


async def main():
    pool = BrowserPool(
        BrowserConfig(
            headless=True,
        )
    )
    crawl = Crawler(pool)
    config = CrawlerConfig(
        name="weixin",
        wait_untilr="domcontentloaded",
        wait_for='#js_content',
        base_selector="",
        fields=[
            {"name": "title", "selector": "h1", "type": "text"},
            {"name": "content", "selector": "#js_content", "type": "markdown", "remove_link": True, "remove_img": True},
        ],
    )
    result = await crawl.crawl('https://mp.weixin.qq.com/s/T1T5ggchwj3H9LqTo0qLtg', config)
    print(result.results["title"])
    print(result.results["content"])


if __name__ == "__main__":
    asyncio.run(main())
