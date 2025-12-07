import asyncio
from logging.config import fileConfig
import os
import sys

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# ---------------------------------------------------------
# Add project root directory to Python path
# Example: C:/Users/ajayb/.../Stock_Alert_System
# ---------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

# ---------------------------------------------------------
# Import models and settings
# ---------------------------------------------------------
from app.core.config import settings
from app.db.base import Base
from app.db import models  # ensure all models are imported

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Metadata for autogenerate
target_metadata = Base.metadata


# ---------------------------------------------------------
# OFFLINE MIGRATIONS
# ---------------------------------------------------------
def run_migrations_offline():
    """Run migrations without a DB connection."""
    context.configure(
        url=settings.DATABASE_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# ONLINE MIGRATIONS
# ---------------------------------------------------------
def do_run_migrations(connection: Connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        url=settings.DATABASE_URL,     # use your .env DB url
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


# ---------------------------------------------------------
# Decide offline / online
# ---------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
