from __future__ import annotations

import base64
from pathlib import Path

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

LOGO_FILE = "logo.png"
ICON_FILE = "icono.png"

COLORS = {
    "cream": "#FFF9C2",
    "pink": "#F1C1DF",
    "olive": "#4E572E",
    "brown": "#7A5E35",
    "cream_soft": "#FFFDF0",
    "pink_soft": "#F9E8F3",
    "cream_mid": "#F5E89A",
    "pink_mid": "#E8A8CF",
    "olive_dark": "#3D4524",
    "text": "#4E572E",
    "text_muted": "#7A5E35",
    "text_on_dark": "#FFF9C2",
    "white": "#FFFFFF",
}

SIDEBAR_NAV_ORDER = [
    "dashboard",
    "productos",
    "clientes",
    "ventas",
    "contabilidad",
    "pedidos",
    "alertas",
]

SIDEBAR_NAV_ICONS = {
    "dashboard": "M3 3h8v8H3V3zm10 0h8v8h-8V3zM3 13h8v8H3v-8zm10 0h8v8h-8v-8z",
    "productos": "M4 7h16l-1.5 11h-13L4 7zm2.5-4h11l1 4h-13l1-4z",
    "clientes": "M9 11a3 3 0 100-6 3 3 0 000 6zm-5 8c0-2.5 3.5-4.5 8-4.5s8 2 8 4.5",
    "ventas": "M7 7h13l-1.5 10h-10L7 7zm2-3h9",
    "contabilidad": "M3 7h18v11a2 2 0 01-2 2H5a2 2 0 01-2-2V7zm16 0V5a2 2 0 00-2-2H7a2 2 0 00-2 2v2m-4 4h8",
    "pedidos": "M6 3h12v18H6V3zm2 7h8m-8 4h8",
    "alertas": "M12 3a5 5 0 00-5 5v3l-2 2h14l-2-2V8a5 5 0 00-5-5zm-1 15h2",
}

MOBILE_NAV_LABELS = {
    "dashboard": "Inicio",
    "productos": "Productos",
    "clientes": "Clientes",
    "ventas": "Ventas",
    "contabilidad": "Contabilidad",
    "pedidos": "Pedidos",
    "alertas": "Alertas",
}


def _sidebar_icon_masks_css() -> str:
    from urllib.parse import quote

    olive = COLORS["olive"]
    rules = []
    for page_key in SIDEBAR_NAV_ORDER:
        path = SIDEBAR_NAV_ICONS[page_key]
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
            f'stroke="black" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            f'<path d="{path}"/></svg>'
        )
        encoded = quote(svg)
        rules.append(
            f"""
            .selv-nav-icon-{page_key} {{
                display: none !important;
            }}

            @media (min-width: 769px) {{
                body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .st-key-nav_{page_key} .stButton > button::before {{
                    content: "" !important;
                    display: block !important;
                    position: absolute;
                    left: 50%;
                    top: 50%;
                    transform: translate(-50%, -50%);
                    width: 1.2rem;
                    height: 1.2rem;
                    background-color: {olive};
                    -webkit-mask: url("data:image/svg+xml,{encoded}") center / contain no-repeat;
                    mask: url("data:image/svg+xml,{encoded}") center / contain no-repeat;
                }}
            }}
            """
        )
    return "\n".join(rules)


def _table_pagination_css(*, body_prefix: str = "") -> str:
    c = COLORS
    p = body_prefix
    return f"""
    {p}.selv-pagination-text {{
        color: {c['brown']};
        font-size: 0.88rem;
        font-weight: 600;
        margin: 0;
        line-height: 1.35;
        white-space: nowrap;
    }}

    {p}.selv-pagination-page {{
        color: {c['olive']};
        font-weight: 800;
        text-align: right;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer {{
        background: rgba(255, 255, 255, 0.68) !important;
        border: 1.5px solid {c['pink']} !important;
        border-radius: 14px !important;
        padding: 0.62rem 0.9rem !important;
        margin-top: 0.65rem !important;
        margin-bottom: 0.15rem !important;
        box-shadow: 0 4px 14px rgba(78, 87, 46, 0.05) !important;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] {{
        flex-wrap: nowrap !important;
        align-items: center !important;
        gap: 0.65rem !important;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
        min-width: 0 !important;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer .stButton > button {{
        min-height: 2.25rem !important;
        padding: 0.35rem 0.65rem !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stSelectbox"] label {{
        font-size: 0.82rem !important;
        color: {c['brown']} !important;
        font-weight: 700 !important;
        margin-bottom: 0.15rem !important;
        white-space: nowrap !important;
    }}

    {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-baseweb="select"] > div {{
        min-height: 2.25rem !important;
        border-radius: 10px !important;
    }}

    @media (min-width: 769px) {{
        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer .stButton > button {{
            width: auto !important;
            min-width: 6rem !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3),
        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {{
            flex: 0 0 auto !important;
            width: auto !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5) {{
            flex: 0 0 11rem !important;
            width: 11rem !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stSelectbox"] label {{
            margin-bottom: 0 !important;
        }}
    }}

    @media (max-width: 768px) {{
        {p}.selv-pagination-text {{
            font-size: 0.8rem;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer {{
            padding: 0.55rem 0.7rem 0.65rem !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] {{
            display: grid !important;
            grid-template-columns: 1fr 1fr 1.15fr !important;
            grid-template-rows: auto auto !important;
            gap: 0.45rem 0.5rem !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            flex: none !important;
            width: auto !important;
            min-width: 0 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(1) {{
            grid-column: 1 / 2 !important;
            grid-row: 1 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(2) {{
            grid-column: 2 / 4 !important;
            grid-row: 1 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(3) {{
            grid-column: 1 / 2 !important;
            grid-row: 2 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(4) {{
            grid-column: 2 / 3 !important;
            grid-row: 2 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer [data-testid="stHorizontalBlock"] > [data-testid="column"]:nth-child(5) {{
            grid-column: 3 / 4 !important;
            grid-row: 2 !important;
        }}

        {p}.stElementContainer:has(.selv-pagination-root) + .stElementContainer .stButton > button {{
            width: 100% !important;
            min-height: 2.15rem !important;
            font-size: 0.82rem !important;
        }}
    }}
    """


def _mobile_streamlit_chrome_hide_css(body_prefix: str = "") -> str:
    return f"""
    {body_prefix}header[data-testid="stHeader"],
    {body_prefix}[data-testid="stToolbar"],
    {body_prefix}[data-testid="stDecoration"],
    {body_prefix}[data-testid="stStatusWidget"],
    {body_prefix}[data-testid="stAppDeployButton"],
    {body_prefix}[data-testid="stMainMenu"],
    {body_prefix}[data-testid="stBottomBlockContainer"],
    {body_prefix}footer,
    {body_prefix}[class*="viewerBadge"],
    {body_prefix}[class*="stAppDeployButton"] {{
        display: none !important;
        height: 0 !important;
        min-height: 0 !important;
        width: 0 !important;
        min-width: 0 !important;
        max-width: 0 !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }}
    """


