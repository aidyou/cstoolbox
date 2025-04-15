# ChatSpeed Toolbox (CSToolbox)

简体中文 | [English](README.MD)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

作为 [ChatSpeed](https://github.com/aidyou/chatspeed) 的扩展工具集，提供网络搜索、网页内容爬取和图表生成等功能。

## 协议

本项目采用 [MIT 协议](LICENSE) 开源，您可以自由使用、修改和分发本软件。

## 功能特性

- 🔍 **网络搜索** - 支持多种搜索引擎（Google、Bing、百度等）
- 🕷️ **网页爬取** - 从网页提取结构化内容（支持 Markdown/HTML 格式）
- 📊 **图表生成** - 快速生成各类数据可视化图表，支持曲线图、柱状图和饼图
- 📄 **PDF处理** - 从PDF文档提取文本内容

## 安装方式

### Docker 安装（推荐）

```bash
# 快速启动
docker run -d \
  -p 12321:12321 \
  -e BROWSER_POOL_MIN_SIZE=2 \
  -e BROWSER_POOL_MAX_SIZE=10 \
  -e REGION=com \
  insuns/cstoolbox:latest
```

### 或使用 docker-compose

docker-compose.yml

```yaml
services:
  crawler:
    image: insuns/cstoolbox:latest
    working_dir: /app
    command: ["python", "api.py"]
    environment:
      # The minimum thread pool created when the browser starts. Enabling the thread pool can accelerate the data crawling speed.
      - BROWSER_POOL_MIN_SIZE = 2
      # The maximum thread pool size allowed for the browser
      - BROWSER_POOL_MAX_SIZE = 10
      # you proxy server
      # - PROXY=http://127.0.0.1:15154
      # region for search engine
      - REGION=com
      #
      # define browser user agent
      # - USER_AGENT = ''
      #
      # define user agent mode, can be "random" or None, If None, use the provided user_agent as-is. Default: None.
      # - USER_AGENT_MODE = None
      #
      # The directory used to store browser data. Usually, it does not need to be defined.
      # If you define an address, it is recommended to mount the local directory.
      # - USER_DATA_DIR = '/path/to/user/data/dir'
    restart: always
    ports:
      - "127.0.0.1:12321:12321"
```

执行:

```bash
docker-compose up -d
```

### Conda 安装

1. 克隆源代码仓库:

```bash
git clone https://github.com/aidyou/cstoolbox.git
cd cstoolbox
```

2. 创建并激活conda环境:

```bash
conda create -n cstoolbox python=3.10
conda activate cstoolbox
```

3. 安装依赖:

```bash
pip install -r requirements.txt
```

4. 启动服务:

```bash
python api.py
```

## API 使用

### 调用示例

```python
import requests

# 网页搜索
response = requests.post("http://localhost:12321/chp/web_search", json={
    "provider": "google",
    "kw": "人工智能",
    "page": 1,
    "number": 10
})

# 网页爬取
response = requests.get("http://localhost:12321/chp/web_crawler", params={
    "url": "https://example.com",
    "format": "markdown"
})

# 图表生成
response = requests.post("http://localhost:12321/chp/plot", json={
    "plot_type": "bar",
    "data": {"x": [1,2,3], "y": [4,5,6]},
    "title": "示例图表"
})

# 下载 pdf 并解析
response = requests.get("http://localhost:12321/chp/pdf", params={
    "url": "https://domain.com/path/to/file.pdf"
})
```

## 开发

```bash
# 安装依赖
pip install -r requirements.txt

# 启动开发服务器
python api.py
```

## 后续版本计划

当前版本为过渡版，后续将配合 [Chatspeed](https://github.com/aidyou/chatspeed)  新增 MCP 协议

### 协议升级至MCP

⚠️ 重要变更：为了提升系统性能和扩展能力，我们计划在下个主要版本(v0.2)中将 新增MCP(Model Context Protocol)协议。现有接口不受影响，后续接口将全部采用MCP协议。
