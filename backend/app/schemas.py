from pydantic import BaseModel
from typing import List, Optional, Dict, Any


# ============================================================
# Procurement Item
# ============================================================

class ProcurementItem(BaseModel):
    description: str
    quantity: int
    estimated_cost: float


# ============================================================
# Gemini Extraction
# ============================================================

class ProcurementExtraction(BaseModel):
    requester_name: str
    items: List[ProcurementItem]
    total_estimated_cost: float


# ============================================================
# Procurement Item Response
# ============================================================

class ProcurementItemResponse(ProcurementItem):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# Procurement Request Response
# ============================================================

class ProcurementRequestResponse(BaseModel):
    id: int
    requester_name: str
    total_estimated_cost: float
    items: List[ProcurementItemResponse]

    class Config:
        from_attributes = True


# ============================================================
# Document Processing Response
# ============================================================

class DocumentProcessingResponse(BaseModel):
    id: int
    filename: str
    status: str

    ocr_text: Optional[str] = None

    structured_data: Optional[Dict[str, Any]] = None

    request_id: Optional[int] = None

    error_message: Optional[str] = None

    class Config:
        from_attributes = True