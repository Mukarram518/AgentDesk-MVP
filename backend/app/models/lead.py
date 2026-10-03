import uuid
from typing import Optional
from sqlalchemy import ForeignKey, Integer, String, Text, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Lead(Base, TimestampMixin):
    """Business lead captured from customer conversation."""

    __tablename__ = "leads"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="WARM", nullable=False, index=True)
    score: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationship to Business
    business: Mapped["Business"] = relationship(
        "Business",
        back_populates="leads",
    )

    def __repr__(self) -> str:
        return f"<Lead(id={self.id}, business_id={self.business_id}, status='{self.status}', score={self.score})>"
