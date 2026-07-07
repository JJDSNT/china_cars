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
- `ops/metadata/brand_classification.yml`: classificacao de marcas chinesas para a ANFAVEA, com `aliases` por marca (ex.: GWM ≡ Great Wall ≡ Haval) para casar as grafias do workbook anual e dos arquivos por marca.
- `ops/lineage/lineage.yml`: relacao entre fonte, transformacao e saida.
- `ops/quality/expectations.yml`: expectativas minimas de qualidade dos dados.
- `ops/quality/results/latest.yml`: resultado mais recente dos testes de qualidade e integridade.
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
uv run python scripts/run_quality_checks.py
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

> **Foco principal: caminhoes.** Os demais segmentos entram por completude; a leitura central e a de veiculos de carga.

Visoes disponiveis:

- ANFAVEA: evolucao mensal dos emplacamentos de marcas chinesas em banda piso-estimativa (ver metodologia abaixo), acumulados anuais e abertura por marca (BYD, GWM, Omoda, Caoa Chery, Geely e demais nos meses com detalhe).
- Comex Stat/MDIC: importacoes originarias da China por mes, prefixo NCM e NCM completo, com **quantidade de veiculos** (unidades) como metrica principal e valor FOB como referencia secundaria. A dimensao **classe de carga** separa o 8704 em leve (<= 5 t) vs caminhoes (> 5 t), dumpers e cavalos-mecanicos.
- Estoque no canal: veiculos importados da China (Comex) x emplacamentos de marcas chinesas (ANFAVEA), ambos em volume, com **"Caminhoes (pesados > 5t)"** como segmento padrao.
- Dados: tabelas finais `gold_` e a raw `raw_anfavea_origin_brand_monthly`.

## Metodologia (pontos-chave)

- **ANFAVEA - banda piso/estimativa**: o workbook anual so abre por marca as empresas associadas; marcas chinesas como BYD e GWM ficam na linha agregada "Outras empresas". O detalhe por marca vem dos arquivos de emplacamento de importados/nacionais por empresa e marca, publicados para 2026. Por isso a serie chinesa e uma banda: `emplacamentos_chinesas_min` (piso, marcas confirmadas, exato) e `emplacamentos` (estimativa/teto, usando "Outras empresas" como proxy nos meses sem detalhe). A coluna `metodo_outras` indica a origem de cada ponto.
- **Comex - volume em veiculos**: a metrica principal e `quantidade_veiculos`, contada apenas para NCMs de veiculos completos (8702/8703/8704/8706/8711/87012) medidos em numero de unidades. **8711 sao motocicletas**, que dominam o volume e devem ser lidas separadamente dos automoveis (8703). Autopecas (8708, medidas em kg) e carrocerias (8707) entram apenas em valor FOB e peso.
- **Foco em caminhoes (8701/8704)**: o 8704 e classificado por classe de peso (`classe_carga`) para isolar o caminhao pesado (> 5 t) do comercial leve (<= 5 t). Do 8701 entra apenas o subconjunto `87012` (cavalos-mecanicos / caminhoes-trator), por completude — o 8701 inteiro traria trator agricola e motocultivador (fora de escopo) e uma anomalia de reporte em 870130 no ano de 2023. A importacao chinesa de cavalos-mecanicos e desprezivel (219 unidades em 2021-2026).
- **Arquivos rolantes**: o download reatualiza os arquivos do ano corrente (workbook ANFAVEA e CSVs do Comex), que crescem a cada divulgacao mensal.

Artefatos finais:

- DuckDB: `data/processed/china_cars.duckdb`
- Excel: `outputs/excel/china_cars_outputs.xlsx`
- Dashboard: `dashboard/app.py`
- Relatorio: `reports/analysis_report.md` (+ `.pdf`)
