from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    TIMESTAMP,
    ForeignKey,
    Text,
    JSON,
    text
)

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from .database import Base


# ============================================================
# Procurement Request
# ============================================================

class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    requester_name = Column(
        String(255),
        nullable=False
    )

    total_estimated_cost = Column(
        Numeric(12, 2),
        nullable=False
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    items = relationship(
        "ProcurementItem",
        back_populates="request",
        cascade="all, delete-orphan"
    )


# ============================================================
# Procurement Items
# ============================================================

class ProcurementItem(Base):
    __tablename__ = "procurement_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    request_id = Column(
        Integer,
        ForeignKey(
            "procurement_requests.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    description = Column(
        String(255),
        nullable=False
    )

    quantity = Column(
        Integer,
        nullable=False
    )

    estimated_cost = Column(
        Numeric(12, 2),
        nullable=False
    )

    request = relationship(
        "ProcurementRequest",
        back_populates="items"
    )


# ============================================================
# Document Processing
# ============================================================

class DocumentProcessing(Base):
    __tablename__ = "document_processing"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    filename = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(500),
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False,
        default="queued"
    )

    ocr_status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    gemini_status = Column(
        String(50),
        nullable=False,
        default="pending"
    )

    ocr_text = Column(
        Text,
        nullable=True
    )

    structured_data = Column(
        JSON,
        nullable=True
    )

    request_id = Column(
        Integer,
        ForeignKey(
            "procurement_requests.id"
        ),
        nullable=True
    )

    error_message = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    updated_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )