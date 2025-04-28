import random
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Union, Any

from pydantic import BaseModel, Field


class BrowserType(str, Enum):
    """Supported browser types"""

    CHROMIUM = "chromium"
    FIREFOX = "firefox"
    WEBKIT = "webkit"


class BrowserConfig(BaseModel):
    """Browser configuration"""

    type: BrowserType = BrowserType.CHROMIUM
    executable_path: Optional[str] = None
    headless: bool = True
    timeout: Optional[float] = None
    proxy: Optional[str] = None
    user_agent: Optional[str] = None
    viewport: Optional[Dict[str, int]] = None
    exclude_urls: Optional[List[str]] = None
    ignore_https_errors: bool = True
    java_script_enabled: bool = True
    user_data_dir: Optional[str] = None
    text_mode: Optional[bool] = False
    env: Optional[Dict[str, Union[str, float, bool]]] = None
    extra_args: Optional[list[str]] = []


class PageConfig(BaseModel):
    """Page configuration"""

    # wait for a selector to appear or a function to return a truthy value
    # if start with js:, will execute js code, otherwise will use playwright's wait_for_function
    # if start with css:, will use playwright's wait_for_selector
    wait_for: Optional[str] = None

    # wait until the page is in a certain state, can be one of the following:
    #  - domcontentloaded: The DOM content has been loaded, but external resources like images and stylesheets may still be loading.
    #  - load: The page has finished loading, including all resources.
    #  - networkidle: The network is idle (no requests for 500ms).
    wait_until: Optional[str] = "domcontentloaded"
    wait_timeout: Optional[int] = 15000
    page_timeout: int = 15000
    init_js_code: Optional[str] = None


@dataclass
class FieldType:
    """Field type for extraction"""

    TEXT: str = "text"
    HTML: str = "html"
    ATTRIBUTE: str = "attribute"
    MARKDOWN: str = "markdown"


class FieldConfig(BaseModel):
    """Field configuration for extraction"""

    name: str
    selector: str
    type: Union[FieldType, str] = FieldType.TEXT
    attribute: Optional[str] = None
    # clean options
    # remove link: try to remove link tag but keep it's content, just for markdown and html
    remove_link: Optional[bool] = False
    # remove img: try to remove img tag, just for markdown and html
    remove_img: Optional[bool] = True


class EventType(str, Enum):
    """Supported event types"""

    Click = "click"  # perform a click on the element
    Fill = "fill"  # fill the input element with the value
    Enter = "enter"  # press the enter key on the keyboard


class EventConfig(BaseModel):
    """Event configuration for extraction"""

    event: Union[EventType | str] = EventType.Click
    selector: str
    value: Optional[str] = None
    timeout: Optional[int] = 15000


class CrawlerConfig(BaseModel):
    """Crawler configuration"""

    name: Optional[str] = None
    # wait for a selector to appear or a function to return a truthy value
    # if start with js:, will execute js code, otherwise will use playwright's wait_for_function
    # if start with css:, will use playwright's wait_for_selector
    wait_for: Optional[str] = None

    # wait until the page is in a certain state, can be one of the following:
    #  - domcontentloaded: The DOM content has been loaded, but external resources like images and stylesheets may still be loading.
    #  - load: The page has finished loading, including all resources.
    #  - networkidle: The network is idle (no requests for 500ms).
    wait_until: Optional[str] = "domcontentloaded"
    wait_timeout: Optional[int] = 15000
    page_timeout: int = 15000
    init_js_code: Optional[str] = None
    js_code: Optional[Union[str, List[str]]] = None
    events: Optional[List[EventConfig]] = None
    # if base_selector is set, will extract data from each element matched by base_selector, and return a list of data
    # if not, will extract data from the whole page, and return a dict data, key is the field name, value is the field value
    base_selector: Optional[str] = None
    fields: List[Union[FieldConfig, str]] = Field(default_factory=list)

    return_full_html: bool = False

    # Global option for data extraction
    # remove link: try to remove link tag but keep it's content, just for content extraction
    remove_link: Optional[bool] = False


class CrewlerResult(BaseModel):
    """Crawler result"""

    title: str = ""
    url: str = ""
    html: str = ""
    cleaned_html: str = ""
    markdown: str = ""
    results: Union[List[Dict[str, Any]], Dict[str, Any]] = None
    success: bool = False
    error_message: Optional[str] = None
