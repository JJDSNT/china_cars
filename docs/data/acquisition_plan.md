# Plano de Aquisicao de Dados

## ANFAVEA

Fonte:

- Site ANFAVEA, secao Economia > Dados Estatisticos.
- Arquivos Excel anuais de autoveiculos.
- Arquivos especificos de emplacamento de nacionais e importados por empresa e marca.
- Series historicas mensais para conciliacao de totais.

Periodo:

- Inicio: 2021-01.
- Fim: mes mais recente de 2026 disponivel na ANFAVEA no momento da extracao.

Dados brutos esperados:

```text
data/raw/anfavea/
  2021/
  2022/
  2023/
  2024/
  2025/
  2026/
```

Campos alvo:

- ano_mes
- empresa
- marca
- origem do veiculo, quando disponivel
- segmento, quando disponivel
- emplacamentos
- arquivo_fonte
- data_extracao

Observacao:

A ANFAVEA informa que nao disponibiliza estatisticas detalhadas por modelo. O recorte de "carros chineses" deve ser feito por marca/empresa, usando classificacao mantida pelo projeto.

## Comex Stat/MDIC

Fonte:

- Comex Stat/MDIC.

Periodo:

- Inicio: 2021-01.
- Fim: 2026-06.

Filtros:

- Pais: China.
- Codigos: `8702`, `8703`, `8704`, `8706`, `8707`, `8708`, `87011`.
- Periodicidade: mensal.

Campos alvo:

- ano_mes
- fluxo
- pais
- codigo_ncm
- descricao_ncm
- valor_fob_usd
- kg_liquido
- quantidade_estatistica
- unidade_estatistica
- data_extracao

Pendencias:

- Confirmar importacao, exportacao ou ambos.
- Confirmar se os codigos serao tratados como prefixos de NCM ou como codigos completos.
- Confirmar o codigo `87011`.

