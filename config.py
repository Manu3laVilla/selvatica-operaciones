import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CREDENTIALS_PATH = os.getenv(
    "GOOGLE_CREDENTIALS_PATH",
    str(BASE_DIR / "credentials" / "service_account.json"),
)
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID", "")


def is_preview_mode() -> bool:
    if os.getenv("PREVIEW_MODE", "").lower() in ("1", "true", "yes"):
        return True
    if not SPREADSHEET_ID:
        return True
    return not Path(CREDENTIALS_PATH).exists()

SHEET_PRODUCTOS = "Productos"
SHEET_CLIENTES = "Clientes"
SHEET_VENTAS = "Ventas"
SHEET_PEDIDOS = "Pedidos"
SHEET_CONTABILIDAD = "Contabilidad"

ORDER_STATES = [
    "Pendiente",
    "Confirmado",
    "En preparación",
    "Enviado",
    "Entregado",
    "Cancelado",
]

ACCESSORY_CATEGORIES = [
    "Collares",
    "Pulseras",
    "Aretes",
    "Anillos",
    "Broches",
    "Bolsos",
    "Cinturones",
    "Gorras y sombreros",
    "Otros",
]

INCOME_CATEGORIES = [
    "Capital",
    "Inversión",
    "Otro ingreso",
]

EXPENSE_CATEGORIES = [
    "Insumos",
    "Equipos",
    "Gasto extra",
    "Otro gasto",
]

MOVEMENT_TYPES = ["Ingreso", "Gasto"]

SHEET_SCHEMAS = {
    SHEET_PRODUCTOS: [
        "id",
        "nombre",
        "descripcion",
        "categoria",
        "precio",
        "stock",
        "stock_minimo",
        "activo",
        "fecha_registro",
    ],
    SHEET_CLIENTES: [
        "id",
        "nombre",
        "email",
        "telefono",
        "direccion",
        "notas",
        "fecha_registro",
    ],
    SHEET_VENTAS: [
        "id",
        "fecha",
        "cliente_id",
        "cliente_nombre",
        "producto_id",
        "producto_nombre",
        "cantidad",
        "precio_unitario",
        "subtotal",
        "pedido_id",
    ],
    SHEET_PEDIDOS: [
        "id",
        "cliente_id",
        "cliente_nombre",
        "items_json",
        "total",
        "estado",
        "fecha_creacion",
        "fecha_actualizacion",
        "notas",
    ],
    SHEET_CONTABILIDAD: [
        "id",
        "fecha",
        "tipo",
        "categoria",
        "concepto",
        "monto",
        "notas",
    ],
}

CURRENCY_CODE = "COP"


def format_cop(amount: float | int | None) -> str:
    """Formatea un valor en pesos colombianos (ej. $28.500)."""
    if amount is None:
        return ""
    try:
        value = round(float(amount))
    except (TypeError, ValueError):
        return str(amount)

    sign = "-" if value < 0 else ""
    absolute = abs(value)
    text = f"{absolute:,}".replace(",", ".")
    return f"{sign}${text}"


CURRENCY_COLUMN_NAMES = {
    "precio",
    "precio_unitario",
    "subtotal",
    "monto",
    "total",
    "subtotal",
}
