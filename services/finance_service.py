from __future__ import annotations

from typing import Any

import pandas as pd

from config import SHEET_CONTABILIDAD
from services.sheets_db import get_db, new_id, now_str


def list_movements() -> pd.DataFrame:
    df = get_db().get_dataframe(SHEET_CONTABILIDAD)
    if df.empty:
        return df

    if "monto" in df.columns:
        df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    return df.sort_values("fecha", ascending=False) if "fecha" in df.columns else df


def register_movement(
    tipo: str,
    categoria: str,
    concepto: str,
    monto: float,
    notas: str = "",
) -> dict[str, Any]:
    amount = float(monto)
    if amount <= 0:
        raise ValueError("El monto debe ser mayor a cero.")

    concept = concepto.strip()
    if not concept:
        raise ValueError("El concepto es obligatorio.")

    movement = {
        "id": new_id("FIN"),
        "fecha": now_str(),
        "tipo": tipo,
        "categoria": categoria,
        "concepto": concept,
        "monto": amount,
        "notas": notas.strip(),
    }

    get_db().append_row(SHEET_CONTABILIDAD, list(movement.values()))
    return movement
