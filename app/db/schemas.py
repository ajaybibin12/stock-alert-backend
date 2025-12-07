from pydantic import BaseModel, EmailStr
from typing import Optional
import enum
from datetime import datetime

# ---------- USER SCHEMAS ----------
class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        orm_mode = True


# ---------- ALERT SCHEMAS (will use later) ----------
class DirectionEnum(str, enum.Enum):
    above = "above"
    below = "below"

class AlertCreate(BaseModel):
    symbol: str
    target_price: float
    direction: DirectionEnum

class AlertOut(BaseModel):
    id: int
    symbol: str
    target_price: float
    direction: str
    is_triggered: bool
    created_at: datetime

    class Config:
        orm_mode = True
