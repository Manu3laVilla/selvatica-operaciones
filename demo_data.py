from __future__ import annotations

import pandas as pd

_DEMO_CATEGORIES = [
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

_DEMO_PRODUCT_NAMES = [
    "Collar perlas doradas",
    "Aretes flor rosa",
    "Pulsera conchas",
    "Anillo hoja dorada",
    "Broche mariposa",
    "Bolso tejido natural",
    "Cinturón trenzado",
    "Gorra bordada Selvatica",
    "Collar capas delicado",
    "Aretes aro perlados",
    "Pulsera charms tropical",
    "Anillo piedra rosa",
    "Broche flor vintage",
    "Bolso mini crossbody",
    "Cinturón hebilla dorada",
    "Collar con dije luna",
    "Aretes largos cascada",
    "Pulsera perlas irregular",
    "Anillo ajustable hoja",
    "Broche perlas nacar",
    "Bolso shopper artesanal",
    "Gorra bucket verano",
    "Collar choker satén",
    "Aretes studs cristal",
    "Pulsera macramé arena",
    "Anillo doble banda",
    "Broche geométrico",
    "Bolso clutch fiesta",
]


def _demo_price(index: int) -> float:
    return float(18000 + ((index * 2500) % 75000))


def products() -> pd.DataFrame:
    rows = []
    for index, nombre in enumerate(_DEMO_PRODUCT_NAMES, start=1):
        categoria = _DEMO_CATEGORIES[(index - 1) % len(_DEMO_CATEGORIES)]
        precio = _demo_price(index)
        stock = 3 + (index * 2) % 18
        stock_minimo = 2 + (index % 4)
        rows.append(
            {
                "id": f"PRD-DEMO{index:02d}",
                "nombre": nombre,
                "descripcion": f"Accesorio demo {nombre.lower()}",
                "categoria": categoria,
                "precio": precio,
                "stock": stock,
                "stock_minimo": stock_minimo,
                "activo": "Si",
                "fecha_registro": f"2026-07-{((index - 1) % 28) + 1:02d} 10:{index % 60:02d}:00",
            }
        )
    return pd.DataFrame(rows)


_DEMO_CUSTOMER_NAMES = [
    "María López",
    "Ana Ruiz",
    "Carla Mendoza",
    "Sofía Herrera",
    "Valentina Castro",
    "Camila Rojas",
    "Daniela Vargas",
    "Laura Jiménez",
    "Paula Navarro",
    "Isabella Torres",
    "Gabriela Pineda",
    "Natalia Ortega",
    "Andrea Salazar",
    "Juliana Romero",
    "Fernanda Guzmán",
    "Lucía Delgado",
    "Mariana Soto",
    "Catalina Reyes",
    "Ximena Aguilar",
    "Regina Morales",
    "Elena Fuentes",
    "Patricia Núñez",
]


def customers() -> pd.DataFrame:
    rows = []
    zones = ["Centro", "Norte", "Sur", "Oriente", "Occidente"]
    for index, nombre in enumerate(_DEMO_CUSTOMER_NAMES, start=1):
        slug = nombre.lower().replace(" ", ".").replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u").replace("ñ", "n")
        rows.append(
            {
                "id": f"CLI-DEMO{index:02d}",
                "nombre": nombre,
                "email": f"{slug}@ejemplo.com",
                "telefono": f"300-{1000000 + index:07d}",
                "direccion": zones[(index - 1) % len(zones)],
                "notas": "Cliente frecuente" if index % 5 == 0 else "",
                "fecha_registro": f"2026-07-{((index - 1) % 28) + 1:02d} 09:{index % 60:02d}:00",
            }
        )
    return pd.DataFrame(rows)


def sales() -> pd.DataFrame:
    products_df = products()
    customers_df = customers()
    rows = []
    for index in range(1, 29):
        product = products_df.iloc[(index - 1) % len(products_df)]
        customer = customers_df.iloc[(index - 1) % len(customers_df)]
        qty = 1 + (index % 3)
        price = float(product["precio"])
        rows.append(
            {
                "id": f"VTA-DEMO{index:02d}",
                "fecha": f"2026-07-{((index - 1) % 28) + 1:02d} {8 + (index % 10):02d}:{(index * 7) % 60:02d}:00",
                "cliente_id": customer["id"],
                "cliente_nombre": customer["nombre"],
                "producto_id": product["id"],
                "producto_nombre": product["nombre"],
                "cantidad": qty,
                "precio_unitario": price,
                "subtotal": round(price * qty, 2),
                "pedido_id": "PED-DEMO02" if index == 2 else "",
            }
        )
    return pd.DataFrame(rows)


def orders() -> pd.DataFrame:
    aretes_price = _demo_price(2)
    pulsera_price = _demo_price(3)
    return pd.DataFrame(
        [
            {
                "id": "PED-DEMO01",
                "cliente_id": "CLI-DEMO01",
                "cliente_nombre": "María López",
                "items_json": (
                    f'[{{"producto_id":"PRD-DEMO02","producto_nombre":"Aretes flor rosa",'
                    f'"cantidad":1,"precio_unitario":{aretes_price},"subtotal":{aretes_price}}}]'
                ),
                "total": aretes_price,
                "estado": "Confirmado",
                "fecha_creacion": "2026-08-05 12:00:00",
                "fecha_actualizacion": "2026-08-05 12:30:00",
                "notas": "Para regalo",
            },
            {
                "id": "PED-DEMO02",
                "cliente_id": "CLI-DEMO02",
                "cliente_nombre": "Ana Ruiz",
                "items_json": (
                    f'[{{"producto_id":"PRD-DEMO03","producto_nombre":"Pulsera conchas",'
                    f'"cantidad":2,"precio_unitario":{pulsera_price},"subtotal":{pulsera_price * 2}}}]'
                ),
                "total": pulsera_price * 2,
                "estado": "Entregado",
                "fecha_creacion": "2026-07-20 10:00:00",
                "fecha_actualizacion": "2026-07-25 15:00:00",
                "notas": "",
            },
        ]
    )


def low_stock_alerts() -> pd.DataFrame:
    products_df = products()
    alerts = products_df[products_df["stock"] <= products_df["stock_minimo"]].copy()
    alerts["faltante"] = alerts["stock_minimo"] - alerts["stock"]
    return alerts


def finance_movements() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": "FIN-DEMO01",
                "fecha": "2026-08-01 09:00:00",
                "tipo": "Ingreso",
                "categoria": "Capital",
                "concepto": "Aporte inicial del negocio",
                "monto": 5_000_000,
                "notas": "Fondo de arranque",
            },
            {
                "id": "FIN-DEMO02",
                "fecha": "2026-08-02 11:30:00",
                "tipo": "Ingreso",
                "categoria": "Inversión",
                "concepto": "Reinversión de utilidades",
                "monto": 1_200_000,
                "notas": "",
            },
            {
                "id": "FIN-DEMO03",
                "fecha": "2026-08-03 14:15:00",
                "tipo": "Gasto",
                "categoria": "Insumos",
                "concepto": "Compra de perlas, broches y cadenas",
                "monto": 850_000,
                "notas": "Proveedor local",
            },
            {
                "id": "FIN-DEMO04",
                "fecha": "2026-08-04 10:00:00",
                "tipo": "Gasto",
                "categoria": "Equipos",
                "concepto": "Pinzas y kit de herramientas",
                "monto": 320_000,
                "notas": "",
            },
            {
                "id": "FIN-DEMO05",
                "fecha": "2026-08-05 16:45:00",
                "tipo": "Gasto",
                "categoria": "Gasto extra",
                "concepto": "Envíos y empaques especiales",
                "monto": 145_500,
                "notas": "Mes de agosto",
            },
        ]
    )
