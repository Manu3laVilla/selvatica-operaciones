from __future__ import annotations

import json
from typing import Any

import pandas as pd

from config import ORDER_STATES, SHEET_PEDIDOS
from services.product_service import adjust_stock, get_product
from services.sale_service import register_sale, register_sales_from_order
from services.sheets_db import get_db, new_id, now_str


def list_orders() -> pd.DataFrame:
    df = get_db().get_dataframe(SHEET_PEDIDOS)
    if df.empty:
        return df

    if "total" in df.columns:
        df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
    return df.sort_values("fecha_creacion", ascending=False) if "fecha_creacion" in df.columns else df


def get_order(order_id: str) -> dict[str, Any] | None:
    df = list_orders()
    if df.empty:
        return None
    match = df[df["id"].astype(str) == str(order_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def _parse_items(items_json: str) -> list[dict[str, Any]]:
    if not items_json:
        return []
    try:
        items = json.loads(items_json)
        return items if isinstance(items, list) else []
    except json.JSONDecodeError:
        return []


def create_order(
    cliente_id: str,
    cliente_nombre: str,
    items: list[dict[str, Any]],
    notas: str = "",
    register_sales: bool = False,
) -> dict[str, Any]:
    if not items:
        raise ValueError("El pedido debe incluir al menos un producto.")

    normalized_items: list[dict[str, Any]] = []
    total = 0.0

    for item in items:
        product = get_product(str(item["producto_id"]))
        if product is None:
            raise ValueError(f"Producto no encontrado: {item['producto_id']}")

        qty = int(item["cantidad"])
        if qty <= 0:
            raise ValueError("Cada producto debe tener cantidad mayor a cero.")

        price = float(product.get("precio", 0))
        subtotal = price * qty
        total += subtotal

        normalized_items.append(
            {
                "producto_id": product["id"],
                "producto_nombre": product.get("nombre", ""),
                "cantidad": qty,
                "precio_unitario": price,
                "subtotal": subtotal,
            }
        )

    order_id = new_id("PED")
    order = {
        "id": order_id,
        "cliente_id": cliente_id,
        "cliente_nombre": cliente_nombre,
        "items_json": json.dumps(normalized_items, ensure_ascii=False),
        "total": total,
        "estado": "Pendiente",
        "fecha_creacion": now_str(),
        "fecha_actualizacion": now_str(),
        "notas": notas.strip(),
    }
    get_db().append_row(SHEET_PEDIDOS, list(order.values()))

    if register_sales:
        for item in normalized_items:
            register_sale(
                cliente_id=cliente_id,
                cliente_nombre=cliente_nombre,
                producto_id=item["producto_id"],
                cantidad=item["cantidad"],
                pedido_id=order_id,
            )

    return order


def update_order_status(order_id: str, new_status: str) -> bool:
    if new_status not in ORDER_STATES:
        raise ValueError(f"Estado inválido. Usa uno de: {', '.join(ORDER_STATES)}")

    db = get_db()
    row_number = db.find_row_number(SHEET_PEDIDOS, "id", order_id)
    if row_number is None:
        return False

    order = get_order(order_id)
    if order is None:
        return False

    previous_status = str(order.get("estado", ""))
    order["estado"] = new_status
    order["fecha_actualizacion"] = now_str()
    db.update_row(SHEET_PEDIDOS, row_number, list(order.values()))

    items = _parse_items(str(order.get("items_json", "")))

    if previous_status != "Entregado" and new_status == "Entregado":
        register_sales_from_order(order, items)

    if previous_status != "Cancelado" and new_status == "Cancelado":
        for item in items:
            adjust_stock(str(item["producto_id"]), int(item["cantidad"]))

    return True


def get_order_items(order_id: str) -> list[dict[str, Any]]:
    order = get_order(order_id)
    if order is None:
        return []
    return _parse_items(str(order.get("items_json", "")))
