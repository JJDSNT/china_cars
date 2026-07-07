# Fontes de Dados

| Fonte | Descricao | Formato | Local esperado | Periodicidade | Responsavel |
| --- | --- | --- | --- | --- | --- |
| ANFAVEA | Emplacamento/licenciamento de autoveiculos por empresa/marca e series mensais de totais | Excel | `data/raw/anfavea/` | Mensal/anual conforme publicacao | A definir |
| Comex Stat/MDIC | Comercio exterior por pais e NCM | CSV/API/exportacao da consulta | `data/raw/comex_stat/` | Mensal | A definir |
| CAAM | Associacao Chinesa de Fabricantes de Automoveis; dados da industria chinesa, producao, vendas e exportacoes | HTML/PDF/planilha, conforme publicacao | `data/raw/caam/` | Mensal | A definir |
| CPCA | Associacao Chinesa de Automoveis de Passageiros; dados de mercado de passageiros, rankings e relatorios mensais | HTML/PDF/planilha, conforme publicacao | `data/raw/cpca/` | Mensal | A definir |

## Convencoes

- Manter os arquivos originais em `data/raw/` sem edicao manual.
- Documentar encoding, delimitador, data de extracao e origem.
- Quando uma fonte mudar de layout, registrar a mudanca aqui e em `ops/metadata/datasets.yml`.
- Manter o arquivo bruto com nome que inclua fonte, periodo e data de extracao.

## Papel das fontes chinesas

CAAM e CPCA devem ser usadas como fontes auxiliares para contexto, classificacao e conciliacao da dinamica do mercado/exportacoes chinesas. Elas nao substituem:

- ANFAVEA, que permanece como fonte primaria para emplacamentos no Brasil.
- Comex Stat/MDIC, que permanece como fonte primaria para comercio exterior Brasil-China.
