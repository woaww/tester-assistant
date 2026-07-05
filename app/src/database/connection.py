"""Асинхронное подключение к PostgreSQL (SQLAlchemy + asyncpg)."""

import logging
import os
from typing import AsyncGenerator

from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

load_dotenv()

_log = logging.getLogger(__name__)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres@localhost:5432/locator_db",
)

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        _log.info("PostgreSQL: соединение установлено")
    except Exception:
        _log.exception("PostgreSQL: ошибка подключения")
        raise


async def close_db() -> None:
    await engine.dispose()
    _log.info("PostgreSQL: пул соединений закрыт")
