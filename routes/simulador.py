from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar
from routes.auth import login_required
from services.calculos import calcular_lucro

simulador_bp = Blueprint("simulador", __name__)


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


# ------------------ SIMULADOR ------------------
@simulador_bp.route("/simulador", methods=["GET", "POST"])
@login_required
def investimentos():
    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor_investido', 0))
        taxa = float(request.form.get('taxa', 0))
        tempo = int(request.form.get('tempo', 0))

        lucro = calcular_lucro(valor, taxa, tempo)

        cursor.execute("""
            INSERT INTO investimentos (
                usuario_id, tipo, valor_investido, taxa, tempo, lucro
            )
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            session['usuario_id'],
            tipo, valor, taxa, tempo, lucro
        ))

        conn.commit()

    cursor.execute(
        "SELECT * FROM investimentos WHERE usuario_id = ?",
        (session['usuario_id'],)
    )

    dados = cursor.fetchall()
    conn.close()

    return render_template('simulador.html', investimentos=dados)