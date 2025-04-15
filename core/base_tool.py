from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Base tool class, all tools should inherit this class"""

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict:
        """
        Execute the main logic of the tool

        Args:
            **kwargs: Keyword arguments required for tool execution

        Returns:
            Tool execution result
        """
        pass

    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return tool name"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Return tool description"""
        pass
