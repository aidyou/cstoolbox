import aiohttp
import pdfplumber
import os
import tempfile

from typing import Any

from cstoolbox.core.base_tool import BaseTool


class PDFTool(BaseTool):
    """PDF tool implementation"""

    @property
    def tool_name(self) -> str:
        return "pdf"

    @property
    def description(self) -> str:
        return "Download and parse PDF documents"

    async def execute(self, **kwargs: Any) -> dict:
        """
        Download and parse PDF documents

        Args:
            url: URL of the PDF document

        Returns:
            Dictionary containing the plot image URL
        """
        pdf_file = await self.download(kwargs["url"])
        return await self.parse(pdf_file)

    async def download(self, url: str, max_size: int = 100 * 1024 * 1024) -> bytes:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content_length = int(response.headers.get("Content-Length", 0))
                    if content_length > max_size:
                        raise Exception(f"File size {content_length} exceeds the limit {max_size} bytes")
                    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                        async for chunk in response.content.iter_chunked(1024 * 1024):  # 每次读取 1MB
                            tmp_file.write(chunk)
                        return tmp_file.name
                else:
                    raise Exception(f"Failed to download PDF: {response.status}")

    async def parse(self, file_path: str) -> dict:
        try:
            with pdfplumber.open(file_path) as pdf:
                content = []
                tables = []
                for page in pdf.pages:
                    content.append(page.extract_text(x_tolerance=1, y_tolerance=1))
                    page_tables = page.extract_tables()
                    if page_tables:
                        tables.extend(page_tables)
                metadata = pdf.metadata
            return {"content": content, "tables": tables, "metadata": metadata}
        finally:
            if os.path.exists(file_path):
                os.remove(file_path)
