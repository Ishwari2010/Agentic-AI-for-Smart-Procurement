from pydantic import BaseModel
from typing import List


# -----------------------------
# Item Schema
# -----------------------------
class ProcurementItem(BaseModel):
    description: str
    quantity: int
    estimated_cost: float


# -----------------------------
# Gemini Extraction Schema
# -----------------------------
class ProcurementExtraction(BaseModel):
    requester_name: str
    items: List[ProcurementItem]
    total_estimated_cost: float


# -----------------------------
# Database Response Schemas
# -----------------------------
class ProcurementItemResponse(ProcurementItem):
    id: int

    class Config:
        from_attributes = True


class ProcurementRequestResponse(BaseModel):
    id: int
    requester_name: str
    total_estimated_cost: float
    items: List[ProcurementItemResponse]

    class Config:
        from_attributes = True