from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar

import os
from routes.auth import auth_bp, login_required
from services.yfinance_service import yfinance_bp, obter_preco_atual

from flask import jsonify

perfil_bp = Blueprint("perfil", __name__, url_prefix="/perfil")

@perfil_bp.route("/cotacao/<ticker>")
def cotacao(ticker):
    from services.yfinance_service import obter_historico

    ticker = ticker.strip().upper()

    return jsonify(obter_historico(ticker))

@perfil_bp.route("/historico/<ticker>")
@login_required
def historico(ticker):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT data, lucro
        FROM historico_acoes
        WHERE usuario_id = ? AND ticker = ?
        ORDER BY data ASC
    """, (session["usuario_id"], ticker))

    dados = cursor.fetchall()
    conn.close()

    return jsonify({
        "labels": [d["data"] for d in dados],
        "valores": [d["lucro"] for d in dados]
    })

@perfil_bp.route('/portifolio')
@login_required
def portifolio():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    # Soma todas as ações da empresa, independente do tipo
    cursor.execute("""
        SELECT empresa, ticker, SUM(num_acoes) as total_acoes
        FROM empresas
        WHERE usuario_id = ?
        GROUP BY empresa, ticker
        ORDER BY empresa
    """, (usuario_id,))

    portfolio = cursor.fetchall()
    conn.close()

    return render_template('portifolio.html', portfolio=portfolio)

# ================= DETALHE DA AÇÃO =================
@perfil_bp.route('/detalhe_acao/<ticker>/<tipo>')
@login_required
def detalhe_acao(ticker, tipo):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    usuario_id = session["usuario_id"]

    conn = conectar()
    cursor = conn.cursor()

    # Pega todas as ações da empresa, agrupando por tipo_acao
    cursor.execute("""
        SELECT tipo_acao,
               SUM(num_acoes) AS total_acoes,
               AVG(preco_acao) AS preco_medio,
               MIN(lote) AS lote_min,
               MAX(lote) AS lote_max,
               GROUP_CONCAT(setor, ', ') AS setores
        FROM empresas
        WHERE usuario_id = ? AND ticker = ?
        GROUP BY tipo_acao
        ORDER BY tipo_acao
    """, (usuario_id, ticker))

    detalhes = cursor.fetchall()
    conn.close()

    # Nome da empresa para o cabeçalho
    acao = detalhes[0] if detalhes else None

    return render_template('detalhe_acao.html', acao=acao, detalhes=detalhes)

# ------------------ PERFIL ------------------
@perfil_bp.route("/perfil")
@login_required
def perfil():
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM empresas WHERE usuario_id = ?",
        (session["usuario_id"],)
    )
    empresas_rows = cursor.fetchall()

    empresas_atualizadas = []
    for row in empresas_rows:
        empresa = dict(row)

        ticker = empresa['ticker'].strip().upper()
        preco_b3 = obter_preco_atual(ticker)

        empresa['divida'] = float(empresa.get('divida') or 0)

        if preco_b3:
            preco_custo = float(empresa['preco_acao'] or 0)
            quantidade = int(empresa['num_acoes'] or 0)

            empresa['preco_atual_b3'] = preco_b3
            empresa['variacao_valor'] = round((preco_b3 - preco_custo) * quantidade, 2)
        else:
            empresa['preco_atual_b3'] = empresa['preco_acao']
            empresa['variacao_valor'] = 0

        empresas_atualizadas.append(empresa)

    # 🔥 FOTO DO USUÁRIO AQUI
    foto_path = f"perfil/{session['usuario_id']}.png"

    conn.close()

    return render_template(
        "perfil.html",
        usuario=session["usuario_nome"],
        empresas=empresas_atualizadas,
        foto_path=foto_path
    )


# ------------------ UPLOAD FOTO ------------------
@perfil_bp.route("/upload_foto", methods=["POST"])
@login_required
def upload_foto():
    if "foto" not in request.files:
        flash("Nenhum arquivo enviado!", "danger")
        return redirect(url_for("perfil.perfil"))

    foto = request.files["foto"]

    if foto.filename == "":
        flash("Nenhum arquivo selecionado!", "warning")
        return redirect(url_for("perfil.perfil"))

    # extensão original
    ext = os.path.splitext(foto.filename)[1].lower()

    # validação básica
    if ext not in [".png", ".jpg", ".jpeg", ".webp"]:
        flash("Formato não permitido!", "danger")
        return redirect(url_for("perfil.perfil"))

    # 🔥 nome fixo por usuário
    filename = f"{session['usuario_id']}.png"
    pasta = os.path.join("static", "perfil")
    caminho = os.path.join(pasta, filename)

    os.makedirs(pasta, exist_ok=True)
    foto.save(caminho)

    # 🔥 caminho FINAL obrigatório
    pasta = os.path.join("static", "perfil")
    caminho = os.path.join(pasta, filename)

    flash("Foto atualizada com sucesso!", "success")
    return redirect(url_for("perfil.perfil"))