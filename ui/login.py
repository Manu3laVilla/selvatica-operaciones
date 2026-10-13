from __future__ import annotations

import html
import time

import streamlit as st

from services.auth_service import (
    clear_auth_session,
    establish_auth_session,
    get_auth_username,
    get_session_ttl_seconds,
    is_auth_enabled,
    is_session_valid,
    touch_auth_session,
    verify_login,
)
from ui.auth_persistence import (
    bootstrap_cookie_manager,
    clear_auth_cookie,
    try_restore_auth_from_cookie,
    write_auth_cookie,
)
from ui.theme import COLORS, _asset_data_uri, resolve_icon_path, resolve_logo_path


def get_login_css() -> str:
    c = COLORS
    return f"""
    body:has(.selv-login-marker) [data-testid="stSidebar"],
    body:has(.selv-login-marker) [data-testid="stSidebarCollapsedControl"],
    body:has(.selv-login-marker) .selv-mobile-nav-shell {{
        display: none !important;
    }}

    body:has(.selv-login-marker) .selv-login-doodle,
    body:has(.selv-login-marker) img.selv-login-doodle {{
        display: none !important;
        visibility: hidden !important;
        width: 0 !important;
        height: 0 !important;
    }}

    body:has(.selv-login-marker) .main .block-container {{
        max-width: 30rem !important;
        padding-top: clamp(1.5rem, 6vh, 3.5rem) !important;
        padding-bottom: 2.5rem !important;
    }}

    .selv-login-shell {{
        width: 100%;
        margin: 0 auto;
    }}

    .selv-login-hero {{
        text-align: center;
        margin-bottom: 1.35rem;
    }}

    .selv-login-logo {{
        width: min(220px, 72vw);
        margin: 0 auto 0.65rem;
    }}

    .selv-login-logo img {{
        width: 100%;
        height: auto;
        display: block;
        filter: drop-shadow(0 6px 14px rgba(78, 87, 46, 0.14));
    }}

    .selv-login-icon {{
        width: 4.25rem;
        height: 4.25rem;
        margin: 0 auto 0.85rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.78);
        border: 2px solid {c['pink']};
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 8px 20px rgba(78, 87, 46, 0.1);
    }}

    .selv-login-icon img {{
        width: 3rem;
        height: 3rem;
        object-fit: contain;
    }}

    .selv-login-title {{
        font-size: 1.65rem;
        font-weight: 800;
        color: {c['olive']};
        letter-spacing: -0.02em;
        margin: 0 0 0.2rem;
    }}

    .selv-login-subtitle {{
        font-size: 1rem;
        font-weight: 600;
        color: {c['brown']};
        margin: 0;
    }}

    body:has(.selv-login-marker) [data-testid="stForm"] {{
        background: {c['white']};
        border: 2px solid {c['pink']};
        border-radius: 18px;
        padding: 1.35rem 1.25rem 1.1rem;
        box-shadow: 0 10px 28px rgba(78, 87, 46, 0.1);
    }}

    body:has(.selv-login-marker) [data-testid="stForm"] label {{
        color: {c['olive']} !important;
        font-weight: 700 !important;
    }}

    body:has(.selv-login-marker) [data-testid="stForm"] input {{
        border-radius: 12px !important;
        border: 2px solid {c['pink_soft']} !important;
        color: {c['olive']} !important;
    }}

    body:has(.selv-login-marker) [data-testid="stForm"] .stFormSubmitButton button {{
        width: 100%;
        border-radius: 12px !important;
        font-weight: 800 !important;
        background: {c['olive']} !important;
        color: {c['cream']} !important;
        border: 2px solid {c['olive_dark']} !important;
    }}

    body:has(.selv-login-marker) [data-testid="stForm"] .stFormSubmitButton button:hover {{
        background: {c['olive_dark']} !important;
        border-color: {c['olive_dark']} !important;
    }}

    .selv-login-footnote {{
        text-align: center;
        margin-top: 1rem;
        font-size: 0.82rem;
        color: {c['brown']};
        font-weight: 600;
    }}
    """


