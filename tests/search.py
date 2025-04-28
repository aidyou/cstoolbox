import asyncio

from cstoolbox.browser.pool import BrowserPool
from cstoolbox.browser.config import BrowserConfig
from cstoolbox.browser.crawler import CrawlerConfig, Crawler


async def main():
    pool = BrowserPool(BrowserConfig(headless=True, text_mode=True, proxy='http://127.0.0.1:15154'))
    crawl = Crawler(pool)
    config = CrawlerConfig(
        name="bing",
        wait_untilr="domcontentloaded",
        wait_for='body',
        base_selector="#b_results > li.b_algo",
        fields=[
            {"name": "sitename", "selector": ".tilk", "type": "attribute", "attribute": "aria-label"},
            {"name": "title", "selector": "h2 a", "type": "text"},
            {"name": "url", "selector": "h2 a", "type": "attribute", "attribute": "href"},
            {"name": "summary", "selector": ".b_caption p", "type": "text"},
        ],
    )
    result = await crawl.crawl(
        'https://www.bing.com/search?q=deepseek+r2&form=QBLH&sp=-1&ghc=1&lq=0&pq=deepseek+r&sc=12-10&qs=n&sk=',
        config,
    )
    print(result.results)


if __name__ == "__main__":
    asyncio.run(main())
