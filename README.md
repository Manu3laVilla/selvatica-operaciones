# Selvatica | Centro de Operaciones

Sistema de inventario y ventas para **tienda de accesorios**, con **Google Sheets** como base de datos.

## Funcionalidades

- Registro y edición de **accesorios** (collares, pulseras, aretes, etc.)
- Registro de **clientes**
- Registro de **ventas** con descuento automático de stock
- Gestión de **pedidos** con estados
- **Alertas** por stock bajo
- **Dashboard** con métricas y resumen

## Diferencias con Calixta (ropa)

Calixta y Selvatica comparten la misma arquitectura. El proyecto de ropa no tenía campos específicos de tallas o variantes, así que **todas las funcionalidades aplican** para accesorios. Lo adaptado para Selvatica:

| Aspecto | Calixta (ropa) | Selvatica (accesorios) |
|---------|----------------|------------------------|
| Categorías | Texto libre | Selector con categorías de accesorios |
| Textos UI | "Productos" genérico | "Accesorios" en formularios y métricas |
| Identidad visual | Azul corporativo | Paleta alegre (rosa, magenta, oliva, naranja) |
| Decoración | Sin doodles | Doodles en cada página |

## Requisitos

- Python 3.10+
- Cuenta de Google
- Proyecto en Google Cloud con Sheets API habilitada

## 1. Configurar Google Sheets API

### Paso A: Crear proyecto en Google Cloud

1. Entra a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un proyecto nuevo (ej: `selvatica-operaciones`)
3. Ve a **APIs y servicios > Biblioteca**
4. Busca y habilita:
   - **Google Sheets API**
   - **Google Drive API**

### Paso B: Crear Service Account

1. Ve a **APIs y servicios > Credenciales**
2. Clic en **Crear credenciales > Cuenta de servicio**
3. Asigna un nombre (ej: `selvatica-sheets`)
4. En la cuenta creada, ve a la pestaña **Claves**
5. **Agregar clave > Crear clave nueva > JSON**
6. Guarda el archivo descargado como:

```
credentials/service_account.json
```

### Paso C: Crear la hoja de cálculo

1. Crea una hoja nueva en [Google Sheets](https://sheets.google.com)
2. Copia el **ID** de la URL:

```
https://docs.google.com/spreadsheets/d/ESTE_ES_EL_ID/edit
```

3. **Comparte la hoja** con el email del Service Account  
   (aparece en el JSON como `client_email`) con permiso de **Editor**

## 2. Instalar y ejecutar

```bash
cd selvatica-centro-operaciones
python -m venv .venv

# Windows
.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
copy .env.example .env   # Windows
# cp .env.example .env   # macOS/Linux
```

Edita `.env`:

```env
GOOGLE_CREDENTIALS_PATH=credentials/service_account.json
SPREADSHEET_ID=tu_id_de_la_hoja
```

Ejecuta la app:

```bash
streamlit run app.py
```

La app creará automáticamente las pestañas:

| Pestaña   | Contenido                          |
|-----------|------------------------------------|
| Productos | Inventario de accesorios           |
| Clientes  | Cartera de clientes                |
| Ventas    | Historial de ventas                |
| Pedidos   | Pedidos y estados                  |

## 3. Estados de pedidos

- Pendiente
- Confirmado
- En preparación
- Enviado
- Entregado
- Cancelado

Al **cancelar** un pedido, el stock de sus productos se repone automáticamente.

## 4. Categorías de accesorios

- Collares
- Pulseras
- Aretes
- Anillos
- Broches
- Bolsos
- Cinturones
- Gorras y sombreros
- Otros

## 5. Assets de marca

Los doodles y logos están en `assets/`. Si tienes las imágenes originales en PNG, puedes reemplazar los SVG en `assets/doodles/` y `assets/logo.svg` para usar tus archivos exactos.

## 6. Despliegue (opcional)

Puedes desplegar gratis en [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Sube el repo a GitHub (sin subir `credentials/` ni `.env`)
2. En Streamlit Cloud, agrega los secrets con el contenido del JSON y el `SPREADSHEET_ID`

## Estructura del proyecto

```
selvatica-centro-operaciones/
├── app.py                  # Interfaz principal
├── config.py               # Configuración, categorías y esquemas
├── ui/
│   └── theme.py            # Estilos y doodles decorativos
├── assets/
│   ├── logo.svg
│   ├── logo-cream.svg
│   └── doodles/            # Ilustraciones decorativas
├── services/
│   ├── sheets_db.py
│   ├── product_service.py
│   ├── customer_service.py
│   ├── sale_service.py
│   ├── order_service.py
│   └── alert_service.py
├── credentials/
└── requirements.txt
```

## Notas

- Las ventas descuentan stock automáticamente.
- Las alertas se activan cuando `stock <= stock_minimo`.
- Puedes ver y editar los datos directamente en Google Sheets.
- Usa una hoja de Google Sheets **separada** de Calixta para no mezclar inventarios.
