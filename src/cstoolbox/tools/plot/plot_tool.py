import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from typing import Any

from cstoolbox.core.base_tool import BaseTool


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

        # 保存图表到内存缓冲区
        from io import BytesIO
        import base64

        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()

        # 编码为base64字符串
        img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

        # 返回base64图像数据
        return {"url": f"data:image/png;base64,{img_base64}"}


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
