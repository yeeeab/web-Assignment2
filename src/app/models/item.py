import enum
from sqlalchemy import String, Text, Enum, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class ItemStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True, nullable=False)

    title: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    start_price: Mapped[int] = mapped_column(Integer, nullable=False)
    bid_unit: Mapped[int] = mapped_column(Integer, nullable=False, default=100)

    status: Mapped[ItemStatus] = mapped_column(Enum(ItemStatus), index=True, default=ItemStatus.DRAFT, nullable=False)

    starts_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), index=True, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # 관계(편의용) - N+1 피하려면 조회에서 join/selectinload 사용
    seller = relationship("User", lazy="selectin")
    category = relationship("Category", lazy="selectin")
