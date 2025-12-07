from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from colorama import Fore, Style, init
from app.core.security import get_current_user
from app.db.session import get_db
from app.db.models import Alert, DirectionEnum
from app.db.schemas import AlertCreate, AlertOut
from typing import List

router = APIRouter()


# ------------------- CREATE ALERT -------------------
@router.post("/create", response_model=AlertOut)
async def create_alert(
    alert_data: AlertCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    alert = Alert(
        user_id=user.id,
        symbol=alert_data.symbol.upper(),
        target_price=alert_data.target_price,
        direction=alert_data.direction,
        is_triggered=False,
    )
    # prevent duplicate alerts
    existing = await db.execute(
        select(Alert).where(
            Alert.user_id == user.id,
            Alert.symbol == alert.symbol.upper(),
            Alert.is_triggered == False,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=400, detail="An active alert for this symbol already exists."
        )
    print(Fore.YELLOW + f"Creating alert for user {user.email}: {alert.symbol} {alert.direction} {alert.target_price} {alert.created_at}" + Style.RESET_ALL)

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return alert


# ------------------- LIST ALERTS -------------------
@router.get("/", response_model=List[AlertOut])
async def get_alerts(
    db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(
        select(Alert).where(Alert.user_id == user.id).order_by(Alert.id.desc())
    )
    alerts = result.scalars().all()
    return alerts


# ------------------- DELETE ALERT -------------------
@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: int, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)
):
    result = await db.execute(
        select(Alert).where(Alert.id == alert_id, Alert.user_id == user.id)
    )
    alert = result.scalar_one_or_none()

    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    await db.delete(alert)
    await db.commit()

    return {Fore.GREEN + "status": "deleted", "alert_id": alert_id}
