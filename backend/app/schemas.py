from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    created_at: datetime


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class TagOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str


class TagWithCount(TagOut):
    count: int = 0


class CategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    parent_id: Optional[int] = None
    sort_order: int = 0
    count: int = 0


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    parent_id: Optional[int] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: Optional[int] = None


class BookmarkCreate(BaseModel):
    url: str = Field(min_length=1, max_length=2048)
    category_name: Optional[str] = None
    tags: List[str] = Field(default_factory=list)


class BookmarkUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category_name: Optional[str] = None
    tags: Optional[List[str]] = None
    is_favorite: Optional[bool] = None


class ReorderPayload(BaseModel):
    scope: str
    ids: List[int]


class BookmarkOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    url: str
    title: str
    description: str
    content_markdown: str
    favicon_url: str
    category_id: Optional[int] = None
    is_favorite: bool
    created_at: datetime
    updated_at: datetime
    tags: List[TagOut] = Field(default_factory=list)
    category: Optional[CategoryOut] = None

    @field_validator("title", "description", "content_markdown", "favicon_url", mode="before")
    @classmethod
    def _none_to_empty(cls, v):
        return v if v is not None else ""


class BookmarkListOut(BaseModel):
    items: List[BookmarkOut]
    total: int
    page: int
    page_size: int


class ImportRequest(BaseModel):
    data: str


class ImportResult(BaseModel):
    imported: int
    skipped: int
