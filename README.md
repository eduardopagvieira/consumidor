# Reclamações no Consumidor.gov.br

Projeto em andamento. Etapa atual é a coleta de dados.

## Pergunta

Quais setores e empresas concentram as reclamações dos consumidores, e quais resolvem melhor? Como tempo de resposta, índice de solução e nota do consumidor variam entre segmentos? O que os consumidores mais relatam?

## Fonte

Dados abertos do Consumidor.gov.br, da Secretaria Nacional do Consumidor (`https://www.consumidor.gov.br/pages/dadosabertos/externo/`).

O site publica um zip por mês com as reclamações finalizadas. Em 2025 são 2.328.863 reclamações, com região, UF, cidade, sexo e faixa etária do consumidor, empresa, segmento, assunto, problema, tempo de resposta, situação, avaliação e nota.

Observações sobre os dados de 2025
* O volume cresce ao longo do ano, de cerca de 149 mil reclamações em janeiro para 275 mil em dezembro.
* Setembro traz duas colunas a mais (Interação com Judiciário e Último Complemento Consumidor), que ficam vazias nos outros meses.
* A nota do consumidor falta em 67% das reclamações, porque a avaliação é opcional.

## Método

1. Os zips mensais são baixados pelo navegador. O site tem uma proteção contra robôs que recusa downloads feitos por script, então `links_2025.html` reúne os links diretos dos 12 meses.
2. `baixar_consumidor.py` encontra os zips (em Downloads ou nas pastas do projeto), move para `dados/brutos/`, confere o tamanho de cada um com o publicado no site e junta tudo em `dados/consumidor_2025.csv`, com uma coluna indicando o arquivo de origem.

Próximas etapas são limpeza, indicadores por setor e empresa e análise do texto das reclamações.

## Como rodar

1. Abra `links_2025.html` no navegador e baixe os 12 arquivos.
2. Rode o script.

```bash
pip install -r requirements.txt
python baixar_consumidor.py              # 2025
python baixar_consumidor.py --ano 2024   # outro ano, com os zips já baixados
```

No Windows com Miniconda, use `rodar_consumidor.bat`.

Os dados não ficam no repositório.
