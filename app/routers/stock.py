from fastapi import APIRouter, Depends, HTTPException
from app.core.security import get_current_user
import httpx
import time

router = APIRouter()

@router.get("/history")
async def get_stock_history(
    symbol: str,
    period: str = "7d",   # ✅ renamed from range → period
    user=Depends(get_current_user),
):
    """
    Yahoo Finance Stock History (FREE & UNLIMITED)
    Periods supported: 1d, 7d, 1m
    """

    now = int(time.time())

    periods = {
        "1d": 1,
        "7d": 7,
        "1m": 30,
    }

    if period not in periods:
        raise HTTPException(status_code=400, detail="Invalid period")

    days = periods[period]
    start = now - days * 24 * 60 * 60

    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{symbol}?period1={start}&period2={now}&interval=1d&events=history"
    )

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with httpx.AsyncClient(headers=headers) as client:
        resp = await client.get(url)

    if resp.status_code != 200 or not resp.text.strip():
        raise HTTPException(status_code=502, detail="Yahoo Finance API blocked the request")

    data = resp.json()

    try:
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        quotes = result["indicators"]["quote"][0]
    except Exception:
        raise HTTPException(status_code=404, detail="No chart data available")

    formatted = []
    for i in range(len(timestamps)):   # ✅ works now
        formatted.append({
            "time": timestamps[i] * 1000,
            "open": quotes["open"][i],
            "high": quotes["high"][i],
            "low": quotes["low"][i],
            "close": quotes["close"][i],
        })

    return formatted
