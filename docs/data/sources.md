# Fontes de Dados

| Fonte | Descricao | Formato | Local esperado | Periodicidade | Responsavel |
| --- | --- | --- | --- | --- | --- |
| ANFAVEA | Emplacamento/licenciamento de autoveiculos por empresa/marca e series mensais de totais | Excel | `data/raw/anfavea/` | Mensal/anual conforme publicacao | A definir |
| Comex Stat/MDIC | Comercio exterior por pais e NCM | CSV/API/exportacao da consulta | `data/raw/comex_stat/` | Mensal | A definir |

## Convencoes

- Manter os arquivos originais em `data/raw/` sem edicao manual.
- Documentar encoding, delimitador, data de extracao e origem.
- Quando uma fonte mudar de layout, registrar a mudanca aqui e em `ops/metadata/datasets.yml`.
- Manter o arquivo bruto com nome que inclua fonte, periodo e data de extracao.
