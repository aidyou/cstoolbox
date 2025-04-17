import os
from pathlib import Path

# Region settings (e.g., "cn", "com", "uk"). Default: "com".
region = os.getenv("CS_REGION", "com")

# Proxy server URL (e.g., "http://username:password@proxy:port"). If None, no proxy is used.
proxy = os.getenv("CS_PROXY", "http://host.docker.internal:15154")

# server host
server_host = os.getenv("CS_SERVER_HOST", "127.0.0.1")

# server port
server_port = int(os.getenv("CS_SERVER_PORT", 12321))

# min size of crawl pool
browser_pool_min_size = os.getenv("CS_BROWSER_POOL_MIN_SIZE", 2)

# max size of crawl pool
browser_pool_max_size = os.getenv("CS_BROWSER_POOL_MAX_SIZE", 10)

#  user_data_dir (str or None): Path to a user data directory for persistent sessions.
# If None, a temporary directory may be used. Default: None.
user_data_dir = os.getenv("CS_USER_DATA_DIR")

headless = os.getenv("CS_HEADLESS", "true")

# Region specific base URLs
region_urls = {
    "google": {
        "com": "https://www.google.com",
        "cn": "https://www.google.com.hk",
        "hk": "https://www.google.com.hk",
        "jp": "https://www.google.co.jp",
        "kr": "https://www.google.co.kr",
        "uk": "https://www.google.co.uk",
        "de": "https://www.google.de",
        "fr": "https://www.google.fr",
    },
    "google_news": {
        "com": "https://www.google.com",
        "cn": "https://www.google.com.hk",
        "hk": "https://www.google.com.hk",
    },
    "bing": {
        "cn": "https://cn.bing.com",
        "com": "https://www.bing.com",
        "uk": "https://www.bing.co.uk",
        "de": "https://www.bing.de",
        "fr": "https://www.bing.fr",
        "jp": "https://www.bing.co.jp",
        "kr": "https://www.bing.co.kr",
    },
    "duckduckgo": {"com": "https://duckduckgo.com"},
    "baidu": {"com": "https://www.baidu.com"},
    "baidu_news": {"com": "https://www.baidu.com"},
    # "yandex": {
    #     "com": "https://yandex.com",
    #     "ru": "https://yandex.ru",
    # },
    # "naver": {"com": "https://search.naver.com"},
    # "yahoo": {
    #     "com": "https://search.yahoo.com",
    #     "jp": "https://search.yahoo.co.jp",
    # },
    # "qwant": {"com": "https://www.qwant.com"},
    # "ecosia": {"com": "https://www.ecosia.org"},
}

# Logging level (e.g., "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"). Default: "INFO".
log_level = os.getenv("CS_LOG_LEVEL", "INFO")

# Custom User-Agent string to use.
user_agent = os.getenv("CS_USER_AGENT")

# Mode for generating the user agent (e.g., "random"). If None, use the provided user_agent as-is. Default: None.
user_agent_mode = os.getenv("CS_USER_AGENT_MODE", "random")

server_root = Path(__file__).resolve().parent.parent
