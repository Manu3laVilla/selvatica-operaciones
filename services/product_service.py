from __future__ import annotations

from typing import Any

import pandas as pd

from config import SHEET_PRODUCTOS
from services.sheets_db import get_db, new_id, now_str


def list_products(active_only: bool = False) -> pd.DataFrame:
    df = get_db().get_dataframe(SHEET_PRODUCTOS)
    if df.empty:
        return df

    for col in ("precio", "stock", "stock_minimo"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    if active_only and "activo" in df.columns:
        df = df[df["activo"].astype(str).str.lower().isin(["si", "sí", "true", "1", "yes"])]
    return df


def get_product(product_id: str) -> dict[str, Any] | None:
    df = list_products()
    if df.empty:
        return None
    match = df[df["id"].astype(str) == str(product_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def create_product(
    nombre: str,
    descripcion: str,
    categoria: str,
    precio: float,
    stock: int,
    stock_minimo: int,
) -> dict[str, Any]:
    product = {
        "id": new_id("PRD"),
        "nombre": nombre.strip(),
        "descripcion": descripcion.strip(),
        "categoria": categoria.strip(),
        "precio": float(precio),
        "stock": int(stock),
        "stock_minimo": int(stock_minimo),
        "activo": "Si",
        "fecha_registro": now_str(),
    }
    get_db().append_row(SHEET_PRODUCTOS, list(product.values()))
    return product


def update_product(product_id: str, updates: dict[str, Any]) -> bool:
    db = get_db()
    row_number = db.find_row_number(SHEET_PRODUCTOS, "id", product_id)
    if row_number is None:
        return False

    product = get_product(product_id)
    if product is None:
        return False

    product.update(updates)
    db.update_row(SHEET_PRODUCTOS, row_number, list(product.values()))
    return True


def adjust_stock(product_id: str, delta: int) -> bool:
    product = get_product(product_id)
    if product is None:
        return False

    new_stock = int(product.get("stock", 0)) + int(delta)
    if new_stock < 0:
        raise ValueError("Stock insuficiente para esta operación.")

    return update_product(product_id, {"stock": new_stock})
