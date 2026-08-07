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


def get_spreadsheet_id() -> str:
    env_id = os.getenv("SPREADSHEET_ID", "").strip()
    if env_id:
        return env_id
    try:
        import streamlit as st

        return str(st.secrets.get("SPREADSHEET_ID", "")).strip()
    except Exception:
        return ""


_SERVICE_ACCOUNT_SECRET_KEYS = (
    "gcp_service_account",
    "google_service_account",
    "service_account",
)


def get_service_account_info() -> dict | None:
    try:
        import streamlit as st

        for key in _SERVICE_ACCOUNT_SECRET_KEYS:
            if key in st.secrets:
                return dict(st.secrets[key])
    except Exception:
        pass
    return None


def has_google_credentials() -> bool:
    if Path(CREDENTIALS_PATH).exists():
        return True
    return get_service_account_info() is not None


def is_preview_mode() -> bool:
    if os.getenv("PREVIEW_MODE", "").lower() in ("1", "true", "yes"):
        return True
    if not get_spreadsheet_id():
        return True
    return not has_google_credentials()

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

# Segundos que se reutilizan lecturas de Google Sheets entre reruns de Streamlit.
SHEETS_CACHE_TTL_SECONDS = 60


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
