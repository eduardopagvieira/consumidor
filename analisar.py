"""
Análise das reclamações finalizadas no Consumidor.gov.br.

Lê dados/tratados/reclamacoes_AAAA.csv.gz (gerado por limpar.py) e produz

    resultados/*.csv   tabelas da análise (pequenas, ficam no repositório)
    figuras/*.png      gráficos usados no README

Indicadores (os mesmos usados pelo Consumidor.gov.br)
    índice de resposta   reclamações respondidas pela empresa / total
    índice de solução    avaliadas como resolvidas / avaliadas pelo consumidor
    satisfação           nota média de 1 a 5, entre as avaliadas
    tempo de resposta    média de dias até a resposta da empresa (prazo máximo de 10 dias)

Só cerca de 1 em cada 3 consumidores avalia o atendimento. O índice de solução e a nota
descrevem esse grupo, que pode ser diferente de quem não avalia.

Uso
    python analisar.py
    python analisar.py --ano 2024
"""

import argparse
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

RESULTADOS = Path("resultados")
FIGURAS = Path("figuras")
MIN_EMPRESA = 5000              # empresas com menos reclamações ficam fora do ranking

SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_2 = "#52514e"
APAGADO = "#898781"
GRADE = "#e1e0d9"
EIXO = "#c3c2b7"
AZUL = "#2a78d6"

plt.rcParams.update({
    "font.family": ["Segoe UI", "DejaVu Sans"],
    "font.size": 10,
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "axes.edgecolor": EIXO,
    "axes.labelcolor": TINTA_2,
    "xtick.color": APAGADO,
    "ytick.color": APAGADO,
    "text.color": TINTA,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.titlelocation": "left",
    "axes.titlesize": 13,
    "axes.titleweight": "bold",
    "axes.titlepad": 30,
})
FONTE = "Fonte: Consumidor.gov.br, Secretaria Nacional do Consumidor (dados abertos). Elaboração própria."


def pct(v, casas=0):
    return f"{v * 100:.{casas}f}%".replace(".", ",")


def inteiro(v):
    return f"{v:,.0f}".replace(",", ".")


def mil(v):
    return f"{v / 1000:.0f} mil" if v >= 1000 else inteiro(v)


def finalizar(fig, ax, titulo, sub, arquivo):
    ax.set_title(titulo)
    ax.annotate(sub, (0, 1), xycoords="axes fraction", xytext=(0, 8), textcoords="offset points",
                color=TINTA_2, fontsize=9.5, va="bottom")
    fig.text(0.01, 0.01, FONTE, color=APAGADO, fontsize=8, ha="left", va="bottom")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    fig.savefig(FIGURAS / arquivo, dpi=160)
    plt.close(fig)


