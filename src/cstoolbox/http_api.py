import asyncio
import signal
import uvicorn

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter, HTTPException, Request, Query, status, Body
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from urllib.parse import unquote, urlparse

from .core import crawler_manager
from .config import config
from .http_api_helper import fail, success
from .mcp_helper import signal_handler, get_baidu_time_period, get_bing_time_period
from .tools.crawl import SearchTool, CrawlTool
from .tools.plot import PlotTool
from .tools.pdf import PDFTool

# shutdown event
shutdown_event = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application lifecycle events"""
    global shutdown_event
    try:
        # Create the shutdown event
        shutdown_event = asyncio.Event()
        yield
    finally:
        # Clean up resources when closing
        await crawler_manager.close()


# Create router with /chp prefix
router = APIRouter(prefix="/chp")
# Use lifespan to create FastAPI application
app = FastAPI(lifespan=lifespan)


@router.post("/plot")
async def plot(
    plot_type: str = Body(..., description="Type of plot (line, bar, pie)"),
    data: dict = Body(..., description="Plot data"),
    title: str = Body("", description="Plot title"),
    x_label: str = Body("", description="Label for x-axis"),
    y_label: str = Body("", description="Label for y-axis"),
) -> JSONResponse:
    plot_tool = PlotTool()
    result = await plot_tool.execute(
        plot_type=plot_type,
        data=data,
        title=title,
        x_label=x_label,
        y_label=y_label,
    )
    return success(data=result)


@router.get("/web_search")
async def web_search(
    provider: str = Query(..., description="Search engine name, such as google, bing, etc."),
    kw: str = Query(..., description="Search keyword"),
    page: int = Query(1, description="Page number, default is 1"),
    number: int = Query(10, description="Number of requests, default is 10"),
    time_period: str = Query(
        "",
        description="Time range, such as day (one day ago), week (one week ago), month (one month ago), year (one year ago)",
    ),
) -> JSONResponse:
    """
    Search data through search engine and return search results
    Note: /chp prefix is automatically mapped when chatspeed calls, do not remove

    Args:
        provider (str, optional): Search engine name. Available providers: google google_news, bing, baidu, baidu_news.
        kw (str, optional): Keyword.
        page (int, optional): Page number. Defaults to 1.
        number (int, optional): Number of requests. Defaults to 10.

    Returns:
        JSONResponse: Search results.
    """
    # Set time range parameter based on different search engine
    if time_period:
        if provider == "baidu":
            time_period = get_baidu_time_period(time_period)
        elif provider == "baidu_news":
            time_period = ""
        elif provider == "google":
            time_period = f"qdr:{time_period[0]}"  # day -> d, week -> w, month -> m, year -> y
        elif provider == "google_news":
            time_period = f"qdr:{time_period[0]}"
        elif provider == "bing":
            time_period = get_bing_time_period(time_period)
    try:
        search_tool = SearchTool()
        results = await search_tool.execute(provider=provider, kw=kw, page=page, number=number, time_period=time_period)
        return success(data=results if results else [])
    except Exception as e:
        return fail(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/web_crawler")
async def web_crawler(
    url: str = Query(..., description="Data extraction URL"),
    format: str = Query("markdown", description="Output format, markdown or html"),
    remove_link: bool = Query(True, description="Whether to remove links from the extracted content"),
) -> JSONResponse:
    """
    Extract data from the provided URL and return the result
    Note: /chp prefix is automatically mapped when chatspeed calls, do not remove

    Args:
        url (str, optional): Data extraction URL.
        format (str, optional): Output format, markdown or html. Defaults to markdown.

    Raises:
        HTTPException: If extraction fails

    Returns:
        JSONResponse: Extraction result
    """
    try:
        # URL decode
        decoded_url = unquote(url)
        lower_url = decoded_url.lower()
        UNSUPPORTED_EXTENSIONS = {
            # 文档类型
            ".pdf",
            ".doc",
            ".docx",
            ".xls",
            ".xlsx",
            # 图片类型
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".svg",
            ".ico",
            ".bmp",
            ".tiff",
            # 音频/视频类型
            ".mp3",
            ".mp4",
            ".flv",
            ".webm",
            ".m3u8",
            ".mov",
            ".wmv",
            ".avi",
            ".asf",
            ".asx",
            ".rm",
            ".rmvb",
            ".mkv",
        }

        if any(lower_url.endswith(ext) for ext in UNSUPPORTED_EXTENSIONS):
            return fail(
                message="Unsupported file type. Cannot extract data from media files",
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # Validate URL format
        parsed_url = urlparse(decoded_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid URL format")

        crawl_tool = CrawlTool()
        results = await crawl_tool.execute(url=decoded_url, format=format, remove_link=remove_link)

        if not results:
            return fail(
                message="Unable to extract data from the specified URL",
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return success(data=results)

    except HTTPException as he:
        return fail(message=he.detail, status_code=he.status_code)
    except Exception as e:
        return fail(message=str(e), status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)


@router.get("/pdf")
async def pdf(
    url: str = Query(..., description="URL of the PDF document"),
) -> JSONResponse:
    pdf_tool = PDFTool()
    result = await pdf_tool.execute(url=url)
    return success(data=result)


@app.get("/ping")
async def ping() -> JSONResponse:
    return success(data={"ping": "pong"})


# Register router with the app after all endpoints are defined
app.include_router(router)


# Custom 404 handler
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc: HTTPException):
    return fail(
        message="The requested interface does not exist",
        detail=f"Path {request.url.path} is undefined",
        status_code=404,
        add_error_status_code=True,
    )


if __name__ == "__main__":
    # Register signal handlers
    for sig in (signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, lambda s, f: signal_handler())

    # Configure and start server
    config = uvicorn.Config(app, host='127.0.0.1', port=12321, loop="asyncio")
    server = uvicorn.Server(config)
    server.run()