def _mobile_drawer_nav_css() -> str:
    c = COLORS
    return f"""
    .selv-mobile-nav-shell {{
        display: none;
    }}

    @media (max-width: 768px) {{
        .stElementContainer:has(.selv-mobile-nav-shell),
        [data-testid="stMarkdownContainer"]:has(.selv-mobile-nav-shell),
        [data-testid="stMarkdown"]:has(.selv-mobile-nav-shell) {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            width: 0 !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
            overflow: visible !important;
            z-index: 999999 !important;
            border: none !important;
            background: transparent !important;
            pointer-events: none !important;
        }}

        .selv-mobile-nav-shell {{
            display: block !important;
            pointer-events: none !important;
        }}

        .selv-mobile-nav-details {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            z-index: 999999 !important;
            pointer-events: none !important;
        }}

        .selv-mobile-nav-details > summary {{
            list-style: none !important;
        }}

        .selv-mobile-nav-details > summary::-webkit-details-marker {{
            display: none !important;
        }}

        .selv-mobile-menu-toggle {{
            position: fixed !important;
            top: calc(0.65rem + env(safe-area-inset-top, 0px)) !important;
            left: 0.75rem !important;
            z-index: 1000001 !important;
            width: 2.65rem !important;
            height: 2.65rem !important;
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 0.28rem !important;
            margin: 0 !important;
            padding: 0 !important;
            border: 2px solid rgba(122, 94, 53, 0.18) !important;
            border-radius: 12px !important;
            background: linear-gradient(180deg, {c['white']} 0%, {c['cream']} 100%) !important;
            box-shadow: 0 4px 14px rgba(78, 87, 46, 0.14) !important;
            cursor: pointer !important;
            pointer-events: auto !important;
            box-sizing: border-box !important;
        }}

        .selv-mobile-menu-toggle span {{
            display: block !important;
            width: 1.15rem !important;
            height: 2px !important;
            border-radius: 999px !important;
            background: {c['olive']} !important;
        }}

        .selv-mobile-nav-details[open] .selv-mobile-menu-toggle span:nth-child(1) {{
            transform: translateY(6px) rotate(45deg) !important;
        }}

        .selv-mobile-nav-details[open] .selv-mobile-menu-toggle span:nth-child(2) {{
            opacity: 0 !important;
        }}

        .selv-mobile-nav-details[open] .selv-mobile-menu-toggle span:nth-child(3) {{
            transform: translateY(-6px) rotate(-45deg) !important;
        }}

        .selv-mobile-nav-details[open]::before {{
            content: "" !important;
            position: fixed !important;
            inset: 0 !important;
            background: rgba(78, 87, 46, 0.35) !important;
            z-index: 999998 !important;
            pointer-events: auto !important;
        }}

        .selv-mobile-drawer {{
            position: fixed !important;
            top: 0 !important;
            left: 0 !important;
            bottom: 0 !important;
            width: min(18.5rem, 84vw) !important;
            display: flex !important;
            flex-direction: column !important;
            gap: 0.35rem !important;
            margin: 0 !important;
            padding: calc(4.25rem + env(safe-area-inset-top, 0px)) 0.85rem
                calc(1rem + env(safe-area-inset-bottom, 0px)) !important;
            background: linear-gradient(180deg, {c['cream']} 0%, {c['pink_soft']} 100%) !important;
            border-right: 2px solid rgba(241, 193, 223, 0.85) !important;
            box-shadow: 8px 0 28px rgba(78, 87, 46, 0.16) !important;
            overflow-y: auto !important;
            pointer-events: auto !important;
            box-sizing: border-box !important;
            z-index: 1000000 !important;
            transform: translateX(-105%) !important;
            transition: transform 0.24s ease !important;
        }}

        .selv-mobile-nav-details[open] .selv-mobile-drawer {{
            transform: translateX(0) !important;
        }}

        .selv-mobile-nav-details:not([open]) .selv-mobile-drawer {{
            visibility: hidden !important;
            pointer-events: none !important;
        }}

        .selv-mobile-nav-item {{
            position: relative !important;
            display: flex !important;
            align-items: center !important;
            gap: 0.7rem !important;
            min-height: 2.85rem !important;
            padding: 0.55rem 0.75rem !important;
            border-radius: 12px !important;
            text-decoration: none !important;
            border: 1px solid transparent !important;
            color: {c['olive']} !important;
            font-family: 'Nunito', 'Segoe UI', sans-serif !important;
            font-size: 0.92rem !important;
            font-weight: 700 !important;
            box-sizing: border-box !important;
        }}

        .selv-mobile-nav-label {{
            flex: 1 1 auto !important;
            min-width: 0 !important;
            line-height: 1.2 !important;
        }}

        .selv-mobile-nav-icon {{
            display: block !important;
            width: 22px !important;
            height: 22px !important;
            min-width: 22px !important;
            min-height: 22px !important;
            object-fit: contain !important;
            flex-shrink: 0 !important;
            pointer-events: none !important;
        }}

        .selv-mobile-nav-badge {{
            min-width: 1.15rem !important;
            height: 1.15rem !important;
            padding: 0 0.3rem !important;
            border-radius: 999px !important;
            background: {c['pink']} !important;
            color: {c['olive']} !important;
            font-family: 'Nunito', 'Segoe UI', sans-serif !important;
            font-size: 0.62rem !important;
            font-weight: 800 !important;
            line-height: 1.15rem !important;
            text-align: center !important;
            border: 1px solid rgba(122, 94, 53, 0.2) !important;
            flex-shrink: 0 !important;
        }}

        .selv-mobile-nav-item--active {{
            background: {c['white']} !important;
            border-color: rgba(122, 94, 53, 0.15) !important;
            box-shadow: 0 2px 8px rgba(122, 94, 53, 0.1) !important;
        }}
    }}
    """


def _mobile_bottom_bar_css() -> str:
    streamlit_hide = _mobile_streamlit_chrome_hide_css()
    drawer_css = _mobile_drawer_nav_css()
    return f"""
    {drawer_css}

    @media (max-width: 768px) {{
        {streamlit_hide}

        [data-testid="stSidebar"],
        [data-testid="stSidebarCollapsedControl"],
        [data-testid="stExpandSidebarButton"],
        [data-testid="stSidebarCollapseButton"] {{
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
            visibility: hidden !important;
        }}

        section[data-testid="stMain"],
        section[data-testid="stMain"] > div,
        section[data-testid="stMain"] .block-container,
        [data-testid="stMainBlockContainer"],
        [data-testid="stAppViewContainer"] {{
            padding-bottom: calc(1rem + env(safe-area-inset-bottom, 0px)) !important;
        }}

        section[data-testid="stMain"] .block-container,
        [data-testid="stMainBlockContainer"] {{
            padding-top: calc(3.75rem + env(safe-area-inset-top, 0px)) !important;
        }}

        .st-key-mobile_bottom_nav,
        .st-key-mobile_bottom_nav ~ * {{
            display: none !important;
        }}
    }}
    """


def _mobile_nav_icon_data_uri(page_key: str) -> str:
    path = SIDEBAR_NAV_ICONS[page_key]
    olive = COLORS["olive"]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{olive}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f'<path d="{path}"/></svg>'
    )
    encoded = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"


def _mobile_nav_badge_count(label: str, page_key: str) -> str | None:
    if page_key == "alertas" and "(" in label:
        return label.split("(")[-1].rstrip(")")
    return None


