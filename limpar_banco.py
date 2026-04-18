from database.banco import conectar


def limpar_usuarios():
    conn = conectar()
    cursor = conn.cursor()

    # DELETE remove as linhas, mas mantém a estrutura da tabela
    cursor.execute("DELETE FROM usuarios")

    # Opcional: Reiniciar o contador de IDs (auto-incremento)
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='usuarios'")

    conn.commit()
    conn.close()
    print("Tabela de usuários limpa com sucesso!")


if __name__ == "__main__":
    limpar_usuarios()
