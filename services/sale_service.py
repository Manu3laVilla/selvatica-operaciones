from __future__ import annotations

from typing import Any

import pandas as pd

from config import SHEET_VENTAS
from services.product_service import adjust_stock, get_product
from services.db import get_db, new_id, now_str


def list_sales() -> pd.DataFrame:
    df = get_db().get_dataframe(SHEET_VENTAS)
    if df.empty:
        return df

    for col in ("cantidad", "precio_unitario", "subtotal"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df.sort_values("fecha", ascending=False) if "fecha" in df.columns else df


def sales_exist_for_order(pedido_id: str) -> bool:
    df = list_sales()
    if df.empty or "pedido_id" not in df.columns:
        return False
    return (
        df["pedido_id"]
        .astype(str)
        .str.strip()
        .eq(str(pedido_id).strip())
        .any()
    )


def register_sale(
    cliente_id: str,
    cliente_nombre: str,
    producto_id: str,
    cantidad: int,
    pedido_id: str = "",
    *,
    precio_unitario: float | None = None,
    producto_nombre: str | None = None,
    adjust_inventory: bool = True,
) -> dict[str, Any]:
    product = get_product(producto_id)
    if product is None:
        raise ValueError("Producto no encontrado.")

    qty = int(cantidad)
    if qty <= 0:
        raise ValueError("La cantidad debe ser mayor a cero.")

    price = (
        float(precio_unitario)
        if precio_unitario is not None
        else float(product.get("precio", 0))
    )
    subtotal = price * qty

    sale = {
        "id": new_id("VTA"),
        "fecha": now_str(),
        "cliente_id": cliente_id,
        "cliente_nombre": cliente_nombre,
        "producto_id": producto_id,
        "producto_nombre": producto_nombre or product.get("nombre", ""),
        "cantidad": qty,
        "precio_unitario": price,
        "subtotal": subtotal,
        "pedido_id": pedido_id,
    }

    if adjust_inventory:
        adjust_stock(producto_id, -qty)
    get_db().append_row(SHEET_VENTAS, list(sale.values()))
    return sale


def register_sales_from_order(order: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    order_id = str(order.get("id", "")).strip()
    if not order_id or sales_exist_for_order(order_id):
        return []

    cliente_id = str(order.get("cliente_id", ""))
    cliente_nombre = str(order.get("cliente_nombre", ""))
    created: list[dict[str, Any]] = []

    for item in items:
        sale = register_sale(
            cliente_id=cliente_id,
            cliente_nombre=cliente_nombre,
            producto_id=str(item["producto_id"]),
            cantidad=int(item["cantidad"]),
            pedido_id=order_id,
            precio_unitario=float(item.get("precio_unitario", 0)),
            producto_nombre=str(item.get("producto_nombre", "")),
            adjust_inventory=False,
        )
        created.append(sale)

    return created


def reverse_sales_for_order(pedido_id: str) -> list[dict[str, Any]]:
    db = get_db()
    df = list_sales()
    if df.empty or "pedido_id" not in df.columns:
        return []

    matches = df[df["pedido_id"].astype(str).str.strip() == str(pedido_id).strip()]
    if matches.empty:
        return []

    row_numbers: list[tuple[int, dict[str, Any]]] = []
    for _, sale in matches.iterrows():
        row_number = db.find_row_number(SHEET_VENTAS, "id", str(sale["id"]))
        if row_number is not None:
            row_numbers.append((row_number, sale.to_dict()))

    reversed_sales: list[dict[str, Any]] = []
    for row_number, sale in sorted(row_numbers, key=lambda item: item[0], reverse=True):
        adjust_stock(str(sale["producto_id"]), int(sale["cantidad"]))
        db.delete_row(SHEET_VENTAS, row_number)
        reversed_sales.append(sale)

    return reversed_sales
