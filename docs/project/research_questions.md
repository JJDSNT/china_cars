# Perguntas de Pesquisa

## I. Emplacamentos de carros chineses

Pergunta:

> Qual a evolucao dos emplacamentos de carros chineses de acordo com os dados da ANFAVEA, entre os anos de 2021 ate este momento de 2026 em bases mensais?

Resposta esperada:

- Serie mensal de emplacamentos de marcas chinesas.
- Quebra por empresa/marca quando a fonte permitir.
- Total mensal e acumulado anual.
- Participacao dos carros chineses no total de autoveiculos ou no segmento selecionado, quando houver denominador consistente.

Tabelas finais previstas:

- `gold_anfavea_chinese_registrations_monthly`
- `gold_anfavea_chinese_registrations_by_brand_monthly`

## II. Comercio exterior automotivo Brasil-China

Pergunta:

> Consultar a Comex Stat/MDIC filtrando o pais China e os NCMs de numeros 8702, 8703, 8704, 8706, 8707, 8708 e 87011 para o periodo de 2021 ate o mes de junho de 2026 em bases mensais.

Resposta esperada:

- Serie mensal por NCM.
- Valor FOB.
- Kg liquido.
- Quantidade estatistica, quando disponivel.
- Fluxo de importacao e/ou exportacao, conforme decisao metodologica.

Tabelas finais previstas:

- `gold_comex_china_automotive_monthly`
- `gold_comex_china_automotive_by_ncm_monthly`

## Pendencias metodologicas

- Confirmar se o fluxo Comex Stat desejado e importacao, exportacao ou ambos.
- Confirmar o tratamento do codigo `87011`.
- Definir a lista oficial de marcas chinesas para classificar os dados da ANFAVEA.
- Definir se "carros" inclui apenas automoveis ou tambem comerciais leves, caminhões e ônibus.

## Fontes auxiliares chinesas

CAAM e CPCA entram como fontes complementares para contexto e validacao metodologica:

- CAAM: dados agregados da industria automotiva chinesa, incluindo producao, vendas e exportacoes quando disponiveis.
- CPCA: dados de automoveis de passageiros, rankings, relatorios mensais e informacoes de fabricantes/marcas.

Essas fontes nao substituem a ANFAVEA para emplacamentos no Brasil nem o Comex Stat/MDIC para comercio exterior Brasil-China.
