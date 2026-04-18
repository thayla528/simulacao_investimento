from flask import Blueprint


import yfinance as yf

yfinance_bp= Blueprint("yfinance", __name__)

def obter_preco_atual(ticker):
    try:
        # Formata o ticker para o padrão Yahoo Finance (Ex: PETR4 -> PETR4.SA)
        t = ticker.strip().upper()
        if not t.endswith('.SA'):
            t += '.SA'

        acao = yf.Ticker(t)
        # Puxa o histórico do último dia
        dados = acao.history(period="1d")

        if not dados.empty:
            # Retorna o preço de fechamento mais recente
            return round(dados['Close'].iloc[-1], 2)
        return None
    except Exception as e:
        print(f"Erro ao buscar ticker {ticker}: {e}")
        return None