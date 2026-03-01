from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from infrastructure.database import Base

class FlagORM(Base):
    __tablename__ = "flags"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

class OverrideORM(Base):
    __tablename__ = "overrides"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flag_name: Mapped[str] = mapped_column(String, ForeignKey("flags.name"), nullable=False)
    
    # Generic keys allow the lookup_chain to be completely dynamic
    override_type: Mapped[str] = mapped_column(String, nullable=False)   # e.g., "user", "group", "region"
    override_value: Mapped[str] = mapped_column(String, nullable=False)  # e.g., "alice", "beta-testers", "US"
    
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint("flag_name", "override_type", "override_value", name="uix_flag_override"),
    )
