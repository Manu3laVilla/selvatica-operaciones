from __future__ import annotations

from typing import Any

import pandas as pd

from config import SHEET_CLIENTES
from services.sheets_db import get_db, new_id, now_str


def list_customers() -> pd.DataFrame:
    return get_db().get_dataframe(SHEET_CLIENTES)


def get_customer(customer_id: str) -> dict[str, Any] | None:
    df = list_customers()
    if df.empty:
        return None
    match = df[df["id"].astype(str) == str(customer_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def create_customer(
    nombre: str,
    email: str,
    telefono: str,
    direccion: str,
    notas: str = "",
) -> dict[str, Any]:
    customer = {
        "id": new_id("CLI"),
        "nombre": nombre.strip(),
        "email": email.strip(),
        "telefono": telefono.strip(),
        "direccion": direccion.strip(),
        "notas": notas.strip(),
        "fecha_registro": now_str(),
    }
    get_db().append_row(SHEET_CLIENTES, list(customer.values()))
    return customer


def update_customer(customer_id: str, updates: dict[str, Any]) -> bool:
    db = get_db()
    row_number = db.find_row_number(SHEET_CLIENTES, "id", customer_id)
    if row_number is None:
        return False

    customer = get_customer(customer_id)
    if customer is None:
        return False

    customer.update(updates)
    db.update_row(SHEET_CLIENTES, row_number, list(customer.values()))
    return True
