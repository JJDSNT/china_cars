# Perguntas de Pesquisa

> **Foco principal:** caminhoes (veiculos de carga). Os demais segmentos entram por
> completude, mas a leitura central e a de caminhoes.

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
- `gold_anfavea_chinese_registrations_by_segment_monthly`

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
- `gold_comex_china_automotive_by_prefix_monthly`
- `gold_comex_china_automotive_by_ncm_monthly` (inclui `classe_carga` do 8704)

## Pendencias metodologicas

- Confirmar se o fluxo Comex Stat desejado e importacao, exportacao ou ambos.
- Codigo `8711` (motocicletas) confirmado pelo solicitante; a grafia `87011` na pergunta original era erro de digitacao.
- Prefixo `87012` (cavalos-mecanicos, 8701.2x) adicionado por completude da definicao de caminhao; 8701 inteiro fica de fora (trator agricola/motocultivador fora de escopo + anomalia em 870130 no ano de 2023). Importacao chinesa de cavalos-mecanicos e desprezivel.
- Definir a lista oficial de marcas chinesas para classificar os dados da ANFAVEA.
- Foco confirmado em caminhoes; demais segmentos por completude. O 8704 e classificado por classe de peso (`classe_carga`) para isolar o caminhao pesado (> 5 t) do comercial leve (<= 5 t).

## Fontes chinesas para evidencia e validacao

CAAM e CPCA entram como fontes validas para responder, confirmar ou qualificar as perguntas de pesquisa:

- CAAM: dados agregados da industria automotiva chinesa, incluindo producao, vendas e exportacoes quando disponiveis.
- CPCA: dados de automoveis de passageiros, rankings, relatorios mensais e informacoes de fabricantes/marcas.

A classificacao de cada fonte deve depender da aderencia empirica:

- primaria, quando responder diretamente a pergunta;
- corroborativa, quando medir o mesmo fenomeno por outra fonte/definicao;
- contextual, quando explicar mercado, fabricantes ou dinamica chinesa sem medir diretamente o indicador final.
