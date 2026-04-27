from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database.banco import conectar
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

auth_bp = Blueprint("auth", __name__)

# 🔐 HASH FAKE (proteção contra enumeração de usuário)
FAKE_HASH = generate_password_hash("senha_fake")


# 🔒 DECORATOR DE PROTEÇÃO
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "usuario_id" not in session:
            flash("Por favor, faça login para acessar esta página.", "warning")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


# ---------------- LOGIN ----------------
@auth_bp.route("/", methods=["GET", "POST"])
def login():

    # 🔁 Evita login duplicado
    if "usuario_id" in session:
        return redirect(url_for("perfil.perfil"))

    if request.method == "POST":
        email = request.form.get("form-email")
        senha_digitada = request.form.get("form-senha")

        # 🔍 Validação básica
        if not email or not senha_digitada:
            flash("Preencha todos os campos.", "warning")
            return redirect(url_for("auth.login"))

        email = email.lower().strip()

        # 🔐 Conexão segura
        with conectar() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE email=?", (email,))
            usuario = cursor.fetchone()

        # 🔒 Proteção contra enumeração
        hash_senha = usuario["senha"] if usuario else FAKE_HASH

        if check_password_hash(hash_senha, senha_digitada) and usuario:
            # ✅ PADRÃO CORRETO (usuario_id)
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]

            return redirect(url_for("perfil.perfil"))

        flash("E-mail ou senha incorretos", "danger")

    return render_template("login.html")


# ---------------- CADASTRO ----------------
@auth_bp.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha_plana = request.form.get("senha")

        # 🔍 Validação
        if not nome or not email or not senha_plana:
            flash("Preencha todos os campos.", "warning")
            return redirect(url_for("auth.cadastro"))

        if len(senha_plana) < 6:
            flash("A senha deve ter pelo menos 6 caracteres.", "warning")
            return redirect(url_for("auth.cadastro"))

        email = email.lower().strip()

        # 🔐 Hash da senha
        senha_com_hash = generate_password_hash(senha_plana)

        try:
            with conectar() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
                    (nome, email, senha_com_hash)
                )
                conn.commit()

            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("auth.login"))

        except sqlite3.IntegrityError:
            flash("Este e-mail já está cadastrado.", "warning")

        except Exception:
            flash("Erro interno. Tente novamente.", "danger")

    return render_template("cadastro.html")


@auth_bp.route("/excluir_conta", methods=["POST"])
@login_required
def excluir_conta():
    usuario_id = session.get("usuario_id")

    try:
        conn = conectar()
        cursor = conn.cursor()

        # Opcional: Deletar manualmente se não houver CASCADE no banco
        cursor.execute("DELETE FROM empresas WHERE usuario_id = ?", (usuario_id,))
        cursor.execute("DELETE FROM historico WHERE usuario_id = ?", (usuario_id,))
        cursor.execute("DELETE FROM investimentos WHERE usuario_id = ?", (usuario_id,))

        # Deleta o usuário
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))

        conn.commit()
        conn.close()

        session.clear()
        flash("Sua conta e todos os dados foram excluídos permanentemente.", "warning")
        return redirect(url_for("auth.login"))

    except Exception as e:
        print(f"Erro ao excluir conta: {e}")
        flash("Erro ao processar a exclusão da conta.", "danger")
        return redirect(url_for("historico.historico"))


@auth_bp.route("/alterar_perfil", methods=["POST"])
@login_required
def alterar_perfil():
    nova_senha = request.form.get("nova_senha")
    usuario_id = session.get("usuario_id")

    if nova_senha:
        hash_senha = generate_password_hash(nova_senha)
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET senha = ? WHERE id = ?", (hash_senha, usuario_id))
        conn.commit()
        conn.close()
        flash("Senha atualizada com sucesso!", "success")
    else:
        flash("Nenhuma alteração realizada.", "info")

    return redirect(url_for("historico.historico"))

# ---------------- LOGOUT ----------------
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("auth.login"))