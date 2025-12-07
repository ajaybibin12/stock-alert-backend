from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.db.models import User
from app.db.schemas import UserCreate, UserLogin, UserOut
from app.services.auth_service import hash_password, verify_password, create_access_token

router = APIRouter()

# ------------- REGISTER ----------------
@router.post("/register", response_model=UserOut)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    # check exists
    result = await db.execute(select(User).where(User.email == user.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    new_user = User(
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    return new_user


# ------------- LOGIN ----------------
@router.post("/login")
async def login(user: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user.email))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=400, detail="Invalid login credentials")

    if not verify_password(user.password, existing.password_hash):
        raise HTTPException(status_code=400, detail="Invalid login credentials")

    token = create_access_token(existing.id)

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": existing.id, "email": existing.email}
    }
