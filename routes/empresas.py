from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from database.banco import conectar
from routes.auth import login_required
import yfinance as yf
from services.utils import parse_float

empresas_bp = Blueprint("empresas", __name__)



def registrar_log(usuario_id, ticker, acao):
    try:
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO historico (usuario_id, ticker, acao, data_hora)
            VALUES (?, ?, ?, datetime('now', 'localtime'))
        """, (usuario_id, ticker, acao))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"ERRO AO GRAVAR LOG: {e}")

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

        # 1. Buscamos todos os dados necessários antes de deletar
        cursor.execute("SELECT ticker, num_acoes, preco_acao FROM empresas WHERE id = ?", (id,))
        empresa = cursor.fetchone()

        if empresa:
            ticker = empresa['ticker']
            qtd = empresa['num_acoes']
            preco = empresa['preco_acao']

            # Montamos a string de detalhe para o histórico
            detalhe = f"EXCLUSÃO: Encerrou {qtd} ações a R$ {preco:.2f}"

            # 2. Executamos o delete
            cursor.execute(
                "DELETE FROM empresas WHERE id = ? AND usuario_id = ?",
                (id, session["usuario_id"])
            )
            conn.commit()

            # 3. Registramos no histórico uma única vez com o detalhe completo
            registrar_log(session["usuario_id"], ticker, detalhe)

            flash("Empresa excluída com sucesso!", "success")
        else:
            flash("Empresa não encontrada!", "danger")

        conn.close()

    except Exception as e:
        print("ERRO AO EXCLUIR:", e)
        flash("Erro ao excluir empresa!", "danger")

    return redirect(url_for("historico.historico"))  # Redireciona para o histórico para ver o log


# ------------------ EDITAR EMPRESA ------------------
# ------------------ EDITAR EMPRESA ------------------
@empresas_bp.route("/editar_empresa/<int:id>", methods=["GET", "POST"])
@login_required
def editar_empresa(id):
    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        # 1. CAPTURA DADOS ANTIGOS PARA O HISTÓRICO ANTES DO UPDATE
        cursor.execute("SELECT num_acoes, preco_acao FROM empresas WHERE id = ?", (id,))
        antigo = cursor.fetchone()

        # 2. SEUS CAMPOS ORIGINAIS (MANTIDOS 100%)
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

        # 3. EXECUTA O UPDATE
        cursor.execute("""
                       UPDATE empresas
                       SET ticker=?,
                           empresa=?,
                           setor=?,
                           num_acoes=?,
                           preco_acao=?,
                           lucro_liquido=?,
                           patrimonio=?,
                           ativos=?,
                           divida=?,
                           lote=?,
                           tipo_acao=?
                       WHERE id = ?
                         AND usuario_id = ?
                       """, (
                           ticker, empresa_nome, setor, num_acoes, preco_acao,
                           lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao,
                           id, session["usuario_id"]
                       ))

        # 4. GERA O DETALHE DA EDIÇÃO
        if antigo:
            detalhe = f"EDIÇÃO: Qtd {antigo['num_acoes']} ➔ {num_acoes} | Preço R$ {antigo['preco_acao']:.2f} ➔ R$ {preco_acao:.2f}"
        else:
            detalhe = f"EDIÇÃO: Dados do ativo {ticker} atualizados"

        conn.commit()
        conn.close()

        # 5. REGISTRA NO HISTÓRICO COM DETALHES
        registrar_log(session["usuario_id"], ticker, detalhe)

        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for("perfil.perfil"))

    # 🔒 BUSCA PARA EXIBIR NO FORMULÁRIO (GET)
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
# ------------------ CADASTRAR EMPRESA ------------------
@empresas_bp.route("/cadastrar_empresa", methods=["POST"])
@login_required
def cadastrar_empresa():
    try:
        ticker = (request.form.get("ticker") or "").strip().upper()
        empresa_nome = (request.form.get("empresa") or "").strip()
        setor = (request.form.get("setor") or "").strip()
        num_acoes = int(request.form.get("num_acoes") or 0)
        preco_acao = parse_float(request.form.get("preco_acao"))
        lucro_liquido = parse_float(request.form.get("lucro_liquido"))
        patrimonio = parse_float(request.form.get("patrimonio"))
        ativos = parse_float(request.form.get("ativos"))
        divida = parse_float(request.form.get("divida"))
        dividendos_12m = parse_float(request.form.get("dividendos_12m"))  # Novo campo
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
                lucro_liquido, patrimonio, ativos, divida, dividendos_12m,lote, tipo_acao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?)
        """, (
            session["usuario_id"],
            ticker, empresa_nome, setor, num_acoes, preco_acao,
            lucro_liquido, patrimonio, ativos, divida, dividendos_12m, lote, tipo_acao
        ))

        conn.commit()
        conn.close()

        # MONTA O DETALHE DE ENTRADA E REGISTRA O LOG
        detalhe_entrada = f"CADASTRO: Entrada de {num_acoes} ações a R$ {preco_acao:.2f}"
        registrar_log(session["usuario_id"], ticker, detalhe_entrada)

        flash("Empresa cadastrada com sucesso!", "success")

    except Exception as e:
        print("ERRO AO CADASTRAR EMPRESA:", e)
        flash("Erro ao cadastrar empresa!", "danger")

    return redirect(url_for("perfil.perfil"))


