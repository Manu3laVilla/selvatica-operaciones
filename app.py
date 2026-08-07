import streamlit as st

import json

import demo_data
from config import (
    DEFAULT_EXPENSE_TYPES,
    DEFAULT_INCOME_TYPES,
    DEFAULT_ORDER_STATES,
    DEFAULT_PRODUCT_CATEGORIES,
    format_cop,
    is_preview_mode,
    resolves_data_backend,
)
from services.alert_service import get_low_stock_alerts
from services.catalog_service import (
    create_expense_type,
    create_income_type,
    create_order_state,
    create_product_category,
    delete_expense_type,
    delete_income_type,
    delete_order_state,
    delete_product_category,
    ensure_catalog_defaults,
    expense_type_names,
    income_type_names,
    list_expense_types,
    list_income_types,
    list_order_states,
    list_product_categories,
    state_generates_sale,
    state_reverses_sale,
    update_expense_type,
    update_income_type,
    update_order_state,
    update_product_category,
)
from services.customer_service import create_customer, list_customers, update_customer
from services.finance_service import (
    format_movement_date,
    list_movements,
    register_movement,
    update_movement,
)
from services.order_service import (
    create_order,
    get_order_items,
    list_orders,
    release_stock_for_items,
    reserve_stock_for_items,
    update_order_status,
)
from services.product_service import create_product, list_products, update_product
from services.sale_service import list_sales, sales_exist_for_order
from services.db import get_db, new_id, now_str
from ui.theme import (
    get_global_css,
    render_mobile_bottom_nav,
    render_page_header,
    render_sidebar_branding,
    render_sidebar_expand_lock,
    render_streamlit_chrome_hide_script,
    render_sidebar_nav,
    render_table,
    section_tabs,
    show_alert,
    sync_mobile_nav_from_query,
    sync_sidebar_compact_state,
    queue_action_message,
    render_action_message,
)

st.set_page_config(
    page_title="Selvatica | Centro de Operaciones",
    page_icon="🌸",
    layout="wide",
    initial_sidebar_state="expanded",
)

sync_sidebar_compact_state()
st.markdown(f"<style>{get_global_css()}</style>", unsafe_allow_html=True)
render_streamlit_chrome_hide_script()
render_sidebar_expand_lock()

if "preview_mode" not in st.session_state:
    st.session_state.preview_mode = is_preview_mode()


def init_connection() -> bool:
    if st.session_state.preview_mode:
        return True

    try:
        get_db().connect()
        ensure_catalog_defaults()
        st.session_state.preview_mode = False
        return True
    except Exception as exc:
        st.session_state.preview_mode = True
        show_alert("Modo vista previa — datos de ejemplo (sin conexión a la base)", "warning")
        st.caption(
            "Configura DATABASE_URL (Supabase) o SPREADSHEET_ID + credenciales de Google "
            f"en .env / Streamlit Secrets. Detalle: {exc}"
        )
        return True


def _catalog_is_active(value) -> bool:
    return str(value).strip().lower() in ("si", "sí", "true", "1", "yes")


def _init_preview_catalogs() -> None:
    if st.session_state.get("preview_catalogs_ready"):
        return

    st.session_state.preview_catalogs = {
        "categorias": [
            {
                "id": f"CAT-P{i:02d}",
                "nombre": name,
                "activo": "Si",
                "orden": i,
                "fecha_registro": "2026-08-01 10:00:00",
            }
            for i, name in enumerate(DEFAULT_PRODUCT_CATEGORIES, start=1)
        ],
        "tipos_ingreso": [
            {
                "id": f"ING-P{i:02d}",
                "nombre": name,
                "activo": "Si",
                "orden": i,
                "fecha_registro": "2026-08-01 10:00:00",
            }
            for i, name in enumerate(DEFAULT_INCOME_TYPES, start=1)
        ],
        "tipos_gasto": [
            {
                "id": f"GAS-P{i:02d}",
                "nombre": name,
                "activo": "Si",
                "orden": i,
                "fecha_registro": "2026-08-01 10:00:00",
            }
            for i, name in enumerate(DEFAULT_EXPENSE_TYPES, start=1)
        ],
        "estados_pedido": [
            {
                "id": f"EST-P{i:02d}",
                "nombre": state["nombre"],
                "activo": "Si",
                "orden": i,
                "genera_venta": state["genera_venta"],
                "revierte_venta": state["revierte_venta"],
                "fecha_registro": "2026-08-01 10:00:00",
            }
            for i, state in enumerate(DEFAULT_ORDER_STATES, start=1)
        ],
    }
    st.session_state.preview_catalogs_ready = True


def _preview_catalog_df(key: str):
    import pandas as pd

    _init_preview_catalogs()
    return pd.DataFrame(st.session_state.preview_catalogs[key])


def _product_categories_df(active_only: bool = False):
    if st.session_state.preview_mode:
        df = _preview_catalog_df("categorias")
    else:
        df = list_product_categories(active_only=False)
    if active_only and not df.empty:
        df = df[df["activo"].map(_catalog_is_active)]
    return df.sort_values("orden") if not df.empty and "orden" in df.columns else df


def _income_types_df(active_only: bool = False):
    if st.session_state.preview_mode:
        df = _preview_catalog_df("tipos_ingreso")
    else:
        df = list_income_types(active_only=False)
    if active_only and not df.empty:
        df = df[df["activo"].map(_catalog_is_active)]
    return df.sort_values("orden") if not df.empty and "orden" in df.columns else df


def _expense_types_df(active_only: bool = False):
    if st.session_state.preview_mode:
        df = _preview_catalog_df("tipos_gasto")
    else:
        df = list_expense_types(active_only=False)
    if active_only and not df.empty:
        df = df[df["activo"].map(_catalog_is_active)]
    return df.sort_values("orden") if not df.empty and "orden" in df.columns else df


def _order_states_df(active_only: bool = False):
    if st.session_state.preview_mode:
        df = _preview_catalog_df("estados_pedido")
    else:
        df = list_order_states(active_only=False)
    if active_only and not df.empty:
        df = df[df["activo"].map(_catalog_is_active)]
    return df.sort_values("orden") if not df.empty and "orden" in df.columns else df


def _product_category_names(active_only: bool = True) -> list[str]:
    df = _product_categories_df(active_only=active_only)
    if df.empty:
        return list(DEFAULT_PRODUCT_CATEGORIES)
    return df["nombre"].astype(str).tolist()


def _income_type_names(active_only: bool = True) -> list[str]:
    df = _income_types_df(active_only=active_only)
    if df.empty:
        return list(DEFAULT_INCOME_TYPES)
    return df["nombre"].astype(str).tolist()


def _expense_type_names(active_only: bool = True) -> list[str]:
    df = _expense_types_df(active_only=active_only)
    if df.empty:
        return list(DEFAULT_EXPENSE_TYPES)
    return df["nombre"].astype(str).tolist()


def _order_state_names(active_only: bool = True) -> list[str]:
    df = _order_states_df(active_only=active_only)
    if df.empty:
        return [state["nombre"] for state in DEFAULT_ORDER_STATES]
    return df["nombre"].astype(str).tolist()


def _order_state_generates_sale(state_name: str) -> bool:
    if st.session_state.preview_mode:
        df = _order_states_df()
        match = df[df["nombre"].astype(str) == str(state_name)]
        if match.empty:
            return state_name == "Entregado"
        return _catalog_is_active(match.iloc[0].get("genera_venta", "No"))
    return state_generates_sale(state_name)


def _order_state_reverses_sale(state_name: str) -> bool:
    if st.session_state.preview_mode:
        df = _order_states_df()
        match = df[df["nombre"].astype(str) == str(state_name)]
        if match.empty:
            return state_name == "Cancelado"
        return _catalog_is_active(match.iloc[0].get("revierte_venta", "No"))
    return state_reverses_sale(state_name)


def _products(active_only: bool = False):
    if st.session_state.preview_mode:
        df = demo_data.products()
        if active_only:
            df = df[df["activo"].astype(str).str.lower().isin(["si", "sí", "true", "1"])]
        return df
    return list_products(active_only=active_only)


def _customers():
    return demo_data.customers() if st.session_state.preview_mode else list_customers()


def _init_preview_sales() -> None:
    if "preview_sales" not in st.session_state:
        st.session_state.preview_sales = demo_data.sales().to_dict("records")


def _init_preview_orders() -> None:
    if "preview_orders" not in st.session_state:
        st.session_state.preview_orders = demo_data.orders().to_dict("records")


def _sales():
    import pandas as pd

    if st.session_state.preview_mode:
        _init_preview_sales()
        return pd.DataFrame(st.session_state.preview_sales)
    return list_sales()


def _orders():
    import pandas as pd

    if st.session_state.preview_mode:
        _init_preview_orders()
        df = pd.DataFrame(st.session_state.preview_orders)
        if df.empty:
            return df
        if "total" in df.columns:
            df["total"] = pd.to_numeric(df["total"], errors="coerce").fillna(0)
        if "fecha_creacion" in df.columns:
            return df.sort_values("fecha_creacion", ascending=False)
        return df
    return list_orders()


def _alerts():
    return demo_data.low_stock_alerts() if st.session_state.preview_mode else get_low_stock_alerts()


def _init_preview_finance() -> None:
    if "preview_finance" not in st.session_state:
        st.session_state.preview_finance = demo_data.finance_movements().to_dict("records")


def _finance_movements():
    import pandas as pd

    if st.session_state.preview_mode:
        _init_preview_finance()
        return pd.DataFrame(st.session_state.preview_finance)
    return list_movements()


