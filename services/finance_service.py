from __future__ import annotations

from datetime import date, datetime
from typing import Any

import pandas as pd

from config import SHEET_CONTABILIDAD
from services.db import get_db, new_id, now_str


def format_movement_date(value: date | datetime | str | None = None) -> str:
    if value is None:
        return now_str()

    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(value, date):
        return f"{value.strftime('%Y-%m-%d')} 00:00:00"

    text = str(value).strip()
    if not text:
        return now_str()

    parsed = pd.to_datetime(text, errors="coerce")
    if pd.isna(parsed):
        return now_str()
    return parsed.strftime("%Y-%m-%d %H:%M:%S")


def list_movements() -> pd.DataFrame:
    df = get_db().get_dataframe(SHEET_CONTABILIDAD)
    if df.empty:
        return df

    if "monto" in df.columns:
        df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    return df.sort_values("fecha", ascending=False) if "fecha" in df.columns else df


def get_movement(movement_id: str) -> dict[str, Any] | None:
    df = list_movements()
    if df.empty:
        return None
    match = df[df["id"].astype(str) == str(movement_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def register_movement(
    tipo: str,
    categoria: str,
    concepto: str,
    monto: float,
    notas: str = "",
    *,
    fecha: date | datetime | str | None = None,
) -> dict[str, Any]:
    amount = float(monto)
    if amount <= 0:
        raise ValueError("El monto debe ser mayor a cero.")

    concept = concepto.strip()
    if not concept:
        raise ValueError("El concepto es obligatorio.")

    category = categoria.strip()
    if not category:
        raise ValueError("La categoría es obligatoria.")

    movement = {
        "id": new_id("FIN"),
        "fecha": format_movement_date(fecha),
        "tipo": tipo,
        "categoria": category,
        "concepto": concept,
        "monto": amount,
        "notas": notas.strip(),
    }

    get_db().append_row(SHEET_CONTABILIDAD, list(movement.values()))
    return movement


def update_movement(movement_id: str, updates: dict[str, Any]) -> bool:
    db = get_db()
    row_number = db.find_row_number(SHEET_CONTABILIDAD, "id", movement_id)
    if row_number is None:
        return False

    movement = get_movement(movement_id)
    if movement is None:
        return False

    if "fecha" in updates:
        updates["fecha"] = format_movement_date(updates["fecha"])
    if "concepto" in updates:
        updates["concepto"] = str(updates["concepto"]).strip()
    if "categoria" in updates:
        updates["categoria"] = str(updates["categoria"]).strip()
    if "notas" in updates:
        updates["notas"] = str(updates["notas"]).strip()
    if "monto" in updates:
        amount = float(updates["monto"])
        if amount <= 0:
            raise ValueError("El monto debe ser mayor a cero.")
        updates["monto"] = amount

    movement.update(updates)
    if not str(movement.get("concepto", "")).strip():
        raise ValueError("El concepto es obligatorio.")
    if not str(movement.get("categoria", "")).strip():
        raise ValueError("La categoría es obligatoria.")

    db.update_row(SHEET_CONTABILIDAD, row_number, list(movement.values()))
    return True