def barras_h(serie, rotulos, titulo, sub, arquivo, formato=pct):
    serie = serie.sort_values()
    fig, ax = plt.subplots(figsize=(9, 0.4 * len(serie) + 1.7))
    y = np.arange(len(serie))
    ax.barh(y, serie.to_numpy(), height=0.62, color=AZUL, edgecolor=SUPERFICIE, linewidth=1)
    for i, (k, v) in enumerate(serie.items()):
        ax.text(v + serie.max() * 0.01, i, f"{formato(v)}  {rotulos.get(k, '')}".rstrip(), va="center",
                fontsize=9, color=TINTA_2)
    ax.set_yticks(y, serie.index, color=TINTA)
    ax.set_xlim(0, serie.max() * 1.32)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: formato(v)))
    ax.grid(axis="x", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    finalizar(fig, ax, titulo, sub, arquivo)


def indicadores(df, chave):
    g = df.groupby(chave, observed=True).agg(
        reclamacoes=("empresa", "size"),
        procurou_empresa=("procurou_empresa", "mean"),
        indice_resposta=("respondida", "mean"),
        tempo_resposta_dias=("tempo_resposta_dias", "mean"),
        pct_avaliadas=("avaliada", "mean"),
        indice_solucao=("resolvida", "mean"),
        nota_media=("nota", "mean"),
    )
    g["participacao"] = g["reclamacoes"] / len(df)
    return g.sort_values("reclamacoes", ascending=False)


SEGMENTOS_CURTOS = {
    "Bancos, Financeiras e Administradoras de Cartão": "Bancos, financeiras e cartões",
    "Operadoras de Telecomunicações (Telefonia, Internet, TV por assinatura)": "Telecomunicações",
    "Bancos de Dados e Cadastros de Consumidores": "Cadastros de consumidores",
    "Provedores de Conteúdo e Outros Serviços na Internet": "Serviços na internet",
    "Operadoras de Planos de Saúde e Administradoras de Benefícios": "Planos de saúde",
    "Empresas de Intermediação de Serviços / Negócios": "Intermediação de serviços",
    "Seguros, Capitalização e Previdência": "Seguros e previdência",
    "Empresas de Pagamento Eletrônico": "Pagamento eletrônico",
    "Empresas de Recuperação de Crédito": "Recuperação de crédito",
}


def curto(nome, limite=48):
    nome = str(nome)
    return nome if len(nome) <= limite else nome[: limite - 1].rstrip() + "…"


def analisar(ano):
    RESULTADOS.mkdir(exist_ok=True)
    FIGURAS.mkdir(exist_ok=True)

    categorias = ["regiao", "uf", "sexo", "faixa_etaria", "empresa", "segmento", "area", "assunto",
                  "grupo_problema", "problema", "canal_compra", "situacao", "avaliacao", "mes"]
    t = pd.read_csv(f"dados/tratados/reclamacoes_{ano}.csv.gz", encoding="utf-8-sig",
                    usecols=categorias + ["procurou_empresa", "respondida", "avaliada", "resolvida",
                                          "tempo_resposta_dias", "nota"],
                    dtype={**{c: "category" for c in categorias}, "procurou_empresa": "boolean",
                           "respondida": "boolean", "resolvida": "boolean"})
    total = len(t)
    avaliadas = t[t["avaliada"]]

    # Visão geral
    resumo = {
        "reclamações finalizadas": inteiro(total),
        "empresas reclamadas": inteiro(t["empresa"].nunique()),
        "procuraram a empresa antes": pct(t["procurou_empresa"].mean()),
        "índice de resposta": pct(t["respondida"].mean(), 1),
        "tempo médio de resposta (dias)": f"{t['tempo_resposta_dias'].mean():.1f}".replace(".", ","),
        "avaliadas pelo consumidor": pct(t["avaliada"].mean()),
        "índice de solução (entre avaliadas)": pct(avaliadas["resolvida"].mean()),
        "nota média (1 a 5)": f"{avaliadas['nota'].mean():.2f}".replace(".", ","),
        "notas 1": pct((avaliadas["nota"] == 1).mean()),
        "notas 5": pct((avaliadas["nota"] == 5).mean()),
    }

    # Mês
    por_mes = indicadores(t, "mes").sort_index()
    por_mes.to_csv(RESULTADOS / "por_mes.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    meses = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    x = np.arange(len(por_mes))
    ax.bar(x, por_mes["reclamacoes"], width=0.66, color=AZUL, edgecolor=SUPERFICIE, linewidth=1)
    for i in (0, len(por_mes) - 1):
        v = por_mes["reclamacoes"].iloc[i]
        ax.text(i, v * 1.015, mil(v), ha="center", va="bottom", fontsize=9, color=TINTA_2)
    ax.set_xticks(x, [meses[int(m[-2:]) - 1] for m in por_mes.index])
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: mil(v)))
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    crescimento = por_mes["reclamacoes"].iloc[-1] / por_mes["reclamacoes"].iloc[0] - 1
    finalizar(fig, ax, f"As reclamações cresceram {pct(crescimento)} ao longo de {ano}",
              f"Reclamações finalizadas por mês, {ano}", "01_volume_mensal.png")

    # Segmentos
    por_seg = indicadores(t, "segmento")
    por_seg.to_csv(RESULTADOS / "por_segmento.csv", encoding="utf-8-sig")
    top_seg = por_seg.head(12)
    rot_seg = {k: SEGMENTOS_CURTOS.get(k, curto(k)) for k in top_seg.index}
    barras_h(top_seg["participacao"].rename(index=rot_seg), {},
             f"Bancos e financeiras concentram {pct(top_seg['participacao'].iloc[0])} das reclamações",
             f"Parcela do total de {inteiro(total)} reclamações em {ano}, 12 segmentos com mais reclamações",
             "02_segmentos.png")
    taxa_geral = avaliadas["resolvida"].mean()
    barras_h(top_seg["indice_solucao"].rename(index=rot_seg), {},
             "Quanto se resolve depende muito do segmento",
             f"Resolvidas entre as avaliadas pelo consumidor, 12 maiores segmentos. Média geral {pct(taxa_geral)}",
             "03_solucao_segmentos.png")

    # Empresas
    por_emp = indicadores(t, "empresa")
    por_emp.to_csv(RESULTADOS / "por_empresa.csv", encoding="utf-8-sig")
    grandes = por_emp[por_emp["reclamacoes"] >= MIN_EMPRESA]
    grandes.to_csv(RESULTADOS / "ranking_empresas.csv", encoding="utf-8-sig")
    top_emp = por_emp.head(20)
    barras_h(top_emp["indice_solucao"].rename(index=lambda k: curto(k, 40)),
             {curto(k, 40): f"({mil(v)} reclamações)" for k, v in top_emp["reclamacoes"].items()},
             "Entre as maiores reclamadas, a solução varia de "
             f"{pct(top_emp['indice_solucao'].min())} a {pct(top_emp['indice_solucao'].max())}",
             f"Índice de solução das 20 empresas com mais reclamações em {ano}",
             "04_empresas.png")

    # Problemas
    por_grupo = indicadores(t, "grupo_problema")
    por_grupo.to_csv(RESULTADOS / "por_grupo_problema.csv", encoding="utf-8-sig")
    indicadores(t, "problema").head(30).to_csv(RESULTADOS / "top30_problemas.csv", encoding="utf-8-sig")
    barras_h(por_grupo["participacao"], {},
             f"{por_grupo.index[0]} responde por {pct(por_grupo['participacao'].iloc[0])} das reclamações",
             f"Parcela das reclamações por grupo de problema, {ano}", "05_grupos_problema.png")

    # Outros recortes, só em tabela
    for chave, arquivo in (("uf", "por_uf"), ("regiao", "por_regiao"), ("faixa_etaria", "por_faixa_etaria"),
                           ("sexo", "por_sexo"), ("canal_compra", "por_canal_compra"), ("area", "por_area")):
        indicadores(t, chave).to_csv(RESULTADOS / f"{arquivo}.csv", encoding="utf-8-sig")
    procurou = indicadores(t, "procurou_empresa")
    procurou.to_csv(RESULTADOS / "por_procurou_empresa.csv", encoding="utf-8-sig")

    pd.Series(resumo, name="valor").rename_axis("indicador").to_csv(RESULTADOS / "resumo.csv", encoding="utf-8-sig")

    cols = ["reclamacoes", "participacao", "indice_resposta", "tempo_resposta_dias", "indice_solucao", "nota_media"]
    print("Resumo")
    for k, v in resumo.items():
        print(f"  {k}: {v}")
    print("\nSegmentos (12 maiores)\n", top_seg[cols].round(3).to_string())
    print("\nEmpresas (20 maiores)\n", top_emp[cols].round(3).to_string())
    print("\nRanking (>= 5 mil) melhores\n", grandes.sort_values("indice_solucao", ascending=False)[cols].head(8).round(3).to_string())
    print("\nRanking (>= 5 mil) piores\n", grandes.sort_values("indice_solucao")[cols].head(8).round(3).to_string())
    print("\nGrupos de problema\n", por_grupo[cols].round(3).to_string())
    print("\nProcurou a empresa antes\n", procurou[cols].round(3).to_string())
    print("\nFaixa etária\n", indicadores(t, "faixa_etaria")[cols].round(3).to_string())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", default="2025")
    analisar(parser.parse_args().ano)