def _mobile_responsive_css() -> str:
    c = COLORS
    return f"""
    @media (max-width: 768px) {{
        section[data-testid="stMain"] .block-container,
        [data-testid="stMainBlockContainer"] {{
            padding-left: 0.85rem !important;
            padding-right: 0.85rem !important;
            padding-top: calc(3.75rem + env(safe-area-inset-top, 0px)) !important;
            max-width: 100% !important;
        }}

        .main-header {{
            font-size: 1.55rem !important;
            line-height: 1.3 !important;
            margin-top: 0 !important;
            overflow: visible !important;
        }}

        .sub-header {{
            font-size: 0.88rem !important;
            margin-bottom: 0.85rem !important;
            line-height: 1.35 !important;
        }}

        .page-doodle-wrap {{
            margin-bottom: 0.35rem !important;
            padding-top: 0.15rem !important;
            overflow: visible !important;
        }}

        section[data-testid="stMain"] [data-testid="stMarkdown"]:has(.page-doodle-wrap),
        section[data-testid="stMain"] [data-testid="stMarkdownContainer"]:has(.page-doodle-wrap),
        section[data-testid="stMain"] .stElementContainer:has(.page-doodle-wrap) {{
            overflow: visible !important;
        }}

        div[data-testid="stMetric"] {{
            padding: 0.6rem 0.75rem !important;
            margin-bottom: 0.45rem !important;
        }}

        div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
            font-size: 1.35rem !important;
        }}

        section[data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.45rem !important;
        }}

        section[data-testid="stMain"] [data-testid="column"] {{
            min-width: calc(50% - 0.35rem) !important;
            flex: 1 1 calc(50% - 0.35rem) !important;
        }}

        .selv-secnav-bar {{
            flex-wrap: nowrap !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            gap: 0.25rem !important;
            padding-bottom: 0.15rem !important;
        }}

        .selv-secnav-btn {{
            flex: 0 0 auto !important;
            font-size: 0.78rem !important;
            padding: 0.52rem 0.75rem !important;
            white-space: nowrap !important;
        }}

        .selv-table-wrap {{
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
            margin-bottom: 0.5rem !important;
        }}

        .selv-table {{
            min-width: 520px !important;
            font-size: 0.82rem !important;
        }}

        .selv-table th,
        .selv-table td {{
            padding: 0.55rem 0.6rem !important;
        }}

        [data-testid="stDataFrame"] {{
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }}

        section[data-testid="stMain"] .stButton > button {{
            width: 100% !important;
        }}

        {_table_pagination_css()}

        section[data-testid="stMain"] .stTextInput,
        section[data-testid="stMain"] .stNumberInput,
        section[data-testid="stMain"] .stSelectbox,
        section[data-testid="stMain"] .stTextArea,
        section[data-testid="stMain"] .stMultiSelect {{
            width: 100% !important;
        }}

        .selv-alert {{
            padding: 0.7rem 0.85rem !important;
            font-size: 0.88rem !important;
            margin: 0.55rem 0 !important;
        }}

        [data-testid="stForm"] {{
            padding: 0.85rem !important;
            margin-bottom: 0.5rem !important;
        }}
    }}
    """


def resolve_asset(filename: str, folder: Path | None = None) -> Path | None:
    folder = folder or ASSETS_DIR
    path = folder / filename
    if path.exists():
        return path

    stem = Path(filename).stem
    for ext in (".png", ".webp", ".jpg", ".jpeg", ".svg"):
        candidate = folder / f"{stem}{ext}"
        if candidate.exists():
            return candidate
    return None


def resolve_logo_path() -> Path | None:
    path = ASSETS_DIR / LOGO_FILE
    return path if path.exists() else None


def resolve_icon_path() -> Path | None:
    path = ASSETS_DIR / ICON_FILE
    return path if path.exists() else None


def _asset_data_uri(path: Path) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    suffix = path.suffix.lower()
    mime_map = {
        ".svg": "image/svg+xml",
        ".png": "image/png",
        ".webp": "image/webp",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
    }
    mime = mime_map.get(suffix, "application/octet-stream")
    return f"data:{mime};base64,{encoded}"


