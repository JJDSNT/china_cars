# Metricas

Documente aqui as metricas finais usadas em planilhas, relatorios e dashboard.

| Metrica | Definicao | Formula | Tabela base | Observacoes |
| --- | --- | --- | --- | --- |
| Emplacamentos chineses - piso | Soma mensal apenas de marcas chinesas confirmadas nominalmente | `sum(emplacamentos_chinesas_min)` | `gold_anfavea_chinese_registrations_monthly` | Exato; nunca superestima. Marcas em `ops/metadata/brand_classification.yml` |
| Emplacamentos chineses - estimativa | Piso mais a linha agregada "Outras empresas" nos meses sem detalhe por marca | `sum(emplacamentos)` | `gold_anfavea_chinese_registrations_monthly` | Teto: "Outras empresas" inclui marcas nao chinesas (Kia, Porsche, Volvo). Coluna `metodo_outras` indica detalhe_por_marca vs proxy_outras_empresas |
| Participacao mensal de carros chineses | Participacao no total ANFAVEA do mes | `emplacamentos / emplacamentos_total_anfavea` (e `participacao_min` para o piso) | `gold_anfavea_chinese_registrations_monthly` | Banda piso-teto |
| Emplacamentos por marca | Detalhe por marca (inclui BYD/GWM/Omoda nos meses com arquivo por marca) | `sum(emplacamentos)` por `company_or_brand` | `gold_anfavea_chinese_registrations_by_brand_monthly` | Coluna `fonte` distingue workbook anual vs arquivos por marca |
| Quantidade de veiculos importados da China | Unidades importadas de NCMs de veiculos completos medidos em numero de unidades | `sum(quantidade_veiculos)` | `gold_comex_china_automotive_monthly` | **Metrica principal do Comex.** Prefixos 8702/8703/8704/8706/8711/87012 com unidade estatistica 11. 8711 = motocicletas (dominam o volume; separar de automoveis 8703) |
| Caminhoes pesados importados (foco) | Unidades de veiculos de carga acima de 5 t (mais dumpers e cavalos-mecanicos) | `sum(quantidade_veiculos)` onde `classe_carga in ('pesado_acima_5t','dumper_fora_estrada','cavalo_mecanico')` | `gold_comex_china_automotive_by_ncm_monthly` | **Recorte de foco.** `classe_carga` classifica o 8704 pela subposicao de 6 digitos; `cavalo_mecanico` vem do prefixo 87012 (desprezivel: 219 unid. em 2021-2026) |
| Emplacamentos chineses por segmento | Serie mensal por grupo de veiculo em banda piso/estimativa | `sum(emplacamentos_chinesas_min)` / `sum(emplacamentos)` por `vehicle_group` | `gold_anfavea_chinese_registrations_by_segment_monthly` | Grupos: Automoveis, Comerciais leves, Caminhoes, Onibus. Base do comparativo de estoque no canal contra os prefixos NCM do Comex |
| Valor FOB mensal China-NCM | Valor de importacao (referencia secundaria) | `sum(valor_fob_usd)` | `gold_comex_china_automotive_monthly` | Importacao originaria da China |
| Kg liquido mensal China-NCM | Peso liquido mensal por NCM | `sum(kg_liquido)` | `gold_comex_china_automotive_monthly` | Conforme disponibilidade no Comex Stat |
