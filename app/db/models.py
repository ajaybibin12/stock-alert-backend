from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Float, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base import Base
import enum


class DirectionEnum(str, enum.Enum):
    ABOVE = "above"
    BELOW = "below"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    alerts = relationship("Alert", back_populates="user")

class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    symbol = Column(String(50), nullable=False, index=True)
    target_price = Column(Float, nullable=False)
    direction = Column(Enum(DirectionEnum), nullable=False)
    is_triggered = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="alerts")
    histories = relationship(
        "AlertHistory",
        back_populates="alert",
        cascade="all, delete-orphan",
        passive_deletes=True
    )

class AlertHistory(Base):
    __tablename__ = "alert_history"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(Integer,
        ForeignKey("alerts.id", ondelete="CASCADE"),
        nullable=False
    )
    triggered_price = Column(Float, nullable=False)
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())

    alert = relationship("Alert", back_populates="histories")