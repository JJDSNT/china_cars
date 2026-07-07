# Metricas

Documente aqui as metricas finais usadas em planilhas, relatorios e dashboard.

| Metrica | Definicao | Formula | Tabela base | Observacoes |
| --- | --- | --- | --- | --- |
| Emplacamentos mensais de carros chineses | Soma mensal de emplacamentos de marcas classificadas como chinesas | `sum(emplacamentos)` | `gold_anfavea_chinese_registrations_monthly` | Depende da classificacao em `ops/metadata/brand_classification.yml` |
| Participacao mensal de carros chineses | Participacao dos emplacamentos chineses no total de referencia | `emplacamentos_chineses / emplacamentos_total` | A definir | Denominador precisa ser conciliado com ANFAVEA |
| Valor FOB mensal China-NCM | Valor mensal de comercio exterior com China por NCM | `sum(valor_fob_usd)` | `gold_comex_china_automotive_monthly` | Confirmar fluxo: importacao/exportacao/ambos |
| Kg liquido mensal China-NCM | Peso liquido mensal por NCM | `sum(kg_liquido)` | `gold_comex_china_automotive_monthly` | Conforme disponibilidade no Comex Stat |
