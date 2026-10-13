"""Persiste la sesión: ?selv_sess= en la URL (fiable en Streamlit Cloud) + respaldos."""
from __future__ import annotations

import json
import time
from urllib.parse import unquote

import streamlit as st

from services.auth_service import (
    AUTH_COOKIE_NAME,
    create_auth_token,
    establish_auth_session,
    is_auth_enabled,
    is_session_valid,
    verify_auth_token,
)

_STORAGE_KEY = AUTH_COOKIE_NAME
_TTL_KEY = f"{AUTH_COOKIE_NAME}_ttl"
_RESTORE_FLAG = "_selv_auth_restore_scheduled"
_URL_SYNC_FLAG = "_selv_url_sess_synced"


def _cookie_secure() -> bool:
    try:
        return str(st.context.url or "").startswith("https://")
    except Exception:
        return False


def _read_cookie_header_token() -> str | None:
    try:
        cookie_header = str(st.context.headers.get("Cookie", "") or "")
    except Exception:
        return None
    prefix = f"{AUTH_COOKIE_NAME}="
    for part in cookie_header.split(";"):
        part = part.strip()
        if part.startswith(prefix):
            return unquote(part[len(prefix) :]).strip()
    return None


def _read_persisted_token() -> str | None:
    query_token = st.query_params.get("selv_sess")
    if query_token:
        return str(query_token).strip()

    try:
        cookie_val = st.context.cookies.get(AUTH_COOKIE_NAME)
    except Exception:
        cookie_val = None
    if cookie_val:
        return unquote(str(cookie_val)).strip()

    return _read_cookie_header_token()


def _top_window_script(body: str) -> None:
    st.html(
        f"""
        <script>
        (function () {{
            const w = window.top || window;
            {body}
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _persist_top_window_cookie(token: str, max_age: int) -> None:
    secure_flag = " + (w.location.protocol === 'https:' ? '; Secure' : '')"
    _top_window_script(
        f"""
        const key = {json.dumps(_STORAGE_KEY)};
        const value = {json.dumps(token)};
        const maxAge = {int(max_age)};
        try {{
            w.document.cookie = key + "=" + encodeURIComponent(value)
                + "; path=/; max-age=" + maxAge + "; SameSite=Lax"{secure_flag};
        }} catch (e) {{}}
        """
    )


def _sync_local_storage(token: str, max_age: int) -> None:
    expires_unix = int(time.time()) + int(max_age)
    _top_window_script(
        f"""
        const key = {json.dumps(_STORAGE_KEY)};
        const ttlKey = {json.dumps(_TTL_KEY)};
        const value = {json.dumps(token)};
        const expiresUnix = {expires_unix};
        try {{
            w.localStorage.setItem(key, value);
            w.localStorage.setItem(ttlKey, String(expiresUnix));
        }} catch (e) {{}}
        """
    )


def _current_session_token() -> str | None:
    if not is_session_valid(st.session_state):
        return None
    username = str(st.session_state.get("selv_auth_user") or "")
    expires_at = float(st.session_state.selv_auth_expires_at)
    return create_auth_token(username, expires_at)


def sync_session_url_token() -> None:
    """Mantiene selv_sess en la URL para sobrevivir recargas (Ctrl+Shift+R)."""
    if not is_auth_enabled():
        return

    if not is_session_valid(st.session_state):
        if "selv_sess" in st.query_params:
            del st.query_params["selv_sess"]
        st.session_state.pop(_URL_SYNC_FLAG, None)
        return

    if st.session_state.get(_URL_SYNC_FLAG):
        return

    url_token = st.query_params.get("selv_sess")
    if url_token and verify_auth_token(str(url_token)):
        st.session_state[_URL_SYNC_FLAG] = True
        return

    token = _current_session_token()
    if not token:
        return

    st.query_params["selv_sess"] = token
    st.session_state[_URL_SYNC_FLAG] = True
    st.rerun()


def persist_client_auth(token: str, max_age: int) -> None:
    _persist_top_window_cookie(token, max_age)
    _sync_local_storage(token, max_age)


def clear_client_auth() -> None:
    secure = "; Secure" if _cookie_secure() else ""
    _top_window_script(
        f"""
        const key = {json.dumps(_STORAGE_KEY)};
        const ttlKey = {json.dumps(_TTL_KEY)};
        try {{
            w.localStorage.removeItem(key);
            w.localStorage.removeItem(ttlKey);
        }} catch (e) {{}}
        try {{
            w.document.cookie = key + "=; path=/; max-age=0; SameSite=Lax{secure}";
        }} catch (e) {{}}
        """
    )
    st.session_state.pop("_selv_auth_persisted_token", None)
    st.session_state.pop(_RESTORE_FLAG, None)
    st.session_state.pop(_URL_SYNC_FLAG, None)


def request_client_auth_restore() -> None:
    """Respaldo: localStorage → ?selv_sess= si la URL aún no tiene token."""
    if not is_auth_enabled() or is_session_valid(st.session_state):
        st.session_state.pop(_RESTORE_FLAG, None)
        return
    if st.session_state.get("_selv_block_auth_restore"):
        return
    if _read_persisted_token():
        return
    if st.session_state.get(_RESTORE_FLAG):
        return

    _top_window_script(
        f"""
        const key = {json.dumps(_STORAGE_KEY)};
        const ttlKey = {json.dumps(_TTL_KEY)};
        const token = w.localStorage.getItem(key);
        if (!token) return;
        const ttl = parseInt(w.localStorage.getItem(ttlKey) || "0", 10);
        const now = Math.floor(Date.now() / 1000);
        if (ttl && now >= ttl) {{
            w.localStorage.removeItem(key);
            w.localStorage.removeItem(ttlKey);
            return;
        }}
        const url = new URL(w.location.href);
        if (url.searchParams.get("selv_sess")) return;
        url.searchParams.set("selv_sess", token);
        w.location.replace(url.toString());
        """
    )
    st.session_state[_RESTORE_FLAG] = True


def _restore_from_token(token: str) -> bool:
    verified = verify_auth_token(token)
    if not verified:
        return False
    username, expires_at = verified
    establish_auth_session(st.session_state, username, expires_at=expires_at)
    st.session_state.pop(_RESTORE_FLAG, None)
    st.session_state["_selv_auth_last_renew"] = time.time()
    st.session_state[_URL_SYNC_FLAG] = True
    return True


def try_restore_auth_from_cookie() -> bool:
    if not is_auth_enabled():
        return True
    if st.session_state.get("_selv_block_auth_restore"):
        return False
    if is_session_valid(st.session_state):
        st.session_state.pop(_RESTORE_FLAG, None)
        return True

    token = _read_persisted_token()
    if not token:
        return False

    if _restore_from_token(token):
        write_auth_cookie()
        return True

    clear_client_auth()
    if "selv_sess" in st.query_params:
        del st.query_params["selv_sess"]
    return False


def write_auth_cookie() -> None:
    if not is_auth_enabled() or not is_session_valid(st.session_state):
        return

    token = _current_session_token()
    if not token:
        return
    if st.session_state.get("_selv_auth_persisted_token") == token:
        return

    expires_at = float(st.session_state.selv_auth_expires_at)
    max_age = max(60, int(expires_at - time.time()))
    persist_client_auth(token, max_age)
    st.session_state["_selv_auth_persisted_token"] = token


def clear_auth_cookie() -> None:
    if not is_auth_enabled():
        return
    clear_client_auth()
