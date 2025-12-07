from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine_sync = create_engine(settings.DATABASE_URL.replace("+asyncpg", ""))

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_sync)
