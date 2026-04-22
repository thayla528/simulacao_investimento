from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar
from routes.auth import login_required
from services.calculos import calcular_lucro
import yfinance as yf

from services.investimentos import calcular_resultado

simulador_bp = Blueprint("simulador", __name__)


# ------------------ TAXA AUTOMÁTICA ------------------
@simulador_bp.route("/buscar_ativo/<ticker>")
@login_required
def buscar_ativo(ticker):
    try:
        acao = yf.Ticker(ticker)
        hist = acao.history(period="1d")

        info = acao.info

        if hist.empty:
            return {"erro": True}

        preco = hist["Close"].iloc[-1]

        return {
            "erro": False,
            "preco": round(preco, 2),
            "nome": info.get("shortName", ticker)
        }

    except:
        return {"erro": True}

# ------------------ TAXA AUTOMÁTICA ------------------



# ------------------ EDITAR ------------------
@simulador_bp.route("/editar_simulador/<int:id>", methods=["GET", "POST"])
@login_required
def editar_simulador(id):
    conn = conectar()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM investimentos WHERE id = ? AND usuario_id = ?",
        (id, session["usuario_id"])
    )
    investimento = cursor.fetchone()

    if not investimento:
        flash("Investimento não encontrado!", "danger")
        return redirect(url_for("simulador.investimentos"))

    if request.method == "POST":
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor_investido', 0))

        # 🔥 AGORA AUTOMÁTICO

        tempo = int(request.form.get('tempo', 0))

        # 🔥 ADICIONA ISSO
        tipo_tempo = request.form.get('tipo_tempo', 'meses')

        if tipo_tempo == "anos":
            tempo = tempo * 12

        # 🔥 pega taxa do slider
        taxa = float(request.form.get('taxa_final', 0)) / 100

        # 🔥 calcula lucro
        lucro = valor * taxa * (tempo / 12)

        cursor.execute("""
            UPDATE investimentos
            SET tipo=?, valor_investido=?, taxa=?, tempo=?, lucro=?
            WHERE id=? AND usuario_id=?
        """, (
            tipo, valor, taxa * 100, tempo, lucro,
            id, session["usuario_id"]
        ))

        conn.commit()
        conn.close()

        flash("Investimento atualizado!", "success")
        return redirect(url_for("simulador.investimentos"))

    conn.close()
    return render_template("editar_simulador.html", investimento=investimento)


# ------------------ EXCLUIR ------------------
@simulador_bp.route("/excluir_simulador/<int:id>")
@login_required
def excluir_simulador(id):
    try:
        conn = conectar()
        cursor = conn.cursor()

        cursor.execute(
            "DELETE FROM investimentos WHERE id = ? AND usuario_id = ?",
            (id, session["usuario_id"])
        )

        conn.commit()
        conn.close()

        flash("Investimento excluído com sucesso!", "success")

    except Exception as e:
        print("ERRO AO EXCLUIR:", e)
        flash("Erro ao excluir investimento!", "danger")

    return redirect(url_for("simulador.investimentos"))

def safe_float(val):
    try:
        return float(val)
    except:
        return 0.0

# ------------------ SIMULADOR ------------------
@simulador_bp.route("/simulador", methods=["GET", "POST"])
@login_required
def investimentos():
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor_investido', 0))
        tempo = int(request.form.get('tempo', 0))

        tipo_tempo = request.form.get('tipo_tempo', 'meses')
        if tipo_tempo == "anos":
            tempo *= 12

        # 🔥 taxa automática
        taxa_base, _ = calcular_resultado(valor, tipo, tempo)

        # 🔥 percentual do slider
        percentual = float(request.form.get('percentual_taxa', 100))

        # 🔥 aplica percentual
        taxa_final = taxa_base * (percentual / 100)

        # 🔥 lucro
        lucro = valor * taxa_final * (tempo / 12)

        cursor.execute("""
            INSERT INTO investimentos (
                usuario_id, tipo, valor_investido, taxa, tempo, lucro, percentual
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            session['usuario_id'],
            tipo,
            valor,
            taxa_final * 100,
            tempo,
            lucro,
            percentual
        ))

        conn.commit()

    # 🔥 ISSO TEM QUE FICAR FORA DO IF
    cursor.execute(
        "SELECT * FROM investimentos WHERE usuario_id = ?",
        (session['usuario_id'],)
    )

    dados = cursor.fetchall()

    # 🔥 CONVERTE PARA DICIONÁRIO
    dados_formatados = []

    for d in dados:
        dados_formatados.append({
            "id": d["id"],  # 🔥 FALTAVA ISSO
            "tipo": d["tipo"],
            "valor_investido": d["valor_investido"],
            "taxa": d["taxa"],
            "tempo": d["tempo"],
            "lucro": d["lucro"],
            "percentual": d["percentual"]
        })

    conn.close()

    return render_template('simulador.html', investimentos=dados_formatados)