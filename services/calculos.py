def calcular_lucro(valor, taxa, tempo):
    try:
        valor = float(valor)
        taxa = float(taxa)
        tempo = int(tempo)

        taxa_mensal = (taxa / 100) / 12
        lucro = valor * ((1 + taxa_mensal) ** tempo - 1)

        return round(lucro, 2)
    except:
        return 0