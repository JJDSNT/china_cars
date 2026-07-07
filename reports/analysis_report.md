# Relatorio de Analise

Data de execucao: 2026-07-07

## Escopo executado

Este relatorio responde a duas perguntas de pesquisa:

1. Evolucao mensal dos emplacamentos de carros chineses nos dados da ANFAVEA, de janeiro de 2021 ao mes mais recente disponivel no arquivo baixado de 2026.
2. Importacoes brasileiras originarias da China no Comex Stat/MDIC para os prefixos/codigos `8702`, `8703`, `8704`, `8706`, `8707`, `8708` e `8711`, de janeiro de 2021 a junho de 2026.

## Resultados ANFAVEA

Cobertura obtida: janeiro de 2021 a junho de 2026.

O recorte de marcas chinesas cobre BYD, GWM (Great Wall/Haval), Caoa Chery, Caoa Changan, Geely, Leapmotor, Omoda/Jaecoo, GAC, Jetour, MG, NETA, Zeekr, JAC, Effa, Foton, Shineray, Sany e Sinotruk, conforme `ops/metadata/brand_classification.yml`.

A serie e apresentada em **banda**, por limitacao da fonte:

- **Piso**: apenas marcas chinesas identificadas nominalmente. Isso inclui as marcas associadas a Anfavea (Caoa Chery, Geely, Leapmotor etc.) em todo o periodo e, a partir de 2026, o detalhe por marca das "Outras empresas" (BYD, GWM, Omoda, GAC, ...), disponivel nos arquivos de emplacamento de importados/nacionais por empresa e marca.
- **Estimativa (teto)**: piso mais a linha agregada "Outras empresas" do workbook anual nos meses sem detalhe por marca. E um teto porque essa linha inclui algumas marcas nao chinesas (Kia, Porsche, Volvo). Nos meses de 2026 com detalhe, cerca de 92% de "Outras empresas" e chinesa.

Para 2021-2023 a verdade esta proxima do piso (BYD e GWM ainda nao tinham escala no Brasil); para 2024-2026 sobe em direcao ao teto.

| Ano | Piso (marcas confirmadas) | Estimativa (com Outras) | Total ANFAVEA | Part. piso | Part. estimativa |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2021 | 39.747 | 60.959 | 2.119.851 | 1,87% | 2,88% |
| 2022 | 35.034 | 53.700 | 2.104.460 | 1,66% | 2,55% |
| 2023 | 31.480 | 83.210 | 2.308.689 | 1,36% | 3,60% |
| 2024 | 60.933 | 193.319 | 2.634.904 | 2,31% | 7,34% |
| 2025 | 75.399 | 271.300 | 2.689.634 | 2,80% | 10,09% |
| 2026, jan-jun | 98.729 | 235.030 | 1.420.675 | 6,95% | 16,54% |

Detalhe por marca disponivel (jan-fev de 2026, "Outras empresas" abertas): BYD lidera com 21.481 emplacamentos no bimestre, seguida por GWM (9.314), Caoa Chery (6.949), Omoda/Jaecoo (3.522), Geely (1.759) e GAC (1.176). Em janeiro de 2026, o conjunto de marcas chinesas atingiu ~22,9 mil emplacamentos, ou 13,4% do mercado ANFAVEA no mes.

Nota sobre a versao anterior: o recorte antigo cobria apenas Caoa Chery, Caoa Changan e Leapmotor e omitia BYD, GWM e demais marcas dentro de "Outras empresas", subestimando o volume chines por um fator de aproximadamente cinco vezes nos meses recentes.

## Resultados Comex Stat/MDIC

Cobertura obtida: importacoes, China como pais de origem, janeiro de 2021 a junho de 2026.

Metrica principal: **quantidade de veiculos** (unidades) dos NCMs de veiculos completos (8702, 8703, 8704, 8706, 8711), medidos em numero de unidades. O valor FOB entra como referencia secundaria. Autopecas (8708) e carrocerias (8707) nao entram na contagem de veiculos porque sao medidas majoritariamente em quilogramas — somar sua "quantidade estatistica" a de veiculos produzia um numero sem sentido fisico (era o caso da versao anterior).

