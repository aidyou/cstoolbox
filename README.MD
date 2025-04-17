# ChatSpeed Toolbox (CSToolbox)

[简体中文](README-Zh.MD) | English

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An extension toolkit for [ChatSpeed](https://github.com/aidyou/chatspeed), providing web search, web content crawling, and chart generation capabilities.

## License

This project is open-sourced under the [MIT License](LICENSE). You are free to use, modify, and distribute this software.

## Features

- 🔍 **Web Search** - Supports multiple search engines (Google, Bing, Baidu, etc.)
- 🕷️ **Web Crawling** - Extracts structured content from web pages (supports Markdown/HTML formats)
- 📊 **Chart Generation** - Quickly generates various data visualization charts, including line charts, bar charts, and pie charts
- 📄 **PDF Processing** - Extracts text content from PDF documents

## Installation

### Docker Installation (Recommended)

```bash
# Quick start
docker run -d \
  --name cstb \
  --restart always \
  -p 12321:12321 \
  -e CS_BROWSER_POOL_MIN_SIZE=2 \
  -e CS_BROWSER_POOL_MAX_SIZE=10 \
  -e CS_REGION=com \
  insuns/cstoolbox:latest
```

### Or using docker-compose

docker-compose.yml

```yaml
services:
  crawler:
    image: insuns/cstoolbox:latest
    container_name: cstb
    working_dir: /app
    command: ["python", "api.py"]
    environment:
      # The port used by the server. If not defined, the default port is 12321.
      # - CS_SERVER_PORT=12321
      #
      # The minimum thread pool created when the browser starts. Enabling the thread pool can accelerate the data crawling speed.
      - CS_BROWSER_POOL_MIN_SIZE = 2
      # The maximum thread pool size allowed for the browser
      - CS_BROWSER_POOL_MAX_SIZE = 10
      # your proxy server for browser
      # - CS_PROXY=http://127.0.0.1:15154
      #
      # region for search engine, com, cn, us, etc. default: com
      # - CS_REGION=com
      #
      # define browser user agent
      # - CS_USER_AGENT = ''
      #
      # define user agent mode, can be "random" or None, If None, use the provided user_agent as-is. Default: None.
      # - CS_USER_AGENT_MODE = None
      #
      # The directory used to store browser data. Usually, it does not need to be defined.
      # If you define an address, it is recommended to mount the local directory.
      # - CS_USER_DATA_DIR = '/path/to/user/data/dir'
      #
      # log level, can be 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
      # - CS_LOG_LEVEL = 'INFO'
      #
      # The screenshot config for playwright. if true, the screenshot will be saved in logs dir.
      # - CS_SCREENSHOT = true

    restart: always
    ports:
      - "127.0.0.1:12321:12321"
```

Execute:

```bash
docker-compose up -d
```

### Conda Installation

1. Clone source code repository:

```bash
git clone https://github.com/aidyou/cstoolbox.git
cd cstoolbox
```

2. Create and activate conda environment:

```bash
conda create -n cstoolbox python=3.8
conda activate cstoolbox
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Start service:

```bash
python api.py
```

## API Usage

### Example Calls

```python
import requests

# Web search
response = requests.post("http://localhost:12321/chp/web_search", json={
    "provider": "google",
    "kw": "artificial intelligence",
    "page": 1,
    "number": 10
})

# Web crawling
response = requests.get("http://localhost:12321/chp/web_crawler", params={
    "url": "https://example.com",
    "format": "markdown"
})

# Chart generation
response = requests.post("http://localhost:12321/chp/plot", json={
    "plot_type": "bar",
    "data": {"x": [1,2,3], "y": [4,5,6]},
    "title": "Example Chart"
})

# Download and parse PDF
response = requests.get("http://localhost:12321/chp/pdf", params={
    "url": "https://domain.com/path/to/file.pdf"
})
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Start development server
python api.py
```

## Future Plans

The current version is transitional. Future versions will integrate with [Chatspeed](https://github.com/aidyou/chatspeed) to add MCP protocol support.

### Protocol Upgrade to MCP

⚠️ Important Change: To enhance system performance and expandability, we plan to add MCP (Model Context Protocol) support in the next major version (v0.2). Existing APIs will remain unaffected, while new interfaces will fully adopt the MCP protocol.
