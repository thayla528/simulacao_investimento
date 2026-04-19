import sqlite3

conn = sqlite3.connect("database/banco.db")
cursor = conn.cursor()

cursor.execute("SELECT id, nome FROM usuarios")
usuarios = cursor.fetchall()

print("USUÁRIOS DO SISTEMA:")
for u in usuarios:
    print(u)

conn.close()