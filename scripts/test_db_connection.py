"""Prueba la conexión Postgres usando variables de .env (sin imprimir contraseñas)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_database_url, resolves_data_backend
from services.postgres_db import PostgresDB


def main() -> None:
    backend = resolves_data_backend()
    url = get_database_url()
    print(f"backend={backend or '(ninguno)'}")
    if not url:
        print("Falta DATABASE_URL o DATABASE_POOLER_URL en .env")
        return
    host = url.split("@")[-1].split("/")[0]
    print(f"host={host}")
    try:
        PostgresDB().connect()
        print("Conexión OK")
    except Exception as exc:
        print(f"Conexión falló: {exc}")


if __name__ == "__main__":
    main()
