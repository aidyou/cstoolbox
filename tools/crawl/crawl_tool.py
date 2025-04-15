from core.base_tool import BaseTool
from typing import Any

from .impl.crawl_impl import DataExtractor


class CrawlTool(BaseTool):
    """Crawl tool implementation"""

    @property
    def tool_name(self) -> str:
        return "crawler"

    @property
    def description(self) -> str:
        return "Used to perform web crawl"

    async def execute(self, **kwargs: Any) -> dict:
        """
        Execute crawl operation

        Args:
            url: URL to crawl

        Returns:
            Crawl results dictionary
        """
        url = kwargs["url"]
        format = kwargs["format"]
        if format == "md":
            format = "markdown"
        elif format not in ["markdown", "html"]:
            format = "html"

        extractor = DataExtractor()
        result = await extractor.extract(url, format)
        if result and not result.get("content"):
            return None
        return result
