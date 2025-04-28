# ==============================================================================
# Pre-converted Glob patterns for Playwright route matching.
# Derived from the original block_domains list for efficiency.
# Each pattern follows the format **/{domain_or_pattern}/**
# ==============================================================================
block_domains = [
    # 广告和跟踪 (Google, Baidu, Alibaba)
    '**/*.doubleclick.net/**',
    '**/googleadservices.com/**',
    '**/www.googleadservices.com/**',
    '**/googlesyndication.com/**',
    '**/*.googlesyndication.com/**',
    '**/google-analytics.com/**',
    '**/www.google-analytics.com/**',
    '**/*.google-analytics.com/**',
    '**/*.google.com/ads/**',
    '**/*.google.com/pagead/**',
    '**/adservice.google.com/**',
    '**/bdstatic.com/**',  # 百度静态资源
    '**/pos.baidu.com/**',  # 百度联盟
    '**/*.tanx.com/**',  # 阿里妈妈 Tanx
    '**/*.alimama.com/**',  # 阿里妈妈
    # 联盟营销 (Affiliate Marketing)
    '**/*.cj.com/**',
    '**/dpbolvw.net/**',  # CJ
    '**/tkqlhce.com/**',  # CJ
    '**/jdoqocy.com/**',  # CJ
    '**/anrdoezrs.net/**',  # CJ
    '**/*.linksynergy.com/**',  # Rakuten
    '**/*.ran.com/**',  # Rakuten Affiliate Network
    '**/*.shareasale.com/**',
    '**/*.awin1.com/**',
    '**/*.dwin1.com/**',
    '**/*.impact.com/**',
    '**/impactradius.com/**',
    '**/*.prf.hn/**',  # Impact 短链/重定向
    '**/*.sjv.io/**',  # Impact 相关重定向
    '**/*.clickbank.net/**',
    '**/hop.clickbank.net/**',
    # 其他常见广告/分析/跟踪
    '**/*.amazon-adsystem.com/**',
    '**/adsystem.amazon.com/**',
    '**/*.facebook.net/**',  # Facebook Pixel, Connect 等
    '**/connect.facebook.net/**',
    '**/*.facebook.com/tr/**',  # Facebook Pixel (img) - Pattern from original list
    '**/*.krxd.net/**',  # Krux / Salesforce DMP
    '**/*.scorecardresearch.com/**',  # Comscore
    '**/*.quantserve.com/**',  # Quantcast
    '**/*.adroll.com/**',
    '**/*.outbrain.com/**',
    '**/*.taboola.com/**',
    '**/*.criteo.com/**',
    '**/*.criteo.net/**',
    '**/*.adsrvr.org/**',  # The Trade Desk
    '**/*.rlcdn.com/**',  # LiveRamp / Rapleaf
    '**/*.hotjar.com/**',  # Hotjar
    '**/*.pingdom.net/**',  # Pingdom 监控脚本
    '**/*.twitter.com/i/ads/**',  # Twitter 广告
    '**/analytics.twitter.com/**',
    '**/*.licdn.com/**',  # LinkedIn Insight Tag
    '**/*.bing.com/ads/**',  # Bing Ads
    '**/bat.bing.com/**',  # Bing UET Tag
    # 常见统计网站域名 (请谨慎评估是否真的需要屏蔽)
    '**/www.pinggu.org/**',
    '**/www.itongji.cn/**',
    '**/bbs.itongji.cn/**',
    '**/www.businessanalysis.cn/**',
    '**/www.magnsoftbi.com/**',
    '**/www.bridge.com/**',
    '**/51.la/**',
    # 社交分享按钮/小部件
    '**/platform.twitter.com/**',
    '**/platform.linkedin.com/**',
    '**/assets.pinterest.com/**',
]
