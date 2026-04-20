from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar

import os
from routes.auth import auth_bp, login_required
from services.yfinance_service import yfinance_bp, obter_preco_atual

perfil_bp = Blueprint("perfil", __name__)


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