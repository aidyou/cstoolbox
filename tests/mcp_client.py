from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

project_root = Path(__file__).resolve().parent.parent

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=[f"{project_root}/src/cstoolbox/main.py"],
    env={
        "CS_LOG_LEVEL": "DEBUG",
        "CS_LOG_DIR": "logs",
        "CS_PROXY": "http://localhost:15154",
        "CS_REGION": "com",
        "CS_HEADLESS": "false",
        "CS_BROWSER_TYPE": "chromium",
        "CS_EXECUTABLE_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "CS_USER_DATA_DIR": "/Users/xc/Library/Application Support/Google/Chrome/Default",
    },
)


# Optional: create a sampling callback
async def handle_sampling_message(
    message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write, sampling_callback=handle_sampling_message) as session:
            # Initialize the connection
            await session.initialize()

            # List available tools
            tools = await session.list_tools()

            # Call a tool
            # result = await session.call_tool(
            #     "web_search",
            #     arguments={"provider": "bing", "kw": "天人、阿修罗等六道", "number": 10, "page": 1},
            # )
            # print(result)

            result = await session.call_tool(
                "web_search",
                arguments={
                    "provider": "google",
                    "kw": "deepseek r2, gemini 3, chatgpt 5",
                    "number": 10,
                    "page": 1,
                    "time_period": "month",
                },
            )
            print(result)

            # result = await session.call_tool("web_crawler", arguments={"url": "https://github.com/aidyou/cstoolbox"})
            # print(result)

            # # Call a web crawler tool
            # result = await session.call_tool("web_crawler", arguments={"url": "https://github.com/aidyou/cstoolbox"})
            # print(result)

            # # Call a plot tool
            # result = await session.call_tool(
            #     "plot",
            #     arguments={
            #         "data": {
            #             "x": ["A", "B", "C", "D", "E"],
            #             "y": [1, 4, 9, 16, 25],
            #         },
            #         "plot_type": "line",
            #     },
            # )
            # print(result)

            # # Call a pdf tool
            # result = await session.call_tool("pdf", arguments={"url": "https://arxiv.org/pdf/2501.12948"})
            # print(result)


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
