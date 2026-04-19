import sqlite3

conn = sqlite3.connect("database/banco.db")
cursor = conn.cursor()

cursor.execute("DELETE FROM usuarios")
cursor.execute("DELETE FROM empresas")
cursor.execute("DELETE FROM investimentos")

conn.commit()
conn.close()

print("🔥 BANCO LIMPO DE VERDADE")