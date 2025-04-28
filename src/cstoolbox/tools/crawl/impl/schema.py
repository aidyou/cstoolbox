from pydantic import BaseModel, field_validator
from typing import Optional, List


class ExtractField(BaseModel):
    """crawl4ai schema field configuration"""

    name: str
    selector: str
    type: str
    attribute: Optional[str] = None
    remove_link: Optional[bool] = True
    remove_img: Optional[bool] = True


class ExtractSchema(BaseModel):
    """crawl4ai extraction schema"""

    base_selector: str
    fields: List[ExtractField]
    error_selectors: Optional[List[str]] = None

    @field_validator("fields", "base_selector")
    def validate_fields(cls, v):
        if not v:
            raise ValueError("fields list cannot be empty")
        return v
