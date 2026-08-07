from __future__ import annotations

from typing import Any

import pandas as pd

from config import (
    CATALOG_SCHEMA,
    DEFAULT_EXPENSE_TYPES,
    DEFAULT_INCOME_TYPES,
    DEFAULT_ORDER_STATES,
    DEFAULT_PRODUCT_CATEGORIES,
    ORDER_STATE_SCHEMA,
    SHEET_CATEGORIAS,
    SHEET_CONTABILIDAD,
    SHEET_ESTADOS_PEDIDO,
    SHEET_PEDIDOS,
    SHEET_PRODUCTOS,
    SHEET_SCHEMAS,
    SHEET_TIPOS_GASTO,
    SHEET_TIPOS_INGRESO,
)
from services.sheets_db import get_db, new_id, now_str


def _is_active(value: Any) -> bool:
    return str(value).strip().lower() in ("si", "sí", "true", "1", "yes")


def _as_yes_no(value: Any) -> str:
    return "Si" if _is_active(value) else "No"


def _sorted_catalog(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "orden" in df.columns:
        df = df.copy()
        df["orden"] = pd.to_numeric(df["orden"], errors="coerce").fillna(999).astype(int)
        return df.sort_values(["orden", "nombre"], ascending=[True, True])
    return df.sort_values("nombre")


def _list_catalog(sheet_name: str, *, active_only: bool = False) -> pd.DataFrame:
    df = get_db().get_dataframe(sheet_name)
    if df.empty:
        return df
    if active_only and "activo" in df.columns:
        df = df[df["activo"].map(_is_active)]
    return _sorted_catalog(df)


def _get_catalog_item(sheet_name: str, item_id: str) -> dict[str, Any] | None:
    df = _list_catalog(sheet_name)
    if df.empty:
        return None
    match = df[df["id"].astype(str) == str(item_id)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def _next_order(sheet_name: str) -> int:
    df = _list_catalog(sheet_name)
    if df.empty or "orden" not in df.columns:
        return 1
    return int(pd.to_numeric(df["orden"], errors="coerce").fillna(0).max()) + 1


def _row_from_item(sheet_name: str, item: dict[str, Any]) -> list[Any]:
    return [item.get(field, "") for field in SHEET_SCHEMAS[sheet_name]]


def _create_catalog_item(sheet_name: str, nombre: str, *, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    name = nombre.strip()
    if not name:
        raise ValueError("El nombre es obligatorio.")

    df = _list_catalog(sheet_name)
    if not df.empty and df["nombre"].astype(str).str.strip().str.lower().eq(name.lower()).any():
        raise ValueError(f"Ya existe un registro con el nombre «{name}».")

    item: dict[str, Any] = {
        "id": new_id("CAT"),
        "nombre": name,
        "activo": "Si",
        "orden": _next_order(sheet_name),
        "fecha_registro": now_str(),
    }
    if extra:
        item.update(extra)

    get_db().append_row(sheet_name, _row_from_item(sheet_name, item))
    return item


def _update_catalog_item(sheet_name: str, item_id: str, updates: dict[str, Any]) -> bool:
    db = get_db()
    row_number = db.find_row_number(sheet_name, "id", item_id)
    if row_number is None:
        return False

    current = _get_catalog_item(sheet_name, item_id)
    if current is None:
        return False

    if "nombre" in updates:
        new_name = str(updates["nombre"]).strip()
        if not new_name:
            raise ValueError("El nombre es obligatorio.")
        df = _list_catalog(sheet_name)
        duplicates = df[
            (df["id"].astype(str) != str(item_id))
            & (df["nombre"].astype(str).str.strip().str.lower() == new_name.lower())
        ]
        if not duplicates.empty:
            raise ValueError(f"Ya existe un registro con el nombre «{new_name}».")
        current["nombre"] = new_name

    if "activo" in updates:
        current["activo"] = _as_yes_no(updates["activo"])

    if "orden" in updates:
        current["orden"] = int(updates["orden"])

    for key, value in updates.items():
        if key in ("nombre", "activo", "orden"):
            continue
        if key in current:
            if key in ("genera_venta", "revierte_venta"):
                current[key] = _as_yes_no(value)
            else:
                current[key] = value

    db.update_row(sheet_name, row_number, _row_from_item(sheet_name, current))
    return True


def _delete_catalog_item(sheet_name: str, item_id: str) -> bool:
    db = get_db()
    row_number = db.find_row_number(sheet_name, "id", item_id)
    if row_number is None:
        return False
    db.delete_row(sheet_name, row_number)
    return True


def _seed_simple_catalog(sheet_name: str, names: list[str]) -> None:
    df = get_db().get_dataframe(sheet_name)
    if not df.empty:
        return
    for index, name in enumerate(names, start=1):
        item = {
            "id": new_id("CAT"),
            "nombre": name,
            "activo": "Si",
            "orden": index,
            "fecha_registro": now_str(),
        }
        get_db().append_row(sheet_name, _row_from_item(sheet_name, item))


def _seed_order_states() -> None:
    df = get_db().get_dataframe(SHEET_ESTADOS_PEDIDO)
    if not df.empty:
        return
    for index, state in enumerate(DEFAULT_ORDER_STATES, start=1):
        item = {
            "id": new_id("EST"),
            "nombre": state["nombre"],
            "activo": "Si",
            "orden": index,
            "genera_venta": state["genera_venta"],
            "revierte_venta": state["revierte_venta"],
            "fecha_registro": now_str(),
        }
        get_db().append_row(SHEET_ESTADOS_PEDIDO, _row_from_item(SHEET_ESTADOS_PEDIDO, item))


def ensure_catalog_defaults() -> None:
    """Crea catálogos iniciales si las hojas están vacías."""
    _seed_simple_catalog(SHEET_CATEGORIAS, DEFAULT_PRODUCT_CATEGORIES)
    _seed_simple_catalog(SHEET_TIPOS_INGRESO, DEFAULT_INCOME_TYPES)
    _seed_simple_catalog(SHEET_TIPOS_GASTO, DEFAULT_EXPENSE_TYPES)
    _seed_order_states()


def list_product_categories(*, active_only: bool = False) -> pd.DataFrame:
    return _list_catalog(SHEET_CATEGORIAS, active_only=active_only)


def list_income_types(*, active_only: bool = False) -> pd.DataFrame:
    return _list_catalog(SHEET_TIPOS_INGRESO, active_only=active_only)


def list_expense_types(*, active_only: bool = False) -> pd.DataFrame:
    return _list_catalog(SHEET_TIPOS_GASTO, active_only=active_only)


def list_order_states(*, active_only: bool = False) -> pd.DataFrame:
    return _list_catalog(SHEET_ESTADOS_PEDIDO, active_only=active_only)


def product_category_names(*, active_only: bool = True) -> list[str]:
    df = list_product_categories(active_only=active_only)
    if df.empty:
        return list(DEFAULT_PRODUCT_CATEGORIES)
    return df["nombre"].astype(str).tolist()


def income_type_names(*, active_only: bool = True) -> list[str]:
    df = list_income_types(active_only=active_only)
    if df.empty:
        return list(DEFAULT_INCOME_TYPES)
    return df["nombre"].astype(str).tolist()


def expense_type_names(*, active_only: bool = True) -> list[str]:
    df = list_expense_types(active_only=active_only)
    if df.empty:
        return list(DEFAULT_EXPENSE_TYPES)
    return df["nombre"].astype(str).tolist()


def order_state_names(*, active_only: bool = True) -> list[str]:
    df = list_order_states(active_only=active_only)
    if df.empty:
        return [state["nombre"] for state in DEFAULT_ORDER_STATES]
    return df["nombre"].astype(str).tolist()


def get_default_order_state_name() -> str:
    names = order_state_names(active_only=True)
    return names[0] if names else DEFAULT_ORDER_STATES[0]["nombre"]


def _get_order_state_row(state_name: str) -> dict[str, Any] | None:
    df = list_order_states()
    if df.empty:
        for state in DEFAULT_ORDER_STATES:
            if state["nombre"] == state_name:
                return {
                    "nombre": state["nombre"],
                    "genera_venta": state["genera_venta"],
                    "revierte_venta": state["revierte_venta"],
                    "activo": "Si",
                }
        return None
    match = df[df["nombre"].astype(str) == str(state_name)]
    if match.empty:
        return None
    return match.iloc[0].to_dict()


def state_generates_sale(state_name: str) -> bool:
    row = _get_order_state_row(state_name)
    if row is None:
        return state_name == "Entregado"
    return _is_active(row.get("genera_venta", "No"))


def state_reverses_sale(state_name: str) -> bool:
    row = _get_order_state_row(state_name)
    if row is None:
        return state_name == "Cancelado"
    return _is_active(row.get("revierte_venta", "No"))


def validate_order_state(state_name: str, *, active_only: bool = True) -> bool:
    return state_name in order_state_names(active_only=active_only)


def create_product_category(nombre: str) -> dict[str, Any]:
    return _create_catalog_item(SHEET_CATEGORIAS, nombre)


def update_product_category(item_id: str, updates: dict[str, Any]) -> bool:
    return _update_catalog_item(SHEET_CATEGORIAS, item_id, updates)


def delete_product_category(item_id: str) -> None:
    current = _get_catalog_item(SHEET_CATEGORIAS, item_id)
    if current is None:
        raise ValueError("Categoría no encontrada.")
    name = str(current.get("nombre", ""))
    products = get_db().get_dataframe(SHEET_PRODUCTOS)
    if not products.empty and products["categoria"].astype(str).eq(name).any():
        raise ValueError(
            f"No se puede eliminar «{name}» porque hay productos que la usan. "
            "Inactívala en su lugar."
        )
    if not _delete_catalog_item(SHEET_CATEGORIAS, item_id):
        raise ValueError("No se pudo eliminar la categoría.")


def create_income_type(nombre: str) -> dict[str, Any]:
    return _create_catalog_item(SHEET_TIPOS_INGRESO, nombre)


def update_income_type(item_id: str, updates: dict[str, Any]) -> bool:
    return _update_catalog_item(SHEET_TIPOS_INGRESO, item_id, updates)


def delete_income_type(item_id: str) -> None:
    current = _get_catalog_item(SHEET_TIPOS_INGRESO, item_id)
    if current is None:
        raise ValueError("Tipo de ingreso no encontrado.")
    name = str(current.get("nombre", ""))
    movements = get_db().get_dataframe(SHEET_CONTABILIDAD)
    if not movements.empty:
        used = movements[
            (movements["tipo"].astype(str) == "Ingreso")
            & (movements["categoria"].astype(str) == name)
        ]
        if not used.empty:
            raise ValueError(
                f"No se puede eliminar «{name}» porque hay movimientos que lo usan. "
                "Inactívalo en su lugar."
            )
    if not _delete_catalog_item(SHEET_TIPOS_INGRESO, item_id):
        raise ValueError("No se pudo eliminar el tipo de ingreso.")


def create_expense_type(nombre: str) -> dict[str, Any]:
    return _create_catalog_item(SHEET_TIPOS_GASTO, nombre)


def update_expense_type(item_id: str, updates: dict[str, Any]) -> bool:
    return _update_catalog_item(SHEET_TIPOS_GASTO, item_id, updates)


def delete_expense_type(item_id: str) -> None:
    current = _get_catalog_item(SHEET_TIPOS_GASTO, item_id)
    if current is None:
        raise ValueError("Tipo de gasto no encontrado.")
    name = str(current.get("nombre", ""))
    movements = get_db().get_dataframe(SHEET_CONTABILIDAD)
    if not movements.empty:
        used = movements[
            (movements["tipo"].astype(str) == "Gasto")
            & (movements["categoria"].astype(str) == name)
        ]
        if not used.empty:
            raise ValueError(
                f"No se puede eliminar «{name}» porque hay movimientos que lo usan. "
                "Inactívalo en su lugar."
            )
    if not _delete_catalog_item(SHEET_TIPOS_GASTO, item_id):
        raise ValueError("No se pudo eliminar el tipo de gasto.")


def create_order_state(
    nombre: str,
    *,
    genera_venta: bool = False,
    revierte_venta: bool = False,
) -> dict[str, Any]:
    return _create_catalog_item(
        SHEET_ESTADOS_PEDIDO,
        nombre,
        extra={
            "genera_venta": _as_yes_no(genera_venta),
            "revierte_venta": _as_yes_no(revierte_venta),
        },
    )


def update_order_state(item_id: str, updates: dict[str, Any]) -> bool:
    return _update_catalog_item(SHEET_ESTADOS_PEDIDO, item_id, updates)


def delete_order_state(item_id: str) -> None:
    current = _get_catalog_item(SHEET_ESTADOS_PEDIDO, item_id)
    if current is None:
        raise ValueError("Estado no encontrado.")
    name = str(current.get("nombre", ""))
    orders = get_db().get_dataframe(SHEET_PEDIDOS)
    if not orders.empty and orders["estado"].astype(str).eq(name).any():
        raise ValueError(
            f"No se puede eliminar «{name}» porque hay pedidos con ese estado. "
            "Inactívalo en su lugar."
        )
    active_states = list_order_states(active_only=True)
    if _is_active(current.get("activo")) and len(active_states) <= 1:
        raise ValueError("Debe quedar al menos un estado de pedido activo.")
    if not _delete_catalog_item(SHEET_ESTADOS_PEDIDO, item_id):
        raise ValueError("No se pudo eliminar el estado.")