def get_global_css() -> str:
    c = COLORS
    icon_masks = _sidebar_icon_masks_css()
    mobile_bar_css = _mobile_bottom_bar_css()
    mobile_page_css = _mobile_responsive_css()
    return f"""
    @import url('https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap');

    :root {{
        --selv-cream: {c['cream']};
        --selv-pink: {c['pink']};
        --selv-olive: {c['olive']};
        --selv-brown: {c['brown']};
        --selv-text: {c['text']};
        --selv-text-muted: {c['text_muted']};
        --selv-text-on-dark: {c['text_on_dark']};
    }}

    .stApp {{
        background: linear-gradient(
            165deg,
            {c['cream']} 0%,
            {c['cream_mid']} 38%,
            {c['pink']} 100%
        );
        font-family: 'Nunito', 'Segoe UI', sans-serif;
        color: {c['text']};
    }}

    /* ── Sidebar (degradado invertido respecto al contenido) ── */
    @media (min-width: 769px) {{
        :root {{
            --sidebar-width: 16rem;
            --sidebar-compact-width: 5.5rem;
        }}

        /* Streamlit 1.61: no usar colapso nativo (rompe el layout con translateX) */
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stExpandSidebarButton"],
        header[data-testid="stHeader"] {{
            display: none !important;
        }}

        /* Streamlit 1.61: forzar sidebar visible en desktop (evita colapso al recargar) */
        [data-testid="stSidebar"],
        section[data-testid="stSidebar"],
        .stSidebar {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: none !important;
            translate: none !important;
            margin-left: 0 !important;
            flex-shrink: 0 !important;
        }}

        [data-testid="stSidebar"][aria-expanded="false"],
        section[data-testid="stSidebar"][aria-expanded="false"] {{
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: none !important;
            translate: none !important;
            margin-left: 0 !important;
        }}

        body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) [data-testid="stSidebar"],
        body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) section[data-testid="stSidebar"] {{
            width: 16rem !important;
            min-width: 16rem !important;
            max-width: 16rem !important;
        }}

        body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) [data-testid="stSidebar"][aria-expanded="false"],
        body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) section[data-testid="stSidebar"][aria-expanded="false"] {{
            width: 16rem !important;
            min-width: 16rem !important;
            max-width: 16rem !important;
        }}

        body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) [data-testid="stSidebar"] [data-testid="block-container"] {{
            padding: 0.85rem 0.65rem 1rem !important;
        }}

        section[data-testid="stMain"] .block-container,
        [data-testid="stMainBlockContainer"] {{
            padding-top: 1.75rem !important;
        }}

        /* Botón compacto del sidebar */
        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] {{
            position: absolute !important;
            top: 0.35rem !important;
            right: 0.35rem !important;
            z-index: 5 !important;
            width: auto !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
        }}

        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle .stButton,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] .stButton {{
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }}

        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle .stButton > button,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] .stButton > button,
        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle button[kind="tertiary"],
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] button[kind="tertiary"] {{
            width: 2rem !important;
            min-width: 2rem !important;
            height: 2rem !important;
            min-height: 2rem !important;
            padding: 0 !important;
            margin: 0 !important;
            border-radius: 8px !important;
            border: none !important;
            outline: none !important;
            background: transparent !important;
            background-color: transparent !important;
            color: {c['olive']} !important;
            font-size: 1.1rem !important;
            font-weight: 800 !important;
            line-height: 1 !important;
            box-shadow: none !important;
            -webkit-box-shadow: none !important;
        }}

        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle .stButton > button:hover,
        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle .stButton > button:focus,
        [data-testid="stSidebar"] .st-key-selv_sidebar_compact_toggle .stButton > button:active,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] .stButton > button:hover,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] .stButton > button:focus,
        [data-testid="stSidebar"] [class*="st-key-selv_sidebar_compact_toggle"] .stButton > button:active {{
            background: rgba(255, 255, 255, 0.2) !important;
            background-color: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
            -webkit-box-shadow: none !important;
        }}
    }}

    [data-testid="stSidebar"] {{
        background: linear-gradient(
            180deg,
            {c['pink']} 0%,
            {c['pink_mid']} 42%,
            {c['cream']} 100%
        ) !important;
        border-right: 1px solid rgba(122, 94, 53, 0.22);
        box-shadow: 4px 0 24px rgba(78, 87, 46, 0.06);
    }}

    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong {{
        color: {c['olive']} !important;
    }}

    [data-testid="stSidebar"] hr {{
        border: none;
        border-top: 1px solid rgba(122, 94, 53, 0.18);
        margin: 1rem 0;
    }}

    /* ── Menú lateral: expandido = solo texto ── */
    [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton {{
        margin-bottom: 0.12rem;
    }}

    [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button {{
        position: relative !important;
        display: flex !important;
        align-items: center !important;
        justify-content: flex-start !important;
        width: 100% !important;
        min-height: 2.55rem !important;
        padding: 0.68rem 0.9rem !important;
        border-radius: 10px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        color: {c['olive']} !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-align: left !important;
        transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease !important;
    }}

    body:not(:has(.selv-sidebar-mode-marker[data-compact="1"])) [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button::before {{
        content: none !important;
        display: none !important;
    }}

    [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button[kind="primary"] {{
        background: linear-gradient(
            90deg,
            rgba(241, 193, 223, 0.72) 0%,
            rgba(255, 249, 194, 0.45) 100%
        ) !important;
        color: {c['olive']} !important;
        border: 1px solid transparent !important;
        border-left: 3px solid {c['brown']} !important;
        box-shadow: 0 2px 10px rgba(122, 94, 53, 0.08) !important;
        font-weight: 700 !important;
    }}

    [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button[kind="secondary"]:hover {{
        background: rgba(255, 255, 255, 0.5) !important;
        color: {c['olive_dark']} !important;
        border-color: rgba(241, 193, 223, 0.7) !important;
    }}

    {icon_masks}

    /* Sidebar compacto — desktop (controlado por session_state en Python) */
    @media (min-width: 769px) {{
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"],
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) section[data-testid="stSidebar"],
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) .stSidebar {{
            width: 5.5rem !important;
            min-width: 5.5rem !important;
            max-width: 5.5rem !important;
            transform: none !important;
            translate: none !important;
            overflow: hidden !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [data-testid="block-container"] {{
            padding: 0.25rem 0.15rem 0.5rem !important;
            position: relative !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebarUserContent"] {{
            display: flex !important;
            flex-direction: column !important;
            align-items: center !important;
            width: 100% !important;
            padding: 0.15rem 0.1rem !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .sidebar-tagline,
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .selv-sidebar-footer,
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] hr,
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .selv-sidebar-logo-full,
        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [data-testid="stDivider"] {{
            display: none !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .selv-sidebar-icon-mini {{
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            margin: 0.15rem auto 0.45rem auto !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] .selv-sidebar-icon-mini img {{
            width: 1.75rem !important;
            height: 1.75rem !important;
            object-fit: contain !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [class*="st-key-nav_"] {{
            width: auto !important;
            margin: 0 auto 0.12rem auto !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton {{
            width: 2.5rem !important;
            margin: 0 auto !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button {{
            width: 2.5rem !important;
            min-width: 2.5rem !important;
            max-width: 2.5rem !important;
            min-height: 2.5rem !important;
            height: 2.5rem !important;
            padding: 0 !important;
            justify-content: center !important;
            border-left: 1px solid transparent !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button p {{
            display: none !important;
        }}

        body:has(.selv-sidebar-mode-marker[data-compact="1"]) [data-testid="stSidebar"] [class*="st-key-nav_"] .stButton > button[kind="primary"] {{
            background: {c['pink']} !important;
            border: 1px solid rgba(122, 94, 53, 0.15) !important;
        }}
    }}

    [data-testid="stSidebar"] .selv-sidebar-icon-mini {{
        display: none;
    }}

    [data-testid="stSidebar"] .selv-sidebar-logo-full {{
        display: block;
        width: 100%;
        margin-bottom: 0.15rem;
        text-align: center;
    }}

    [data-testid="stSidebar"] .selv-sidebar-logo-full img {{
        width: 100%;
        max-width: 100%;
        height: auto;
        display: block;
        margin: 0 auto;
    }}

    [data-testid="stSidebar"] .selv-sidebar-footer {{
        font-size: 0.82rem;
        color: {c['brown']};
        line-height: 1.35;
    }}

    [data-testid="stSidebar"] .selv-sidebar-footer strong {{
        color: {c['olive']};
    }}

    /* Toggle compacto — reglas globales (alta prioridad) */
    [data-testid="stSidebar"] [class*="selv_sidebar_compact_toggle"] .stButton > button,
    [data-testid="stSidebar"] [class*="selv_sidebar_compact_toggle"] button {{
        background: transparent !important;
        background-color: transparent !important;
        border: none !important;
        outline: none !important;
        box-shadow: none !important;
    }}

    [data-testid="stSidebar"] [class*="selv_sidebar_compact_toggle"] {{
        background: transparent !important;
        box-shadow: none !important;
    }}

    /* ── Tablas HTML ── */
    .selv-table-wrap {{
        overflow-x: auto;
        border: 2px solid {c['pink']};
        border-radius: 14px;
        background: {c['white']};
        box-shadow: 0 4px 14px rgba(78, 87, 46, 0.06);
    }}

    .selv-table {{
        width: 100%;
        border-collapse: collapse;
        font-family: 'Nunito', 'Segoe UI', sans-serif;
        font-size: 0.92rem;
    }}

    .selv-table thead th {{
        background: {c['pink']};
        color: {c['olive']};
        font-weight: 800;
        text-align: left;
        padding: 0.8rem 1rem;
        border-bottom: 2px solid {c['brown']};
        white-space: nowrap;
    }}

    .selv-table tbody td {{
        color: {c['olive']};
        padding: 0.7rem 1rem;
        border-bottom: 1px solid {c['pink_soft']};
        vertical-align: middle;
    }}

    .selv-table tbody tr:nth-child(even) td {{
        background: {c['cream_soft']};
    }}

    .selv-table tbody tr:hover td {{
        background: {c['cream']};
    }}

    .selv-table tbody tr:last-child td {{
        border-bottom: none;
    }}

    {_table_pagination_css()}

    /* ── Contenido principal ── */
    .main-header {{
        font-size: 2.1rem;
        font-weight: 800;
        color: {c['olive']};
        margin-bottom: 0.15rem;
        letter-spacing: -0.02em;
    }}

    .sub-header {{
        color: {c['brown']};
        margin-bottom: 1.25rem;
        font-size: 1.05rem;
        font-weight: 600;
    }}

    .page-doodle-wrap {{
        position: relative;
        margin-bottom: 0.5rem;
    }}

    .page-doodles {{
        display: flex;
        gap: 0.75rem;
        align-items: center;
        margin-bottom: 0.75rem;
        flex-wrap: wrap;
    }}

    .page-doodles img {{
        width: 52px;
        height: 52px;
        object-fit: contain;
        opacity: 0.95;
        filter: drop-shadow(0 2px 4px rgba(78, 87, 46, 0.12));
    }}

    .alert-box {{
        background: linear-gradient(90deg, {c['cream']} 0%, {c['pink_soft']} 100%);
        border-left: 5px solid {c['brown']};
        padding: 1rem 1.1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }}

    /* Métricas */
    div[data-testid="stMetric"] {{
        background: {c['white']};
        border: 2px solid {c['pink']};
        border-radius: 14px;
        padding: 0.75rem 1rem;
        box-shadow: 0 3px 10px rgba(78, 87, 46, 0.08);
    }}

    div[data-testid="stMetric"] label {{
        color: {c['brown']} !important;
        font-weight: 700;
    }}

    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: {c['olive']} !important;
        font-weight: 800;
        overflow: visible !important;
        text-overflow: unset !important;
    }}

    div[data-testid="stMetric"] [data-testid="stMetricValue"] > div {{
        overflow: visible !important;
        text-overflow: unset !important;
        white-space: nowrap !important;
    }}

    .main .block-container:has(.selv-dashboard-kpis-marker) div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {{
        gap: 1rem !important;
        margin-bottom: 0.85rem !important;
    }}

    /* Tabs nativos de Streamlit — ocultar si quedan */
    .stTabs {{
        display: none;
    }}

    /* Métricas */
    [data-testid="stAlert"] {{
        border-radius: 12px !important;
        border: 2px solid {c['brown']} !important;
        padding: 0.75rem 1rem !important;
    }}

    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAlert"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stAlert"] div {{
        color: {c['olive']} !important;
        font-weight: 600 !important;
    }}

    [data-testid="stAlert"]:has([data-baseweb="toast"][kind="warning"]),
    div[data-testid="stNotification"]:has([kind="warning"]) {{
        background-color: {c['cream']} !important;
    }}

    [data-testid="stAlert"]:has([data-baseweb="toast"][kind="info"]) {{
        background-color: {c['pink_soft']} !important;
    }}

    [data-testid="stAlert"]:has([data-baseweb="toast"][kind="success"]) {{
        background-color: #E8F5D8 !important;
        border-color: {c['olive']} !important;
    }}

    [data-testid="stAlert"]:has([data-baseweb="toast"][kind="error"]) {{
        background-color: #FDE8E8 !important;
        border-color: #9B3A3A !important;
    }}

    /* Forzar texto oscuro en todas las alertas */
    .stAlert,
    .stAlert > div,
    [data-baseweb="notification"] {{
        background-color: {c['cream']} !important;
        color: {c['olive']} !important;
    }}

    .stAlert * {{
        color: {c['olive']} !important;
    }}

    /* Tablas — tema claro acorde a la paleta */
    [data-testid="stDataFrame"] {{
        border: 2px solid {c['pink']};
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 14px rgba(78, 87, 46, 0.06);
        --gdg-bg-cell: #FFFFFF;
        --gdg-bg-header: {c['pink']};
        --gdg-bg-header-has-focus: {c['pink_soft']};
        --gdg-bg-header-hovered: {c['pink_soft']};
        --gdg-text-dark: {c['olive']};
        --gdg-text-medium: {c['brown']};
        --gdg-text-light: #A89878;
        --gdg-border-color: {c['pink']};
        --gdg-accent-color: {c['olive']};
        --gdg-accent-light: {c['pink_soft']};
    }}

    [data-testid="stDataFrame"] div[class*="glideDataEditor"],
    [data-testid="stDataFrame"] .dvn-scroller {{
        background: {c['white']} !important;
    }}

    /* Inputs y selects */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"] > div {{
        background: {c['white']} !important;
        color: {c['olive']} !important;
        border-color: {c['pink']} !important;
        border-radius: 8px !important;
    }}

    /* Caption y textos auxiliares */
    [data-testid="stCaptionContainer"] p {{
        color: {c['brown']} !important;
    }}

    /* Bloque principal con tarjeta suave */
    [data-testid="stMainBlockContainer"] {{
        padding-top: 1rem;
    }}

    /* Botones de acción (solo área principal, no menús) */
    section[data-testid="stMain"] .stButton > button[kind="primary"] {{
        background: {c['olive']} !important;
        color: {c['text_on_dark']} !important;
        border: 1px solid {c['olive_dark']} !important;
        border-radius: 10px;
        font-weight: 700;
        box-shadow: 0 2px 8px rgba(61, 69, 36, 0.15);
    }}

    section[data-testid="stMain"] .stButton > button[kind="primary"]:hover {{
        background: {c['brown']} !important;
        color: {c['cream']} !important;
        border-color: {c['olive']} !important;
    }}

    section[data-testid="stMain"] .stButton > button[kind="secondary"] {{
        background: rgba(255, 255, 255, 0.75) !important;
        color: {c['olive']} !important;
        border: 1px solid rgba(122, 94, 53, 0.25) !important;
        border-radius: 10px;
        font-weight: 600;
    }}

    section[data-testid="stMain"] .stButton > button[kind="secondary"]:hover {{
        background: {c['white']} !important;
        border-color: {c['brown']} !important;
    }}

    /* ── Menús de subpáginas (mismo estilo que sidebar) ── */
    .selv-secnav-bar,
    [data-testid="stHtml"] .selv-secnav-bar,
    [data-testid="stMarkdownContainer"] .selv-secnav-bar {{
        display: flex !important;
        flex-wrap: wrap !important;
        align-items: stretch !important;
        gap: 0.35rem !important;
        padding: 0.35rem !important;
        margin-bottom: 1.25rem !important;
        background: rgba(255, 255, 255, 0.45) !important;
        border: 1px solid rgba(241, 193, 223, 0.85) !important;
        border-radius: 14px !important;
        box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.65) !important;
    }}

    a.selv-secnav-btn,
    .selv-secnav-bar a,
    [data-testid="stHtml"] a.selv-secnav-btn,
    [data-testid="stMarkdownContainer"] a.selv-secnav-btn {{
        flex: 1 1 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        min-height: 2.55rem !important;
        padding: 0.68rem 0.9rem !important;
        border-radius: 10px !important;
        background: transparent !important;
        border: 1px solid transparent !important;
        box-shadow: none !important;
        color: {c['olive']} !important;
        font-family: 'Nunito', 'Segoe UI', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.9rem !important;
        text-align: center !important;
        text-decoration: none !important;
        text-underline-offset: unset !important;
        cursor: pointer !important;
        transition: background 0.18s ease, border-color 0.18s ease, color 0.18s ease !important;
        white-space: nowrap !important;
        box-sizing: border-box !important;
        -webkit-tap-highlight-color: transparent !important;
    }}

    a.selv-secnav-btn:link,
    a.selv-secnav-btn:visited,
    .selv-secnav-bar a:link,
    .selv-secnav-bar a:visited {{
        color: {c['olive']} !important;
        text-decoration: none !important;
    }}

    a.selv-secnav-btn:hover,
    .selv-secnav-bar a:hover {{
        background: rgba(255, 255, 255, 0.5) !important;
        color: {c['olive_dark']} !important;
        border-color: rgba(241, 193, 223, 0.7) !important;
        text-decoration: none !important;
    }}

    a.selv-secnav-btn--active,
    a.selv-secnav-btn--active:link,
    a.selv-secnav-btn--active:visited,
    .selv-secnav-bar a.selv-secnav-btn--active {{
        background: linear-gradient(
            90deg,
            rgba(241, 193, 223, 0.72) 0%,
            rgba(255, 249, 194, 0.45) 100%
        ) !important;
        color: {c['olive']} !important;
        border: 1px solid transparent !important;
        border-left: 3px solid {c['brown']} !important;
        box-shadow: 0 2px 10px rgba(122, 94, 53, 0.08) !important;
        font-weight: 700 !important;
        text-decoration: none !important;
    }}

    a.selv-secnav-btn--active:hover,
    .selv-secnav-bar a.selv-secnav-btn--active:hover {{
        background: linear-gradient(
            90deg,
            rgba(241, 193, 223, 0.82) 0%,
            rgba(255, 249, 194, 0.55) 100%
        ) !important;
        color: {c['olive']} !important;
        border-left-color: {c['brown']} !important;
        text-decoration: none !important;
    }}

    /* Encabezados */
    h1, h2, h3, .stSubheader {{
        color: {c['olive']} !important;
        font-weight: 700;
    }}

    /* Formularios — solo área principal */
    section[data-testid="stMain"] .stSelectbox label,
    section[data-testid="stMain"] .stTextInput label,
    section[data-testid="stMain"] .stNumberInput label,
    section[data-testid="stMain"] .stTextArea label,
    section[data-testid="stMain"] .stCheckbox label,
    section[data-testid="stMain"] .stMultiSelect label {{
        color: {c['olive']} !important;
        font-weight: 600;
    }}

    .sidebar-tagline {{
        text-align: center;
        font-size: 0.88rem;
        font-weight: 800;
        margin: 0.15rem 0 1.1rem 0;
        color: {c['olive']};
        letter-spacing: 0.04em;
        text-transform: uppercase;
        opacity: 0.85;
    }}

    /* Alertas personalizadas Selvatica */
    .selv-alert {{
        border-radius: 12px;
        padding: 0.85rem 1.1rem;
        margin: 0.75rem 0;
        font-weight: 600;
        border: 2px solid {c['brown']};
        color: {c['olive']};
    }}
    .selv-alert-warning {{
        background: {c['cream']};
        border-color: {c['brown']};
    }}
    .selv-alert-info {{
        background: {c['pink_soft']};
        border-color: {c['pink']};
    }}
    .selv-alert-success {{
        background: #E8F5D8;
        border-color: {c['olive']};
    }}
    .selv-alert-error {{
        background: #FDE8E8;
        border-color: #9B3A3A;
        color: #5C2020;
    }}

    /* Gráficos Altair — fondo transparente y sin recorte */
    [data-testid="stArrowVegaLiteChart"],
    [data-testid="stVegaLiteChart"],
    [data-testid="stArrowVegaLiteChart"] > div,
    [data-testid="stVegaLiteChart"] > div,
    .vega-embed,
    .vega-embed .chart-wrapper,
    .vega-embed .marks {{
        background: transparent !important;
        background-color: transparent !important;
        overflow: visible !important;
    }}

    /* Dashboard — filtros y tarjetas de gráficos */
    .selv-dashboard-filters-marker {{
        display: none;
    }}

    .main .block-container:has(.selv-dashboard-filters-marker) div[data-testid="stVerticalBlockBorderWrapper"] {{
        background: rgba(255, 255, 255, 0.42) !important;
        border: 1.5px solid rgba(181, 126, 220, 0.45) !important;
        border-radius: 18px !important;
        padding: 0.85rem 1rem 1.1rem !important;
        margin-bottom: 1.35rem !important;
        box-shadow: 0 8px 22px rgba(78, 87, 46, 0.08) !important;
    }}

    .main .block-container:has(.selv-dashboard-filters-marker) div[data-testid="stVerticalBlockBorderWrapper"] h3 {{
        margin-top: 0 !important;
        margin-bottom: 0.35rem !important;
        color: {c['olive']} !important;
    }}

    .main .block-container:has(.selv-dashboard-filters-marker) div[data-testid="stHorizontalBlock"]:has([data-testid="stVerticalBlockBorderWrapper"]) {{
        gap: 1.25rem !important;
        margin-bottom: 0.35rem !important;
    }}

    .main .block-container:has(.selv-dashboard-filters-marker) div[data-testid="stHorizontalBlock"]:has(div[data-testid="stMetric"]) {{
        gap: 1rem !important;
        margin-bottom: 1.25rem !important;
    }}

    {mobile_bar_css}

    {mobile_page_css}
    """


