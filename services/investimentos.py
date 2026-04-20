import yfinance as yf
from services.calculos import calcular_lucro


def taxa_automatica(tipo):
    try:
        ativo = yf.Ticker(tipo)
        hist = ativo.history(period="1y")

        if hist.empty:
            return 0.10

        inicio = hist["Close"].iloc[0]
        fim = hist["Close"].iloc[-1]

        retorno = (fim - inicio) / inicio
        retorno = max(min(retorno, 1), -0.5)

        return retorno

    except:
        return 0.10


def calcular_resultado(valor, tipo, tempo):
    taxa = taxa_automatica(tipo)
    lucro = calcular_lucro(valor, taxa * 100, tempo)
    return taxa, lucro