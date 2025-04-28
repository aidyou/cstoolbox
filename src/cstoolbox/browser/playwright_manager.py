"""
Playwright browser implementation for web crawling.
"""

import os
from pathlib import Path
from appdirs import user_cache_dir

from playwright.async_api import BrowserContext, async_playwright

from . import BrowserConfig, BrowserType
from cstoolbox.logger import get_logger

logger = get_logger(__name__)
DEFAULT_ARGS = [
    # GPU/渲染优化
    "--enable-gpu-rasterization",  # 平衡性能与兼容性
    "--disable-software-rasterizer",
    "--disable-gl-drawing-for-tests",
    # 指纹混淆
    "--use-gl=desktop",
    "--disable-accelerated-video",
    # 安全限制
    "--disable-dev-shm-usage",
    # 网络优化
    "--disable-background-networking",
    "--disable-default-apps",
    "--disable-component-update",
    # 功能限制
    "--disable-popup-blocking",
    "--mute-audio",
    "--disable-notifications",
    # 环境模拟
    "--use-fake-ui-for-media-stream",
    "--use-fake-device-for-media-stream",
    "--enable-features=NetworkService",
    # 隐藏自动化特征
    "--disable-infobars",
    "--no-first-run",
    "--hide-scrollbars",
    "--remote-debugging-port=0",
    # 增加稳定性参数
    "--disable-2d-canvas-clip-aa",
    "--disable-breakpad",
    "--disable-cloud-import",
    "--disable-domain-reliability",
    "--disable-ios-physical-web",
    "--disable-partial-raster",
    "--disable-speech-api",
    # 其他
    "--autoplay-policy=user-gesture-required",
    "--disable-sync",
]

BROWSER_TEXT_MODE_OPTIONS = [
    "--blink-settings=imagesEnabled=false",
    "--disable-remote-fonts",
    "--disable-images",
]

IGNORE_ARGS = [
    # ==============================================
    # 下面这些参数是 playwright 默认的启动项
    # ==============================================
    # "--disable-field-trial-config",
    # "--disable-background-networking",
    # "--disable-background-timer-throttling",
    # "--disable-backgrounding-occluded-windows",
    # "--disable-back-forward-cache",
    # "--disable-breakpad",
    # "--disable-client-side-phishing-detection",
    # "--disable-component-extensions-with-background-pages",
    # "--disable-component-update",
    # "--no-default-browser-check",
    # "--disable-default-apps",
    # "--disable-dev-shm-usage",
    # "--disable-extensions",
    # "--disable-features=AcceptCHFrame,AutoExpandDetailsElement,AvoidUnnecessaryBeforeUnloadCheckSync,CertificateTransparencyComponentUpdater,DeferRendererTasksAfterInput,DestroyProfileOnBrowserClose,DialMediaRouteProvider,ExtensionManifestV2Disabled,GlobalMediaControls,HttpsUpgrades,ImprovedCookieControls,LazyFrameLoading,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,Translate",
    # "--allow-pre-commit-input",
    # "--disable-hang-monitor",
    # "--disable-ipc-flooding-protection",
    # "--disable-popup-blocking",
    # "--disable-prompt-on-repost",
    # "--disable-renderer-backgrounding",
    # "--force-color-profile=srgb",
    # "--metrics-recording-only",
    # "--no-first-run",
    # "--no-service-autorun",
    # "--export-tagged-pdf",
    # "--disable-search-engine-choice-screen",
    # "--unsafely-disable-devtools-self-xss-warnings",
    # "--enable-use-zoom-for-dsf=false",
    # "--no-sandbox",
    # "--remote-debugging-pipe", # 这个参数不能禁止，否则 playwright 无法控制浏览器
    # ====================
    # 下面这些参数「必须留着」
    # ====================
    "--enable-automation",  # 如果去除，会被识别为自动化测试
    "--password-store=basic",  # 会导致 google.com 异常（要验证）
    "--use-mock-keychain",  # 会导致 chrome 的登录状态异常
]


class PlaywrightManager:
    """Playwright implementation of browser pool"""

    def __init__(self, config: BrowserConfig):
        if not config.type:
            config.type = BrowserType.CHROMIUM

        def update_args(args: dict, new_args: list):
            for arg in new_args:
                if "=" in arg:
                    key, value = arg.split("=", 1)
                    args[key] = value
                else:
                    args[arg] = None

        args = {}
        update_args(args, DEFAULT_ARGS)

        if config.extra_args:
            update_args(args, config.extra_args)
        if config.proxy:
            args["--proxy-server"] = config.proxy
        if config.text_mode:
            update_args(args, BROWSER_TEXT_MODE_OPTIONS)

        config.extra_args = []
        for key, value in args.items():
            if value:
                config.extra_args.append(f"{key}={value}")
            else:
                config.extra_args.append(key)

        self.config = config

    async def launch_browser(self) -> BrowserContext:
        """Launch browser with configuration"""
        playwright = await async_playwright().start()

        launch_options = {
            "headless": self.config.headless,
            "timeout": self.config.timeout,
            "args": self.config.extra_args,
            "env": self.config.env,
            "ignore_https_errors": self.config.ignore_https_errors,
            "java_script_enabled": self.config.java_script_enabled,
            "ignore_default_args": IGNORE_ARGS,
        }

        if self.config.user_data_dir:
            user_data_dir = Path(os.path.expanduser(self.config.user_data_dir))
            if not user_data_dir.exists():
                try:
                    os.makedirs(user_data_dir, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to setup user data dir: {e}")
            launch_options["user_data_dir"] = str(user_data_dir)
            logger.info(f"Using user data dir: {user_data_dir}")
        else:
            # 如果没有提供user_data_dir，创建一个临时目录
            user_data_dir = Path(user_cache_dir("cstoolbox")) / self.config.type
            try:
                os.makedirs(user_data_dir, exist_ok=True)
            except Exception as e:
                logger.warning(f"Failed to setup user data dir: {e}")
            launch_options["user_data_dir"] = str(user_data_dir)
            logger.info(f"Using user data dir: {user_data_dir}")

        if self.config.executable_path:
            launch_options["executable_path"] = self.config.executable_path

        if self.config.user_agent:
            launch_options["user_agent"] = self.config.user_agent
        if self.config.viewport:
            launch_options["viewport"] = self.config.viewport

        if self.config.type == BrowserType.CHROMIUM:
            return await playwright.chromium.launch_persistent_context(**launch_options)
        elif self.config.type == BrowserType.FIREFOX:
            return await playwright.firefox.launch_persistent_context(**launch_options)
        else:
            return await playwright.webkit.launch_persistent_context(**launch_options)
