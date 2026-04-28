from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class TextAlign(str, Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"


class BoundingBox(BaseModel):
    x: float = Field(..., description="Left coordinate in pixels")
    y: float = Field(..., description="Top coordinate in pixels")
    w: float = Field(..., description="Width in pixels")
    h: float = Field(..., description="Height in pixels")


class TextBlock(BaseModel):
    id: str
    text: str
    bbox: BoundingBox
    fontSize: float = Field(default=16.0, description="Font size in points")
    fontFamily: str = Field(default="Malgun Gothic")
    bold: bool = False
    italic: bool = False
    color: str = Field(default="#000000", description="Hex color e.g. #ff0000")
    align: TextAlign = TextAlign.LEFT
    lineBreaks: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)


# ── Upload ──────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    image_id: str
    filename: str
    width: int
    height: int
    image_url: str


# ── Analyze ─────────────────────────────────────────────────────────────────

class AnalyzeResponse(BaseModel):
    image_id: str
    image_width: int
    image_height: int
    blocks: List[TextBlock]


# ── Inpaint ─────────────────────────────────────────────────────────────────

class InpaintRequest(BaseModel):
    image_id: str
    blocks: List[TextBlock]
    dilation_kernel: int = Field(default=5, ge=1, le=30, description="Mask dilation kernel size")
    inpaint_radius: int = Field(default=3, ge=1, le=15)
    inpaint_method: str = Field(default="telea", pattern="^(telea|ns)$")


class InpaintResponse(BaseModel):
    cleaned_image_id: str
    cleaned_image_url: str


# ── Generate PPT ─────────────────────────────────────────────────────────────

class GeneratePPTRequest(BaseModel):
    image_id: str
    cleaned_image_id: str
    blocks: List[TextBlock]
    image_width: int
    image_height: int


class GeneratePPTResponse(BaseModel):
    file_id: str
    download_url: str


# ── Error ────────────────────────────────────────────────────────────────────

class ErrorDetail(BaseModel):
    error: str
    detail: str
    suggestions: List[str] = Field(default_factory=list)
