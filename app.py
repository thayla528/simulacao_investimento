from flask import Flask, jsonify
import os
import pandas as pd

import sys
print(sys.executable)

from routes.auth import auth_bp
from routes.empresas import empresas_bp
from services.yfinance_service import yfinance_bp
from routes.simulador import simulador_bp
from routes.perfil import perfil_bp
from database.banco import criar_tabela

criar_tabela()

app = Flask(__name__)

app.secret_key = os.urandom(24)

# Blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(empresas_bp)
app.register_blueprint(yfinance_bp)
app.register_blueprint(simulador_bp)
app.register_blueprint(perfil_bp)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SECURE=False,  # True quando usar HTTPS
    SESSION_COOKIE_SAMESITE="Lax"
)

# ------------------ TESOURO DIRETO ------------------
@app.route("/taxas_tesouro")
def taxas_tesouro():
    url = "https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv"

    try:
        df = pd.read_csv(url, sep=';', decimal=',', encoding='utf-8')
        ultima_data = df['Data Base'].max()
        df_hoje = df[df['Data Base'] == ultima_data].drop_duplicates('Tipo Titulo')

        resultado = []
        for _, row in df_hoje.iterrows():
            resultado.append({
                "titulo": row['Tipo Titulo'],
                "taxa": row['Taxa Compra Manha']
            })

        return resultado
    except Exception as e:
        print(f"Erro ao buscar Tesouro: {e}")
        return []


# ------------------ RODAR ------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)