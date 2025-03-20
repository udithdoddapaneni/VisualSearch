"""Pydantic models for Searcher."""
from typing import Literal

from pydantic import BaseModel, Field


class Query(BaseModel):
    """Query Class."""

    text: str = Field(default="", strict=True)
    type: Literal["image", "video"] = "image"
    n: int = Field(default=10, strict=True)

class Docs(BaseModel):
    """Documents Class."""

    texts: list[str] = Field(default=[], strict=True)
    filenames: list[str] = Field(default=[], strict=True)
    types: list[str] = Field(default=[], strict=True)
    timestamps: list[int] = Field(default=[], strict=True)
