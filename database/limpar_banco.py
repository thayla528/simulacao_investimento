import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "banco.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("DELETE FROM usuarios")
cursor.execute("DELETE FROM empresas")
cursor.execute("DELETE FROM investimentos")

conn.commit()
conn.close()

print("🔥 BANCO LIMPO DE VERDADE:", DB_PATH)