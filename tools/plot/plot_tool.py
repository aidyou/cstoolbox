import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

import hashlib
import os

from datetime import datetime
from typing import Any

from config.config import server_host, server_port
from core.base_tool import BaseTool


class PlotTool(BaseTool):
    """Plot tool implementation"""

    @property
    def tool_name(self) -> str:
        return "plotter"

    @property
    def description(self) -> str:
        return "Used to generate plots (line, bar, pie)"

    async def execute(self, **kwargs: Any) -> dict:
        """
        Generate a plot based on the provided data and type

        Args:
            plot_type: Type of plot (line, bar, pie)
            data: Dictionary containing plot data
            title: Plot title
            x_label: Label for x-axis
            y_label: Label for y-axis

        Returns:
            Dictionary containing the plot image URL
        """
        plot_type = kwargs.get("plot_type", "line")
        data = kwargs["data"]

        sign_str = []
        plt.figure()
        if plot_type == "line":
            plt.plot(data["x"], data["y"])
        elif plot_type == "bar":
            plt.bar(data["x"], data["y"])
        elif plot_type == "pie":
            plt.pie(data["values"], labels=data["labels"])
        else:
            raise ValueError("Invalid plot type, must be line, bar, or pie")

        if kwargs.get("title"):
            plt.title(kwargs["title"])
        if kwargs.get("x_label"):
            plt.xlabel(kwargs["x_label"])
        if kwargs.get("y_label"):
            plt.ylabel(kwargs["y_label"])

        # 生成唯一文件名
        sign_str = []
        sign_str.append(str(kwargs.get("plot_type", "line")))
        sign_str.append(str(kwargs.get("data", {})))
        sign_str.append(str(kwargs.get("title", "")))
        sign_str.append(str(kwargs.get("x_label", "")))
        sign_str.append(str(kwargs.get("y_label", "")))

        # 生成MD5签名
        signature = hashlib.md5("".join(sign_str).encode()).hexdigest()
        filename = f"{signature}.png"
        filepath = os.path.join("static", "imgs", filename)

        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 保存图表到文件
        plt.savefig(filepath)
        plt.close()

        # 返回图表URL
        return {"url": f"http://{server_host}:{server_port}/static/imgs/{filename}"}


async def __main():
    plotter = PlotTool()

    # 生成曲线图
    line_data = {"x": [1, 2, 3, 4], "y": [10, 20, 25, 30]}
    line_plot = await plotter.execute(
        plot_type="line",
        data=line_data,
        title="Line Plot",
        x_label="X Axis",
        y_label="Y Axis",
    )

    # 生成柱状图
    bar_data = {"x": ["A", "B", "C"], "y": [15, 25, 30]}
    bar_plot = await plotter.execute(
        plot_type="bar",
        data=bar_data,
        title="Bar Plot",
        x_label="Categories",
        y_label="Values",
    )

    # 生成饼图
    pie_data = {"values": [30, 40, 20, 10], "labels": ["A", "B", "C", "D"]}
    pie_plot = await plotter.execute(plot_type="pie", data=pie_data, title="Pie Chart")

    print(line_plot)
    print(bar_plot)
    print(pie_plot)


if __name__ == "__main__":
    asyncio.run(__main())
