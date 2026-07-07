# Plano de Aquisicao de Dados

## ANFAVEA

Fonte:

- Site ANFAVEA, secao Economia > Dados Estatisticos.
- Arquivos Excel anuais de autoveiculos.
- Arquivos especificos de emplacamento de nacionais e importados por empresa e marca.
- Series historicas mensais para conciliacao de totais.

Periodo:

- Inicio: 2021-01.
- Fim: mes mais recente de 2026 disponivel na ANFAVEA no momento da extracao.

Dados brutos esperados:

```text
data/raw/anfavea/
  2021/
  2022/
  2023/
  2024/
  2025/
  2026/
```

Campos alvo:

- ano_mes
- empresa
- marca
- origem do veiculo, quando disponivel
- segmento, quando disponivel
- emplacamentos
- arquivo_fonte
- data_extracao

Observacao:

A ANFAVEA informa que nao disponibiliza estatisticas detalhadas por modelo. O recorte de "carros chineses" deve ser feito por marca/empresa, usando classificacao mantida pelo projeto.

## Comex Stat/MDIC

Fonte:

- Comex Stat/MDIC.

Periodo:

- Inicio: 2021-01.
- Fim: 2026-06.

Filtros:

- Pais: China.
- Codigos: `8702`, `8703`, `8704`, `8706`, `8707`, `8708`, `8711` (a grafia inicial `87011` era erro de digitacao).
- Periodicidade: mensal.

Campos alvo:

- ano_mes
- fluxo
- pais
- codigo_ncm
- descricao_ncm
- valor_fob_usd
- kg_liquido
- quantidade_estatistica
- unidade_estatistica
- data_extracao

Pendencias:

- Confirmar importacao, exportacao ou ambos.
- Confirmar se os codigos serao tratados como prefixos de NCM ou como codigos completos.
- Codigo `8711` (motocicletas) confirmado pelo solicitante (grafia `87011` era erro de digitacao).

## CAAM

Fonte:

- China Association of Automobile Manufacturers.
- Site oficial: `http://www.caam.org.cn/`.

Uso no projeto:

- Fonte valida para responder ou confirmar resultados quando houver definicao, granularidade e periodo compativeis com as perguntas.
- Possivel fonte de conciliacao macro para exportacoes chinesas de veiculos.
- Apoio metodologico para entender a diferenca entre dados de fabricantes, atacado, varejo e exportacao.

Dados brutos esperados:

```text
data/raw/caam/
  2021/
  2022/
  2023/
  2024/
  2025/
  2026/
```

Campos alvo, quando disponiveis:

- ano_mes
- categoria
- producao
- vendas
- exportacoes
- veiculos_nova_energia
- fonte_url
- data_extracao

Pendencias:

- Confirmar disponibilidade publica historica mensal em formato estruturado.
- Definir, por tabela coletada, se os dados CAAM respondem diretamente uma pergunta, validam uma resposta ou apenas contextualizam.

## CPCA

Fonte:

- China Passenger Car Association / China Automobile Dealers Association Passenger Car Market Information Joint Branch.
- Site oficial: `https://www.cpcaauto.com/`.
- Area de dados: `https://data.cpcadata.com/`.

Uso no projeto:

- Fonte valida para dados de automoveis de passageiros, rankings de fabricantes/marcas e relatorios mensais.
- Apoio para classificar marcas chinesas, identificar fabricantes relevantes e contextualizar exportacoes/NEVs.
- Pode responder diretamente ou validar as perguntas se houver recorte compativel com Brasil, periodo mensal e definicao operacional alinhada.

Dados brutos esperados:

```text
data/raw/cpca/
  2021/
  2022/
  2023/
  2024/
  2025/
  2026/
```

Campos alvo, quando disponiveis:

- ano_mes
- fabricante
- marca
- segmento
- varejo
- atacado
- exportacoes
- veiculos_nova_energia
- fonte_url
- data_extracao

Pendencias:

- Verificar se a area de dados permite download automatizado ou se exige coleta manual.
- Separar claramente varejo, atacado e exportacao para evitar mistura com emplacamentos brasileiros.
