from flask import Flask, render_template, session, request, redirect, url_for, flash
import os
from banco import conectar  # banco.py deve conter conectar() e criar_tabela()
import yfinance as yf
import pandas as pd

app = Flask(__name__)
app.secret_key = "chave_secreta"

# ------------------ LOGIN ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("form-email")
        senha = request.form.get("form-senha")
        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE email=? AND senha=?", (email, senha))
        usuario = cursor.fetchone()
        conn.close()
        if usuario:
            session["usuario"] = usuario['nome']
            return redirect(url_for("perfil"))
        flash("Erro no login", "danger")
    return render_template("login.html")


import pandas as pd


@app.route("/taxas_tesouro")
def taxas_tesouro():
    # Link direto para o CSV oficial do Tesouro Direto
    url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"

    try:
        # O arquivo usa ';' como separador e ',' para decimais
        df = pd.read_csv(url, sep=';', decimal=',', encoding='utf-8')

        # Filtramos pela Data Base mais recente para pegar as taxas de hoje
        ultima_data = df['Data Base'].max()
        df_hoje = df[df['Data Base'] == ultima_data].drop_duplicates('Tipo Titulo')

        # Selecionamos apenas o necessário para o seu simulador
        # 'Taxa Compra Manha' é a rentabilidade oferecida
        resultado = []
        for _, row in df_hoje.iterrows():
            resultado.append({
                "titulo": row['Tipo Titulo'],
                "taxa": row['Taxa Compra Manha']
            })

        return resultado  # Retorna a lista para o JavaScript do simulador
    except Exception as e:
        print(f"Erro ao buscar Tesouro: {e}")
        return []


