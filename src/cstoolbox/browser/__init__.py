"""
Browser package for Playwright-based web crawling.

This module serves as the package entry point and exports public interfaces.
"""

from .config import BrowserConfig, BrowserType, CrawlerConfig, CrewlerResult, FieldConfig, FieldType, PageConfig
from .block import block_domains
from .crawler import Crawler
from .playwright_manager import PlaywrightManager
from .pool import BrowserPool

__all__ = [
    'block_domains',
    'BrowserType',
    'BrowserConfig',
    'CrawlerConfig',
    'CrewlerResult',
    'FieldConfig',
    'FieldType',
    'PageConfig',
    'Crawler',
    'BrowserPool',
    'PlaywrightManager',
]
