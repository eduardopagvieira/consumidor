"""
Organiza e junta os dados abertos do Consumidor.gov.br (reclamações finalizadas).

Por que não baixa sozinho: o site usa uma proteção anti-robô (F5) que recusa
requisições feitas por script. Os zips mensais precisam ser baixados pelo navegador.
Use links_2025.html (um link por mês) e depois rode este script.

Uso:
    python baixar_consumidor.py              # pega os zips de 2025 em Downloads, confere e junta
    python baixar_consumidor.py --ano 2024   # outro ano (os zips precisam estar baixados)

Saídas:
    dados/brutos/finalizadas_AAAA-MM.zip     arquivos originais, nunca editados
    dados/consumidor_AAAA.csv                todos os meses juntos numa tabela
"""

import argparse
import io
import shutil
import zipfile
from pathlib import Path

import pandas as pd

PASTA = Path("dados/brutos")
AQUI = Path(__file__).resolve().parent
# Lugares onde o navegador pode ter salvo os zips
ORIGENS = [Path.home() / "Downloads", AQUI, AQUI.parent, AQUI.parent.parent]

# Tamanhos publicados no site (bytes), para conferir se o download veio inteiro
TAMANHOS_2025 = {
    "01": 5082765, "02": 5313999, "03": 4875998, "04": 5685648,
    "05": 5843771, "06": 6304467, "07": 6875680, "08": 7293932,
    "09": 6159326, "10": 8275619, "11": 6435499, "12": 8898404,
}


def trazer_de_downloads(ano):
    """Move para dados/brutos os zips do ano salvos em Downloads ou nas pastas acima (inclusive 'nome (1).zip')."""
    PASTA.mkdir(parents=True, exist_ok=True)
    for pasta in ORIGENS:
        for origem in sorted(pasta.glob(f"finalizadas_{ano}-*.zip")):
            nome = origem.name.split(" (")[0].removesuffix(".zip") + ".zip"
            destino = PASTA / nome
            if not destino.exists():
                shutil.move(str(origem), destino)
                print(f"  movido de {pasta}: {nome}")


def conferir(ano):
    zips = sorted(PASTA.glob(f"finalizadas_{ano}-*.zip"))
    meses = {z.stem[-2:] for z in zips}
    faltam = sorted(set(f"{m:02d}" for m in range(1, 13)) - meses)
    if faltam:
        print(f"Faltam os meses: {', '.join(faltam)}  (baixe pelo links_{ano}.html)")
    if ano == "2025":
        for z in zips:
            esperado = TAMANHOS_2025.get(z.stem[-2:])
            if esperado and z.stat().st_size != esperado:
                print(f"  ATENÇÃO: {z.name} tem {z.stat().st_size} bytes, esperado {esperado} (download incompleto?)")
    return zips


def ler_csv_do_zip(caminho):
    with zipfile.ZipFile(caminho) as z:
        internos = [n for n in z.namelist() if n.lower().endswith(".csv")]
        if not internos:
            raise ValueError(f"{caminho.name} não tem CSV dentro: {z.namelist()}")
        bruto = z.read(internos[0])
    for codificacao in ("utf-8-sig", "latin1"):
        try:
            texto = bruto.decode(codificacao)
            break
        except UnicodeDecodeError:
            continue
    separador = ";" if texto[:2000].count(";") > texto[:2000].count(",") else ","
    tabela = pd.read_csv(io.StringIO(texto), sep=separador, dtype=str, low_memory=False)
    tabela.insert(0, "arquivo_origem", caminho.name)
    return tabela


def juntar(zips, ano):
    partes = []
    for z in zips:
        t = ler_csv_do_zip(z)
        print(f"  {z.name}: {len(t)} linhas, {t.shape[1] - 1} colunas")
        partes.append(t)
    tabela = pd.concat(partes, ignore_index=True)
    saida = Path(f"dados/consumidor_{ano}.csv")
    tabela.to_csv(saida, index=False, encoding="utf-8-sig")
    print(f"{len(tabela)} reclamações e {tabela.shape[1]} colunas salvas em {saida}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ano", default="2025")
    args = parser.parse_args()

    trazer_de_downloads(args.ano)
    zips = conferir(args.ano)
    if zips:
        juntar(zips, args.ano)
    else:
        print(f"Nenhum zip de {args.ano} encontrado em {PASTA} nem em Downloads.")
