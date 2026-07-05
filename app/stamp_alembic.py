"""
Регистрация alembic_version после создания таблиц через create_tables.py.

Alembic не знает о существующей схеме, поэтому нужно вручную
записать версию в таблицу alembic_version.
"""
import asyncio
import sys
from pathlib import Path
import os

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL не задан. Укажи строку подключения к Postgres, например "
        "`postgresql+asyncpg://user:pass@localhost:5432/locator_db`."
    )

# ID миграции из файла 20260407_172616_initial_schema.py
REVISION_ID = "initial_schema"


async def stamp_alembic():
    engine = create_async_engine(DATABASE_URL, echo=True)
    async with engine.begin() as conn:
        # Создаём таблицу alembic_version если нет
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version (
                version_num VARCHAR(32) NOT NULL PRIMARY KEY
            )
        """))
        # Upsert версии
        await conn.execute(
            text("""
                INSERT INTO alembic_version (version_num)
                VALUES (:revision)
                ON CONFLICT (version_num) DO UPDATE SET version_num = EXCLUDED.version_num
            """),
            {"revision": REVISION_ID},
        )
    await engine.dispose()
    print(f"\n[OK] alembic_version установлен на '{REVISION_ID}'")


if __name__ == "__main__":
    asyncio.run(stamp_alembic())