def _login_hero_html() -> str:
    logo_path = resolve_logo_path()
    icon_path = resolve_icon_path()

    logo_block = ""
    if logo_path is not None:
        logo_block = (
            f'<div class="selv-login-logo">'
            f'<img src="{_asset_data_uri(logo_path)}" alt="Selvatica" />'
            f"</div>"
        )
    elif icon_path is not None:
        logo_block = (
            f'<div class="selv-login-icon">'
            f'<img src="{_asset_data_uri(icon_path)}" alt="Selvatica" />'
            f"</div>"
        )

    return f"""
    <div class="selv-login-shell">
        <div class="selv-login-hero">
            {logo_block}
            <p class="selv-login-title">Centro de Operaciones</p>
            <p class="selv-login-subtitle">Inicia sesión para continuar</p>
        </div>
    </div>
    """


def _renew_session_if_needed() -> None:
    if not st.session_state.get("selv_authenticated"):
        return
    now = time.time()
    last_renew = float(st.session_state.get("_selv_auth_last_renew", 0))
    expires_at = st.session_state.get("selv_auth_expires_at")
    if expires_at is None:
        touch_auth_session(st.session_state)
        st.session_state["_selv_auth_last_renew"] = now
        write_auth_cookie()
        return
    if now - last_renew < 300:
        return
    if float(expires_at) - now > get_session_ttl_seconds() * 0.5:
        return
    touch_auth_session(st.session_state)
    st.session_state["_selv_auth_last_renew"] = now
    write_auth_cookie()


def is_authenticated() -> bool:
    if not is_auth_enabled():
        return True
    if not is_session_valid(st.session_state):
        return False
    _renew_session_if_needed()
    if not st.session_state.get("_selv_auth_client_synced"):
        write_auth_cookie()
        st.session_state["_selv_auth_client_synced"] = True
    return True


def ensure_authenticated() -> bool:
    """Muestra el login y devuelve False si el usuario aún no está autenticado."""
    from ui.auth_persistence import request_client_auth_restore

    if not is_auth_enabled():
        return True

    try_restore_auth_from_cookie()
    if is_authenticated():
        return True

    request_client_auth_restore()
    bootstrap_cookie_manager(force=True)
    try_restore_auth_from_cookie()
    if is_authenticated():
        return True

    st.markdown(f"<style>{get_login_css()}</style>", unsafe_allow_html=True)
    st.markdown('<div class="selv-login-marker" aria-hidden="true"></div>', unsafe_allow_html=True)
    st.markdown(_login_hero_html(), unsafe_allow_html=True)

    with st.form("selv_login_form", clear_on_submit=False):
        username = st.text_input("Usuario", value="", autocomplete="username")
        password = st.text_input(
            "Contraseña",
            type="password",
            autocomplete="current-password",
        )
        submitted = st.form_submit_button("Ingresar", use_container_width=True)

    if submitted:
        if verify_login(username, password):
            establish_auth_session(
                st.session_state,
                username.strip() or get_auth_username(),
            )
            st.session_state["_selv_auth_last_renew"] = time.time()
            write_auth_cookie()
            st.rerun()
        st.error("Usuario o contraseña incorrectos.")

    st.markdown(
        '<p class="selv-login-footnote">Acceso restringido al equipo Selvatica.</p>',
        unsafe_allow_html=True,
    )
    return False


def render_logout_button() -> None:
    if not is_auth_enabled():
        return

    user = html.escape(str(st.session_state.get("selv_auth_user") or get_auth_username()))
    st.sidebar.markdown(
        f'<div class="selv-sidebar-session">'
        f"<strong>Sesión:</strong> {user}</div>",
        unsafe_allow_html=True,
    )
    if st.sidebar.button(
        "Cerrar sesión",
        key="selv_logout",
        type="secondary",
        use_container_width=True,
    ):
        clear_auth_session(st.session_state)
        clear_auth_cookie()
        if "selv_sess" in st.query_params:
            del st.query_params["selv_sess"]
        st.rerun()
