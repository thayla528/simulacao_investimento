from database.banco import criar_tabela
import os

# Caminho do banco
banco_path = "database/banco.db"

# Deleta o arquivo se ele existir
if os.path.exists(banco_path):
    os.remove(banco_path)
    print("Banco antigo removido!")

# Cria do zero com a coluna nova
criar_tabela()
print("Novo banco criado com a coluna dividendos_12m!")
