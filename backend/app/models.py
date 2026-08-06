from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    TIMESTAMP,
    ForeignKey,
    text
)
from sqlalchemy.orm import relationship

from .database import Base


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(Integer, primary_key=True, index=True)
    requester_name = Column(String(255), nullable=False)
    total_estimated_cost = Column(Numeric(12, 2), nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=text("CURRENT_TIMESTAMP")
    )

    items = relationship(
        "ProcurementItem",
        back_populates="request",
        cascade="all, delete-orphan"
    )


class ProcurementItem(Base):
    __tablename__ = "procurement_items"

    id = Column(Integer, primary_key=True, index=True)

    request_id = Column(
        Integer,
        ForeignKey("procurement_requests.id")
    )

    description = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    estimated_cost = Column(Numeric(12, 2), nullable=False)

    request = relationship(
        "ProcurementRequest",
        back_populates="items"
    )