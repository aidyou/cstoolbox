# Region settings (e.g., "cn", "com", "uk"). Default: "cn".
region = "com"

# Proxy server URL (e.g., "http://username:password@proxy:port"). If None, no proxy is used.
proxy = "http://127.0.0.1:15154"

# proxy config: {"server": "...", "username": "..."}
# proxy 如果不为空，则本项设置不会被用到
proxy_config = None

# server host
server_host = "127.0.0.1"

# server port
server_port = 12321

# min size of crawl pool
browser_pool_min_size = 2

# max size of crawl pool
browser_pool_max_size = 10

# 用来浏览器健康度检查地址
health_check_url = "https://www.baidu.com"

#  user_data_dir (str or None): Path to a user data directory for persistent sessions.
# If None, a temporary directory may be used. Default: None.
user_data_dir = None

browser_type = "chromium"
headless = "true"

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
log_level = "INFO"

# Custom User-Agent string to use.
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

# Mode for generating the user agent (e.g., "random"). If None, use the provided user_agent as-is. Default: None.
user_agent_mode = None
