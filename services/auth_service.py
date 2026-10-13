from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time

DEFAULT_SESSION_TTL_SECONDS = 3600
AUTH_COOKIE_NAME = "selv_auth"


def _get_setting(name: str) -> str:
    env_value = os.getenv(name, "").strip()
    if env_value:
        return env_value
    try:
        import streamlit as st

        return str(st.secrets.get(name, "")).strip()
    except Exception:
        return ""


def get_auth_username() -> str:
    return _get_setting("AUTH_USERNAME") or "selvatica"


def get_auth_password() -> str:
    return _get_setting("AUTH_PASSWORD")


def is_auth_enabled() -> bool:
    flag = _get_setting("AUTH_ENABLED").lower()
    if flag in ("0", "false", "no", "off"):
        return False
    if flag in ("1", "true", "yes", "on"):
        return bool(get_auth_password())
    return bool(get_auth_password())


def get_auth_secret() -> bytes:
    raw = _get_setting("AUTH_SECRET") or get_auth_password() or "selvatica-default-secret"
    return hashlib.sha256(raw.encode()).digest()


def create_auth_token(username: str, expires_at: float) -> str:
    payload = json.dumps(
        {"u": username, "exp": expires_at},
        separators=(",", ":"),
    ).encode()
    signature = hmac.new(get_auth_secret(), payload, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(payload + b"." + signature).decode()


def verify_auth_token(token: str) -> tuple[str, float] | None:
    try:
        raw = base64.urlsafe_b64decode(token.encode())
        payload, signature = raw.rsplit(b".", 1)
        expected = hmac.new(get_auth_secret(), payload, hashlib.sha256).digest()
        if not hmac.compare_digest(signature, expected):
            return None
        data = json.loads(payload.decode())
        expires_at = float(data["exp"])
        if time.time() >= expires_at:
            return None
        return str(data["u"]), expires_at
    except Exception:
        return None


def get_session_ttl_seconds() -> int:
    raw_seconds = _get_setting("AUTH_SESSION_SECONDS")
    if raw_seconds.isdigit():
        return max(60, int(raw_seconds))
    raw_hours = _get_setting("AUTH_SESSION_HOURS")
    if raw_hours:
        try:
            return max(60, int(float(raw_hours) * 3600))
        except ValueError:
            pass
    return DEFAULT_SESSION_TTL_SECONDS


def touch_auth_session(session_state) -> None:
    session_state.selv_auth_expires_at = time.time() + get_session_ttl_seconds()


def is_session_valid(session_state) -> bool:
    if not session_state.get("selv_authenticated"):
        return False
    expires_at = session_state.get("selv_auth_expires_at")
    if expires_at is None:
        touch_auth_session(session_state)
        return True
    return time.time() < float(expires_at)


def establish_auth_session(
    session_state,
    username: str,
    *,
    expires_at: float | None = None,
) -> None:
    session_state.pop("_selv_block_auth_restore", None)
    session_state.selv_authenticated = True
    session_state.selv_auth_user = username
    if expires_at is not None:
        session_state.selv_auth_expires_at = expires_at
    else:
        touch_auth_session(session_state)


def verify_login(username: str, password: str) -> bool:
    if not is_auth_enabled():
        return True
    expected_user = get_auth_username()
    expected_password = get_auth_password()
    if not expected_password:
        return False
    return secrets.compare_digest(
        username.strip().lower(), expected_user.strip().lower()
    ) and secrets.compare_digest(password, expected_password)


def clear_auth_session(session_state) -> None:
    session_state.pop("selv_authenticated", None)
    session_state.pop("selv_auth_user", None)
    session_state.pop("selv_auth_expires_at", None)
    session_state.pop("_selv_auth_last_renew", None)
    session_state.pop("_selv_auth_persisted_token", None)
    session_state.pop("_selv_auth_client_synced", None)
    session_state.pop("_selv_url_sess_synced", None)
    session_state.pop("_selv_auth_restore_scheduled", None)
    session_state["_selv_block_auth_restore"] = True
