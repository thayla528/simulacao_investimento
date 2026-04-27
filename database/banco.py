import sqlite3

def conectar():
    conn = sqlite3.connect("database/banco.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def criar_tabela():
    conn = conectar()
    cursor = conn.cursor()

    # --- TABELA DE USUÁRIOS ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    """)

    # --- TABELA DE EMPRESAS (AÇÕES) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
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

    # --- TABELA DE INVESTIMENTOS (RENDA FIXA) ---
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS investimentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER NOT NULL,
            tipo TEXT,
            valor_investido REAL,
            taxa REAL,
            tempo INTEGER,
            lucro REAL,
            percentual REAL DEFAULT 100
        )
    """)

    # --- TABELA DE HISTÓRICO UNIFICADO ---
    # Esta tabela servirá para Ações e Renda Fixa
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS historico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            ticker TEXT, 
            acao TEXT, 
            data_hora DATETIME,
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )
    """)

    conn.commit()
    conn.close()
