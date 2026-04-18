from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

auth_bp = Blueprint("auth", __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("form-email")
        senha_digitada = request.form.get("form-senha")

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
        usuario = cursor.fetchone()
        conn.close()

        if usuario and check_password_hash(usuario['senha'], senha_digitada):
            # AGORA SALVA ID + NOME
            session["usuario_id"] = usuario['id']
            session["usuario"] = usuario['nome']

            return redirect(url_for("perfil.perfil"))

        flash("E-mail ou senha incorretos", "danger")

    return render_template("login.html")

@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha_plana = request.form.get("senha")

        senha_com_hash = generate_password_hash(senha_plana)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                (nome, email, senha_com_hash)
            )
            conn.commit()
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "danger")
        finally:
            conn.close()

    return render_template("cadastro.html")

@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("auth.login"))