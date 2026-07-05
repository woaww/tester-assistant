"""
Скрипт создания таблиц в БД напрямую через SQLAlchemy.
Используется вместо Alembic при проблемах с кодировкой.

Запуск из директории app:
    python create_tables.py
"""
import asyncio
import sys
from pathlib import Path
import os

# Добавляем родительскую директорию
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from src.database.models import Base  # noqa: E402


DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не задан. Укажи строку подключения к Postgres, например "
        "`postgresql+asyncpg://user:pass@localhost:5432/locator_db`."
    )


async def create_tables():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()
    print("\n[OK] Все таблицы успешно созданы!")


if __name__ == "__main__":
    asyncio.run(create_tables())
