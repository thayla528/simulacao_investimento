from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar
from routes.auth import login_required
from services.calculos import calcular_lucro

simulador_bp = Blueprint("simulador", __name__)


# ------------------ EXCLUIR SIMULADOR ------------------
@simulador_bp.route("/excluir_simulador/<int:id>")
@login_required
def excluir_simulador(id):
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    try:
        conn = conectar()
        cursor = conn.cursor()

        # garante que só remove dados do usuário logado
        cursor.execute(
            "DELETE FROM investimentos WHERE id = ? AND usuario = ?",
            (id, session["usuario"])
        )

        conn.commit()
        conn.close()

        flash("Investimento excluído com sucesso!", "success")

    except Exception as e:
        print("ERRO AO EXCLUIR SIMULADOR:", e)
        flash("Erro ao excluir investimento!", "danger")

    return redirect(url_for("simulador.simulador"))


# ------------------ SIMULADOR ------------------
@simulador_bp.route("/simulador", methods=["GET", "POST"])
@login_required
def investimentos():
    if "usuario" not in session:
        return redirect(url_for("auth.login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor_investido', 0))
        taxa = float(request.form.get('taxa', 0))
        tempo = int(request.form.get('tempo', 0))

        lucro = calcular_lucro(valor, taxa, tempo)

        cursor.execute("""
            INSERT INTO investimentos (usuario, tipo, valor_investido, taxa, tempo, lucro)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['usuario'], tipo, valor, taxa, tempo, lucro))

        conn.commit()

    cursor.execute("SELECT * FROM investimentos WHERE usuario = ?", (session['usuario'],))
    dados = cursor.fetchall()
    conn.close()

    return render_template('simulador.html', investimentos=dados)