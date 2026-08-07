from __future__ import annotations

import json
import time
from typing import Any

import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import Json, RealDictCursor

from config import (
    SHEET_CATEGORIAS,
    SHEET_CLIENTES,
    SHEET_CONTABILIDAD,
    SHEET_ESTADOS_PEDIDO,
    SHEET_PEDIDOS,
    SHEET_PRODUCTOS,
    SHEET_SCHEMAS,
    SHEET_TIPOS_GASTO,
    SHEET_TIPOS_INGRESO,
    SHEET_VENTAS,
    SHEETS_CACHE_TTL_SECONDS,
    get_database_url,
)

SHEET_TO_TABLE: dict[str, str] = {
    SHEET_PRODUCTOS: "productos",
    SHEET_CLIENTES: "clientes",
    SHEET_VENTAS: "ventas",
    SHEET_PEDIDOS: "pedidos",
    SHEET_CONTABILIDAD: "contabilidad",
    SHEET_CATEGORIAS: "categorias_producto",
    SHEET_TIPOS_INGRESO: "tipos_ingreso",
    SHEET_TIPOS_GASTO: "tipos_gasto",
    SHEET_ESTADOS_PEDIDO: "estados_pedido",
}

JSON_COLUMNS = {"items_json"}


def _normalize_value(column: str, value: Any) -> Any:
    if value is None:
        return None
    if column in JSON_COLUMNS:
        if isinstance(value, (dict, list)):
            return Json(value)
        if isinstance(value, str):
            text = value.strip()
            if not text:
                return Json([])
            try:
                return Json(json.loads(text))
            except json.JSONDecodeError:
                return Json([])
        return Json(value)
    if hasattr(value, "isoformat"):
        return value.isoformat(sep=" ", timespec="seconds")
    return value


def _serialize_record(record: dict[str, Any]) -> dict[str, Any]:
    serialized: dict[str, Any] = {}
    for key, value in record.items():
        if key in JSON_COLUMNS and value is not None and not isinstance(value, str):
            serialized[key] = json.dumps(value, ensure_ascii=False)
        elif hasattr(value, "isoformat"):
            serialized[key] = value.isoformat(sep=" ", timespec="seconds")
        else:
            serialized[key] = value
    return serialized


class PostgresDB:
    def __init__(self) -> None:
        self._connection = None
        self._records_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}

    def connect(self):
        if self._connection is not None and not self._connection.closed:
            return self._connection

        database_url = get_database_url()
        if not database_url:
            raise ValueError(
                "Falta DATABASE_URL. Configúralo en .env o en Streamlit Secrets."
            )

        self._connection = psycopg2.connect(database_url, sslmode="require")
        self._connection.autocommit = True
        return self._connection

    def _invalidate_cache(self, sheet_name: str | None = None) -> None:
        if sheet_name is None:
            self._records_cache.clear()
        else:
            self._records_cache.pop(sheet_name, None)

    def _table_name(self, sheet_name: str) -> str:
        table = SHEET_TO_TABLE.get(sheet_name)
        if table is None:
            raise ValueError(f"Tabla no configurada para: {sheet_name}")
        return table

    def get_records(self, sheet_name: str) -> list[dict[str, Any]]:
        now = time.monotonic()
        cached = self._records_cache.get(sheet_name)
        if cached is not None:
            cached_at, records = cached
            if now - cached_at < SHEETS_CACHE_TTL_SECONDS:
                return records

        table = self._table_name(sheet_name)
        headers = SHEET_SCHEMAS[sheet_name]
        query = sql.SQL("SELECT {} FROM {}").format(
            sql.SQL(", ").join(sql.Identifier(column) for column in headers),
            sql.Identifier(table),
        )

        connection = self.connect()
        with connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query)
            rows = cursor.fetchall()

        records = [_serialize_record(dict(row)) for row in rows]
        self._records_cache[sheet_name] = (now, records)
        return records

    def get_dataframe(self, sheet_name: str) -> pd.DataFrame:
        records = self.get_records(sheet_name)
        if not records:
            return pd.DataFrame(columns=SHEET_SCHEMAS[sheet_name])
        return pd.DataFrame(records)

    def append_row(self, sheet_name: str, row: list[Any]) -> None:
        headers = SHEET_SCHEMAS[sheet_name]
        data = {
            header: _normalize_value(header, value)
            for header, value in zip(headers, row, strict=True)
        }
        table = self._table_name(sheet_name)
        columns = list(data.keys())
        values = [data[column] for column in columns]

        query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(", ").join(sql.Identifier(column) for column in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )

        connection = self.connect()
        with connection.cursor() as cursor:
            cursor.execute(query, values)
        self._invalidate_cache(sheet_name)

    def update_row(self, sheet_name: str, row_number: int, row: list[Any]) -> None:
        headers = SHEET_SCHEMAS[sheet_name]
        data = {
            header: _normalize_value(header, value)
            for header, value in zip(headers, row, strict=True)
        }
        record_id = str(data.get("id", "")).strip()
        if not record_id:
            raise ValueError("No se pudo identificar el registro a actualizar.")

        table = self._table_name(sheet_name)
        assignments = [
            sql.SQL("{} = %s").format(sql.Identifier(column))
            for column in headers
            if column != "id"
        ]
        values = [data[column] for column in headers if column != "id"]
        values.append(record_id)

        query = sql.SQL("UPDATE {} SET {} WHERE {} = %s").format(
            sql.Identifier(table),
            sql.SQL(", ").join(assignments),
            sql.Identifier("id"),
        )

        connection = self.connect()
        with connection.cursor() as cursor:
            cursor.execute(query, values)
        self._invalidate_cache(sheet_name)

    def find_row_number(self, sheet_name: str, id_field: str, record_id: str) -> int | None:
        records = self.get_records(sheet_name)
        for index, record in enumerate(records):
            if str(record.get(id_field, "")) == str(record_id):
                return index + 2
        return None

    def delete_row(self, sheet_name: str, row_number: int) -> None:
        records = self.get_records(sheet_name)
        index = row_number - 2
        if index < 0 or index >= len(records):
            return

        record_id = str(records[index].get("id", "")).strip()
        if not record_id:
            return

        table = self._table_name(sheet_name)
        query = sql.SQL("DELETE FROM {} WHERE {} = %s").format(
            sql.Identifier(table),
            sql.Identifier("id"),
        )

        connection = self.connect()
        with connection.cursor() as cursor:
            cursor.execute(query, (record_id,))
        self._invalidate_cache(sheet_name)

    def get_worksheet(self, name: str):
        self.connect()
        return name
