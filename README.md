# China Cars Data Project

Projeto de engenharia e analise de dados para coletar dados brutos, refinar as camadas analiticas, gerar planilhas Excel e disponibilizar uma visualizacao interativa com DuckDB.

## Estrutura

```text
config/              Configuracoes de fontes, parametros e paths
data/
  raw/               Dados brutos, como recebidos das fontes
  interim/           Dados convertidos ou padronizados, ainda proximos da origem
  processed/         Dados limpos e integrados
  curated/           Tabelas finais para analise e consumo
docs/
  project/           Decisoes, escopo e documentacao do projeto
  data/              Dicionario de dados, fontes, regras e metricas
  operations/        Runbooks e procedimentos operacionais
ops/
  metadata/          Metadados tecnicos e administrativos do projeto
  lineage/           Linhagem entre fontes, tabelas e entregaveis
  quality/           Expectativas e resultados de qualidade
  run_logs/          Historico de execucoes do pipeline
sql/
  bronze/            SQL de carga e normalizacao inicial
  silver/            SQL de limpeza, joins e regras de negocio
  gold/              SQL de tabelas finais e metricas
src/china_cars/      Codigo reutilizavel do pipeline
scripts/             Entrypoints operacionais
notebooks/           Exploracao e prototipos
outputs/
  excel/             Planilhas finais
  figures/           Figuras exportadas
dashboard/           Aplicacao interativa
reports/             Relatorios e documentacao analitica
tests/               Testes automatizados
```

## Documentacao

- `docs/project/overview.md`: contexto, objetivos, escopo e entregaveis.
- `docs/project/research_questions.md`: perguntas de pesquisa e saidas esperadas.
- `docs/data/acquisition_plan.md`: plano de aquisicao das fontes ANFAVEA e Comex Stat/MDIC.
- `docs/data/data_dictionary.md`: tabelas, colunas, tipos, definicoes e regras.
- `docs/data/sources.md`: fontes, arquivos esperados, periodicidade e responsaveis.
- `docs/data/metrics.md`: metricas finais e criterios de calculo.
- `docs/operations/runbook.md`: como executar, monitorar e corrigir o pipeline.

## Operacao e metadados

- `ops/metadata/project.yml`: metadados gerais do projeto.
- `ops/metadata/datasets.yml`: inventario dos datasets e camadas.
- `ops/metadata/research_scope.yml`: escopo estruturado das perguntas de pesquisa.
- `ops/metadata/brand_classification.yml`: classificacao de marcas chinesas para a ANFAVEA.
- `ops/lineage/lineage.yml`: relacao entre fonte, transformacao e saida.
- `ops/quality/expectations.yml`: expectativas minimas de qualidade dos dados.
- `ops/run_logs/.gitkeep`: destino para logs ou manifestos de execucao.

## Fluxo proposto

1. Colocar arquivos originais em `data/raw/`, separados por fonte quando necessario.
2. Registrar ou ajustar configuracoes em `config/sources.yml`.
3. Executar o pipeline para construir o banco DuckDB local em `data/processed/china_cars.duckdb`.
4. Gerar as tabelas finais da camada `curated`.
5. Exportar planilhas para `outputs/excel/`.
6. Abrir o dashboard interativo.

## Comandos

```bash
uv sync --extra dev
uv run python scripts/download_data.py
uv run python scripts/run_pipeline.py
uv run streamlit run dashboard/app.py
```

## Dashboard

O dashboard interativo fica em `dashboard/app.py` e usa o DuckDB gerado pelo pipeline como backend:

```bash
uv run streamlit run dashboard/app.py
```

Depois de iniciar, acesse:

```text
http://localhost:8501
```

Visoes disponiveis:

- ANFAVEA: evolucao mensal dos emplacamentos de marcas chinesas cobertas na base, acumulados anuais e abertura por marca.
- Comex Stat/MDIC: importacoes originarias da China por mes, prefixo NCM e NCM completo.
- Dados: tabelas finais `gold_` usadas no Excel e no relatorio.

Artefatos finais:

- DuckDB: `data/processed/china_cars.duckdb`
- Excel: `outputs/excel/china_cars_outputs.xlsx`
- Dashboard: `dashboard/app.py`
- Relatorio: `reports/analysis_report.md`
