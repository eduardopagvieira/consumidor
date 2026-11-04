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
LARANJA = "#eb6834"

# Grupos usados na comparação entre bancos tradicionais e digitais (cartões do mesmo grupo entram junto)
BANCOS_TRADICIONAIS = {
    "Banco Santander": "Santander", "Banco do Brasil": "Banco do Brasil", "Ourocard": "Banco do Brasil",
    "Banco Bradesco": "Bradesco", "Bradesco Cartões": "Bradesco", "Bradescard": "Bradesco",
    "Caixa Econômica Federal": "Caixa", "Banco Itaú Unibanco": "Itaú", "Cartões Itaú": "Itaú",
}
BANCOS_DIGITAIS = {
    "Nubank": "Nubank", "Banco Inter (Banco Intermedium)": "Inter", "C6 Bank": "C6 Bank",
    "Mercado Pago": "Mercado Pago", "PicPay": "PicPay", "Will Bank": "Will Bank", "NEON Financeira": "Neon",
    "Pagseguro": "PagBank", "PagBank (Antiga PagSeguro)": "PagBank",
}

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


def literatura(t, ano):
    """Indicadores que dialogam com os estudos sobre o Consumidor.gov.br (ver README)."""
    total = len(t)
    resolvidas = (t["resolvida"] == True).sum()
    nao_avaliadas = (~t["avaliada"]).sum()

    # Três formas de medir a solução. A plataforma conta as não avaliadas como resolvidas.
    medidas = {
        "oficial (resolvidas + não avaliadas, sobre o total)": (resolvidas + nao_avaliadas) / total,
        "entre as avaliadas (usado neste projeto)": resolvidas / t["avaliada"].sum(),
        "estrita (resolvidas sobre o total)": resolvidas / total,
    }
    pd.Series(medidas, name="indice_solucao").rename_axis("medida").to_csv(
        RESULTADOS / "tres_medidas_de_solucao.csv", encoding="utf-8-sig")

    emp = t.groupby("empresa", observed=True).agg(reclamacoes=("empresa", "size"), avaliadas=("avaliada", "mean"),
                                                 resolvidas=("resolvida", lambda s: (s == True).sum()))
    emp["indice_oficial"] = (emp["resolvidas"] + emp["reclamacoes"] * (1 - emp["avaliadas"])) / emp["reclamacoes"]
    emp["indice_avaliadas"] = emp["resolvidas"] / (emp["reclamacoes"] * emp["avaliadas"])
    grandes = emp[emp["reclamacoes"] >= MIN_EMPRESA].copy()
    grandes["posicao_oficial"] = grandes["indice_oficial"].rank(ascending=False).astype(int)
    grandes["posicao_avaliadas"] = grandes["indice_avaliadas"].rank(ascending=False).astype(int)
    grandes.sort_values("indice_oficial", ascending=False).to_csv(
        RESULTADOS / "empresas_indice_oficial_e_avaliadas.csv", encoding="utf-8-sig")
    correl = grandes[["indice_oficial", "indice_avaliadas"]].corr(method="spearman").iloc[0, 1]
    correl_aval = grandes[["avaliadas", "indice_oficial"]].corr(method="spearman").iloc[0, 1]

    top = emp.sort_values("reclamacoes", ascending=False).head(20).sort_values("indice_avaliadas")
    fig, ax = plt.subplots(figsize=(9, 8.2))
    y = np.arange(len(top))
    ax.hlines(y, top["indice_avaliadas"], top["indice_oficial"], color=EIXO, linewidth=2)
    ax.plot(top["indice_avaliadas"], y, "o", color=AZUL, markersize=8, markeredgecolor=SUPERFICIE,
            markeredgewidth=2, label="Resolvidas entre as avaliadas")
    ax.plot(top["indice_oficial"], y, "o", color=LARANJA, markersize=8, markeredgecolor=SUPERFICIE,
            markeredgewidth=2, label="Índice oficial (não avaliadas contam como resolvidas)")
    for i, (_, l) in enumerate(top.iterrows()):
        ax.text(l["indice_oficial"] + 0.012, i, f"{pct(l['avaliadas'])} avaliadas", va="center", fontsize=8.5,
                color=TINTA_2)
    ax.set_yticks(y, [curto(k, 34) for k in top.index], color=TINTA)
    ax.set_xlim(0, 1.12)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pct(v)))
    ax.grid(axis="x", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    ax.legend(frameon=False, loc="lower left", fontsize=9, bbox_to_anchor=(0, -0.13), ncol=2)
    finalizar(fig, ax, "O índice oficial infla a solução de quem tem poucas avaliações",
              f"Duas medidas do índice de solução, 20 empresas com mais reclamações em {ano}", "06_indice_oficial.png")

    # Distribuição das notas (formato em J das avaliações online)
    notas = t.loc[t["avaliada"], "nota"].value_counts(normalize=True).sort_index()
    notas.rename("parcela").to_csv(RESULTADOS / "distribuicao_notas.csv", encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(notas.index, notas.to_numpy(), width=0.62, color=AZUL, edgecolor=SUPERFICIE, linewidth=1)
    for k, v in notas.items():
        ax.text(k, v + 0.008, pct(v), ha="center", va="bottom", fontsize=9.5, color=TINTA)
    ax.set_xticks(notas.index, [f"Nota {int(k)}" for k in notas.index], color=TINTA)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pct(v)))
    ax.grid(axis="y", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    finalizar(fig, ax, "Quem avalia tende aos extremos",
              f"Distribuição das notas dadas pelos {pct(t['avaliada'].mean())} de consumidores que avaliaram, {ano}",
              "07_distribuicao_notas.png")

    # Bancos tradicionais e digitais
    grupos = {**{k: (v, "Tradicional") for k, v in BANCOS_TRADICIONAIS.items()},
              **{k: (v, "Digital") for k, v in BANCOS_DIGITAIS.items()}}
    b = t[t["empresa"].isin(grupos.keys())].copy()
    b["empresa"] = b["empresa"].astype(str)
    b["banco"] = b["empresa"].map(lambda e: grupos[e][0])
    b["tipo"] = b["empresa"].map(lambda e: grupos[e][1])
    por_banco = indicadores(b, "banco")
    por_banco["tipo"] = por_banco.index.map({v: tp for v, tp in grupos.values()})
    por_banco.to_csv(RESULTADOS / "bancos_tradicionais_e_digitais.csv", encoding="utf-8-sig")
    por_tipo = indicadores(b, "tipo")
    por_tipo.to_csv(RESULTADOS / "bancos_por_tipo.csv", encoding="utf-8-sig")

    r = por_banco.sort_values("indice_solucao")
    fig, ax = plt.subplots(figsize=(9, 6))
    y = np.arange(len(r))
    cores = [LARANJA if tp == "Digital" else AZUL for tp in r["tipo"]]
    ax.barh(y, r["indice_solucao"], height=0.62, color=cores, edgecolor=SUPERFICIE, linewidth=1)
    for i, (_, l) in enumerate(r.iterrows()):
        ax.text(l["indice_solucao"] + 0.008, i, f"{pct(l['indice_solucao'])}  ({mil(l['reclamacoes'])} reclamações)",
                va="center", fontsize=9, color=TINTA_2)
    ax.set_yticks(y, r.index, color=TINTA)
    ax.set_xlim(0, r["indice_solucao"].max() * 1.45)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: pct(v)))
    ax.grid(axis="x", color=GRADE, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(length=0)
    ax.spines["left"].set_visible(False)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=AZUL, label="Banco tradicional"), Patch(color=LARANJA, label="Banco digital ou carteira")],
              frameon=False, loc="lower right", fontsize=9)
    finalizar(fig, ax, "Ser digital não garante resolver mais",
              f"Resolvidas entre as avaliadas, grandes bancos e instituições digitais, {ano}", "08_bancos.png")

    return {
        "índice de solução oficial (não avaliadas contam como resolvidas)": pct(medidas[list(medidas)[0]]),
        "índice de solução entre as avaliadas": pct(medidas[list(medidas)[1]]),
        "índice de solução estrito (resolvidas sobre o total)": pct(medidas[list(medidas)[2]]),
        "correlação de postos entre índice oficial e entre avaliadas (empresas com 5 mil+)": f"{correl:.2f}".replace(".", ","),
        "correlação de postos entre taxa de avaliação e índice oficial": f"{correl_aval:.2f}".replace(".", ","),
        "notas 1 ou 5 entre as avaliações": pct(notas.get(1, 0) + notas.get(5, 0)),
        "solução entre avaliadas, bancos tradicionais": pct(por_tipo.loc["Tradicional", "indice_solucao"]),
        "solução entre avaliadas, bancos digitais": pct(por_tipo.loc["Digital", "indice_solucao"]),
        "solução entre avaliadas, digitais sem o Nubank":
            pct(b.loc[(b["tipo"] == "Digital") & (b["banco"] != "Nubank"), "resolvida"].mean()),
        "nota média, bancos tradicionais": f"{por_tipo.loc['Tradicional', 'nota_media']:.2f}".replace(".", ","),
        "nota média, bancos digitais": f"{por_tipo.loc['Digital', 'nota_media']:.2f}".replace(".", ","),
        "solução entre avaliadas, procurou a empresa antes": pct(t.loc[t["procurou_empresa"] == True, "resolvida"].mean()),
        "solução entre avaliadas, não procurou antes": pct(t.loc[t["procurou_empresa"] == False, "resolvida"].mean()),
    }


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

    resumo.update(literatura(t, ano))
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