@empresas_bp.route("/buscar_acao/<ticker>")
@login_required
def buscar_acao(ticker):
    try:
        ticker = ticker.strip().upper()

        # --- AUTOMAÇÃO DO TIPO DE AÇÃO ---
        if ticker.endswith('3'):
            tipo_automatico = "ON"
        elif ticker.endswith(('4', '5', '6')):
            tipo_automatico = "PN"
        elif ticker.endswith('11'):
            tipo_automatico = "UNIT"
        else:
            tipo_automatico = "OUTROS"

        # Chamada à API do Yahoo Finance
        acao = yf.Ticker(f"{ticker}.SA")
        info = acao.info

        # Validação básica de existência do ativo
        if not info or ("shortName" not in info and "longName" not in info):
            return jsonify({"erro": "Ativo não encontrado"})

        # Pegando dados do Balanço e DRE
        try:
            balanco = acao.balance_sheet.iloc[:, 0]
            dre = acao.financials.iloc[:, 0]

            lucro_liquido = float(dre.get('Net Income', 0))
            patrimonio = float(balanco.get('Stockholders Equity', 0))
            ativos = float(balanco.get('Total Assets', 0))
            divida = float(balanco.get('Total Debt', 0))
        except Exception:
            lucro_liquido = info.get("netIncomeToCommon", 0)
            patrimonio = info.get("totalStockholderEquity", 0) or (
                    info.get("bookValue", 0) * info.get("sharesOutstanding", 1))
            ativos = info.get("totalAssets", 0)
            divida = info.get("totalDebt", 0)

        # --- NOVOS DADOS PARA DY E PAYOUT ---
        dividendos_por_acao = info.get("dividendRate", 0) or 0

        # Pega o lucro por ação (EPS) para o cálculo do Payout não dar zero
        lucro_por_acao = info.get("trailingEps", 0) or 0

        # Se não tiver lucro por ação, tentamos calcular o payout direto da API
        payout_ratio = info.get("payoutRatio", 0) or 0

        # Retorno completo para o Frontend
        return jsonify({
            "nome": info.get("shortName") or info.get("longName"),
            "setor": info.get("sector"),
            "preco": info.get("currentPrice") or info.get("regularMarketPrice"),
            "lucro_liquido": lucro_liquido,
            "patrimonio": patrimonio,
            "ativos": ativos,
            "divida": divida,
            "dividendos": dividendos_por_acao,
            "payout_bruto": payout_ratio * 100,  # Enviamos o Payout já em %
            "lpa": lucro_por_acao,  # Lucro Por Ação
            "tipo_acao": tipo_automatico
        })

    except Exception as e:
        print(f"ERRO BUSCAR AÇÃO {ticker}: {e}")
        return jsonify({"erro": "Falha ao buscar dados"})



