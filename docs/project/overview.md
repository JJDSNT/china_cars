# Visao Geral do Projeto

## Objetivo

Responder, com rastreabilidade e qualidade profissional, a duas perguntas de pesquisa sobre a evolucao mensal do mercado brasileiro relacionado a carros chineses e ao comercio exterior de produtos automotivos com origem China.

As respostas finais devem ser reproduziveis, auditaveis e entregues em tres formatos:

- base analitica em DuckDB;
- planilhas Excel finais;
- visualizacao interativa.

## Perguntas de pesquisa

### I. Emplacamentos de carros chineses no Brasil

Qual a evolucao mensal dos emplacamentos de carros chineses, de acordo com os dados da ANFAVEA, entre janeiro de 2021 e o mes mais recente disponivel em 2026?

Fonte primaria planejada:

- ANFAVEA, arquivos Excel de dados estatisticos de autoveiculos.
- Prioridade para arquivos anuais de emplacamento/licenciamento por empresa e marca quando o objetivo for identificar marcas chinesas.
- Series historicas mensais da ANFAVEA como fonte de conciliacao de totais, quando aplicavel.

### II. Comercio exterior automotivo Brasil-China

Consultar a Comex Stat/MDIC filtrando o pais China e os codigos NCM informados para o periodo de janeiro de 2021 ate junho de 2026, em base mensal.

Fonte primaria planejada:

- Comex Stat/MDIC, consulta mensal por NCM e pais.
- CAAM e CPCA, como fontes auxiliares para contexto da industria chinesa, classificacao de marcas/fabricantes e validacao macro. Essas fontes nao substituem ANFAVEA nem Comex Stat/MDIC.

Filtros iniciais:

- Pais: China.
- Periodo: 2021-01 a 2026-06.
- Codigos informados: `8702`, `8703`, `8704`, `8706`, `8707`, `8708`, `87011`.

## Escopo

- Fontes incluidas: ANFAVEA e Comex Stat/MDIC.
- Periodo ANFAVEA: janeiro de 2021 ate o mes mais recente de 2026 disponivel na fonte.
- Periodo Comex Stat: janeiro de 2021 ate junho de 2026.
- Granularidade esperada: mensal.
- Recorte geografico: Brasil; para Comex Stat, relacao com China.
- Unidades esperadas: unidades emplacadas/licenciadas; valor FOB, kg liquido e quantidade estatistica para comercio exterior quando disponiveis.

## Definicoes operacionais

### "Carros chineses"

A ANFAVEA disponibiliza dados por empresa e marca, mas nao detalha por modelo. Portanto, para medir "carros chineses" pela ANFAVEA, o projeto precisa manter uma tabela de classificacao de marcas/empresas consideradas chinesas.

A definicao inicial sera: marcas ou empresas automotivas de origem/controlador chines, conforme tabela de referencia mantida em `ops/metadata/brand_classification.yml`.

Essa classificacao deve ser auditavel e pode exigir revisao manual, pois algumas empresas operam por distribuidores ou joint ventures no Brasil.

### Emplacamento/licenciamento

Nos arquivos da ANFAVEA, a nomenclatura recente alterna entre emplacamento e licenciamento em alguns materiais. Para este projeto, o termo analitico sera `emplacamentos`, mantendo a coluna de origem da ANFAVEA para preservar rastreabilidade.

### NCM `87011`

O codigo `87011` informado precisa de confirmacao antes da extracao final, porque NCM brasileira normalmente e registrada com 8 digitos, enquanto `8702`, `8703`, `8704`, `8706`, `8707` e `8708` sao posicoes de 4 digitos. Hipoteses a validar:

- o codigo pretendido era `8701`;
- o codigo pretendido era um prefixo/subposicao iniciada por `87011`;
- deve ser usada uma lista de NCMs completos de 8 digitos iniciados por esse prefixo.

## Entregaveis

- Banco DuckDB local em `data/processed/china_cars.duckdb`
- Tabelas finais na camada `gold`
- Planilhas Excel em `outputs/excel/`
- Dashboard interativo em `dashboard/`

## Decisoes relevantes

- Toda resposta final deve manter colunas de auditoria: fonte, arquivo/consulta, data de extracao e versao do pipeline.
- Resultados mensais devem usar chave temporal padrao `ano_mes` no formato `YYYY-MM`.
- As tabelas finais para Excel e dashboard devem usar prefixo `gold_`.
- Divergencias entre totais agregados e recortes por marca/NCM devem ser registradas em `ops/quality/`.