def render_page_header(title: str, subtitle: str, page_key: str = "") -> None:
    import streamlit as st

    st.markdown(
        f"""
        <div class="page-doodle-wrap">
            <p class="main-header">{title}</p>
            <p class="sub-header">{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_branding() -> None:
    import streamlit as st

    sync_sidebar_compact_state()
    compact = st.session_state.sidebar_compact

    st.sidebar.markdown(
        f'<div class="selv-sidebar-mode-marker" data-compact="{"1" if compact else "0"}"></div>',
        unsafe_allow_html=True,
    )

    toggle_label = "›" if compact else "‹"
    if st.sidebar.button(
        toggle_label,
        key="selv_sidebar_compact_toggle",
        help="Contraer o expandir menú",
        type="tertiary",
    ):
        st.session_state.sidebar_compact = not compact
        if st.session_state.sidebar_compact:
            st.query_params["sidebar_compact"] = "1"
        elif "sidebar_compact" in st.query_params:
            del st.query_params["sidebar_compact"]
        st.rerun()

    logo_path = resolve_logo_path()
    icon_path = resolve_icon_path()
    if logo_path is not None:
        st.sidebar.markdown(
            f'<div class="selv-sidebar-logo-full"><img src="{_asset_data_uri(logo_path)}" alt="Selvatica" /></div>',
            unsafe_allow_html=True,
        )
    if icon_path is not None:
        st.sidebar.markdown(
            f'<div class="selv-sidebar-icon-mini"><img src="{_asset_data_uri(icon_path)}" alt="Selvatica" /></div>',
            unsafe_allow_html=True,
        )
    st.sidebar.markdown(
        '<div class="sidebar-tagline">Centro de Operaciones</div>',
        unsafe_allow_html=True,
    )


def sidebar_compact_query_suffix() -> str:
    """Sufijo para enlaces que deben conservar el menú compacto."""
    import streamlit as st

    if st.session_state.get("sidebar_compact"):
        return "&sidebar_compact=1"
    return ""


def sync_sidebar_compact_state() -> None:
    """Menú expandido al iniciar; persiste compacto vía query param en sub-secciones."""
    import streamlit as st

    compact_param = st.query_params.get("sidebar_compact")
    if compact_param == "1":
        st.session_state.sidebar_compact = True
    elif compact_param == "0":
        st.session_state.sidebar_compact = False
    elif "sidebar_compact" not in st.session_state:
        st.session_state.sidebar_compact = False


def render_sidebar_expand_lock() -> None:
    """Evita el colapso nativo roto de Streamlit 1.61 en desktop al recargar."""
    import streamlit as st

    st.html(
        """
        <div id="selv-sidebar-expand-lock" hidden aria-hidden="true"></div>
        <script>
        (function () {
            if (window.__selvSidebarExpandInit) return;
            window.__selvSidebarExpandInit = true;

            const isDesktop = () => window.matchMedia("(min-width: 769px)").matches;

            const clearCollapsedState = () => {
                if (!isDesktop()) return;
                try {
                    Object.keys(window.localStorage).forEach((key) => {
                        if (key.startsWith("stSidebarCollapsed-")) {
                            window.localStorage.removeItem(key);
                        }
                    });
                } catch (err) {
                    /* ignore */
                }
            };

            const forceSidebarExpanded = () => {
                if (!isDesktop()) return;

                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                if (!sidebar) return;

                if (sidebar.getAttribute("aria-expanded") === "false") {
                    sidebar.setAttribute("aria-expanded", "true");
                }

                sidebar.style.removeProperty("width");
                sidebar.style.removeProperty("min-width");
                sidebar.style.removeProperty("max-width");
                sidebar.style.removeProperty("transform");
                sidebar.style.removeProperty("margin-left");

                const content = sidebar.querySelector('[data-testid="stSidebarContent"]');
                if (content) {
                    content.style.removeProperty("width");
                    content.style.removeProperty("min-width");
                    content.style.removeProperty("max-width");
                    content.style.removeProperty("transform");
                }
            };

            const run = () => {
                clearCollapsedState();
                forceSidebarExpanded();
            };

            run();
            document.addEventListener("DOMContentLoaded", run);
            window.addEventListener("load", run);

            const observer = new MutationObserver(run);
            observer.observe(document.documentElement, {
                childList: true,
                subtree: true,
                attributes: true,
                attributeFilter: ["aria-expanded", "style", "class"],
            });

            let tries = 0;
            const intervalId = window.setInterval(() => {
                run();
                tries += 1;
                if (tries >= 50) {
                    window.clearInterval(intervalId);
                }
            }, 100);
        })();
        </script>
        """,
    )


def show_alert(message: str, kind: str = "info") -> None:
    import streamlit as st

    css_class = {
        "warning": "selv-alert selv-alert-warning",
        "info": "selv-alert selv-alert-info",
        "success": "selv-alert selv-alert-success",
        "error": "selv-alert selv-alert-error",
    }.get(kind, "selv-alert selv-alert-info")

    st.markdown(f'<div class="{css_class}">{message}</div>', unsafe_allow_html=True)


def render_sidebar_nav(menu: dict[str, str], state_key: str = "nav_page") -> str:
    import streamlit as st

    if state_key not in st.session_state:
        st.session_state[state_key] = next(iter(menu.values()))

    for label, page_key in menu.items():
        active = st.session_state[state_key] == page_key
        if st.sidebar.button(
            label,
            key=f"nav_{page_key}",
            use_container_width=True,
            type="primary" if active else "secondary",
        ):
            st.session_state[state_key] = page_key
            st.rerun()

    return st.session_state[state_key]


def sync_mobile_nav_from_query(
    menu: dict[str, str],
    state_key: str = "nav_page",
) -> None:
    import streamlit as st

    valid_pages = set(menu.values())
    nav_param = st.query_params.get("selv_nav")
    if not nav_param or nav_param not in valid_pages:
        return

    if st.session_state.get(state_key) != nav_param:
        st.session_state[state_key] = nav_param

    if "selv_nav" in st.query_params:
        del st.query_params["selv_nav"]


def _mobile_nav_label(label: str, page_key: str) -> str:
    if page_key == "alertas" and "(" in label:
        count = label.split("(")[-1].rstrip(")")
        return f"Alertas ({count})"
    return MOBILE_NAV_LABELS.get(page_key, label.split()[0])


def _mobile_nav_badge(label: str, page_key: str) -> str:
    import html

    if page_key == "alertas" and "(" in label:
        count = label.split("(")[-1].rstrip(")")
        return f'<span class="selv-mobile-nav-badge">{html.escape(count)}</span>'
    return ""


def render_mobile_bottom_nav(menu: dict[str, str], state_key: str = "nav_page") -> None:
    import html

    import streamlit as st

    current = st.session_state.get(state_key, next(iter(menu.values())))
    sidebar_compact_flag = "1" if st.session_state.get("sidebar_compact") else "0"
    links: list[str] = []
    for label, page_key in menu.items():
        active_class = " selv-mobile-nav-item--active" if current == page_key else ""
        nav_label = _mobile_nav_label(label, page_key)
        icon = _mobile_nav_icon_data_uri(page_key)
        badge_html = _mobile_nav_badge(label, page_key)
        aria_current = ' aria-current="page"' if current == page_key else ""
        links.append(
            f'<a class="selv-mobile-nav-item selv-mobile-nav-item--{html.escape(page_key)}{active_class}" '
            f'href="#" data-selv-nav-page="{html.escape(page_key)}" '
            f'data-sidebar-compact="{sidebar_compact_flag}" '
            f'title="{html.escape(nav_label)}" aria-label="{html.escape(nav_label)}"{aria_current}>'
            f'<img class="selv-mobile-nav-icon" src="{icon}" width="22" height="22" alt="" aria-hidden="true">'
            f'<span class="selv-mobile-nav-label">{html.escape(nav_label)}</span>'
            f"{badge_html}"
            f"</a>"
        )

    st.html(
        f"""
        <div class="selv-mobile-nav-shell" aria-hidden="false">
            <details class="selv-mobile-nav-details">
                <summary class="selv-mobile-menu-toggle" aria-label="Abrir menú">
                    <span></span><span></span><span></span>
                </summary>
                <nav class="selv-mobile-drawer" aria-label="Navegación principal">
                    {"".join(links)}
                </nav>
            </details>
        </div>
        <script>
        (function () {{
            const targetWin = window.top || window;
            const doc = targetWin.document || document;
            doc.querySelectorAll("[data-selv-nav-page]").forEach((link) => {{
                if (link.dataset.selvNavBound === "1") return;
                link.dataset.selvNavBound = "1";
                link.addEventListener("click", (event) => {{
                    event.preventDefault();
                    const page = link.getAttribute("data-selv-nav-page");
                    if (!page) return;
                    const url = new URL(targetWin.location.href);
                    url.searchParams.set("selv_nav", page);
                    if (link.getAttribute("data-sidebar-compact") === "1") {{
                        url.searchParams.set("sidebar_compact", "1");
                    }} else {{
                        url.searchParams.delete("sidebar_compact");
                    }}
                    const details = link.closest(".selv-mobile-nav-details");
                    if (details) details.removeAttribute("open");
                    targetWin.location.assign(url.toString());
                }});
            }});
        }})();
        </script>
        """,
        unsafe_allow_javascript=True,
    )


def _secnav_bar_inline_style() -> str:
    return (
        "display:flex;flex-wrap:wrap;align-items:stretch;gap:0.35rem;"
        "padding:0.35rem;margin:0 0 1.25rem 0;width:100%;box-sizing:border-box;"
        "background:rgba(255,255,255,0.45);"
        "border:1px solid rgba(241,193,223,0.85);border-radius:14px;"
        "box-shadow:inset 0 1px 0 rgba(255,255,255,0.65);"
    )


def _secnav_btn_inline_style(active: bool) -> str:
    olive = COLORS["olive"]
    brown = COLORS["brown"]
    base = (
        "flex:1 1 auto;display:flex;align-items:center;justify-content:center;"
        "min-height:2.55rem;padding:0.68rem 0.9rem;border-radius:10px;"
        "font-family:'Nunito','Segoe UI',sans-serif;font-size:0.9rem;"
        "text-align:center;text-decoration:none !important;"
        "cursor:pointer;white-space:nowrap;box-sizing:border-box;"
        "-webkit-tap-highlight-color:transparent;"
    )
    if active:
        return (
            base
            + "background:linear-gradient(90deg,rgba(241,193,223,0.72) 0%,rgba(255,249,194,0.45) 100%);"
            + f"color:{olive} !important;"
            + f"border:1px solid transparent;border-left:3px solid {brown};"
            + "box-shadow:0 2px 10px rgba(122,94,53,0.08);font-weight:700;"
        )
    return (
        base
        + "background:transparent;"
        + f"color:{olive} !important;"
        + "border:1px solid transparent;font-weight:600;"
    )


def _sync_section_from_query(key: str, options: list[str], state_key: str) -> None:
    import streamlit as st

    param_key = f"sec_{key}"
    value = st.query_params.get(param_key)
    if not value or value not in options:
        return

    st.session_state[state_key] = value
    if param_key in st.query_params:
        del st.query_params[param_key]


def section_tabs(options: list[str], key: str) -> str:
    import html as html_module
    from urllib.parse import quote

    import streamlit as st

    state_key = f"secnav_state_{key}"
    legacy_key = f"section_{key}"

    if state_key not in st.session_state:
        if legacy_key in st.session_state and st.session_state[legacy_key] in options:
            st.session_state[state_key] = st.session_state[legacy_key]
        else:
            st.session_state[state_key] = options[0]

    _sync_section_from_query(key, options, state_key)
    current = st.session_state[state_key]
    page_key = st.session_state.get("nav_page", "dashboard")
    compact_suffix = sidebar_compact_query_suffix()

    items = []
    for option in options:
        active = option == current
        active_cls = " selv-secnav-btn--active" if active else ""
        safe_label = html_module.escape(option)
        href = f"?selv_nav={quote(page_key)}&sec_{key}={quote(option)}{compact_suffix}"
        items.append(
            f'<a class="selv-secnav-btn{active_cls}" href="{href}" '
            f'title="{safe_label}">{safe_label}</a>'
        )

    st.html(
        f'<nav class="selv-secnav-bar" aria-label="Sección">{"".join(items)}</nav>',
        unsafe_allow_javascript=False,
    )

    return current


def render_table(
    df,
    *,
    key: str = "selv_table",
    page_size: int = 10,
    paginate: bool = True,
) -> None:
    import html
    import math

    import pandas as pd
    import streamlit as st

    from config import format_cop

    if df is None:
        return
    if isinstance(df, list):
        if not df:
            return
        df = pd.DataFrame(df)
    if not isinstance(df, pd.DataFrame) or df.empty:
        return

    total = len(df)
    page_size_options = [10, 15, 25, 50]
    size_key = f"{key}_page_size"
    page_key = f"{key}_page"
    last_size_key = f"{key}_last_size"
    total_key = f"{key}_total"

    if size_key not in st.session_state:
        st.session_state[size_key] = page_size
    if st.session_state.get(total_key) != total:
        st.session_state[page_key] = 0
        st.session_state[total_key] = total
    if last_size_key not in st.session_state:
        st.session_state[last_size_key] = st.session_state[size_key]
    elif st.session_state[size_key] != st.session_state[last_size_key]:
        st.session_state[page_key] = 0
        st.session_state[last_size_key] = st.session_state[size_key]

    current_size = int(st.session_state[size_key])
    if current_size not in page_size_options:
        current_size = page_size
        st.session_state[size_key] = current_size

    use_pagination = paginate and total > current_size
    if use_pagination:
        max_page = max(0, math.ceil(total / current_size) - 1)
        if page_key not in st.session_state:
            st.session_state[page_key] = 0
        current_page = min(int(st.session_state[page_key]), max_page)
        st.session_state[page_key] = current_page
        start = current_page * current_size
        end = min(start + current_size, total)
        display_df = df.iloc[start:end].copy()
    else:
        current_page = 0
        max_page = 0
        start = 0
        end = total
        display_df = df.copy()

    currency_columns = {
        "precio",
        "precio_unitario",
        "subtotal",
        "monto",
        "total",
    }
    for col in display_df.columns:
        if str(col).lower() in currency_columns:
            numeric = pd.to_numeric(display_df[col], errors="coerce")
            display_df[col] = numeric.apply(lambda v: format_cop(v) if pd.notna(v) else "")

    cols = list(display_df.columns)
    thead = "".join(f"<th>{html.escape(str(col))}</th>" for col in cols)
    rows = []
    for _, row in display_df.iterrows():
        cells = "".join(f"<td>{html.escape(str(row[col]))}</td>" for col in cols)
        rows.append(f"<tr>{cells}</tr>")

    st.markdown(
        f"""
        <div class="selv-table-wrap">
            <table class="selv-table">
                <thead><tr>{thead}</tr></thead>
                <tbody>{"".join(rows)}</tbody>
            </table>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if not use_pagination:
        return

    st.markdown('<div class="selv-pagination-root" hidden></div>', unsafe_allow_html=True)

    info_col, page_col, prev_col, next_col, size_col = st.columns(
        [1.45, 0.9, 0.8, 0.8, 1.15],
        vertical_alignment="center",
    )
    with info_col:
        st.markdown(
            f'<p class="selv-pagination-text">Mostrando {start + 1}–{end} de {total}</p>',
            unsafe_allow_html=True,
        )
    with page_col:
        st.markdown(
            (
                f'<p class="selv-pagination-text selv-pagination-page">'
                f"Página {current_page + 1} de {max_page + 1}</p>"
            ),
            unsafe_allow_html=True,
        )
    with prev_col:
        if st.button(
            "Anterior",
            key=f"{key}_prev",
            disabled=current_page <= 0,
            use_container_width=True,
        ):
            st.session_state[page_key] = current_page - 1
            st.rerun()
    with next_col:
        if st.button(
            "Siguiente",
            key=f"{key}_next",
            disabled=current_page >= max_page,
            use_container_width=True,
        ):
            st.session_state[page_key] = current_page + 1
            st.rerun()
    with size_col:
        st.selectbox(
            "Filas por página",
            options=page_size_options,
            key=size_key,
        )
