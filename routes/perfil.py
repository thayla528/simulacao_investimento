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
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empresas WHERE usuario = ?", (session["usuario"],))
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

    conn.close()
    return render_template("perfil.html", usuario=session["usuario"], empresas=empresas_atualizadas, os=os)

@perfil_bp.route("/upload_foto", methods=["POST"])
@login_required
def upload_foto():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    if "foto" not in request.files:
        flash("Nenhum arquivo enviado!", "danger")
        return redirect(url_for("perfil.perfil"))

    foto = request.files["foto"]
    if foto.filename == "":
        flash("Nenhum arquivo selecionado!", "warning")
        return redirect(url_for("perfil.perfil"))

    filename = session["usuario"] + ".png"
    caminho = os.path.join("static/perfil", filename)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    foto.save(caminho)

    flash("Foto atualizada com sucesso!", "success")
    return redirect(url_for("perfil.perfil"))
