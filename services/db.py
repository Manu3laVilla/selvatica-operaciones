from __future__ import annotations

import uuid
from datetime import datetime
from functools import lru_cache

from config import resolves_data_backend


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@lru_cache(maxsize=1)
def get_db():
    backend = resolves_data_backend()
    if backend == "supabase":
        from services.postgres_db import PostgresDB

        return PostgresDB()

    from services.sheets_db import SheetsDB

    return SheetsDB()