def _register_finance_movement(
    tipo: str,
    categoria: str,
    concepto: str,
    monto: float,
    notas: str = "",
    *,
    fecha=None,
):
    if st.session_state.preview_mode:
        _init_preview_finance()
        record = {
            "id": new_id("FIN"),
            "fecha": format_movement_date(fecha),
            "tipo": tipo,
            "categoria": categoria,
            "concepto": concepto.strip(),
            "monto": float(monto),
            "notas": notas.strip(),
        }
        st.session_state.preview_finance.insert(0, record)
        return record
    return register_movement(
        tipo,
        categoria,
        concepto,
        monto,
        notas,
        fecha=fecha,
    )


def _update_finance_movement(movement_id: str, updates: dict) -> bool:
    if st.session_state.preview_mode:
        _init_preview_finance()
        for index, record in enumerate(st.session_state.preview_finance):
            if str(record.get("id", "")) != str(movement_id):
                continue
            updated = dict(record)
            updated.update(updates)
            if "fecha" in updates:
                updated["fecha"] = format_movement_date(updates["fecha"])
            if float(updated.get("monto", 0)) <= 0:
                raise ValueError("El monto debe ser mayor a cero.")
            if not str(updated.get("concepto", "")).strip():
                raise ValueError("El concepto es obligatorio.")
            if not str(updated.get("categoria", "")).strip():
                raise ValueError("La categoría es obligatoria.")
            st.session_state.preview_finance[index] = updated
            return True
        return False
    return update_movement(movement_id, updates)


def _movement_form_date(value) -> "date":
    import pandas as pd
    from datetime import date

    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return date.today()
    return parsed.date()


def _movement_option_label(row) -> str:
    movement_date = _movement_form_date(row.get("fecha")).strftime("%Y-%m-%d")
    return (
        f"{movement_date} | {row['tipo']} | {row['concepto']} "
        f"({format_cop(row['monto'])}) — {row['id']}"
    )


def _normalize_finance_movements(movements):
    import pandas as pd

    if movements.empty:
        return movements

    df = movements.copy()
    df["monto"] = pd.to_numeric(df["monto"], errors="coerce").fillna(0)
    df["fecha_dt"] = pd.to_datetime(df["fecha"], errors="coerce")
    return df.sort_values("fecha_dt", ascending=False)


def _finance_filter_controls(
    movements,
    *,
    optional: bool = False,
    key_prefix: str = "contabilidad",
):
    import pandas as pd
    from datetime import date

    df = _normalize_finance_movements(movements)
    if df.empty:
        return df

    if optional:
        apply_filters = st.checkbox(
            "Aplicar filtros",
            value=False,
            key=f"{key_prefix}_apply_filters",
            help="Desactivado muestra todos los movimientos del sistema.",
        )
        if not apply_filters:
            st.caption("Mostrando la totalidad de movimientos registrados.")
            return df.sort_values("fecha_dt", ascending=False)

    min_date = df["fecha_dt"].min().date()
    max_date = df["fecha_dt"].max().date()
    if min_date > max_date:
        min_date = max_date = date.today()

    st.markdown("##### Filtros")
    c1, c2, c3 = st.columns(3)
    with c1:
        tipo_filter = st.selectbox(
            "Tipo de movimiento",
            ["Todos", "Ingresos", "Gastos"],
            key=f"{key_prefix}_filter_tipo",
        )
    with c2:
        fecha_desde = st.date_input(
            "Desde",
            value=min_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_filter_desde",
        )
    with c3:
        fecha_hasta = st.date_input(
            "Hasta",
            value=max_date,
            min_value=min_date,
            max_value=max_date,
            key=f"{key_prefix}_filter_hasta",
        )

    if fecha_desde > fecha_hasta:
        show_alert("La fecha inicial no puede ser posterior a la final.", "warning")
        return df.iloc[0:0]

    filtered = df[
        (df["fecha_dt"].dt.date >= fecha_desde) & (df["fecha_dt"].dt.date <= fecha_hasta)
    ]

    if tipo_filter == "Ingresos":
        filtered = filtered[filtered["tipo"] == "Ingreso"]
    elif tipo_filter == "Gastos":
        filtered = filtered[filtered["tipo"] == "Gasto"]

    return filtered.sort_values("fecha_dt", ascending=False)


def _render_finance_metrics(filtered) -> None:
    if filtered.empty:
        return

    income = filtered[filtered["tipo"] == "Ingreso"]["monto"].sum()
    expenses = filtered[filtered["tipo"] == "Gasto"]["monto"].sum()
    balance = income - expenses

    c1, c2, c3 = st.columns(3)
    c1.metric("Total ingresos", format_cop(income))
    c2.metric("Total gastos", format_cop(expenses))
    c3.metric("Balance contable", format_cop(balance))


def _render_finance_charts(filtered) -> None:
    import altair as alt
    import pandas as pd

    if filtered.empty:
        return

    totals = (
        filtered.groupby("tipo", as_index=False)["monto"]
        .sum()
        .assign(
            etiqueta=lambda d: d["tipo"].map({"Ingreso": "Ingresos", "Gasto": "Gastos"})
        )
    )
    for label in ("Ingresos", "Gastos"):
        if label not in totals["etiqueta"].values:
            tipo = "Ingreso" if label == "Ingresos" else "Gasto"
            totals = pd.concat(
                [totals, pd.DataFrame({"tipo": [tipo], "monto": [0.0], "etiqueta": [label]})],
                ignore_index=True,
            )
    totals = totals.sort_values("etiqueta", key=lambda s: s.map({"Ingresos": 0, "Gastos": 1}))

    income_by_category = (
        filtered[filtered["tipo"] == "Ingreso"]
        .groupby("categoria", as_index=False)["monto"]
        .sum()
        .sort_values("monto", ascending=False)
    )
    expenses_by_category = (
        filtered[filtered["tipo"] == "Gasto"]
        .groupby("categoria", as_index=False)["monto"]
        .sum()
        .sort_values("monto", ascending=False)
    )

    with st.container(border=True):
        st.subheader("Ingresos vs gastos")
        chart = (
            alt.Chart(totals)
            .mark_bar(
                cornerRadiusTopLeft=10,
                cornerRadiusTopRight=10,
                stroke=SELV_CHART_STROKE,
                strokeWidth=0.5,
            )
            .encode(
                x=alt.X("etiqueta:N", title="Tipo", sort=["Ingresos", "Gastos"], axis=_category_axis("Tipo")),
                y=alt.Y(
                    "monto:Q",
                    title="Monto (COP)",
                    axis=alt.Axis(format=",.0f"),
                    scale=alt.Scale(nice=True, padding=0.1),
                ),
                color=alt.Color(
                    "etiqueta:N",
                    scale=alt.Scale(
                        domain=["Ingresos", "Gastos"],
                        range=[SELV_CHART_ACCENT, SELV_CHART_ACCENT_2],
                    ),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("etiqueta:N", title="Tipo"),
                    alt.Tooltip("monto:Q", title="Monto (COP)", format=",.0f"),
                ],
            )
            .properties(height=DASHBOARD_CHART_HEIGHT)
        )
        st.altair_chart(_apply_altair_theme(chart), use_container_width=True)

    row_left, row_right = st.columns(2, gap="large")

    with row_left:
        with st.container(border=True):
            st.subheader("Ingresos por categoría")
            if income_by_category.empty:
                show_alert("Sin ingresos con los filtros seleccionados.", "info")
            else:
                chart = (
                    alt.Chart(income_by_category)
                    .mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10,
                        stroke=SELV_CHART_STROKE,
                        strokeWidth=0.5,
                    )
                    .encode(
                        x=alt.X("categoria:N", title="Categoría", sort="-y", axis=_category_axis("Categoría")),
                        y=alt.Y(
                            "monto:Q",
                            title="Monto (COP)",
                            axis=alt.Axis(format=",.0f"),
                            scale=alt.Scale(nice=True, padding=0.1),
                        ),
                        color=alt.Color(
                            "categoria:N",
                            scale=alt.Scale(range=SELV_CHART_COLORS),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("categoria:N", title="Categoría"),
                            alt.Tooltip("monto:Q", title="Monto (COP)", format=",.0f"),
                        ],
                    )
                    .properties(height=DASHBOARD_CHART_HEIGHT)
                )
                st.altair_chart(_apply_altair_theme(chart), use_container_width=True)

    with row_right:
        with st.container(border=True):
            st.subheader("Gastos por categoría")
            if expenses_by_category.empty:
                show_alert("Sin gastos con los filtros seleccionados.", "info")
            else:
                chart = (
                    alt.Chart(expenses_by_category)
                    .mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10,
                        stroke=SELV_CHART_STROKE,
                        strokeWidth=0.5,
                    )
                    .encode(
                        x=alt.X("categoria:N", title="Categoría", sort="-y", axis=_category_axis("Categoría")),
                        y=alt.Y(
                            "monto:Q",
                            title="Monto (COP)",
                            axis=alt.Axis(format=",.0f"),
                            scale=alt.Scale(nice=True, padding=0.1),
                        ),
                        color=alt.Color(
                            "categoria:N",
                            scale=alt.Scale(range=SELV_CHART_COLORS),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("categoria:N", title="Categoría"),
                            alt.Tooltip("monto:Q", title="Monto (COP)", format=",.0f"),
                        ],
                    )
                    .properties(height=DASHBOARD_CHART_HEIGHT)
                )
                st.altair_chart(_apply_altair_theme(chart), use_container_width=True)


SELV_CHART_COLORS = ["#B57EDC", "#C9A0E8", "#DDB8F2", "#E8C8FA", "#9B6BB8", "#F0D4FF"]
SELV_CHART_ACCENT = "#B57EDC"
SELV_CHART_ACCENT_2 = "#C9A0E8"
SELV_CHART_STROKE = "#8E5AB3"
DASHBOARD_CHART_HEIGHT = 300
DASHBOARD_PIE_HEIGHT = 320


