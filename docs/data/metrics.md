# Metricas

Documente aqui as metricas finais usadas em planilhas, relatorios e dashboard.

| Metrica | Definicao | Formula | Tabela base | Observacoes |
| --- | --- | --- | --- | --- |
| Emplacamentos chineses - piso | Soma mensal apenas de marcas chinesas confirmadas nominalmente | `sum(emplacamentos_chinesas_min)` | `gold_anfavea_chinese_registrations_monthly` | Exato; nunca superestima. Marcas em `ops/metadata/brand_classification.yml` |
| Emplacamentos chineses - estimativa | Piso mais a linha agregada "Outras empresas" nos meses sem detalhe por marca | `sum(emplacamentos)` | `gold_anfavea_chinese_registrations_monthly` | Teto: "Outras empresas" inclui marcas nao chinesas (Kia, Porsche, Volvo). Coluna `metodo_outras` indica detalhe_por_marca vs proxy_outras_empresas |
| Participacao mensal de carros chineses | Participacao no total ANFAVEA do mes | `emplacamentos / emplacamentos_total_anfavea` (e `participacao_min` para o piso) | `gold_anfavea_chinese_registrations_monthly` | Banda piso-teto |
| Emplacamentos por marca | Detalhe por marca (inclui BYD/GWM/Omoda nos meses com arquivo por marca) | `sum(emplacamentos)` por `company_or_brand` | `gold_anfavea_chinese_registrations_by_brand_monthly` | Coluna `fonte` distingue workbook anual vs arquivos por marca |
| Quantidade de veiculos importados da China | Unidades importadas de NCMs de veiculos completos medidos em numero de unidades | `sum(quantidade_veiculos)` | `gold_comex_china_automotive_monthly` | **Metrica principal do Comex.** Prefixos 8702/8703/8704/8706/8711 com unidade estatistica 11. 8711 = motocicletas (dominam o volume; separar de automoveis 8703) |
| Valor FOB mensal China-NCM | Valor de importacao (referencia secundaria) | `sum(valor_fob_usd)` | `gold_comex_china_automotive_monthly` | Importacao originaria da China |
| Kg liquido mensal China-NCM | Peso liquido mensal por NCM | `sum(kg_liquido)` | `gold_comex_china_automotive_monthly` | Conforme disponibilidade no Comex Stat |
