-- Ejecutar en Supabase → SQL Editor (una sola vez por proyecto)

CREATE TABLE IF NOT EXISTS productos (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  descripcion TEXT DEFAULT '',
  categoria TEXT NOT NULL,
  precio NUMERIC(12, 2) NOT NULL DEFAULT 0,
  stock INTEGER NOT NULL DEFAULT 0,
  stock_minimo INTEGER NOT NULL DEFAULT 0,
  activo TEXT NOT NULL DEFAULT 'Si',
  fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS clientes (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  email TEXT DEFAULT '',
  telefono TEXT DEFAULT '',
  direccion TEXT DEFAULT '',
  notas TEXT DEFAULT '',
  fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS ventas (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  cliente_id TEXT,
  cliente_nombre TEXT,
  producto_id TEXT,
  producto_nombre TEXT,
  cantidad INTEGER NOT NULL DEFAULT 1,
  precio_unitario NUMERIC(12, 2) NOT NULL DEFAULT 0,
  subtotal NUMERIC(12, 2) NOT NULL DEFAULT 0,
  pedido_id TEXT
);

CREATE TABLE IF NOT EXISTS pedidos (
  id TEXT PRIMARY KEY,
  cliente_id TEXT,
  cliente_nombre TEXT,
  items_json JSONB NOT NULL DEFAULT '[]'::jsonb,
  total NUMERIC(12, 2) NOT NULL DEFAULT 0,
  estado TEXT NOT NULL,
  fecha_creacion TEXT,
  fecha_actualizacion TEXT,
  notas TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS contabilidad (
  id TEXT PRIMARY KEY,
  fecha TEXT,
  tipo TEXT NOT NULL,
  categoria TEXT NOT NULL,
  concepto TEXT NOT NULL,
  monto NUMERIC(12, 2) NOT NULL DEFAULT 0,
  notas TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS categorias_producto (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  activo TEXT NOT NULL DEFAULT 'Si',
  orden INTEGER NOT NULL DEFAULT 0,
  fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS tipos_ingreso (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  activo TEXT NOT NULL DEFAULT 'Si',
  orden INTEGER NOT NULL DEFAULT 0,
  fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS tipos_gasto (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  activo TEXT NOT NULL DEFAULT 'Si',
  orden INTEGER NOT NULL DEFAULT 0,
  fecha_registro TEXT
);

CREATE TABLE IF NOT EXISTS estados_pedido (
  id TEXT PRIMARY KEY,
  nombre TEXT NOT NULL,
  activo TEXT NOT NULL DEFAULT 'Si',
  orden INTEGER NOT NULL DEFAULT 0,
  genera_venta TEXT NOT NULL DEFAULT 'No',
  revierte_venta TEXT NOT NULL DEFAULT 'No',
  fecha_registro TEXT
);
