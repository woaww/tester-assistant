"""Синхронное подключение psycopg2 по тому же DATABASE_URL, что использует SQLAlchemy async."""

from __future__ import annotations

import urllib.parse

import psycopg2

from src.database.connection import DATABASE_URL


def connect_psycopg2():
    url = DATABASE_URL.replace("+asyncpg", "")
    parsed = urllib.parse.urlparse(url)
    kwargs = {
        "host": parsed.hostname or "localhost",
        "port": parsed.port or 5432,
        "user": parsed.username or "postgres",
        "dbname": parsed.path.lstrip("/") or "locator_db",
    }
    if parsed.password is not None:
        kwargs["password"] = parsed.password
    return psycopg2.connect(**kwargs)
