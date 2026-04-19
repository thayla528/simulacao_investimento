from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.banco import conectar
from routes.auth import login_required
import yfinance as yf

empresas_bp = Blueprint("empresas", __name__)


# ------------------ CADASTRO DE AÇÕES ------------------
@empresas_bp.route("/cadastro_de_acao")
@login_required
def cadastro_de_acao():

    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM empresas WHERE usuario_id = ?",
        (session["usuario_id"],)
    )

    empresas = cursor.fetchall()
    conn.close()

    return render_template("cadastro_acao.html", empresas=empresas)


# ------------------ EXCLUIR EMPRESA ------------------
@empresas_bp.route("/excluir_empresa/<int:id>")
@login_required
def excluir_empresa(id):

    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM empresas WHERE id = ? AND usuario_id = ?",
            (id, session["usuario_id"])
        )

        conn.commit()
        conn.close()

        flash("Empresa excluída com sucesso!", "success")

    except Exception as e:
        print("ERRO AO EXCLUIR:", e)
        flash("Erro ao excluir empresa!", "danger")

    return redirect(url_for("perfil.perfil"))


# ------------------ EDITAR EMPRESA ------------------
@empresas_bp.route("/editar_empresa/<int:id>", methods=["GET", "POST"])
@login_required
def editar_empresa(id):

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":

        def parse_float(val):
            if val is None or val == "":
                return 0.0
            return float(str(val).replace(",", "."))

        ticker = (request.form.get("ticker") or "").strip().upper()
        empresa_nome = (request.form.get("empresa") or "").strip()
        setor = (request.form.get("setor") or "").strip()
        num_acoes = int(request.form.get("num_acoes") or 0)
        preco_acao = parse_float(request.form.get("preco_acao"))
        lucro_liquido = parse_float(request.form.get("lucro_liquido"))
        patrimonio = parse_float(request.form.get("patrimonio"))
        ativos = parse_float(request.form.get("ativos"))
        divida = parse_float(request.form.get("divida"))
        lote = int(request.form.get("lote") or 100)
        tipo_acao = (request.form.get("tipo_acao") or "ON").strip().upper()

        cursor.execute("""
            UPDATE empresas
            SET ticker=?, empresa=?, setor=?, num_acoes=?, preco_acao=?,
                lucro_liquido=?, patrimonio=?, ativos=?, divida=?, lote=?, tipo_acao=?
            WHERE id=? AND usuario_id=?
        """, (
            ticker, empresa_nome, setor, num_acoes, preco_acao,
            lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao,
            id, session["usuario_id"]
        ))

        conn.commit()
        conn.close()

        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for("perfil.perfil"))

    # 🔒 só busca se for do usuário
    cursor.execute(
        "SELECT * FROM empresas WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    )

    empresa = cursor.fetchone()
    conn.close()

    if not empresa:
        flash("Empresa não encontrada!", "danger")
        return redirect(url_for("perfil.perfil"))

    return render_template("editar_acao.html", empresa=empresa)


# ------------------ CADASTRAR EMPRESA ------------------
@empresas_bp.route("/cadastrar_empresa", methods=["POST"])
@login_required
def cadastrar_empresa():

    try:
        def parse_float(val):
            if val is None or val == "":
                return 0.0
            return float(str(val).replace(",", "."))

        ticker = (request.form.get("ticker") or "").strip().upper()
        empresa_nome = (request.form.get("empresa") or "").strip()
        setor = (request.form.get("setor") or "").strip()
        num_acoes = int(request.form.get("num_acoes") or 0)
        preco_acao = parse_float(request.form.get("preco_acao"))
        lucro_liquido = parse_float(request.form.get("lucro_liquido"))
        patrimonio = parse_float(request.form.get("patrimonio"))
        ativos = parse_float(request.form.get("ativos"))
        divida = parse_float(request.form.get("divida"))
        lote = int(request.form.get("lote") or 100)
        tipo_acao = (request.form.get("tipo_acao") or "ON").strip().upper()

        if not ticker or not empresa_nome or not setor or num_acoes <= 0 or preco_acao <= 0:
            flash("Campos obrigatórios inválidos!", "danger")
            return redirect(url_for("perfil.perfil"))

        conn = conectar()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO empresas (
                usuario_id, ticker, empresa, setor, num_acoes, preco_acao,
                lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["usuario_id"],
            ticker, empresa_nome, setor, num_acoes, preco_acao,
            lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao
        ))

        conn.commit()
        conn.close()

        flash("Empresa cadastrada com sucesso!", "success")

    except Exception as e:
        print("ERRO AO CADASTRAR EMPRESA:", e)
        flash("Erro ao cadastrar empresa!", "danger")

    return redirect(url_for("perfil.perfil"))


# ------------------ BUSCAR AÇÃO (API) ------------------
@empresas_bp.route("/buscar_acao/<ticker>")
@login_required
def buscar_acao(ticker):

    try:
        ticker = ticker.strip().upper()

        dados = yf.Ticker(f"{ticker}.SA")
        info = dados.info

        if not info or "shortName" not in info:
            return jsonify({"erro": "Ativo não encontrado"})

        return jsonify({
            "nome": info.get("shortName"),
            "setor": info.get("sector"),
            "preco": info.get("regularMarketPrice"),
            "lucro_liquido": info.get("netIncomeToCommon"),
            "patrimonio": info.get("bookValue"),
            "ativos": info.get("totalAssets"),
            "divida": info.get("totalDebt")
        })

    except Exception as e:
        print("ERRO BUSCAR AÇÃO:", e)
        return jsonify({"erro": "Falha ao buscar dados"})