**Atencao a composicao**: o prefixo `8711` sao **motocicletas**, que dominam o volume importado e formam um mercado distinto do de automoveis. Por isso o total de "veiculos" e apresentado aberto por tipo — misturar motos e automoveis num unico numero mascara a leitura.

Aberto por tipo, acumulado janeiro-junho (unidades):

| Ano | Automoveis (8703) | Motocicletas (8711) | Comerciais (8702/8704) |
| --- | ---: | ---: | ---: |
| 2021 | 35.761 | 82.427 | 213 |
| 2022 | 5.120 | 64.792 | 667 |
| 2023 | 15.894 | 91.078 | 542 |
| 2024 | 129.933 | 180.731 | 894 |
| 2025 | 134.581 | 471.164 | 6.994 |
| 2026 | 384.681 | 1.263.623 | 7.997 |

No acumulado janeiro-junho de 2026 contra 2025: automoveis (8703) importados da China quase triplicaram (+185,8%) e motocicletas (8711) mais que dobraram (+168,2%).

Principais prefixos em 2026, janeiro-junho, por quantidade de veiculos:

| Prefixo NCM | Veiculos (unidades) | Valor FOB US$ (referencia) |
| --- | ---: | ---: |
| 8711 (motocicletas) | 1.263.623 | 158.497.564 |
| 8703 (automoveis de passageiros) | 384.681 | 5.608.528.247 |
| 8704 (veiculos de carga) | 7.895 | 178.061.098 |
| 8702 (transporte coletivo) | 102 | 12.472.228 |
| 8706 (chassis) | 31 | 179.878 |
| 8707 (carrocerias) | 0 | 6.103.850 |
| 8708 (autopecas) | 0 | 1.014.451.083 |

## Estoque no canal (proxy importacao vs emplacamento)

Cruzando o que **entra** no pais (importacao Comex, unidades) com o que e **emplacado** (ANFAVEA, marcas chinesas), obtem-se uma proxy direcional do estoque parado no canal (porto, importador, concessionaria). A serie ANFAVEA por segmento (`gold_anfavea_chinese_registrations_by_segment_monthly`) casa com os prefixos NCM correspondentes: automoveis com 8703; carga (comerciais leves + caminhoes) com 8704; onibus com 8702.

Leituras principais (acumulado por ano, unidades):

| Segmento | 2024 imp / empl | 2025 imp / empl | 2026 jan-jun imp / empl |
| --- | ---: | ---: | ---: |
| Automoveis (8703) | 172.136 / 186.536 | 236.304 / 258.831 | 384.681 / 225.508 |
| Carga (8704) | 4.206 / 6.705 | 7.363 / 11.866 | 7.895 / 8.981 |

- **Automoveis, 2026**: a importacao (384.681) supera os emplacamentos (225.508) em ~159 mil unidades — sinal de **estoque acumulando** no canal, consistente com o front-loading de importacoes antes do aumento do imposto de importacao.
- **Carga/caminhoes**: os emplacamentos superam a importacao direta em todos os anos, sinal de **producao local / montagem CKD** no Brasil (marcas como Effa, Shineray e JAC), e nao de estoque.

Ressalvas: o Comex e por pais de origem e a ANFAVEA por marca chinesa (populacoes que se sobrepoem, nao coincidem); ha defasagem de ~1-3 meses entre importar e emplacar; o NCM 8704 mistura picapes e caminhoes; e o emplacamento de automoveis antes de 2026 usa o proxy "Outras empresas", que inclui algumas marcas nao chinesas.

## Evidencias CPCA e CAAM

As fontes chinesas foram integradas como evidencias validas para confirmar, contrastar ou contextualizar os resultados principais.

### CPCA

Fonte: China Passenger Car Association / China Automobile Dealers Association Passenger Car Market Information Joint Branch.

Cobertura estruturada extraida: fevereiro de 2021 a junho de 2026.

Foram extraidas 203 metricas textuais de artigos mensais da CPCA, incluindo varejo de automoveis de passageiros, varejo NEV, segmentos sedan/MPV/SUV, penetracao NEV quando publicada e estimativa de atacado NEV.

Ultimos pontos disponiveis:

