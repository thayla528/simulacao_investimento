from database.banco import conectar

conn = conectar()
cursor = conn.cursor()

cursor.execute("ALTER TABLE investimentos ADD COLUMN percentual REAL;")
dados = cursor.fetchall()

for d in dados:
    print(dict(d))

conn.close()