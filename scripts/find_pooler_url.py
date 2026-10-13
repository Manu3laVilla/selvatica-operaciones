"""Encuentra el host del Session pooler de Supabase probando regiones conocidas."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import quote_plus, unquote, urlparse

import psycopg2
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT / ".env"

REGIONS = (
    "us-east-1",
    "us-east-2",
    "us-west-1",
    "us-west-2",
    "eu-west-1",
    "eu-west-2",
    "eu-central-1",
    "ap-southeast-1",
    "ap-southeast-2",
    "ap-northeast-1",
    "sa-east-1",
    "ca-central-1",
)
INDEXES = ("0", "1")


def parse_pg_url(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url)
    if not parsed.hostname or not parsed.password:
        raise ValueError("DATABASE_URL inválida")
    user = unquote(parsed.username or "")
    password = unquote(parsed.password)
    ref_match = re.search(r"([a-z0-9]{20})", parsed.hostname or user)
    project_ref = user.split(".")[-1] if "." in user else (ref_match.group(1) if ref_match else "")
    if not project_ref:
        raise ValueError("No se pudo detectar el project ref de Supabase")
    return project_ref, password, user


def build_pooler_url(project_ref: str, password: str, host: str, port: int = 5432) -> str:
    user = quote_plus(f"postgres.{project_ref}")
    pwd = quote_plus(password)
    return f"postgresql://{user}:{pwd}@{host}:{port}/postgres"


def try_connect(url: str) -> bool:
    try:
        conn = psycopg2.connect(url, sslmode="require", connect_timeout=8)
        conn.close()
        return True
    except Exception as exc:
        msg = str(exc).lower()
        if "password authentication failed" in msg:
            print("  Host correcto pero contraseña incorrecta.")
            return False
        return False


def main() -> int:
    load_dotenv(ENV_PATH)
    direct = (ROOT / ".env").read_text(encoding="utf-8")
    import os

    base_url = os.getenv("DATABASE_URL", "").strip()
    if not base_url:
        print("Falta DATABASE_URL en .env")
        return 1

    project_ref, password, _user = parse_pg_url(base_url)
    print(f"Proyecto: {project_ref}")
    print("Buscando Session pooler (IPv4)...")

    for index in INDEXES:
        for region in REGIONS:
            host = f"aws-{index}-{region}.pooler.supabase.com"
            url = build_pooler_url(project_ref, password, host, 5432)
            if try_connect(url):
                print(f"OK: {host}:5432")
                line = f"DATABASE_POOLER_URL={url}\n"
                text = ENV_PATH.read_text(encoding="utf-8")
                if "DATABASE_POOLER_URL=" in text:
                    text = re.sub(
                        r"^#?\s*DATABASE_POOLER_URL=.*$",
                        line.strip(),
                        text,
                        flags=re.MULTILINE,
                    )
                else:
                    text = text.rstrip() + "\n\n" + line
                ENV_PATH.write_text(text, encoding="utf-8")
                print(f"Actualizado {ENV_PATH.name} con DATABASE_POOLER_URL")
                return 0
    print(
        "No se encontró pooler automáticamente. En Supabase → Connect → "
        "Session pooler, copia la URI y pégala como DATABASE_POOLER_URL en .env"
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
