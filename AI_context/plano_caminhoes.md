# Plano: foco em caminhões (China Cars)

> Pasta `AI_context/`: contexto e planos destinados a orientar trabalho assistido por IA
> neste repositório. Este documento registra a decisão e o plano para reforçar o recorte
> de **caminhões**, que é o foco principal da análise.

## Contexto

O projeto responde a duas perguntas (emplacamentos ANFAVEA de marcas chinesas; importações
Comex da China por NCM). O **foco principal declarado é caminhões**. As entregas atuais
(dashboard, relatório) estão equilibradas entre carros, motos e caminhões; este plano
recentra em caminhões e fecha lacunas de NCM.

## Investigação feita (evidência que fundamenta o plano)

1. **Comex 8704 (transporte de carga)** mistura picapes/comerciais leves (carga ≤ 5 t) com
   caminhões (> 5 t). Os pesados de fato (870422/870423) são poucos vindos da China
   (~2,8 mil unid. acumuladas); o grosso do 8704-China é leve (≤ 5 t) e elétrico (870460).
2. **Cavalos-mecânicos / caminhões-trator (8701.2x = 870121/870124/870129)** da China são
   **desprezíveis** — dezenas de unidades por ano. Ou seja, a China quase não exporta
   cavalos-mecânicos para o Brasil.
3. O restante do **8701** da China é **trator agrícola** (8701.9x, em crescimento:
   870192 chegou a 6.509 unid. em 2026) e **motocultivador** (8701.10, que era o que o
   antigo "87011" capturava). Nada disso é caminhão. Além disso, 870130 (esteira) tem uma
   **anomalia de 90.005 unidades em 2023** (provável erro de reporte), que poluiria a série.

**Conclusão**: adicionar o `8701` inteiro traria tratores agrícolas (fora de escopo) e uma
anomalia. O subconjunto relevante para caminhões é apenas `8701.2` (cavalos-mecânicos), que
é minúsculo vindo da China — mas vale incluí-lo para deixar a **definição de "caminhão"
completa** e documentar, com dado, que a importação chinesa de cavalos-mecânicos é irrelevante.
O sinal real de caminhões está em separar **8704 leve × pesado**.

## O que vamos fazer

1. **Adicionar prefixo `87012` (cavalos-mecânicos / caminhões-trator, 8701.2x)** à consulta
   Comex e à contagem de veículos (unidade 11). NÃO adicionar 8701 inteiro (evita tratores
   agrícolas e a anomalia de 870130).
2. **Classificar o 8704 por classe de peso** (nova coluna `classe_carga` no detalhe e na
   tabela `gold_comex_china_automotive_by_ncm_monthly`), pela subposição de 6 dígitos:
   - `leve_ate_5t`: 870421, 870431, 870441, 870451
   - `pesado_acima_5t`: 870422, 870423, 870432, 870442, 870443, 870452
   - `dumper_fora_estrada`: 870410
   - `outros_carga`: 870460 (elétrico sem classe de peso), 870490
   - `cavalo_mecanico`: prefixo 87012
3. **Dashboard — aba "Estoque no canal"**: adicionar segmento **"Caminhões (pesados)"** como
   padrão, cruzando ANFAVEA grupo `Caminhões` × Comex `classe_carga ∈ {pesado_acima_5t,
   dumper_fora_estrada, cavalo_mecanico}`. Manter "Carga total", "Automóveis", "Ônibus".
4. **Dashboard — aba Comex**: expor `classe_carga` como dimensão opcional (rótulos legíveis).
5. **Relatório e docs**: documentar a decisão do 8701/8704, recentrar o texto em caminhões,
   e registrar que cavalos-mecânicos chineses são desprezíveis (achado próprio).

## Ressalvas que permanecem

- Comex é por país de origem; ANFAVEA por marca chinesa — populações que se sobrepõem, não
  coincidem (produção local/CKD faz emplacamento > importação para caminhões).
- Defasagem de ~1–3 meses entre importar e emplacar.
- Série ANFAVEA de caminhões por marca só tem detalhe a partir de 2026; antes usa a linha
  agregada "Outras empresas" do grupo Caminhões (proxy quase 100% chinês).

## Status

- [x] 1. Prefixo 87012 no Comex (incluído por completude; achado: importação chinesa de cavalos-mecânicos é desprezível, 219 unid. em 2021-2026)
- [x] 2. Classe de peso do 8704 (coluna `classe_carga` no detalhe e em `gold_comex_china_automotive_by_ncm_monthly`)
- [x] 3. Segmento "Caminhões (pesados > 5t)" como padrão na aba Estoque
- [x] 4. classe_carga como dimensão (rótulos legíveis) na aba Comex
- [x] 5. Relatório e docs recentrados em caminhões