def _categorical_legend(title: str, item_count: int):
    import altair as alt

    columns = 1 if item_count <= 2 else 2
    return alt.Legend(
        title=title,
        orient="bottom",
        direction="vertical",
        columns=columns,
        labelLimit=150,
        rowPadding=8,
        columnPadding=14,
        padding=8,
    )


def _pie_chart_padding(item_count: int) -> dict[str, int]:
    columns = 1 if item_count <= 2 else 2
    rows = max(1, (item_count + columns - 1) // columns)
    return {
        "top": 16,
        "bottom": max(96, rows * 28 + 56),
        "left": 12,
        "right": 12,
    }


def _category_axis(title: str | None = None, **kwargs):
    import altair as alt

    return alt.Axis(
        title=title,
        labelAngle=-35,
        labelAlign="right",
        labelBaseline="middle",
        labelLimit=110,
        labelOverlap=False,
        labelPadding=4,
        **kwargs,
    )


def _series_axis(title: str | None = None, **kwargs):
    import altair as alt

    return alt.Axis(
        title=title,
        labelLimit=140,
        labelOverlap="greedy",
        **kwargs,
    )


def _apply_altair_theme(chart, *, pie: bool = False, pie_padding: dict | None = None):
    chart = chart.properties(background="transparent").configure(background="transparent")
    if pie:
        chart = chart.properties(
            padding=pie_padding or {"top": 16, "bottom": 96, "left": 12, "right": 12},
        )
    return (
        chart.configure_view(fill=None, stroke=None, strokeWidth=0)
        .configure_axis(
            labelColor="#4E572E",
            titleColor="#4E572E",
            gridColor="rgba(201, 160, 232, 0.35)",
            domainColor="rgba(181, 126, 220, 0.55)",
            labelLimit=120,
            labelOverlap="greedy",
        )
        .configure_title(color="#4E572E", fontSize=16, anchor="start")
        .configure_legend(
            labelColor="#4E572E",
            titleColor="#4E572E",
            orient="bottom",
            direction="vertical",
            columns=2,
            labelLimit=150,
            rowPadding=8,
            columnPadding=14,
            padding=8,
        )
    )


def _sales_with_category(sales, products):
    import pandas as pd

    if sales.empty:
        return sales
    categories = products[["id", "categoria"]].rename(columns={"id": "producto_id"})
    return sales.merge(categories, on="producto_id", how="left")


_DASHBOARD_MONTH_LABELS = {
    1: "Ene",
    2: "Feb",
    3: "Mar",
    4: "Abr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dic",
}


def _format_dashboard_month(period_key: str) -> str:
    import pandas as pd

    period = pd.Period(period_key, freq="M")
    return f"{_DASHBOARD_MONTH_LABELS[period.month]} {period.year}"


def _dashboard_period_options(sales, orders) -> list[str]:
    import pandas as pd

    periods: set[str] = set()
    if not sales.empty and "fecha" in sales.columns:
        dates = pd.to_datetime(sales["fecha"], errors="coerce")
        periods.update(dates.dropna().dt.to_period("M").astype(str))
    if not orders.empty and "fecha_creacion" in orders.columns:
        dates = pd.to_datetime(orders["fecha_creacion"], errors="coerce")
        periods.update(dates.dropna().dt.to_period("M").astype(str))
    return sorted(periods, reverse=True)


def _apply_dashboard_filters(sales, orders, products, month_key, category, order_state):
    import pandas as pd

    filtered_sales = sales.copy()
    filtered_orders = orders.copy()

    if month_key != "Todos":
        if not filtered_sales.empty:
            sale_dates = pd.to_datetime(filtered_sales["fecha"], errors="coerce")
            filtered_sales = filtered_sales[
                sale_dates.dt.to_period("M").astype(str) == month_key
            ]
        if not filtered_orders.empty:
            order_dates = pd.to_datetime(filtered_orders["fecha_creacion"], errors="coerce")
            filtered_orders = filtered_orders[
                order_dates.dt.to_period("M").astype(str) == month_key
            ]

    if category != "Todas" and not filtered_sales.empty:
        product_ids = products.loc[products["categoria"] == category, "id"]
        filtered_sales = filtered_sales[filtered_sales["producto_id"].isin(product_ids)]

    if order_state != "Todos" and not filtered_orders.empty:
        filtered_orders = filtered_orders[filtered_orders["estado"] == order_state]

    return filtered_sales, filtered_orders


def _render_dashboard_filters(sales, orders, products):
    periods = _dashboard_period_options(sales, orders)
    month_options = ["Todos", *periods]

    if not sales.empty:
        categories_in_data = sorted(
            products.loc[products["id"].isin(sales["producto_id"]), "categoria"].unique()
        )
    else:
        categories_in_data = []
    cat_options = ["Todas", *(categories_in_data or _product_category_names(active_only=False))]

    if not orders.empty:
        states_in_data = sorted(orders["estado"].dropna().unique().tolist())
    else:
        states_in_data = list(_order_state_names(active_only=False))
    state_options = ["Todos", *states_in_data]

    st.markdown(
        '<div class="selv-dashboard-filters-marker" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    with st.container(border=True):
        st.markdown("**Filtros del dashboard**")
        f1, f2, f3 = st.columns(3)
        with f1:
            month_key = st.selectbox(
                "Mes",
                month_options,
                format_func=lambda key: (
                    "Todos los meses" if key == "Todos" else _format_dashboard_month(key)
                ),
                key="dashboard_filter_month",
            )
        with f2:
            category = st.selectbox(
                "Categoría de producto",
                cat_options,
                key="dashboard_filter_category",
            )
        with f3:
            order_state = st.selectbox(
                "Estado del pedido",
                state_options,
                key="dashboard_filter_order_state",
            )

    filtered_sales, filtered_orders = _apply_dashboard_filters(
        sales, orders, products, month_key, category, order_state
    )
    return filtered_sales, filtered_orders, month_key, category, order_state


def _product_ids_from_orders(orders) -> set[str]:
    ids: set[str] = set()
    if orders.empty:
        return ids
    for items_json in orders["items_json"].dropna():
        try:
            for item in json.loads(str(items_json)):
                product_id = item.get("producto_id")
                if product_id:
                    ids.add(str(product_id))
        except json.JSONDecodeError:
            continue
    return ids


def _dashboard_filters_active(month_key: str, category: str, order_state: str) -> bool:
    return month_key != "Todos" or category != "Todas" or order_state != "Todos"


def _dashboard_products_count(
    products, filtered_sales, filtered_orders, category, month_key, order_state
) -> int:
    if not _dashboard_filters_active(month_key, category, order_state):
        return len(products)

    scoped = products
    if category != "Todas":
        scoped = scoped[scoped["categoria"] == category]

    product_ids: set[str] = set()
    if month_key != "Todos" or category != "Todas":
        if not filtered_sales.empty:
            product_ids.update(filtered_sales["producto_id"].dropna().astype(str))
    if order_state != "Todos":
        product_ids.update(_product_ids_from_orders(filtered_orders))

    if product_ids:
        return len(scoped[scoped["id"].astype(str).isin(product_ids)])

    if category != "Todas":
        return len(scoped)

    return 0


def _dashboard_clients_count(
    customers, filtered_sales, filtered_orders, month_key, category, order_state
) -> int:
    if not _dashboard_filters_active(month_key, category, order_state):
        return len(customers)

    client_ids: set[str] = set()
    if not filtered_sales.empty:
        client_ids.update(filtered_sales["cliente_id"].dropna().astype(str))
    if order_state != "Todos" and not filtered_orders.empty:
        client_ids.update(filtered_orders["cliente_id"].dropna().astype(str))
    return len(client_ids)


def _dashboard_alerts_count(
    alerts, filtered_sales, filtered_orders, category, month_key, order_state
) -> int:
    if alerts.empty:
        return 0

    scoped = alerts
    if category != "Todas":
        scoped = scoped[scoped["categoria"] == category]

    if month_key != "Todos" or order_state != "Todos":
        product_ids: set[str] = set()
        if not filtered_sales.empty:
            product_ids.update(filtered_sales["producto_id"].dropna().astype(str))
        if order_state != "Todos":
            product_ids.update(_product_ids_from_orders(filtered_orders))
        if not product_ids:
            return 0
        scoped = scoped[scoped["id"].astype(str).isin(product_ids)]

    return len(scoped)


def _compute_dashboard_metrics(
    products,
    customers,
    alerts,
    filtered_sales,
    filtered_orders,
    month_key,
    category,
    order_state,
) -> dict[str, int | float]:
    return {
        "productos": _dashboard_products_count(
            products, filtered_sales, filtered_orders, category, month_key, order_state
        ),
        "clientes": _dashboard_clients_count(
            customers, filtered_sales, filtered_orders, month_key, category, order_state
        ),
        "ventas": len(filtered_sales),
        "total_ventas": _sales_total(filtered_sales),
        "alertas": _dashboard_alerts_count(
            alerts, filtered_sales, filtered_orders, category, month_key, order_state
        ),
    }


def _render_dashboard_charts(sales, orders, products) -> None:
    import altair as alt
    import pandas as pd

    row1_left, row1_right = st.columns(2, gap="large")
    row2_left, row2_right = st.columns(2, gap="large")

    with row1_left:
        with st.container(border=True):
            st.subheader("Ingresos por mes")
            if sales.empty:
                show_alert("Aún no hay ventas registradas.", "info")
            else:
                monthly = sales.copy()
                monthly["subtotal"] = pd.to_numeric(monthly["subtotal"], errors="coerce").fillna(0)
                monthly["mes"] = pd.to_datetime(monthly["fecha"], errors="coerce").dt.to_period("M")
                monthly = (
                    monthly.groupby("mes", as_index=False)["subtotal"]
                    .sum()
                    .assign(
                        mes_key=lambda d: d["mes"].astype(str),
                        mes_label=lambda d: d["mes_key"].map(_format_dashboard_month),
                    )
                )
                chart = (
                    alt.Chart(monthly)
                    .mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10,
                        color=SELV_CHART_ACCENT,
                        stroke=SELV_CHART_STROKE,
                        strokeWidth=0.5,
                    )
                    .encode(
                        x=alt.X(
                            "mes_label:N",
                            title="Mes",
                            sort=alt.EncodingSortField(field="mes_key", order="ascending"),
                            axis=_category_axis("Mes"),
                        ),
                        y=alt.Y("subtotal:Q", title="Ingresos (COP)", axis=alt.Axis(format=",.0f")),
                        tooltip=[
                            alt.Tooltip("mes_label:N", title="Mes"),
                            alt.Tooltip("subtotal:Q", title="Ingresos (COP)", format=",.0f"),
                        ],
                    )
                    .properties(height=DASHBOARD_CHART_HEIGHT)
                )
                st.altair_chart(_apply_altair_theme(chart), use_container_width=True)

    with row1_right:
        with st.container(border=True):
            st.subheader("Pedidos por estado")
            if orders.empty:
                show_alert("Aún no hay pedidos.", "info")
            else:
                status = orders["estado"].value_counts().reset_index()
                status.columns = ["estado", "cantidad"]
                status_count = len(status)
                chart = (
                    alt.Chart(status)
                    .mark_arc(innerRadius=40, outerRadius=70)
                    .encode(
                        theta=alt.Theta("cantidad:Q"),
                        color=alt.Color(
                            "estado:N",
                            scale=alt.Scale(range=SELV_CHART_COLORS),
                            legend=_categorical_legend("Estado", status_count),
                        ),
                        tooltip=[
                            alt.Tooltip("estado:N", title="Estado"),
                            alt.Tooltip("cantidad:Q", title="Pedidos"),
                        ],
                    )
                    .properties(
                        height=DASHBOARD_PIE_HEIGHT + max(0, status_count - 4) * 16,
                    )
                )
                st.altair_chart(
                    _apply_altair_theme(
                        chart,
                        pie=True,
                        pie_padding=_pie_chart_padding(status_count),
                    ),
                    use_container_width=True,
                )

    with row2_left:
        with st.container(border=True):
            st.subheader("Productos más vendidos")
            if sales.empty:
                show_alert("Sin datos de ventas.", "info")
            else:
                top_products = (
                    sales.assign(
                        cantidad=pd.to_numeric(sales["cantidad"], errors="coerce").fillna(0)
                    )
                    .groupby("producto_nombre", as_index=False)["cantidad"]
                    .sum()
                    .sort_values("cantidad", ascending=False)
                    .head(8)
                )
                chart = (
                    alt.Chart(top_products)
                    .mark_bar(
                        cornerRadiusEnd=10,
                        color=SELV_CHART_ACCENT_2,
                        stroke=SELV_CHART_STROKE,
                        strokeWidth=0.5,
                    )
                    .encode(
                        y=alt.Y(
                            "producto_nombre:N",
                            title=None,
                            sort=alt.EncodingSortField(field="cantidad", order="descending"),
                            axis=_series_axis(),
                        ),
                        x=alt.X(
                            "cantidad:Q",
                            title="Unidades vendidas",
                            scale=alt.Scale(nice=True, padding=0.15),
                        ),
                        tooltip=[
                            alt.Tooltip("producto_nombre:N", title="Producto"),
                            alt.Tooltip("cantidad:Q", title="Unidades"),
                        ],
                    )
                    .properties(
                        height=DASHBOARD_CHART_HEIGHT,
                        padding={"right": 18},
                    )
                )
                st.altair_chart(_apply_altair_theme(chart), use_container_width=True)

    with row2_right:
        with st.container(border=True):
            st.subheader("Ventas por categoría")
            enriched = _sales_with_category(sales, products)
            if enriched.empty or enriched["categoria"].isna().all():
                show_alert("Sin ventas por categoría.", "info")
            else:
                by_category = (
                    enriched.assign(
                        subtotal=pd.to_numeric(enriched["subtotal"], errors="coerce").fillna(0)
                    )
                    .groupby("categoria", as_index=False)["subtotal"]
                    .sum()
                    .sort_values("subtotal", ascending=False)
                )
                chart = (
                    alt.Chart(by_category)
                    .mark_bar(
                        cornerRadiusTopLeft=10,
                        cornerRadiusTopRight=10,
                        stroke=SELV_CHART_STROKE,
                        strokeWidth=0.5,
                    )
                    .encode(
                        x=alt.X("categoria:N", title="Categoría", sort="-y", axis=_category_axis("Categoría")),
                        y=alt.Y(
                            "subtotal:Q",
                            title="Ingresos (COP)",
                            axis=alt.Axis(format=",.0f"),
                            scale=alt.Scale(nice=True, padding=0.1),
                        ),
                        color=alt.Color(
                            "categoria:N",
                            scale=alt.Scale(range=SELV_CHART_COLORS),
                            legend=None,
                        ),
                        tooltip=[
                            alt.Tooltip("categoria:N", title="Categoría"),
                            alt.Tooltip("subtotal:Q", title="Ingresos (COP)", format=",.0f"),
                        ],
                    )
                    .properties(height=DASHBOARD_CHART_HEIGHT)
                )
                st.altair_chart(_apply_altair_theme(chart), use_container_width=True)


def _alert_count() -> int:
    try:
        return len(_alerts())
    except Exception:
        return 0


def _register_sales_from_order_preview(order: dict, items: list) -> list:
    _init_preview_sales()
    order_id = str(order.get("id", "")).strip()
    if not order_id:
        return []

    existing = [
        sale
        for sale in st.session_state.preview_sales
        if str(sale.get("pedido_id", "")).strip() == order_id
    ]
    if existing:
        return []

    created = []
    for item in items:
        qty = int(item["cantidad"])
        price = float(item.get("precio_unitario", 0))
        sale = {
            "id": new_id("VTA"),
            "fecha": now_str(),
            "cliente_id": str(order.get("cliente_id", "")),
            "cliente_nombre": str(order.get("cliente_nombre", "")),
            "producto_id": str(item["producto_id"]),
            "producto_nombre": str(item.get("producto_nombre", "")),
            "cantidad": qty,
            "precio_unitario": price,
            "subtotal": price * qty,
            "pedido_id": order_id,
        }
        st.session_state.preview_sales.insert(0, sale)
        created.append(sale)
    return created


def _sales_exist_for_order(order_id: str) -> bool:
    if st.session_state.preview_mode:
        _init_preview_sales()
        order_key = str(order_id).strip()
        return any(
            str(sale.get("pedido_id", "")).strip() == order_key
            for sale in st.session_state.preview_sales
        )
    return sales_exist_for_order(order_id)


def _reverse_sales_from_order_preview(order_id: str) -> None:
    _init_preview_sales()
    order_key = str(order_id).strip()
    remaining = [
        sale
        for sale in st.session_state.preview_sales
        if str(sale.get("pedido_id", "")).strip() != order_key
    ]
    removed = [
        sale
        for sale in st.session_state.preview_sales
        if str(sale.get("pedido_id", "")).strip() == order_key
    ]
    for sale in removed:
        try:
            from services.product_service import adjust_stock

            adjust_stock(str(sale["producto_id"]), int(sale["cantidad"]))
        except Exception:
            pass
    st.session_state.preview_sales = remaining


def _update_order_status(order_id: str, new_status: str) -> bool:
    if new_status not in _order_state_names(active_only=True):
        raise ValueError(f"Estado inválido o inactivo: {new_status}")

    if st.session_state.preview_mode:
        _init_preview_orders()
        for index, order in enumerate(st.session_state.preview_orders):
            if str(order.get("id", "")) != str(order_id):
                continue

            previous_status = str(order.get("estado", ""))
            order["estado"] = new_status
            order["fecha_actualizacion"] = now_str()
            st.session_state.preview_orders[index] = order
            items = _order_items(order_id)

            moving_to_reverse = _order_state_reverses_sale(new_status)
            moving_from_reverse = _order_state_reverses_sale(previous_status)

            if moving_to_reverse:
                if _sales_exist_for_order(order_id):
                    _reverse_sales_from_order_preview(order_id)
                elif not moving_from_reverse:
                    try:
                        release_stock_for_items(items)
                    except Exception:
                        pass

            if (
                moving_from_reverse
                and not moving_to_reverse
                and not _sales_exist_for_order(order_id)
            ):
                try:
                    reserve_stock_for_items(items)
                except Exception:
                    pass

            if _order_state_generates_sale(new_status) and not _sales_exist_for_order(order_id):
                _register_sales_from_order_preview(order, items)
            return True
        return False

    return update_order_status(order_id, new_status)


def _filter_sales(
    sales,
    *,
    cliente_id: str | None = None,
    producto_id: str | None = None,
    pedido_id: str = "",
    date_from=None,
    date_to=None,
    use_date_range: bool = False,
):
    import pandas as pd

    if sales.empty:
        return sales

    filtered = sales.copy()

    if cliente_id:
        filtered = filtered[filtered["cliente_id"].astype(str) == str(cliente_id)]

    if producto_id:
        filtered = filtered[filtered["producto_id"].astype(str) == str(producto_id)]

    pedido_filter = pedido_id.strip()
    if pedido_filter:
        filtered = filtered[
            filtered["pedido_id"].astype(str).str.contains(pedido_filter, case=False, na=False)
        ]

    if use_date_range and date_from is not None and date_to is not None:
        filtered = filtered.assign(
            fecha_dt=pd.to_datetime(filtered["fecha"], errors="coerce")
        )
        filtered = filtered[
            (filtered["fecha_dt"].dt.date >= date_from)
            & (filtered["fecha_dt"].dt.date <= date_to)
        ]
        filtered = filtered.drop(columns=["fecha_dt"])

    if "fecha" in filtered.columns:
        filtered = filtered.sort_values("fecha", ascending=False)
    return filtered


def _order_items(order_id: str):
    if st.session_state.preview_mode:
        orders = _orders()
        match = orders[orders["id"] == order_id]
        if match.empty:
            return []
        try:
            return json.loads(str(match.iloc[0]["items_json"]))
        except json.JSONDecodeError:
            return []
    return get_order_items(order_id)


def _init_order_draft() -> None:
    if "order_draft_items" not in st.session_state:
        st.session_state.order_draft_items = []


def _clear_order_draft() -> None:
    st.session_state.order_draft_items = []


def _product_order_option_label(row) -> str:
    parts = [str(row["id"]), str(row["nombre"])]
    categoria = str(row.get("categoria", "")).strip()
    if categoria:
        parts.append(categoria)
    descripcion = str(row.get("descripcion", "")).strip()
    if descripcion:
        parts.append(descripcion)
    stock_raw = row.get("stock", 0)
    try:
        stock = int(float(stock_raw))
    except (TypeError, ValueError):
        stock = 0
    return f"{' | '.join(parts)} | {format_cop(row['precio'])} (stock: {stock})"


def _compose_order_notes(direccion: str, notas: str) -> str:
    parts: list[str] = []
    if direccion.strip():
        parts.append(f"Dirección de entrega: {direccion.strip()}")
    if notas.strip():
        parts.append(notas.strip())
    return "\n".join(parts)


def _order_draft_quantity(producto_id: str) -> int:
    return sum(
        int(item["cantidad"])
        for item in st.session_state.order_draft_items
        if str(item["producto_id"]) == str(producto_id)
    )


def _add_order_draft_item(producto_id: str, producto_nombre: str, cantidad: int) -> None:
    for item in st.session_state.order_draft_items:
        if str(item["producto_id"]) == str(producto_id):
            item["cantidad"] = int(item["cantidad"]) + cantidad
            return
    st.session_state.order_draft_items.append(
        {
            "producto_id": producto_id,
            "producto_nombre": producto_nombre,
            "cantidad": cantidad,
        }
    )


def _render_order_draft_table(products) -> float:
    import pandas as pd

    if not st.session_state.order_draft_items:
        show_alert("Agrega uno o más productos al pedido.", "info")
        return 0.0

    rows = []
    total = 0.0
    for index, item in enumerate(st.session_state.order_draft_items):
        match = products[products["id"].astype(str) == str(item["producto_id"])]
        price = float(match.iloc[0]["precio"]) if not match.empty else 0.0
        qty = int(item["cantidad"])
        subtotal = price * qty
        total += subtotal
        rows.append(
            {
                "#": index + 1,
                "Producto": item["producto_nombre"],
                "Cantidad": qty,
                "Precio unitario": format_cop(price),
                "Subtotal": format_cop(subtotal),
            }
        )

    st.markdown('<div style="margin-top: 1rem;"></div>', unsafe_allow_html=True)
    render_table(rows, key="order_draft_table", paginate=False)
    st.markdown('<div style="margin-top: 1.25rem;"></div>', unsafe_allow_html=True)
    st.metric("Total del pedido", format_cop(total))
    return total


def _render_new_order_tab(customers, products) -> None:
    import pandas as pd

    _init_order_draft()

    customer_options = {
        f"{row['nombre']} ({row['id']})": (row["id"], row["nombre"])
        for _, row in customers.iterrows()
    }
    product_options = {
        _product_order_option_label(row): (row["id"], row["nombre"])
        for _, row in products.iterrows()
    }

    customer_label = st.selectbox("Cliente", list(customer_options.keys()), key="order_draft_customer")
    direccion = st.text_input("Dirección de entrega", key="order_draft_address")
    notas = st.text_area("Notas", key="order_draft_notes")

    st.subheader("Productos del pedido")
    col_product, col_qty, col_add = st.columns([3, 1, 1])
    with col_product:
        product_label = st.selectbox("Producto", list(product_options.keys()), key="order_draft_product")
    with col_qty:
        cantidad = st.number_input("Cantidad", min_value=1, step=1, key="order_draft_qty")
    with col_add:
        st.markdown('<div style="margin-top: 1.75rem;"></div>', unsafe_allow_html=True)
        if st.button("Agregar", key="order_draft_add", use_container_width=True):
            producto_id, producto_nombre = product_options[product_label]
            match = products[products["id"].astype(str) == str(producto_id)]
            if match.empty:
                show_alert("Producto no encontrado.", "error")
            else:
                stock = int(pd.to_numeric(match.iloc[0].get("stock", 0), errors="coerce") or 0)
                draft_qty = _order_draft_quantity(producto_id)
                if draft_qty + cantidad > stock:
                    show_alert(
                        f"Stock insuficiente para {producto_nombre}. "
                        f"Disponible: {stock}, en el pedido: {draft_qty + cantidad}.",
                        "warning",
                    )
                else:
                    _add_order_draft_item(producto_id, producto_nombre, cantidad)
                    st.rerun()

    st.markdown('<div style="margin-top: 0.75rem;"></div>', unsafe_allow_html=True)
    _render_order_draft_table(products)

    if st.session_state.order_draft_items:
        remove_labels = {
            f"{item['producto_nombre']} (x{item['cantidad']})": index
            for index, item in enumerate(st.session_state.order_draft_items)
        }
        col_remove, col_spacer = st.columns([2, 3])
        with col_remove:
            remove_label = st.selectbox(
                "Quitar producto",
                ["—"] + list(remove_labels.keys()),
                key="order_draft_remove_select",
            )
            if st.button("Quitar del pedido", key="order_draft_remove_btn"):
                if remove_label != "—":
                    st.session_state.order_draft_items.pop(remove_labels[remove_label])
                    st.rerun()

    if st.button("Crear pedido", type="primary", key="order_draft_submit"):
        if not _preview_guard("crear pedidos"):
            return
        if not st.session_state.order_draft_items:
            show_alert("Agrega al menos un producto al pedido.", "error")
            return

        cliente_id, cliente_nombre = customer_options[customer_label]
        items = [
            {"producto_id": item["producto_id"], "cantidad": int(item["cantidad"])}
            for item in st.session_state.order_draft_items
        ]
        try:
            order = create_order(
                cliente_id,
                cliente_nombre,
                items,
                notas=_compose_order_notes(direccion, notas),
            )
            _clear_order_draft()
            queue_action_message(
                f"Pedido creado correctamente: {order['id']} — {len(items)} producto(s), "
                f"total {format_cop(order['total'])}",
            )
            st.rerun()
        except Exception as exc:
            show_alert(str(exc), "error")


def _preview_guard(action: str) -> bool:
    if st.session_state.preview_mode:
        show_alert(
            f"Modo vista previa: no se puede {action}. Configura la base de datos para guardar.",
            "info",
        )
        return False
    return True


def _validate_product_fields(nombre: str, categoria: str) -> str | None:
    if not nombre.strip():
        return "El nombre es obligatorio."
    if not str(categoria).strip():
        return "La categoría es obligatoria."
    return None


def build_nav_menu(alerts: int) -> dict[str, str]:
    return {
        "Dashboard": "dashboard",
        "Productos": "productos",
        "Clientes": "clientes",
        "Ventas": "ventas",
        "Contabilidad": "contabilidad",
        "Pedidos": "pedidos",
        f"Alertas de stock ({alerts})": "alertas",
        "Administración": "administracion",
    }


def sidebar() -> str:
    render_sidebar_branding()

    menu = build_nav_menu(_alert_count())
    page = render_sidebar_nav(menu)
    st.sidebar.divider()
    db_label = "Vista previa" if st.session_state.preview_mode else {
        "supabase": "Supabase",
        "sheets": "Google Sheets",
    }.get(resolves_data_backend() or "", "Conectado")
    st.sidebar.markdown(
        f'<div class="selv-sidebar-footer"><strong>Base de datos:</strong> {db_label}</div>',
        unsafe_allow_html=True,
    )
    return page


def _sales_total(sales) -> float:
    import pandas as pd

    if sales.empty:
        return 0.0
    return float(pd.to_numeric(sales["subtotal"], errors="coerce").fillna(0).sum())


def page_dashboard() -> None:
    render_page_header(
        "Dashboard",
        "Resumen general del inventario y operaciones de productos",
        "dashboard",
    )

    products = _products()
    customers = _customers()
    sales = _sales()
    orders = _orders()
    alerts = _alerts()

    filtered_sales, filtered_orders, month_key, category, order_state = (
        _render_dashboard_filters(sales, orders, products)
    )
    metrics = _compute_dashboard_metrics(
        products,
        customers,
        alerts,
        filtered_sales,
        filtered_orders,
        month_key,
        category,
        order_state,
    )

    st.markdown(
        '<div class="selv-dashboard-kpis-marker" aria-hidden="true"></div>',
        unsafe_allow_html=True,
    )
    st.columns(1)[0].metric("Total en ventas", format_cop(metrics["total_ventas"]))
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Productos", metrics["productos"])
    c2.metric("Clientes", metrics["clientes"])
    c3.metric("Ventas registradas", metrics["ventas"])
    c4.metric("Alertas de stock", metrics["alertas"])

    _render_dashboard_charts(filtered_sales, filtered_orders, products)


def page_products() -> None:
    render_page_header(
        "Productos",
        "Registra y administra tu inventario de productos",
        "productos",
    )

    tab = section_tabs(["Inventario", "Nuevo producto", "Editar producto"], "products_tabs")

    if tab == "Inventario":
        products = _products()
        if products.empty:
            show_alert("No hay productos registrados.", "info")
        else:
            render_table(products, key="products_table")

    elif tab == "Nuevo producto":
        with st.form("new_product_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre *", placeholder="Ej: Collar con perlas")
            categoria = c2.selectbox(
                "Categoría *",
                _product_category_names(active_only=True),
                index=0,
            )
            descripcion = st.text_area(
                "Descripción",
                placeholder="Material, color, medidas, detalles...",
            )
            c3, c4, c5 = st.columns(3)
            precio = c3.number_input(
                "Precio (COP) *",
                min_value=0.0,
                step=500.0,
                format="%.0f",
            )
            stock = c4.number_input("Stock inicial *", min_value=0, step=1)
            stock_minimo = c5.number_input("Stock mínimo (alerta) *", min_value=0, step=1)

            if st.form_submit_button("Guardar producto", type="primary"):
                if not _preview_guard("guardar productos"):
                    pass
                elif error := _validate_product_fields(nombre, categoria):
                    show_alert(error, "error")
                else:
                    product = create_product(
                        nombre, descripcion, categoria, precio, stock, stock_minimo
                    )
                    queue_action_message(
                        f"Producto creado correctamente: {product['nombre']} ({product['id']})",
                    )
                    st.rerun()

    elif tab == "Editar producto":
        products = _products()
        if products.empty:
            show_alert("Primero registra productos.", "info")
        else:
            product_options = {
                f"{row['nombre']} ({row['id']})": row["id"]
                for _, row in products.iterrows()
            }
            selected = st.selectbox("Selecciona producto", list(product_options.keys()))
            product_id = product_options[selected]
            current = products[products["id"] == product_id].iloc[0]

            current_category = str(current.get("categoria", ""))
            category_options = _product_category_names(active_only=False)
            if current_category and current_category not in category_options:
                category_options = [current_category] + category_options

            with st.form("edit_product_form"):
                c1, c2 = st.columns(2)
                nombre = c1.text_input("Nombre *", value=str(current["nombre"]))
                categoria = c2.selectbox(
                    "Categoría *",
                    category_options,
                    index=category_options.index(current_category)
                    if current_category in category_options
                    else 0,
                )
                descripcion = st.text_area(
                    "Descripción", value=str(current.get("descripcion", ""))
                )
                c3, c4, c5, c6 = st.columns(4)
                precio = c3.number_input(
                    "Precio (COP) *",
                    min_value=0.0,
                    step=500.0,
                    format="%.0f",
                    value=float(current.get("precio", 0)),
                )
                stock = c4.number_input("Stock *", value=int(current.get("stock", 0)))
                stock_minimo = c5.number_input(
                    "Stock mínimo *", value=int(current.get("stock_minimo", 0))
                )
                current_activo = str(current.get("activo", "Si")).strip().lower()
                activo = c6.selectbox(
                    "Activo *",
                    ["Si", "No"],
                    index=0
                    if current_activo in ("si", "sí", "yes", "true", "1")
                    else 1,
                )

                if st.form_submit_button("Actualizar", type="primary"):
                    if not _preview_guard("editar productos"):
                        pass
                    elif error := _validate_product_fields(nombre, categoria):
                        show_alert(error, "error")
                    else:
                        update_product(
                            product_id,
                            {
                                "nombre": nombre,
                                "descripcion": descripcion,
                                "categoria": categoria,
                                "precio": precio,
                                "stock": stock,
                                "stock_minimo": stock_minimo,
                                "activo": activo,
                            },
                        )
                        queue_action_message("Producto actualizado correctamente.")
                        st.rerun()


def page_customers() -> None:
    render_page_header(
        "Clientes",
        "Gestiona tu cartera de clientes",
        "clientes",
    )

    tab = section_tabs(["Listado", "Nuevo cliente", "Editar cliente"], "customers_tabs")

    if tab == "Listado":
        customers = _customers()
        if customers.empty:
            show_alert("No hay clientes registrados.", "info")
        else:
            render_table(customers, key="customers_table")

    elif tab == "Nuevo cliente":
        with st.form("new_customer_form", clear_on_submit=True):
            nombre = st.text_input("Nombre *")
            c1, c2 = st.columns(2)
            email = c1.text_input("Email")
            telefono = c2.text_input("Teléfono")
            direccion = st.text_input("Dirección")
            notas = st.text_area("Notas")

            if st.form_submit_button("Guardar cliente", type="primary"):
                if not _preview_guard("guardar clientes"):
                    pass
                elif not nombre.strip():
                    show_alert("El nombre es obligatorio.", "error")
                else:
                    customer = create_customer(nombre, email, telefono, direccion, notas)
                    queue_action_message(
                        f"Cliente creado correctamente: {customer['nombre']} ({customer['id']})",
                    )
                    st.rerun()

    elif tab == "Editar cliente":
        customers = _customers()
        if customers.empty:
            show_alert("Primero registra clientes.", "info")
        else:
            options = {
                f"{row['nombre']} ({row['id']})": row["id"] for _, row in customers.iterrows()
            }
            selected = st.selectbox("Selecciona cliente", list(options.keys()))
            customer_id = options[selected]
            current = customers[customers["id"] == customer_id].iloc[0]

            with st.form("edit_customer_form"):
                nombre = st.text_input("Nombre *", value=str(current["nombre"]))
                c1, c2 = st.columns(2)
                email = c1.text_input("Email", value=str(current.get("email", "")))
                telefono = c2.text_input("Teléfono", value=str(current.get("telefono", "")))
                direccion = st.text_input("Dirección", value=str(current.get("direccion", "")))
                notas = st.text_area("Notas", value=str(current.get("notas", "")))

                if st.form_submit_button("Actualizar", type="primary"):
                    if not _preview_guard("editar clientes"):
                        pass
                    elif not nombre.strip():
                        show_alert("El nombre es obligatorio.", "error")
                    else:
                        update_customer(
                            customer_id,
                            {
                                "nombre": nombre,
                                "email": email,
                                "telefono": telefono,
                                "direccion": direccion,
                                "notas": notas,
                            },
                        )
                        queue_action_message("Cliente actualizado correctamente.")
                        st.rerun()


def page_sales() -> None:
    from datetime import date

    render_page_header(
        "Ventas",
        "Historial generado automáticamente al entregar pedidos",
        "ventas",
    )
    st.caption(
        "Las ventas se crean al marcar un pedido como Entregado. "
        "No se pueden crear ni editar manualmente."
    )

    sales = _sales()
    customers = _customers()
    products = _products()

    today = date.today()
    default_from = today.replace(day=1)

    with st.expander("Filtros", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            client_options = {"Todos": None}
            if not customers.empty:
                client_options.update(
                    {
                        f"{row['nombre']} ({row['id']})": row["id"]
                        for _, row in customers.iterrows()
                    }
                )
            client_label = st.selectbox("Cliente", list(client_options.keys()), key="sales_filter_client")
            cliente_id = client_options[client_label]
        with c2:
            product_options = {"Todos": None}
            if not products.empty:
                product_options.update(
                    {
                        f"{row['nombre']} ({row['id']})": row["id"]
                        for _, row in products.iterrows()
                    }
                )
            product_label = st.selectbox("Producto", list(product_options.keys()), key="sales_filter_product")
            producto_id = product_options[product_label]
        with c3:
            pedido_id_filter = st.text_input("ID de pedido", key="sales_filter_pedido")

        fc1, fc2 = st.columns(2)
        with fc1:
            date_from = st.date_input("Desde", value=default_from, key="sales_date_from")
        with fc2:
            date_to = st.date_input("Hasta", value=today, key="sales_date_to")

        use_date_range = st.checkbox(
            "Filtrar por rango de fechas",
            value=False,
            key="sales_use_date_range",
        )

    filtered = _filter_sales(
        sales,
        cliente_id=cliente_id,
        producto_id=producto_id,
        pedido_id=pedido_id_filter,
        date_from=date_from,
        date_to=date_to,
        use_date_range=use_date_range,
    )

    if filtered.empty:
        show_alert("No hay ventas que coincidan con los filtros.", "info")
    else:
        display = filtered.drop(columns=["fecha_dt"], errors="ignore")
        render_table(display, key="sales_table")


def page_orders() -> None:
    render_page_header(
        "Pedidos",
        "Crea pedidos y actualiza su estado",
        "pedidos",
    )
    st.caption(
        "Al crear un pedido se reserva stock. La venta en dinero se registra "
        "al pasar a un estado con «Genera venta efectiva»."
    )

    tab = section_tabs(["Listado", "Nuevo pedido", "Actualizar estado"], "orders_tabs")

    if tab == "Listado":
        orders = _orders()
        if orders.empty:
            show_alert("No hay pedidos registrados.", "info")
        else:
            display = orders.drop(columns=["items_json"], errors="ignore")
            render_table(display, key="orders_table")

    elif tab == "Nuevo pedido":
        customers = _customers()
        products = _products(active_only=True)

        if customers.empty or products.empty:
            show_alert("Necesitas clientes y productos para crear pedidos.", "warning")
        else:
            _render_new_order_tab(customers, products)

    elif tab == "Actualizar estado":
        orders = _orders()
        if orders.empty:
            show_alert("No hay pedidos para actualizar.", "info")
        else:
            options = {
                f"{row['id']} | {row['cliente_nombre']} | {row['estado']}": row["id"]
                for _, row in orders.iterrows()
            }
            selected = st.selectbox("Selecciona pedido", list(options.keys()))
            order_id = options[selected]
            items = _order_items(order_id)

            if items:
                render_table(
                    [
                        {
                            "Producto": i["producto_nombre"],
                            "Cantidad": i["cantidad"],
                            "Subtotal": i["subtotal"],
                        }
                        for i in items
                    ],
                    key="order_items_table",
                    paginate=False,
                )

            new_status = st.selectbox("Nuevo estado", _order_state_names(active_only=True))
            if st.button("Actualizar estado", type="primary"):
                try:
                    if _update_order_status(order_id, new_status):
                        queue_action_message(
                            f"Pedido actualizado correctamente: {order_id} → {new_status}",
                        )
                        st.rerun()
                    else:
                        show_alert("No se encontró el pedido.", "error")
                except Exception as exc:
                    show_alert(str(exc), "error")


def page_alerts() -> None:
    render_page_header(
        "Alertas de stock",
        "Productos que requieren reposición",
        "alertas",
    )

    alerts = _alerts()
    if alerts.empty:
        show_alert("Todo en orden. No hay productos con stock bajo.", "success")
    else:
        show_alert(f"{len(alerts)} producto(s) por debajo del stock mínimo.", "warning")
        render_table(
            alerts[
                ["id", "nombre", "categoria", "stock", "stock_minimo", "faltante", "precio"]
            ],
            key="alerts_table",
        )


def _render_catalog_list_table(df, *, key: str) -> None:
    if df.empty:
        show_alert("No hay registros en este catálogo.", "info")
        return
    display = df.copy()
    display = display.drop(columns=["orden", "fecha_registro"], errors="ignore")
    if "genera_venta" in display.columns:
        display["genera_venta"] = display["genera_venta"].map(
            lambda v: "Sí" if _catalog_is_active(v) else "No"
        )
    if "revierte_venta" in display.columns:
        display["revierte_venta"] = display["revierte_venta"].map(
            lambda v: "Sí" if _catalog_is_active(v) else "No"
        )
    render_table(display, key=key, paginate=False)


def _render_simple_catalog_admin(
    *,
    title: str,
    list_df_fn,
    create_fn,
    update_fn,
    delete_fn,
    preview_key: str,
    table_key: str,
) -> None:
    st.caption(
        f"Gestiona {title.lower()}. Los registros inactivos no aparecen al crear o editar "
        "productos, ingresos o gastos."
    )

    tab = section_tabs(["Listado", "Nuevo", "Editar", "Eliminar"], f"admin_{preview_key}_tabs")

    if tab == "Listado":
        _render_catalog_list_table(list_df_fn(), key=table_key)

    elif tab == "Nuevo":
        with st.form(f"admin_new_{preview_key}"):
            nombre = st.text_input("Nombre *")
            if st.form_submit_button("Crear", type="primary"):
                if not _preview_guard(f"crear {title.lower()}"):
                    pass
                elif not nombre.strip():
                    show_alert("El nombre es obligatorio.", "error")
                else:
                    try:
                        if st.session_state.preview_mode:
                            _init_preview_catalogs()
                            items = st.session_state.preview_catalogs[preview_key]
                            if any(
                                str(item["nombre"]).strip().lower() == nombre.strip().lower()
                                for item in items
                            ):
                                raise ValueError(f"Ya existe «{nombre.strip()}».")
                            items.append(
                                {
                                    "id": new_id("CAT"),
                                    "nombre": nombre.strip(),
                                    "activo": "Si",
                                    "orden": len(items) + 1,
                                    "fecha_registro": now_str(),
                                }
                            )
                        else:
                            create_fn(nombre.strip())
                        queue_action_message(
                            f"Registro creado correctamente: «{nombre.strip()}»",
                        )
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")

    elif tab == "Editar":
        df = list_df_fn()
        if df.empty:
            show_alert("No hay registros para editar.", "info")
        else:
            options = {
                f"{row['nombre']} ({row['id']})": row["id"] for _, row in df.iterrows()
            }
            selected = st.selectbox(
                "Selecciona registro",
                list(options.keys()),
                key=f"admin_{preview_key}_edit_select",
            )
            item_id = options[selected]
            current = df[df["id"].astype(str) == str(item_id)].iloc[0]

            with st.form(f"admin_edit_{preview_key}"):
                nombre = st.text_input("Nombre", value=str(current["nombre"]))
                activo = st.selectbox(
                    "Activo",
                    ["Si", "No"],
                    index=0 if _catalog_is_active(current.get("activo", "Si")) else 1,
                )
                if st.form_submit_button("Actualizar", type="primary"):
                    if not _preview_guard(f"editar {title.lower()}"):
                        pass
                    else:
                        try:
                            updates = {
                                "nombre": nombre,
                                "activo": activo,
                            }
                            if st.session_state.preview_mode:
                                _init_preview_catalogs()
                                for item in st.session_state.preview_catalogs[preview_key]:
                                    if str(item["id"]) == str(item_id):
                                        item.update(updates)
                                        break
                            else:
                                update_fn(item_id, updates)
                            queue_action_message(
                                f"Registro actualizado correctamente: «{nombre.strip()}»",
                            )
                            st.rerun()
                        except Exception as exc:
                            show_alert(str(exc), "error")

    elif tab == "Eliminar":
        df = list_df_fn()
        if df.empty:
            show_alert("No hay registros para eliminar.", "info")
        else:
            options = {
                f"{row['nombre']} ({row['id']})": row["id"] for _, row in df.iterrows()
            }
            selected = st.selectbox(
                "Selecciona registro",
                list(options.keys()),
                key=f"admin_{preview_key}_delete_select",
            )
            item_id = options[selected]
            if st.button(
                "Eliminar permanentemente",
                type="primary",
                key=f"admin_{preview_key}_delete_btn",
            ):
                if not _preview_guard(f"eliminar {title.lower()}"):
                    pass
                else:
                    try:
                        if st.session_state.preview_mode:
                            _init_preview_catalogs()
                            st.session_state.preview_catalogs[preview_key] = [
                                item
                                for item in st.session_state.preview_catalogs[preview_key]
                                if str(item["id"]) != str(item_id)
                            ]
                        else:
                            delete_fn(item_id)
                        queue_action_message("Registro eliminado correctamente.")
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")


def _render_order_states_admin() -> None:
    st.caption(
        "Configura el flujo de pedidos. Al crear un pedido se reserva stock. "
        "Marca «Genera venta» en los estados que registran la venta en dinero "
        "(sin descontar stock otra vez). Marca «Revierte venta» en los estados que anulan "
        "una venta ya registrada y devuelven el stock; si no hubo venta, liberan la reserva."
    )

    tab = section_tabs(
        ["Listado", "Nuevo", "Editar", "Eliminar"],
        "admin_order_states_tabs",
    )

    if tab == "Listado":
        _render_catalog_list_table(_order_states_df(), key="admin_order_states_table")

    elif tab == "Nuevo":
        with st.form("admin_new_order_state"):
            nombre = st.text_input("Nombre del estado *")
            c1, c2 = st.columns(2)
            genera_venta = c1.checkbox("Genera venta efectiva", value=False)
            revierte_venta = c2.checkbox("Revierte venta si ya se registró", value=False)
            if st.form_submit_button("Crear estado", type="primary"):
                if not _preview_guard("crear estados de pedido"):
                    pass
                elif not nombre.strip():
                    show_alert("El nombre es obligatorio.", "error")
                else:
                    try:
                        if st.session_state.preview_mode:
                            _init_preview_catalogs()
                            items = st.session_state.preview_catalogs["estados_pedido"]
                            items.append(
                                {
                                    "id": new_id("EST"),
                                    "nombre": nombre.strip(),
                                    "activo": "Si",
                                    "orden": len(items) + 1,
                                    "genera_venta": "Si" if genera_venta else "No",
                                    "revierte_venta": "Si" if revierte_venta else "No",
                                    "fecha_registro": now_str(),
                                }
                            )
                        else:
                            create_order_state(
                                nombre.strip(),
                                genera_venta=genera_venta,
                                revierte_venta=revierte_venta,
                            )
                        queue_action_message(
                            f"Estado creado correctamente: «{nombre.strip()}»",
                        )
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")

    elif tab == "Editar":
        df = _order_states_df()
        if df.empty:
            show_alert("No hay estados para editar.", "info")
        else:
            options = {
                f"{row['nombre']} ({row['id']})": row["id"] for _, row in df.iterrows()
            }
            selected = st.selectbox(
                "Selecciona estado",
                list(options.keys()),
                key="admin_order_state_edit_select",
            )
            item_id = options[selected]
            current = df[df["id"].astype(str) == str(item_id)].iloc[0]

            with st.form("admin_edit_order_state"):
                nombre = st.text_input("Nombre", value=str(current["nombre"]))
                activo = st.selectbox(
                    "Activo",
                    ["Si", "No"],
                    index=0 if _catalog_is_active(current.get("activo", "Si")) else 1,
                )
                c1, c2 = st.columns(2)
                genera_venta = c1.checkbox(
                    "Genera venta efectiva",
                    value=_catalog_is_active(current.get("genera_venta", "No")),
                )
                revierte_venta = c2.checkbox(
                    "Revierte venta si ya se registró",
                    value=_catalog_is_active(current.get("revierte_venta", "No")),
                )
                if st.form_submit_button("Actualizar estado", type="primary"):
                    if not _preview_guard("editar estados de pedido"):
                        pass
                    else:
                        try:
                            updates = {
                                "nombre": nombre,
                                "activo": activo,
                                "genera_venta": "Si" if genera_venta else "No",
                                "revierte_venta": "Si" if revierte_venta else "No",
                            }
                            if st.session_state.preview_mode:
                                _init_preview_catalogs()
                                for item in st.session_state.preview_catalogs["estados_pedido"]:
                                    if str(item["id"]) == str(item_id):
                                        item.update(updates)
                                        break
                            else:
                                update_order_state(item_id, updates)
                            queue_action_message(
                                f"Estado actualizado correctamente: «{nombre.strip()}»",
                            )
                            st.rerun()
                        except Exception as exc:
                            show_alert(str(exc), "error")

    elif tab == "Eliminar":
        df = _order_states_df()
        if df.empty:
            show_alert("No hay estados para eliminar.", "info")
        else:
            options = {
                f"{row['nombre']} ({row['id']})": row["id"] for _, row in df.iterrows()
            }
            selected = st.selectbox(
                "Selecciona estado",
                list(options.keys()),
                key="admin_order_state_delete_select",
            )
            item_id = options[selected]
            if st.button("Eliminar estado", type="primary", key="admin_order_state_delete_btn"):
                if not _preview_guard("eliminar estados de pedido"):
                    pass
                else:
                    try:
                        if st.session_state.preview_mode:
                            _init_preview_catalogs()
                            active = [
                                item
                                for item in st.session_state.preview_catalogs["estados_pedido"]
                                if _catalog_is_active(item.get("activo", "Si"))
                            ]
                            if len(active) <= 1:
                                raise ValueError("Debe quedar al menos un estado activo.")
                            st.session_state.preview_catalogs["estados_pedido"] = [
                                item
                                for item in st.session_state.preview_catalogs["estados_pedido"]
                                if str(item["id"]) != str(item_id)
                            ]
                        else:
                            delete_order_state(item_id)
                        queue_action_message("Estado eliminado correctamente.")
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")


def page_administration() -> None:
    render_page_header(
        "Administración",
        "Catálogos del sistema: categorías, tipos de movimiento y estados de pedido",
        "administracion",
    )

    section = section_tabs(
        [
            "Categorías de producto",
            "Tipos de ingreso",
            "Tipos de gasto",
            "Estados de pedido",
        ],
        "admin_main_tabs",
    )

    if section == "Categorías de producto":
        _render_simple_catalog_admin(
            title="Categorías de producto",
            list_df_fn=_product_categories_df,
            create_fn=create_product_category,
            update_fn=update_product_category,
            delete_fn=delete_product_category,
            preview_key="categorias",
            table_key="admin_product_categories_table",
        )
    elif section == "Tipos de ingreso":
        _render_simple_catalog_admin(
            title="Tipos de ingreso",
            list_df_fn=_income_types_df,
            create_fn=create_income_type,
            update_fn=update_income_type,
            delete_fn=delete_income_type,
            preview_key="tipos_ingreso",
            table_key="admin_income_types_table",
        )
    elif section == "Tipos de gasto":
        _render_simple_catalog_admin(
            title="Tipos de gasto",
            list_df_fn=_expense_types_df,
            create_fn=create_expense_type,
            update_fn=update_expense_type,
            delete_fn=delete_expense_type,
            preview_key="tipos_gasto",
            table_key="admin_expense_types_table",
        )
    elif section == "Estados de pedido":
        _render_order_states_admin()


def page_contabilidad() -> None:
    render_page_header(
        "Contabilidad",
        "Capital, inversiones y gastos del negocio (aparte de las ventas)",
        "contabilidad",
    )

    tab = section_tabs(
        ["Resumen", "Nuevo ingreso", "Nuevo gasto", "Editar movimiento", "Movimientos"],
        "contabilidad_tabs",
    )
    movements = _finance_movements()

    if tab == "Resumen":
        if movements.empty:
            show_alert("Aún no hay movimientos registrados.", "info")
        else:
            filtered = _finance_filter_controls(
                movements,
                optional=True,
                key_prefix="contabilidad_resumen",
            )

            if filtered.empty:
                show_alert("No hay movimientos con los filtros seleccionados.", "info")
            else:
                _render_finance_metrics(filtered)

                st.subheader("Por categoría")
                summary = (
                    filtered.groupby(["tipo", "categoria"], as_index=False)["monto"]
                    .sum()
                    .sort_values(["tipo", "monto"], ascending=[True, False])
                )
                summary.columns = ["Tipo", "Categoría", "Monto"]
                render_table(summary, key="finance_summary_table", paginate=False)

                st.markdown('<div style="margin-top: 1.5rem;"></div>', unsafe_allow_html=True)
                _render_finance_charts(filtered)

        st.caption(
            "Las ventas de productos se registran en la sección Ventas. "
            "Aquí llevas capital, inversiones y gastos operativos."
        )

    elif tab == "Nuevo ingreso":
        from datetime import date

        with st.form("new_income_form", clear_on_submit=True):
            fecha = st.date_input("Fecha del movimiento *", value=date.today())
            categoria = st.selectbox("Tipo de ingreso *", _income_type_names(active_only=True))
            concepto = st.text_input(
                "Concepto *",
                placeholder="Ej: Aporte de socios, reinversión, préstamo...",
            )
            monto = st.number_input("Monto (COP) *", min_value=0.0, step=10000.0, format="%.0f")
            notas = st.text_area("Notas", placeholder="Detalles adicionales (opcional)")

            if st.form_submit_button("Registrar ingreso", type="primary"):
                if not _preview_guard("registrar ingresos"):
                    pass
                elif not concepto.strip():
                    show_alert("El concepto es obligatorio.", "error")
                elif monto <= 0:
                    show_alert("El monto debe ser mayor a cero.", "error")
                else:
                    try:
                        record = _register_finance_movement(
                            "Ingreso",
                            categoria,
                            concepto,
                            monto,
                            notas,
                            fecha=fecha,
                        )
                        queue_action_message(
                            f"Ingreso registrado correctamente: {record['concepto']} — "
                            f"{format_cop(record['monto'])}",
                        )
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")

    elif tab == "Nuevo gasto":
        from datetime import date

        with st.form("new_expense_form", clear_on_submit=True):
            fecha = st.date_input("Fecha del movimiento *", value=date.today())
            categoria = st.selectbox("Tipo de gasto *", _expense_type_names(active_only=True))
            concepto = st.text_input(
                "Concepto *",
                placeholder="Ej: Compra de insumos, equipo nuevo, pago extra...",
            )
            monto = st.number_input("Monto (COP) *", min_value=0.0, step=10000.0, format="%.0f")
            notas = st.text_area("Notas", placeholder="Detalles adicionales (opcional)")

            if st.form_submit_button("Registrar gasto", type="primary"):
                if not _preview_guard("registrar gastos"):
                    pass
                elif not concepto.strip():
                    show_alert("El concepto es obligatorio.", "error")
                elif monto <= 0:
                    show_alert("El monto debe ser mayor a cero.", "error")
                else:
                    try:
                        record = _register_finance_movement(
                            "Gasto",
                            categoria,
                            concepto,
                            monto,
                            notas,
                            fecha=fecha,
                        )
                        queue_action_message(
                            f"Gasto registrado correctamente: {record['concepto']} — "
                            f"{format_cop(record['monto'])}",
                        )
                        st.rerun()
                    except Exception as exc:
                        show_alert(str(exc), "error")

    elif tab == "Editar movimiento":
        if movements.empty:
            show_alert("No hay movimientos para editar.", "info")
        else:
            normalized = _normalize_finance_movements(movements)
            movement_options = {
                _movement_option_label(row): row["id"]
                for _, row in normalized.iterrows()
            }
            selected = st.selectbox("Selecciona movimiento", list(movement_options.keys()))
            movement_id = movement_options[selected]
            current = normalized[normalized["id"].astype(str) == str(movement_id)].iloc[0]
            current_tipo = str(current.get("tipo", "Ingreso"))
            current_category = str(current.get("categoria", ""))

            tipo = st.selectbox(
                "Tipo de movimiento *",
                ["Ingreso", "Gasto"],
                index=0 if current_tipo == "Ingreso" else 1,
                key=f"edit_finance_tipo_{movement_id}",
            )
            edit_categories = (
                _income_type_names(active_only=False)
                if tipo == "Ingreso"
                else _expense_type_names(active_only=False)
            )
            if current_category and current_category not in edit_categories:
                edit_categories = [current_category] + edit_categories

            with st.form("edit_finance_form"):
                fecha = st.date_input(
                    "Fecha del movimiento *",
                    value=_movement_form_date(current.get("fecha")),
                )
                categoria = st.selectbox(
                    "Categoría *",
                    edit_categories,
                    index=edit_categories.index(current_category)
                    if current_category in edit_categories
                    else 0,
                )
                concepto = st.text_input("Concepto *", value=str(current.get("concepto", "")))
                monto = st.number_input(
                    "Monto (COP) *",
                    min_value=0.0,
                    step=10000.0,
                    format="%.0f",
                    value=float(current.get("monto", 0)),
                )
                notas = st.text_area("Notas", value=str(current.get("notas", "")))

                if st.form_submit_button("Actualizar movimiento", type="primary"):
                    if not _preview_guard("editar movimientos"):
                        pass
                    elif not concepto.strip():
                        show_alert("El concepto es obligatorio.", "error")
                    elif monto <= 0:
                        show_alert("El monto debe ser mayor a cero.", "error")
                    else:
                        try:
                            _update_finance_movement(
                                movement_id,
                                {
                                    "fecha": fecha,
                                    "tipo": tipo,
                                    "categoria": categoria,
                                    "concepto": concepto,
                                    "monto": monto,
                                    "notas": notas,
                                },
                            )
                            queue_action_message("Movimiento actualizado correctamente.")
                            st.rerun()
                        except Exception as exc:
                            show_alert(str(exc), "error")

    elif tab == "Movimientos":
        if movements.empty:
            show_alert("No hay movimientos registrados.", "info")
        else:
            filtered = _finance_filter_controls(
                movements,
                key_prefix="contabilidad_movimientos",
            )
            if filtered.empty:
                show_alert("No hay movimientos con los filtros seleccionados.", "info")
            else:
                display = filtered.drop(columns=["fecha_dt"], errors="ignore").copy()
                render_table(display, key="finance_movements_table")


def main() -> None:
    init_connection()
    menu = build_nav_menu(_alert_count())
    render_mobile_bottom_nav(menu)
    sync_sidebar_compact_state()
    sync_mobile_nav_from_query(menu)
    page = sidebar()
    render_action_message()

    pages = {
        "dashboard": page_dashboard,
        "productos": page_products,
        "clientes": page_customers,
        "ventas": page_sales,
        "contabilidad": page_contabilidad,
        "pedidos": page_orders,
        "alertas": page_alerts,
        "administracion": page_administration,
    }
    pages[page]()


if __name__ == "__main__":
    main()
