from mcp.server.fastmcp import FastMCP
from urllib.parse import unquote, urlparse

from pydantic import Field
from typing import Literal

from cstoolbox.core.crawler_manager import crawler_manager
from cstoolbox.mcp_helper import fail, success, signal_handler, get_baidu_time_period, get_bing_time_period
from cstoolbox.tools.crawl import SearchTool, CrawlTool
from cstoolbox.tools.plot import PlotTool
from cstoolbox.tools.pdf import PDFTool

# Create MCP server instance
mcp = FastMCP("CSToolbox")


@mcp.tool(description="Perform web search using the specified search engine provider")
async def web_search(
    provider: Literal["google", "bing", "baidu", "google_news", "baidu_news"] = Field(
        "bing", description="Name of provider"
    ),
    kw: str = Field(..., description="Keywords for search"),
    page: int = Field(1, ge=1, le=10, description="Page number"),
    number: int = Field(10, ge=1, le=50, description="Search results per page"),
    time_period: Literal["day", "week", "month", "year", ""] = Field(
        "", description="Time range filter. Default: empty (no time filter)."
    ),
) -> dict:
    """
    Perform web search using specified provider

    Args:
        provider (str):
            Search engine name. Supported values:
            - "google" (General search)
            - "bing" (General search)
            - "baidu" (中文搜索)
            - "google_news" (Google News)
            - "baidu_news" (百度新闻)
        kw (str):
            Search keyword. Example: "AI trends 2024"
        page (int, optional):
            Page number for paginated results. Default: 1. Max: 10.
        number (int, optional):
            Number of results per page. Default: 10. Max: 50.
        time_period (str, optional):
            Filter results by time range. Valid options:
            - "day" (Last 24 hours)
            - "week" (Last week)
            - "month" (Last month)
            - "year" (Last year)
            Default: empty (no time filter)

    Returns:
        dict - Search results in dictionary format
    """
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
        return fail(message="Error performing web search", detail=str(e), status_code=500)


@mcp.tool(description="Extract and return structured data from the provided URL")
async def web_crawler(
    url: str = Field(..., description="Url to extract data"),
    format: Literal["markdown", "html"] = Field("markdown", description="Data format"),
    remove_link: bool = Field(True, description="Whether to remove links from the content"),
) -> dict:
    """
    Extract data from the provided URL and return the result

    Args:
        url (str, optional): Data extraction URL.
        format (str, optional): Output format, markdown or html. Defaults to markdown.
        remove_link (bool, optional): Whether to remove links from the content. Defaults to True.

    Raises:
        HTTPException: If extraction fails

    Returns:
        dict: Extraction result
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
                status_code=415,
            )

        # Validate URL format
        parsed_url = urlparse(decoded_url)
        if not all([parsed_url.scheme, parsed_url.netloc]):
            return fail(message="Invalid URL format", status_code=400)

        crawl_tool = CrawlTool()
        results = await crawl_tool.execute(url=decoded_url, format=format, remove_link=remove_link)

        if not results:
            return fail(
                message="Unable to extract data from the specified URL",
                status_code=500,
            )

        return success(data=results)

    except Exception as e:
        return fail(message="Error performing web crawler", detail=str(e), status_code=500)


@mcp.tool(description="Download PDF file and extract its textual content")
async def pdf(
    url: str = Field(..., description="URL of the PDF document"),
) -> dict:
    try:
        pdf_tool = PDFTool()
        result = await pdf_tool.execute(url=url)
        return success(data=result)
    except Exception as e:
        return fail(message="Error performing pdf extract", detail=str(e), status_code=500)


@mcp.tool(description="Generate data visualization using specified plot type")
async def plot(
    plot_type: Literal["line", "bar", "pie"] = Field(..., description="Type of plot"),
    data: dict = Field(
        ...,
        description="Plot data, e.g., {'x': [1, 2], 'y': [4, 5]} for line or bar, {'labels': ['A', 'B'], 'values': [30, 70]} for pie",
    ),
    title: str = Field("", description="Plot title"),
    x_label: str = Field("", description="Label for x-axis"),
    y_label: str = Field("", description="Label for y-axis"),
) -> dict:
    try:
        plot_tool = PlotTool()
        result = await plot_tool.execute(
            plot_type=plot_type,
            data=data,
            title=title,
            x_label=x_label,
            y_label=y_label,
        )
        return success(data=result)
    except Exception as e:
        return fail(message="Error performing plot", detail=str(e), status_code=500)


def main():
    # Register signal handler for cleanup
    signal_handler()

    try:
        mcp.run()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
