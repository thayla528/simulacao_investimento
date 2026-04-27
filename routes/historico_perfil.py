from flask import Blueprint, render_template, session, redirect, url_for
from database.banco import conectar
from routes.auth import login_required

historico_bp = Blueprint("historico", __name__)

# ------------------ HISTÓRICO GERAL (AÇÕES) ------------------
@historico_bp.route("/historico")
@login_required
def historico():
    usuario_id = session.get("usuario_id")
    conn = conectar()
    cursor = conn.cursor()

    # 1. Busca dados do usuário (E-mail) para o painel lateral
    cursor.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()

    # 2. Busca o histórico Geral (Apenas o que NÃO é Renda Fixa)
    cursor.execute("""
                   SELECT ticker, acao, data_hora
                   FROM historico
                   WHERE usuario_id = ? AND acao NOT LIKE '%RF%'
                   ORDER BY data_hora DESC
                   """, (usuario_id,))
    logs = cursor.fetchall()

    conn.close()
    return render_template("historico_perfil.html", usuario=usuario, logs=logs)

# ------------------ HISTÓRICO ESPECÍFICO RENDA FIXA ------------------
@historico_bp.route("/historico_renda_fixa")
@login_required
def historico_rf():
    usuario_id = session.get("usuario_id")
    conn = conectar()
    cursor = conn.cursor()

    # 1. Busca dados do usuário
    cursor.execute("SELECT email FROM usuarios WHERE id = ?", (usuario_id,))
    usuario = cursor.fetchone()

    # 2. Busca apenas logs de Renda Fixa (Que contenham 'RF' no texto da ação)
    cursor.execute("""
                   SELECT ticker, acao, data_hora
                   FROM historico
                   WHERE usuario_id = ? AND acao LIKE '%RF%'
                   ORDER BY data_hora DESC
                   """, (usuario_id,))
    logs = cursor.fetchall()

    conn.close()
    return render_template("historico_renda_fixa.html", usuario=usuario, logs=logs)
