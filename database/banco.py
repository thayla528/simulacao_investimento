import sqlite3

def conectar():
    conn = sqlite3.connect("database/banco.db")
    conn.row_factory = sqlite3.Row
    return conn


def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            ticker TEXT NOT NULL,
            empresa TEXT NOT NULL,
            setor TEXT NOT NULL,
            num_acoes INTEGER DEFAULT 0,
            preco_acao REAL DEFAULT 0,
            lucro_liquido REAL DEFAULT 0,
            patrimonio REAL DEFAULT 0,
            ativos REAL DEFAULT 0,
            divida REAL DEFAULT 0,
            lote INTEGER DEFAULT 100,
            tipo_acao TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario TEXT,
            tipo TEXT,
            valor_investido REAL,
            taxa REAL,
            tempo INTEGER,
            lucro REAL
        )
    """)

    conn.commit()
    conn.close()