# ------------------ CADASTRO DE USUÁRIO ------------------
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form.get("nome")
        email = request.form.get("email")
        senha = request.form.get("senha")
        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)", (nome, email, senha))
            conn.commit()
            flash("Cadastro realizado com sucesso!", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Erro ao cadastrar: {e}", "danger")
        finally:
            conn.close()
    return render_template("cadastro.html")

# ------------------ PERFIL ------------------
# ------------------ PERFIL (INDIVIDUAL POR USUÁRIO) ------------------
@app.route("/perfil")
def perfil():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    # Adicionado WHERE usuario = ? para mostrar apenas os dados de quem está logado
    cursor.execute("SELECT * FROM empresas WHERE usuario = ?", (session["usuario"],))
    empresas = cursor.fetchall()
    conn.close()

    return render_template("perfil.html", usuario=session["usuario"], empresas=empresas, os=os)


# ------------------ UPLOAD DE FOTO ------------------
@app.route("/upload_foto", methods=["POST"])
def upload_foto():
    if "usuario" not in session:
        return redirect(url_for("login"))
    if "foto" not in request.files:
        flash("Nenhum arquivo enviado!", "danger")
        return redirect(url_for("perfil"))

    foto = request.files["foto"]
    if foto.filename == "":
        flash("Nenhum arquivo selecionado!", "warning")
        return redirect(url_for("perfil"))

    filename = session["usuario"] + ".png"
    caminho = os.path.join("static/perfil", filename)
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    foto.save(caminho)
    flash("Foto atualizada com sucesso!", "success")
    return redirect(url_for("perfil"))

# ------------------ CADASTRO DE AÇÕES ------------------
@app.route("/cadastro_de_acao")
def cadastro_de_acao():
    if "usuario" not in session:

        return redirect(url_for("login"))
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM empresas WHERE usuario = ?", (session["usuario"],))
    empresas = cursor.fetchall()
    conn.close()
    return render_template("cadastro_acao.html", empresas=empresas)



@app.route('/simulador', methods=['GET', 'POST'], endpoint='simulador')
def investimentos():
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == 'POST':
        tipo = request.form.get('tipo')
        valor = float(request.form.get('valor_investido', 0))
        taxa = float(request.form.get('taxa', 0))
        tempo = int(request.form.get('tempo', 0))

        # cálculo simples (juros simples mensal)
        lucro = valor * ((taxa / 100) / 12) * tempo

        cursor.execute("""
            INSERT INTO investimentos (usuario, tipo, valor_investido, taxa, tempo, lucro)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (session['usuario'], tipo, valor, taxa, tempo, lucro))

        conn.commit()

    cursor.execute("SELECT * FROM investimentos WHERE usuario = ?", (session['usuario'],))
    dados = cursor.fetchall()
    conn.close()

    return render_template('simulador.html', investimentos=dados)

# ------------------ CADASTRAR EMPRESA ------------------
@app.route("/cadastrar_empresa", methods=["POST"])
def cadastrar_empresa():
    if "usuario" not in session:
        flash("Você precisa estar logado!", "warning")
        return redirect(url_for("login"))

    try:
        # Captura dados do formulário
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
            return redirect(url_for("perfil"))

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO empresas (
                usuario, ticker, empresa, setor, num_acoes, preco_acao,
                lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session["usuario"],
            ticker, empresa_nome, setor, num_acoes, preco_acao,
            lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao
        ))
        conn.commit()
        conn.close()
        flash("Empresa cadastrada com sucesso!", "success")
    except Exception as e:
        print("ERRO AO CADASTRAR EMPRESA:", e)
        flash(f"Erro ao cadastrar empresa: {e}", "danger")

    return redirect(url_for("perfil"))

# ------------------ EDITAR EMPRESA ------------------
@app.route("/editar_empresa/<int:id>", methods=["GET", "POST"])
def editar_empresa(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

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
            WHERE id=?
        """, (
            ticker, empresa_nome, setor, num_acoes, preco_acao,
            lucro_liquido, patrimonio, ativos, divida, lote, tipo_acao, id
        ))
        conn.commit()
        conn.close()
        flash("Empresa atualizada com sucesso!", "success")
        return redirect(url_for("perfil"))

    cursor.execute("SELECT * FROM empresas WHERE id = ?", (id,))
    empresa = cursor.fetchone()
    conn.close()
    return render_template("editar_acao.html", empresa=empresa)


# ------------------ EDITAR INVESTIMENTO ------------------
@app.route("/editar_simulador/<int:id>", methods=["GET", "POST"])
def editar_simulador(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()

    if request.method == "POST":
        tipo = request.form.get("tipo")
        valor = float(request.form.get("valor_investido", 0))
        taxa = float(request.form.get("taxa", 0))
        tempo = int(request.form.get("tempo", 0))
        lucro = valor * ((taxa / 100) / 12) * tempo  # mesmo cálculo do POST do simulador

        cursor.execute("""
            UPDATE investimentos
            SET tipo=?, valor_investido=?, taxa=?, tempo=?, lucro=?
            WHERE id=? AND usuario=?
        """, (tipo, valor, taxa, tempo, lucro, id, session["usuario"]))
        conn.commit()
        conn.close()
        flash("Investimento atualizado com sucesso!", "success")
        return redirect(url_for("simulador"))

    # Buscar os dados do investimento
    cursor.execute("SELECT * FROM investimentos WHERE id=? AND usuario=?", (id, session["usuario"]))
    investimento = cursor.fetchone()
    conn.close()
    return render_template("editar_simulador.html", investimento=investimento)

# ------------------ EXCLUIR INVESTIMENTO ------------------
@app.route("/excluir_simulador/<int:id>")
def excluir_simulador(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM investimentos WHERE id=? AND usuario=?", (id, session["usuario"]))
    conn.commit()
    conn.close()
    flash("Investimento excluído com sucesso!", "success")
    return redirect(url_for("simulador"))


# ------------------ EXCLUIR EMPRESA ------------------
@app.route("/excluir_empresa/<int:id>")
def excluir_empresa(id):
    if "usuario" not in session:
        return redirect(url_for("login"))

    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM empresas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    flash("Empresa excluída com sucesso!", "success")
    return redirect(url_for("cadastro_de_acao"))


@app.route("/buscar_acao/<ticker>")
def buscar_acao(ticker):
    if not ticker.endswith(".SA"):
        ticker += ".SA"

    try:
        acao = yf.Ticker(ticker)
        info = acao.info

        return {
            "nome": info.get("longName"),
            "preco": info.get("currentPrice") or info.get("regularMarketPrice"),
            "setor": info.get("sector"),
            "lucro_liquido": info.get("netIncomeToCommon"),
            "patrimonio": info.get("totalStockholderEquity"),
            "ativos": info.get("totalAssets"),
            "divida": info.get("totalDebt")
        }
    except:
        return {"erro": "Não encontrado"}


# ------------------ LOGOUT ------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado com sucesso!", "success")
    return redirect(url_for("login"))

# ------------------ RODAR ------------------
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)