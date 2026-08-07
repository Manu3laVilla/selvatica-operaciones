from __future__ import annotations

import time
import uuid
from datetime import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread.exceptions import APIError

from config import (
    CREDENTIALS_PATH,
    SHEET_SCHEMAS,
    SHEETS_CACHE_TTL_SECONDS,
    get_service_account_info,
    get_spreadsheet_id,
    has_google_credentials,
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


def _load_credentials() -> Credentials:
    creds_path = Path(CREDENTIALS_PATH)
    if creds_path.exists():
        return Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)

    if has_google_credentials():
        service_account_info = get_service_account_info()
        if service_account_info:
            return Credentials.from_service_account_info(
                service_account_info,
                scopes=SCOPES,
            )

    raise FileNotFoundError(
        f"No se encontró el archivo de credenciales en: {creds_path}. "
        "Configura credentials/service_account.json localmente o "
        "gcp_service_account en Streamlit Secrets."
    )


class SheetsDB:
    def __init__(self) -> None:
        self._client: gspread.Client | None = None
        self._spreadsheet: gspread.Spreadsheet | None = None
        self._worksheets: dict[str, gspread.Worksheet] = {}
        self._values_cache: dict[str, tuple[float, list[list[str]]]] = {}
        self._sheets_verified = False

    def connect(self) -> gspread.Spreadsheet:
        if self._spreadsheet is not None:
            return self._spreadsheet

        spreadsheet_id = get_spreadsheet_id()
        if not spreadsheet_id:
            raise ValueError(
                "Falta SPREADSHEET_ID. Configúralo en .env o en Streamlit Secrets."
            )

        credentials = _load_credentials()
        self._client = gspread.authorize(credentials)
        self._spreadsheet = self._client.open_by_key(spreadsheet_id)
        self._ensure_sheets()
        return self._spreadsheet

    def _ensure_sheets(self) -> None:
        if self._sheets_verified:
            return

        assert self._spreadsheet is not None
        existing = {ws.title for ws in self._spreadsheet.worksheets()}

        for sheet_name, headers in SHEET_SCHEMAS.items():
            if sheet_name not in existing:
                worksheet = self._spreadsheet.add_worksheet(
                    title=sheet_name, rows=1000, cols=len(headers)
                )
                worksheet.append_row(headers)
            else:
                worksheet = self._spreadsheet.worksheet(sheet_name)
                current = worksheet.row_values(1)
                if current != headers:
                    worksheet.update("A1", [headers])

        self._sheets_verified = True

    def _invalidate_sheet_cache(self, sheet_name: str | None = None) -> None:
        if sheet_name is None:
            self._values_cache.clear()
        else:
            self._values_cache.pop(sheet_name, None)

    def _get_sheet_values(self, sheet_name: str) -> list[list[str]]:
        now = time.monotonic()
        cached = self._values_cache.get(sheet_name)
        if cached is not None:
            cached_at, values = cached
            if now - cached_at < SHEETS_CACHE_TTL_SECONDS:
                return values

        worksheet = self.get_worksheet(sheet_name)
        try:
            values = worksheet.get_all_values()
        except APIError as exc:
            if cached is not None and "429" in str(exc):
                return cached[1]
            raise

        self._values_cache[sheet_name] = (now, values)
        return values

    def get_worksheet(self, name: str) -> gspread.Worksheet:
        if name in self._worksheets:
            return self._worksheets[name]

        spreadsheet = self.connect()
        worksheet = spreadsheet.worksheet(name)
        self._worksheets[name] = worksheet
        return worksheet

    def get_records(self, sheet_name: str) -> list[dict[str, Any]]:
        values = self._get_sheet_values(sheet_name)
        if not values:
            return []

        headers = [str(cell).strip() for cell in values[0]]
        if not headers or not any(headers):
            return []

        records: list[dict[str, Any]] = []
        for row in values[1:]:
            if not any(str(cell).strip() for cell in row):
                continue
            padded = row + [""] * max(0, len(headers) - len(row))
            records.append(
                {
                    headers[index]: padded[index]
                    for index in range(len(headers))
                    if headers[index]
                }
            )
        return records

    def get_dataframe(self, sheet_name: str) -> pd.DataFrame:
        records = self.get_records(sheet_name)
        if not records:
            headers = SHEET_SCHEMAS[sheet_name]
            return pd.DataFrame(columns=headers)
        return pd.DataFrame(records)

    def append_row(self, sheet_name: str, row: list[Any]) -> None:
        worksheet = self.get_worksheet(sheet_name)
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        self._invalidate_sheet_cache(sheet_name)

    def update_row(self, sheet_name: str, row_number: int, row: list[Any]) -> None:
        worksheet = self.get_worksheet(sheet_name)
        headers = SHEET_SCHEMAS[sheet_name]
        cell_range = f"A{row_number}:{chr(64 + len(headers))}{row_number}"
        worksheet.update(cell_range, [row], value_input_option="USER_ENTERED")
        self._invalidate_sheet_cache(sheet_name)

    def find_row_number(self, sheet_name: str, id_field: str, record_id: str) -> int | None:
        values = self._get_sheet_values(sheet_name)
        if not values:
            return None

        headers = [str(cell).strip() for cell in values[0]]
        if id_field not in headers:
            return None

        id_col = headers.index(id_field)
        for index, row in enumerate(values[1:], start=2):
            if len(row) > id_col and str(row[id_col]) == str(record_id):
                return index
        return None

    def delete_row(self, sheet_name: str, row_number: int) -> None:
        worksheet = self.get_worksheet(sheet_name)
        worksheet.delete_rows(row_number)
        self._invalidate_sheet_cache(sheet_name)


@lru_cache(maxsize=1)
def get_db() -> SheetsDB:
    return SheetsDB()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
