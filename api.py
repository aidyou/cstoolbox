import asyncio
import json
import signal
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

from browser import browser_pool
from config import config
from search_extractor import SearchExtractor

# 存储关闭事件
shutdown_event = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """处理应用程序的生命周期事件"""
    global shutdown_event
    try:
        # 创建关闭事件
        shutdown_event = asyncio.Event()
        # 启动时初始化
        await browser_pool.initialize()
        yield
    finally:
        # 关闭时清理
        await browser_pool.close()


# 使用 lifespan 创建 FastAPI 应用
app = FastAPI(lifespan=lifespan)


def signal_handler():
    """处理退出信号"""

    async def _cleanup():
        # 设置关闭事件
        shutdown_event.set()
        # 等待所有任务完成并清理资源
        await browser_pool.close()
        # 停止事件循环
        loop.stop()

    loop = asyncio.get_event_loop()
    loop.create_task(_cleanup())


@app.get("/search")
async def search(
    provider: str = Query(..., description="搜索引擎名称，如 google、bing 等"),
    kw: str = Query(..., description="搜索关键词"),
    page: int = Query(1, description="页码，默认为 1"),
    number: int = Query(10, description="请求查询数，默认为 10"),
) -> JSONResponse:
    extractor = SearchExtractor(provider)
    results = await extractor.search(kw, page=page, number=number)
    return JSONResponse(content=results if results else [])


if __name__ == "__main__":
    # 注册信号处理器
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler())

    # 配置并启动服务器
    config = uvicorn.Config(
        app, host=config.server_host, port=config.server_port, loop="asyncio"
    )
    server = uvicorn.Server(config)
    server.run()
