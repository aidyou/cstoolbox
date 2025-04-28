from typing import Any

from cstoolbox.core.base_tool import BaseTool
from .impl.search_impl import SearchExtractor


class SearchTool(BaseTool):
    """Search tool implementation"""

    @property
    def tool_name(self) -> str:
        return "search"

    @property
    def description(self) -> str:
        return "Used to perform web search"

    async def execute(self, **kwargs: Any) -> dict:
        """
        Execute search operation

        Args:
            provider: Search engine name
            kw: Search keyword
            page: Page number, default is 1
            number: Number of results per page, default is 10
            time_period: Time range, default is empty

        Returns:
            Search results dictionary
        """
        provider = kwargs["provider"]
        kw = kwargs["kw"]
        page = kwargs.get("page", 1)
        number = kwargs.get("number", 10)
        time_period = kwargs.get("time_period", "")

        extractor = SearchExtractor(provider)
        return await extractor.search(kw, page=page, number=number, time_period=time_period)
