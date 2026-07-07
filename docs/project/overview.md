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
- CAAM e CPCA, como fontes validas de evidencia para responder ou confirmar as perguntas quando houver granularidade, definicao e cobertura compativeis.

Filtros iniciais:

- Pais: China.
- Periodo: 2021-01 a 2026-06.
- Codigos informados: `8702`, `8703`, `8704`, `8706`, `8707`, `8708`, `8711` (a grafia inicial `87011` era erro de digitacao, confirmado pelo solicitante).

## Foco principal

O **foco principal da analise sao os caminhoes** (veiculos de carga). Automoveis, motocicletas
e onibus entram por completude do universo automotivo, mas a leitura central e a de caminhoes.
Para isolar o caminhao pesado, o NCM `8704` e classificado por classe de peso (`classe_carga`:
leve <= 5 t vs caminhoes > 5 t, dumpers e cavalos-mecanicos), e o prefixo `87012`
(cavalos-mecanicos / caminhoes-trator, 8701.2x) e incluido por completude da definicao de
caminhao. O `8701` inteiro nao entra: fora o 8701.2, e trator agricola e motocultivador (fora
de escopo), alem de uma anomalia de reporte em 870130 no ano de 2023.

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

### NCM `8711` (motocicletas)

O codigo informado originalmente como `87011` era erro de digitacao; o solicitante confirmou que o pretendido e `8711` (motocicletas, incluindo ciclomotores). Todos os prefixos ficam entao em posicoes de 4 digitos: `8702`, `8703`, `8704`, `8706`, `8707`, `8708` e `8711`, casados contra os NCMs completos de 8 digitos iniciados por cada prefixo.

Observacao analitica: motocicletas dominam o volume importado da China e formam um mercado distinto do de automoveis. Por isso o total de "veiculos" e sempre apresentado aberto por prefixo, permitindo separar automoveis (`8703`) de motos (`8711`).

### Prefixo `87012` (cavalos-mecanicos)

Alem dos prefixos informados, o projeto inclui o prefixo de consulta `87012` (subposicao `8701.2x`: cavalos-mecanicos / caminhoes-trator), por completude da definicao de caminhao — o unico subconjunto do `8701` relevante para carga. O `8701` inteiro nao entra: 8701.9x e trator agricola e 8701.10 e motocultivador (ambos fora de escopo), e 870130 tem uma anomalia de reporte de ~90 mil unidades em 2023. A importacao chinesa de cavalos-mecanicos e desprezivel (219 unidades em toda a serie).

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
