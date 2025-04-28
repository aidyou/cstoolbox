# CSToolbox (ChatSpeed Toolbox)

[简体中文](README-Zh.MD) | English

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

CSToolbox is an extension toolkit for [ChatSpeed](https://github.com/aidyou/chatspeed). It provides features like web search, web content crawling, and chart generation via the MCP protocol.

## Features

- 🔍 **Web Search** - Supports multiple search engines (Google, Bing, Baidu, etc.)
- 🕷️ **Web Crawling** - Extracts structured content from web pages (Supports Markdown/HTML format)
- 📊 **Chart Generation** - Quickly generates various data visualization charts, supporting line charts, bar charts, and pie charts
- 📄 **PDF Processing** - Downloads documents from PDF URLs and extracts text content

## How to Use

### MCP Client Configuration

``` json
{
  "mcpServers": {
    "cstoolbox": {
      "command": "uvx",
      "args": [
        "cstoolbox"
      ],
      "env": {
        "CS_LOG_LEVEL": "DEBUG",
        "CS_LOG_DIR": "logs",
        "CS_PROXY": "http://localhost:15154",
        "CS_BROWSER_TZ": "Asia/Shanghai",
        "CS_BROWSER_LANG": "zh-CN",
        "CS_REGION": "com",
        "CS_HEADLESS": "true",
        "CS_USER_DATA_DIR": null,
        "CS_BROWSER_TYPE": "chromium",
        "CS_EXECUTABLE_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
      }
    }
  }
}
```

#### Environment Variable Descriptions

- `CS_LOG_LEVEL`: Log level. Possible values are `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Defaults to `INFO`.
- `CS_LOG_DIR`: Log directory. Defaults to `logs`.
- `CS_PROXY`: Proxy server address. A proxy is needed in some regions where search engines like `google.com` or `bing.com` are inaccessible. Additionally, some websites have regional restrictions and cannot be accessed without a proxy.
- `CS_BROWSER_TZ`: Timezone. Defaults to `Etc/UTC`.
- `CS_BROWSER_LANG`: Browser language. Defaults to `en-US`.
- `CS_REGION`: Search engine region. Possible values include `com`, `cn`, `us`, `uk`, etc. Defaults to `com`.
- `CS_HEADLESS`: Whether to enable headless mode. Defaults to `true`.
- `CS_BROWSER_TYPE`: Browser type. Possible values are `chromium`, `firefox`, `webkit`. Defaults to `chromium`.
- `CS_EXECUTABLE_PATH`: Browser executable file path. Defaults to empty. You can use this to specify the path to a browser already installed on your system. This allows leveraging the browser's existing state data (like login status, cookies, etc.). If you specify `CS_EXECUTABLE_PATH`, ensure it matches the `CS_BROWSER_TYPE`.
- `CS_USER_DATA_DIR`: User data directory. If you specify `CS_EXECUTABLE_PATH`, it is recommended to set `CS_USER_DATA_DIR` to the parent directory of the browser's "Profile Path".

#### How to find Chrome's Executable Path and Profile Path

1. Open the Chrome browser.
2. Enter `chrome://version/` in the address bar.
3. On the page, you will find the "Executable Path". It will look similar to `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`. This is the path you should set for `CS_EXECUTABLE_PATH`.
4. Find the 'Profile Path', which will look similar to /Users/xxx/Library/Application Support/Google/Chrome/Default. The value for CS_USER_DATA_DIR should be /Users/xxx/Library/Application Support/Google/Chrome (note: this path should exclude the final Default part).

#### ⚠️ Important Notes

- Ensure the proxy is correctly configured when using `google` or `bing` for web searches in certain regions.
- It is best not to set `CS_EXECUTABLE_PATH` to the browser you are currently using, as this can cause conflicts. If you are used to using `google chrome`, you can install other Chromium-based browsers like [Edge](https://www.microsoft.com/en-us/edge/download) or [Brave](https://brave.com/download/). Conversely, if you are used to using the `edge` browser, it is highly recommended that you install [google chrome](https://www.google.com/intl/en_au/chrome/dr/download/).

#### The recommend MCP configuration

``` json
{
  "mcpServers": {
    "cstoolbox": {
      "command": "uvx",
      "args": [
        "cstoolbox"
      ],
      "env": {
        "CS_PROXY": "http://{your-proxy-server}",
        "CS_HEADLESS": "false",
        "CS_BROWSER_TYPE": "chromium",
        "CS_EXECUTABLE_PATH": "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "CS_USER_DATA_DIR": "~/Library/Application Support/Google/Chrome"
      }
    }
  }
}
```

### Python Usage Example

For more Python usage examples, please refer to the `tests/mcp_client.py` file.

```python
from pathlib import Path

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

project_root = Path(__file__).resolve().parent.parent

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",
    args=[f"{project_root}/src/cstoolbox/main.py"],  # Path to cstoolbox mcp main.py
    env={
        "CS_PROXY": "http://localhost:15154",
        "CS_BROWSER_TZ": "Asia/Shanghai",
        "CS_BROWSER_LANG": "zh-CN"
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

            # Call a web search tool
            result = await session.call_tool(
                "web_search",
                arguments={"provider": "bing", "kw": "deepseek r2", "number": 10, "page": 1, "time_period": "month"},
            )
            print(result)

if __name__ == "__main__":
    import asyncio

    asyncio.run(run())

```

## Development

1. Clone the source code repository:

    ```bash
    git clone https://github.com/aidyou/cstoolbox.git
    cd cstoolbox
    ```

2. Install uv
    **macOS/Linux**

    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

    **Windows** Use `irm` to download and install:

    ```bash
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

3. Create and activate a venv environment:

    ```bash
    uv venv --python=python3.12
    source .venv/bin/activate
    # On Windows use: .venv\Scripts\activate
    ```

    *(Note: Added Windows activation command hint for completeness)*

4. Install dependencies:

    ```bash
    uv pip install .
    ```

5. Start the test server:

    ```bash
    mcp dev src/cstoolbox/main.py
    ```

    Now you can perform functional tests via `http://127.0.0.1:6274/#tools`

6. HTTP API Testing
    Add the following configuration to your `.vscode/launch.json` file:

    ```json
    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "http dev",
                "type": "debugpy",
                "request": "launch",
                "module": "cstoolbox.http_api",
                "args": [
                ],
                "console": "integratedTerminal",
                "env": {
                    "PYTHONPATH": "${workspaceFolder}/src",
                    "CS_BROWSER_TZ": "Asia/Shanghai",
                    "CS_BROWSER_LANG": "zh-CN",
                    "CS_LOG_LEVEL": "DEBUG",
                    "CS_PROXY": "http://localhost:15154"
                },
                "python": "${workspaceFolder}/.venv/bin/python"
                // On Windows, adjust python path: "${workspaceFolder}\\.venv\\Scripts\\python.exe"
            }
        ]
    }
    ```

    *(Note: Added Windows python path hint for completeness)*

    Adjust the `CS_*` settings in the `env` configuration according to your actual environment. After starting the debug session in VS Code, you can test using the following endpoints:

    - Search: `curl http://localhost:12321/chp/web_search?provider=google&kw=deepseek+r2&number=10&page=1`
    - Content Crawling: `curl http://localhost:12321/chp/web_crawler?url=https://medium.com/@lbq999/deepseek-r2-is-around-the-corner-c449a41bfec6`

## License

This project is open-sourced under the [MIT License](LICENSE). You are free to use, modify, and distribute this software.
