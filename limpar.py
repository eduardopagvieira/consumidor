"""
Limpeza das reclamações do Consumidor.gov.br.

Lê dados/consumidor_AAAA.csv.gz (gerado por baixar_consumidor.py) e grava
dados/tratados/reclamacoes_AAAA.csv.gz com nomes de coluna padronizados e colunas de análise.

Colunas criadas
    mes               mês da finalização da reclamação (AAAA-MM)
    procurou_empresa  o consumidor tentou resolver com a empresa antes de reclamar
    respondida        a empresa respondeu dentro do prazo
    avaliada          o consumidor avaliou o atendimento (só 1 em cada 3 avalia)
    resolvida         avaliada como resolvida (vazio quando não avaliada)

As duas colunas que só aparecem em setembro de 2025 (Interação com Judiciário e
Último Complemento Consumidor) ficam de fora porque não existem nos outros meses.

Uso
    python limpar.py
    python limpar.py --ano 2024
"""

import argparse
from pathlib import Path

import pandas as pd

RENOMEAR = {
    "Região": "regiao", "UF": "uf", "Cidade": "cidade", "Sexo": "sexo", "Faixa Etária": "faixa_etaria",
    "Data Finalização": "data_finalizacao", "Tempo Resposta": "tempo_resposta_dias",
    "Nome Fantasia": "empresa", "Segmento de Mercado": "segmento", "Área": "area", "Assunto": "assunto",
    "Grupo Problema": "grupo_problema", "Problema": "problema", "Como Comprou Contratou": "canal_compra",
    "Procurou Empresa": "procurou_empresa", "Respondida": "respondida", "Situação": "situacao",
    "Avaliação Reclamação": "avaliacao", "Nota do Consumidor": "nota",
}
REGIOES = {"N": "Norte", "NE": "Nordeste", "CO": "Centro-Oeste", "SE": "Sudeste", "S": "Sul"}
FAIXAS = ["até 20 anos", "entre 21 a 30 anos", "entre 31 a 40 anos", "entre 41 a 50 anos",
          "entre 51 a 60 anos", "entre 61 a 70 anos", "mais de 70 anos"]


def limpar(ano):
    entrada = Path(f"dados/consumidor_{ano}.csv.gz")
    saida = Path(f"dados/tratados/reclamacoes_{ano}.csv.gz")
    saida.parent.mkdir(parents=True, exist_ok=True)

    tipos = {c: "category" for c in RENOMEAR if c not in ("Tempo Resposta", "Nota do Consumidor", "Data Finalização")}
    t = pd.read_csv(entrada, encoding="utf-8-sig", usecols=list(RENOMEAR), dtype=tipos)
    t = t.rename(columns=RENOMEAR)
    print(f"{len(t)} reclamações lidas")

    t["data_finalizacao"] = pd.to_datetime(t["data_finalizacao"], errors="coerce")
    t["mes"] = t["data_finalizacao"].dt.strftime("%Y-%m")
    t["tempo_resposta_dias"] = pd.to_numeric(t["tempo_resposta_dias"], errors="coerce")
    t["nota"] = pd.to_numeric(t["nota"], errors="coerce")

    t["regiao"] = t["regiao"].map(REGIOES).astype("category")
    t["sexo"] = t["sexo"].map({"M": "Masculino", "F": "Feminino", "O": "Outro"}).astype("category")
    t["faixa_etaria"] = pd.Categorical(t["faixa_etaria"], categories=FAIXAS, ordered=True)

    for c in ("procurou_empresa", "respondida"):
        t[c] = t[c].map({"S": True, "N": False}).astype("boolean")
    t["avaliada"] = t["avaliacao"].isin(["Resolvida", "Não Resolvida"])
    t["resolvida"] = t["avaliacao"].map({"Resolvida": True, "Não Resolvida": False}).astype("boolean")

    problemas = {
        "datas inválidas": int(t["data_finalizacao"].isna().sum()),
        "fora do ano": int((t["data_finalizacao"].dt.year != int(ano)).sum()),
        "sem empresa": int(t["empresa"].isna().sum()),
        "nota sem avaliação": int((t["nota"].notna() & ~t["avaliada"]).sum()),
    }
    print("Conferências:", problemas)

    t.to_csv(saida, index=False, encoding="utf-8-sig", compression="gzip", date_format="%Y-%m-%d")
    print(f"{saida} salvo ({saida.stat().st_size / 1e6:.0f} MB, {t.shape[1]} colunas)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", default="2025")
    limpar(parser.parse_args().ano)
