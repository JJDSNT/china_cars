# Relatorio de Analise

Data de execucao: 2026-07-07

## Escopo executado

Este relatorio responde a duas perguntas de pesquisa:

1. Evolucao mensal dos emplacamentos de carros chineses nos dados da ANFAVEA, de janeiro de 2021 ao mes mais recente disponivel no arquivo baixado de 2026.
2. Importacoes brasileiras originarias da China no Comex Stat/MDIC para os prefixos/codigos `8702`, `8703`, `8704`, `8706`, `8707`, `8708` e `87011`, de janeiro de 2021 a junho de 2026.

## Resultados ANFAVEA

Cobertura obtida: janeiro de 2021 a maio de 2026.

O recorte de marcas chinesas identificado nos arquivos anuais ANFAVEA inclui `Caoa Chery`, `Caoa Changan` e `Leapmotor`, conforme classificacao em `ops/metadata/brand_classification.yml`.

| Ano | Emplacamentos chineses | Total ANFAVEA | Participacao |
| --- | ---: | ---: | ---: |
| 2021 | 39.747 | 2.119.851 | 1,88% |
| 2022 | 35.034 | 2.104.460 | 1,66% |
| 2023 | 31.480 | 2.308.689 | 1,36% |
| 2024 | 60.933 | 2.634.904 | 2,31% |
| 2025 | 72.031 | 2.689.634 | 2,68% |
| 2026, jan-mai | 34.183 | 1.148.201 | 2,98% |

Comparacao acumulada janeiro-maio:

| Ano | Emplacamentos chineses | Total ANFAVEA | Participacao |
| --- | ---: | ---: | ---: |
| 2025, jan-mai | 23.516 | 986.157 | 2,38% |
| 2026, jan-mai | 34.183 | 1.148.201 | 2,98% |

Entre janeiro-maio de 2025 e janeiro-maio de 2026, o recorte de marcas chinesas coberto nos arquivos anuais ANFAVEA cresceu 45,4% em unidades emplacadas.

## Resultados Comex Stat/MDIC

Cobertura obtida: importacoes, China como pais de origem, janeiro de 2021 a junho de 2026.

| Ano | Valor FOB US$ | Kg liquido | Quantidade estatistica |
| --- | ---: | ---: | ---: |
| 2021 | 1.040.835.786 | 185.868.583 | 197.192.638 |
| 2022 | 1.298.117.388 | 211.949.624 | 216.565.513 |
| 2023 | 2.173.194.020 | 290.418.564 | 244.714.303 |
| 2024 | 4.692.243.885 | 541.046.581 | 307.354.368 |
| 2025 | 5.075.023.114 | 678.815.489 | 340.532.974 |
| 2026, jan-jun | 6.822.602.065 | 839.102.821 | 254.411.745 |

Comparacao acumulada janeiro-junho:

| Ano | Valor FOB US$ | Kg liquido | Quantidade estatistica |
| --- | ---: | ---: | ---: |
| 2025, jan-jun | 2.852.522.090 | 360.997.407 | 167.965.122 |
| 2026, jan-jun | 6.822.602.065 | 839.102.821 | 254.411.745 |

O valor FOB importado no recorte cresceu 139,2% no acumulado janeiro-junho de 2026 contra janeiro-junho de 2025.

Principais prefixos em 2026, janeiro-junho:

| Prefixo NCM | Valor FOB US$ |
| --- | ---: |
| 8703 | 5.608.528.247 |
| 8708 | 1.014.451.083 |
| 8704 | 178.061.098 |
| 8702 | 12.472.228 |
| 8707 | 6.103.850 |
| 87011 | 2.805.681 |
| 8706 | 179.878 |

## Limitacoes e decisoes metodologicas

- A ANFAVEA informa que nao disponibiliza estatisticas de autoveiculos detalhadas por modelo. O recorte de carros chineses foi feito por marca/empresa.
- Os arquivos anuais ANFAVEA usados no pipeline cobrem as marcas chinesas que aparecem nas abas de emplacamento por empresa. Marcas chinesas fora dessa estrutura anual podem exigir os arquivos especificos por importados/nacionais por marca para todos os anos, que nao estavam publicamente expostos na pagina HTML para 2021-2025 no momento da coleta.
- No Comex Stat, a entrega principal foi feita para importacoes do Brasil originarias da China. Exportacoes nao foram misturadas ao resultado principal porque a pergunta nao especificou o fluxo.
- O codigo `87011` foi tratado como prefixo de NCM. Esse ponto permanece marcado para validacao metodologica, pois NCM operacional possui 8 digitos.
- Os valores podem ser revisados pelas fontes oficiais.

## Entregaveis

- DuckDB: `data/processed/china_cars.duckdb`
- Excel: `outputs/excel/china_cars_outputs.xlsx`
- Dashboard: `dashboard/app.py`
- Tabelas finais:
  - `gold_anfavea_chinese_registrations_monthly`
  - `gold_anfavea_chinese_registrations_by_brand_monthly`
  - `gold_comex_china_automotive_monthly`
  - `gold_comex_china_automotive_by_prefix_monthly`
  - `gold_comex_china_automotive_by_ncm_monthly`

