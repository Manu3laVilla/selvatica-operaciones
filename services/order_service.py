from __future__ import annotations

import json
from typing import Any

import pandas as pd

from config import SHEET_PEDIDOS
from services.catalog_service import (
    get_default_order_state_name,
    state_generates_sale,
    state_reverses_sale,
    validate_order_state,
)
from services.product_service import adjust_stock, get_product
from services.sale_service import (
    register_sales_from_order,
    reverse_sales_for_order,
    sales_exist_for_order,
)
from services.db import get_db, new_id, now_str


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


def reserve_stock_for_items(items: list[dict[str, Any]]) -> None:
    """Reserva inventario descontando stock (al crear o reactivar un pedido)."""
    for item in items:
        product_id = str(item["producto_id"])
        qty = int(item["cantidad"])
        product = get_product(product_id)
        if product is None:
            raise ValueError(f"Producto no encontrado: {product_id}")

        stock = int(product.get("stock", 0))
        if qty > stock:
            name = str(product.get("nombre", product_id))
            raise ValueError(f"Stock insuficiente para {name}. Disponible: {stock}")

        adjust_stock(product_id, -qty)


def release_stock_for_items(items: list[dict[str, Any]]) -> None:
    """Libera inventario reservado (cancelación sin venta registrada)."""
    for item in items:
        adjust_stock(str(item["producto_id"]), int(item["cantidad"]))


def _handle_order_status_stock(
    order_id: str,
    items: list[dict[str, Any]],
    *,
    previous_status: str,
    new_status: str,
) -> None:
    moving_to_reverse = state_reverses_sale(new_status)
    moving_from_reverse = state_reverses_sale(previous_status)

    if moving_to_reverse:
        if sales_exist_for_order(order_id):
            reverse_sales_for_order(order_id)
        elif not moving_from_reverse:
            release_stock_for_items(items)

    if (
        moving_from_reverse
        and not moving_to_reverse
        and not sales_exist_for_order(order_id)
    ):
        reserve_stock_for_items(items)


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
        "estado": get_default_order_state_name(),
        "fecha_creacion": now_str(),
        "fecha_actualizacion": now_str(),
        "notas": notas.strip(),
    }
    reserve_stock_for_items(normalized_items)
    get_db().append_row(SHEET_PEDIDOS, list(order.values()))

    if register_sales:
        register_sales_from_order(order, normalized_items)

    return order


def update_order_status(order_id: str, new_status: str) -> bool:
    if not validate_order_state(new_status, active_only=True):
        raise ValueError(f"Estado inválido o inactivo: {new_status}")

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
    _handle_order_status_stock(
        order_id,
        items,
        previous_status=previous_status,
        new_status=new_status,
    )

    if state_generates_sale(new_status) and not sales_exist_for_order(order_id):
        register_sales_from_order(order, items)

    return True


def get_order_items(order_id: str) -> list[dict[str, Any]]:
    order = get_order(order_id)
    if order is None:
        return []
    return _parse_items(str(order.get("items_json", "")))
