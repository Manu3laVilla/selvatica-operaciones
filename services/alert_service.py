from __future__ import annotations

import pandas as pd

from services.product_service import list_products


def get_low_stock_alerts() -> pd.DataFrame:
    products = list_products(active_only=True)
    if products.empty:
        return products

    alerts = products[products["stock"] <= products["stock_minimo"]].copy()
    if alerts.empty:
        return alerts

    alerts["faltante"] = alerts["stock_minimo"] - alerts["stock"]
    return alerts.sort_values(["faltante", "stock"], ascending=[False, True])


def count_low_stock() -> int:
    alerts = get_low_stock_alerts()
    return len(alerts)
