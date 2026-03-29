import os
import sqlite3
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_INSTALLED = True
except ImportError:
    PSYCOPG2_INSTALLED = False

DB_FILE = "finance_engine.db"
DATABASE_URL = os.environ.get("DATABASE_URL")

def is_postgres():
    return bool(DATABASE_URL) and PSYCOPG2_INSTALLED

def get_connection():
    if is_postgres():
        conn = psycopg2.connect(DATABASE_URL)
        return conn
    else:
        conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

def get_cursor(conn):
    if is_postgres():
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

def q(sql):
    if is_postgres():
        sql = sql.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
        sql = sql.replace('?', '%s')
    return sql

def init_db():
    conn = get_connection()
    c = get_cursor(conn)
    
    # Crear tablas
    c.execute(q('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            preferencias TEXT
        )
    '''))
    
    c.execute(q('''
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            tipo TEXT
        )
    '''))
    
    c.execute(q('''
        CREATE TABLE IF NOT EXISTS metas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_meta TEXT,
            monto_objetivo REAL,
            monto_actual REAL DEFAULT 0.0,
            fecha_limite TEXT,
            icono TEXT
        )
    '''))

    c.execute(q('''
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha TEXT,
            tipo TEXT,
            categoria TEXT,
            monto REAL,
            descripcion TEXT,
            meta_id INTEGER,
            FOREIGN KEY (meta_id) REFERENCES metas (id)
        )
    '''))
    
    c.execute(q('''
        CREATE TABLE IF NOT EXISTS presupuestos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            categoria TEXT,
            monto_limite_mensual REAL
        )
    '''))

    c.execute(q('''
        CREATE TABLE IF NOT EXISTS gastos_fijos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            monto REAL
        )
    '''))

    # Renombrar permanentemente Nómina CFE a Nómina en Historial y Categorías
    c.execute("UPDATE categorias SET nombre = 'Nómina' WHERE nombre = 'Nómina CFE'")
    c.execute("UPDATE transacciones SET categoria = 'Nómina' WHERE categoria = 'Nómina CFE'")

    # Población inicial de categorías
    c.execute('SELECT COUNT(*) as cuenta FROM categorias')
    row = c.fetchone()
    cuenta = row['cuenta'] if row else 0
    if cuenta == 0:
        categorias_iniciales = [
            ("Nómina", "Ingreso"),
            ("Proyectos Extra", "Ingreso"),
            ("Alimentación", "Gasto"),
            ("Transporte", "Gasto"),
            ("Tecnología", "Gasto"),
            ("Educación", "Gasto"),
            ("Ahorro Activo", "Gasto"),
            ("Ocio/Entretenimiento", "Gasto"),
        ]
        if is_postgres():
            c.executemany("INSERT INTO categorias (nombre, tipo) VALUES (%s, %s)", categorias_iniciales)
        else:
            c.executemany("INSERT INTO categorias (nombre, tipo) VALUES (?, ?)", categorias_iniciales)
        
    conn.commit()
    conn.close()

# CRUD Categorías
def get_categorias(tipo=None):
    conn = get_connection()
    c = get_cursor(conn)
    if tipo:
        c.execute(q("SELECT id, nombre, tipo FROM categorias WHERE tipo = ?"), (tipo,))
    else:
        c.execute("SELECT id, nombre, tipo FROM categorias")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_categoria(nombre, tipo):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("INSERT INTO categorias (nombre, tipo) VALUES (?, ?)"), (nombre, tipo))
    conn.commit()
    conn.close()

def delete_categoria(cat_id):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("DELETE FROM categorias WHERE id = ?"), (cat_id,))
    conn.commit()
    conn.close()

# CRUD Transacciones
def get_transacciones():
    conn = get_connection()
    c = get_cursor(conn)
    c.execute("SELECT * FROM transacciones ORDER BY fecha DESC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_transaccion(fecha, tipo, categoria, monto, descripcion, meta_id=None):
    conn = get_connection()
    c = get_cursor(conn)
    if is_postgres():
        c.execute('''
            INSERT INTO transacciones (fecha, tipo, categoria, monto, descripcion, meta_id)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        ''', (fecha, tipo, categoria, monto, descripcion, meta_id))
        txn_id = c.fetchone()['id']
    else:
        c.execute('''
            INSERT INTO transacciones (fecha, tipo, categoria, monto, descripcion, meta_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (fecha, tipo, categoria, monto, descripcion, meta_id))
        txn_id = c.lastrowid
    conn.commit()
    conn.close()
    return txn_id

def delete_transaccion(t_id):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("SELECT tipo, monto, meta_id FROM transacciones WHERE id = ?"), (t_id,))
    row = c.fetchone()
    if row:
        tipo, monto, meta_id = row['tipo'], row['monto'], row['meta_id']
        if tipo == 'Gasto' and meta_id:
            c.execute(q("UPDATE metas SET monto_actual = monto_actual - ? WHERE id = ?"), (monto, meta_id))
        c.execute(q("DELETE FROM transacciones WHERE id = ?"), (t_id,))
        conn.commit()
    conn.close()

# CRUD Gastos Fijos
def get_gastos_fijos():
    conn = get_connection()
    c = get_cursor(conn)
    c.execute("SELECT * FROM gastos_fijos ORDER BY id ASC")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_gasto_fijo(nombre, monto):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("INSERT INTO gastos_fijos (nombre, monto) VALUES (?, ?)"), (nombre, monto))
    conn.commit()
    conn.close()

def delete_gasto_fijo(g_id):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("DELETE FROM gastos_fijos WHERE id = ?"), (g_id,))
    conn.commit()
    conn.close()

# CRUD Metas
def get_metas():
    conn = get_connection()
    c = get_cursor(conn)
    c.execute("SELECT * FROM metas")
    rows = c.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def add_meta(nombre, monto_objetivo, fecha_limite, icono):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q('''
        INSERT INTO metas (nombre_meta, monto_objetivo, monto_actual, fecha_limite, icono)
        VALUES (?, ?, 0.0, ?, ?)
    '''), (nombre, monto_objetivo, fecha_limite, icono))
    conn.commit()
    conn.close()

def update_meta_funds(meta_id, monto_adicional):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("UPDATE metas SET monto_actual = monto_actual + ? WHERE id = ?"), (monto_adicional, meta_id))
    conn.commit()
    conn.close()

def delete_meta(m_id):
    conn = get_connection()
    c = get_cursor(conn)
    c.execute(q("DELETE FROM metas WHERE id = ?"), (m_id,))
    conn.commit()
    conn.close()

# Análisis Financiero
def get_balance_global():
    conn = get_connection()
    c = get_cursor(conn)
    
    c.execute("SELECT SUM(monto) as total FROM transacciones WHERE tipo = 'Ingreso'")
    row = c.fetchone()
    ingresos = float(row['total']) if row and row['total'] else 0.0
    
    c.execute("SELECT SUM(monto) as total FROM transacciones WHERE tipo = 'Gasto'")
    row = c.fetchone()
    gastos = float(row['total']) if row and row['total'] else 0.0
    
    conn.close()
    return float(ingresos), float(gastos), float(ingresos - gastos)

if __name__ == "__main__":
    init_db()