| Mes | Varejo passageiros | Varejo NEV | Atacado NEV estimado | Penetracao NEV |
| --- | ---: | ---: | ---: | ---: |
| 2026-02 | 1.034.000 | 464.000 | - | - |
| 2026-03 | 1.648.000 | 848.000 | - | - |
| 2026-04 | 1.384.000 | 849.000 | - | - |
| 2026-05 | 1.510.000 | 950.000 | - | 62,9% |
| 2026-06 | - | - | 1.510.000 | - |

Uso analitico:

- A CPCA ajuda a validar a direcao do mercado chines de passageiros e NEV.
- A serie nao e equivalente a emplacamentos brasileiros; deve ser usada para acuracia contextual e comparacao de tendencias, salvo quando houver recorte diretamente compativel com a pergunta.
- A propria CPCA distingue varejo, atacado e exportacao; essa distincao foi preservada no pipeline.

### CAAM

Fonte: China Association of Automobile Manufacturers.

Cobertura coletada: 13 comunicados estatisticos entre fevereiro e agosto de 2025, com 49 imagens brutas associadas.

Os comunicados CAAM foram preservados no catalogo `raw_caam_evidence_catalog`. Nesta versao, os numeros dos comunicados CAAM ainda nao foram extraidos para serie estruturada porque os dados coletados estao publicados majoritariamente como imagens. Eles ficam disponiveis para OCR ou transcricao controlada em etapa posterior.

## Limitacoes e decisoes metodologicas

- A ANFAVEA informa que nao disponibiliza estatisticas de autoveiculos detalhadas por modelo. O recorte de carros chineses foi feito por marca/empresa.
- Marcas chinesas como BYD, GWM e Omoda aparecem no workbook anual apenas dentro da linha agregada "Outras empresas", sem abertura por marca. O detalhe por marca so existe nos arquivos de emplacamento de importados/nacionais por empresa e marca, publicamente expostos para 2026 no momento da coleta. Por isso a serie chinesa e apresentada como banda piso-estimativa: o piso e exato, e a estimativa usa a linha "Outras empresas" como teto nos meses sem detalhe. Para fechar a serie por marca de 2021 a 2025 seria necessario obter esses arquivos por marca para os anos anteriores (ou uma fonte complementar como a Fenabrave, que publica emplacamentos mensais por marca).
- No Comex Stat, a entrega principal foi feita para importacoes do Brasil originarias da China. A quantidade de veiculos considera apenas NCMs de veiculos completos medidos em numero de unidades (unidade estatistica 11); autopecas e carrocerias entram apenas nas metricas de valor FOB e peso. Exportacoes nao foram misturadas ao resultado principal porque a pergunta nao especificou o fluxo.
- O codigo `8711` (motocicletas) foi confirmado pelo solicitante como o pretendido; a grafia inicial `87011` era erro de digitacao. Motocicletas dominam o volume importado e constituem um mercado distinto do de automoveis, por isso o total de veiculos e sempre apresentado aberto por prefixo NCM.
- CPCA e CAAM sao fontes validas de evidencia; sua funcao analitica depende da compatibilidade entre indicador, recorte geografico, periodo e definicao operacional.
- Os valores podem ser revisados pelas fontes oficiais.

## Entregaveis

- DuckDB: `data/processed/china_cars.duckdb`
- Excel: `outputs/excel/china_cars_outputs.xlsx`
- Dashboard: `dashboard/app.py`
- Tabelas finais:
  - `gold_anfavea_chinese_registrations_monthly` (serie mensal com banda piso/estimativa)
  - `gold_anfavea_chinese_registrations_by_brand_monthly` (detalhe por marca, inclui BYD/GWM/Omoda em 2026)
  - `gold_anfavea_chinese_registrations_by_segment_monthly` (serie por segmento: automoveis, comerciais leves, caminhoes, onibus)
  - `raw_anfavea_origin_brand_monthly` (emplacamentos por empresa e marca, importados/nacionais)
  - `gold_comex_china_automotive_monthly`
  - `gold_comex_china_automotive_by_prefix_monthly`
  - `gold_comex_china_automotive_by_ncm_monthly`
  - `gold_cpca_passenger_market_monthly`
  - `raw_cpca_article_metrics`
  - `raw_caam_evidence_catalog`
