from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum
import uuid


class ProcessingMode(str, Enum):
    keep_original = "keep_original"
    safe_fill = "safe_fill"
    text_pixel_inpaint = "text_pixel_inpaint"
    gradient_restore = "gradient_restore"
    panel_restore = "panel_restore"
    advanced_inpaint = "advanced_inpaint"
    manual_review = "manual_review"


class RestoreStatus(str, Enum):
    pending = "pending"
    success = "success"
    failed = "failed"
    manual_review = "manual_review"
    rollback = "rollback"


class BBox(BaseModel):
    x: int
    y: int
    w: int
    h: int


class TextBlock(BaseModel):
    id: str = Field(default_factory=lambda: f"text-{uuid.uuid4().hex[:8]}")
    text: str
    bbox: BBox
    polygon: List[List[int]]
    confidence: float
    visible: bool = True
    mode: ProcessingMode = ProcessingMode.text_pixel_inpaint
    risk_score: float = 0.0
    restore_status: RestoreStatus = RestoreStatus.pending


class TextLayer(BaseModel):
    session_id: str
    image_width: int
    image_height: int
    blocks: List[TextBlock]


class UploadResponse(BaseModel):
    session_id: str
    original_url: str
    width: int
    height: int
    filename: str


class DetectResponse(BaseModel):
    session_id: str
    text_layer: TextLayer
    block_count: int


class MaskResponse(BaseModel):
    session_id: str
    text_mask_url: str
    protection_mask_url: str
    final_remove_mask_url: str


class RemoveResponse(BaseModel):
    session_id: str
    clean_background_url: str
    blocks: List[TextBlock]


class RestoreResponse(BaseModel):
    session_id: str
    restored_background_url: str
    blocks: List[TextBlock]


class UpdateBlocksRequest(BaseModel):
    session_id: str
    blocks: List[TextBlock]


class CreateMasksRequest(BaseModel):
    session_id: str
    blocks: List[TextBlock]
    protection_strength: float = 1.0
