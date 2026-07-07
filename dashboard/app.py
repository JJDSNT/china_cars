import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st
import yaml

from china_cars.db import database_path
from china_cars.paths import PROJECT_ROOT


def load_yaml(relative_path: str):
    """Le um YAML de ops/ de forma tolerante (retorna None se ausente)."""
    path = PROJECT_ROOT / relative_path
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


st.set_page_config(page_title="China Cars", layout="wide")
st.title("China Cars")


def br_int(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")


def usd_bi(value: float) -> str:
    return f"US$ {value / 1_000_000_000:.2f} bi"


# Rotulos legiveis para os prefixos NCM e para colunas usadas como dimensao/metrica.
PREFIX_LABELS = {
    "8702": "Onibus e coletivos (8702)",
    "8703": "Automoveis (8703)",
    "8704": "Veiculos de carga (8704)",
    "8706": "Chassis com motor (8706)",
    "8707": "Carrocerias (8707)",
    "8708": "Autopecas (8708)",
    "8711": "Motocicletas (8711)",
    "87012": "Cavalos-mecanicos (8701.2)",
}
CARGO_CLASS_LABELS = {
    "leve_ate_5t": "Comerciais leves (<= 5 t)",
    "pesado_acima_5t": "Caminhoes (> 5 t)",
    "dumper_fora_estrada": "Fora-de-estrada / dumpers",
    "cavalo_mecanico": "Cavalos-mecanicos",
    "outros_carga": "Carga (outros/nao classificado)",
}
DIMENSION_LABELS = {
    "tipo_ncm": "Tipo (prefixo NCM)",
    "ncm_prefixo_consulta": "Tipo (prefixo NCM)",
    "codigo_ncm": "NCM completo (8 digitos)",
    "classe_carga_label": "Classe de carga (8704 + cavalo-mecanico)",
    "ano": "Ano",
    "ano_mes": "Mes",
}
MEASURE_LABELS = {
    "quantidade_veiculos": "Quantidade de veiculos (unidades)",
    "valor_fob_usd": "Valor FOB (US$)",
    "kg_liquido": "Peso liquido (kg)",
    "quantidade_estatistica": "Quantidade estatistica (bruta)",
}


def prefix_label(code: str) -> str:
    return PREFIX_LABELS.get(str(code), str(code))


# Correspondencia entre segmentos ANFAVEA (emplacamentos) e o Comex (importacao).
# "Caminhoes (pesados)" isola o 8704 acima de 5 t (+ dumpers e cavalos-mecanicos)
# pela classe de carga; "Carga total" usa o 8704 inteiro (picapes + caminhoes).
SEGMENT_MAP = {
    "Caminhoes (pesados > 5t)": {
        "anfavea": ["Caminhões"],
        "comex_classe": ["pesado_acima_5t", "dumper_fora_estrada", "cavalo_mecanico"],
    },
    "Carga total (comerciais + caminhoes)": {
        "anfavea": ["Comerciais leves", "Caminhões"],
        "comex_prefix": ["8704", "87012"],
    },
    "Automoveis": {"anfavea": ["Automóveis"], "comex_prefix": ["8703"]},
    "Onibus": {"anfavea": ["Ônibus"], "comex_prefix": ["8702"]},
}


def filter_period(df: pd.DataFrame, period: tuple[str, str]) -> pd.DataFrame:
    return df[df["ano_mes"].between(period[0], period[1])].copy()


db_path = database_path()
if not db_path.exists():
    st.info("Banco DuckDB ainda nao encontrado. Execute `python scripts/run_pipeline.py`.")
    st.stop()

con = duckdb.connect(str(db_path), read_only=True)

anfavea = con.execute(
    "select * from gold_anfavea_chinese_registrations_monthly order by ano_mes"
).df()
anfavea_brand = con.execute(
    "select * from gold_anfavea_chinese_registrations_by_brand_monthly order by ano_mes"
).df()
anfavea_segment = con.execute(
    "select * from gold_anfavea_chinese_registrations_by_segment_monthly order by ano_mes"
).df()
comex = con.execute("select * from gold_comex_china_automotive_monthly order by ano_mes").df()
comex_prefix = con.execute(
    "select * from gold_comex_china_automotive_by_prefix_monthly order by ano_mes"
).df()
comex_ncm = con.execute(
    "select * from gold_comex_china_automotive_by_ncm_monthly order by ano_mes"
).df()
cpca = con.execute("select * from gold_cpca_passenger_market_monthly order by ano_mes").df()
cpca_metrics = con.execute("select * from raw_cpca_article_metrics order by ano_mes").df()
caam_catalog = con.execute(
    "select * from raw_caam_evidence_catalog order by published_date, title"
).df()

all_periods = sorted(set(anfavea["ano_mes"]).union(set(comex["ano_mes"])).union(set(cpca["ano_mes"])))
period = st.sidebar.select_slider(
    "Periodo",
    options=all_periods,
    value=(all_periods[0], all_periods[-1]),
)

(
    tab_anfavea,
    tab_comex,
    tab_estoque,
    tab_cpca,
    tab_caam,
    tab_compare,
    tab_data,
    tab_saude,
) = st.tabs(
    [
        "ANFAVEA",
        "Comex Stat",
        "Estoque no canal",
        "CPCA",
        "CAAM",
        "Comparativo",
        "Dados",
        "Saude dos dados",
    ]
)

with tab_anfavea:
    filtered = filter_period(anfavea, period)
    filtered_brand = filter_period(anfavea_brand, period)

    st.caption(
        "Volume de emplacamentos de marcas chinesas. A serie tem uma **banda**: "
        "piso = apenas marcas chinesas confirmadas; teto/estimativa = piso + a linha "
        "agregada \"Outras empresas\" (inclui algumas marcas nao chinesas) nos meses "
        "sem detalhe por marca. Meses recentes com detalhe (arquivos por marca de 2026) "
        "trazem BYD, GWM, Omoda e demais nominalmente."
    )

    latest = filtered.iloc[-1] if not filtered.empty else None
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses", len(filtered))
    c2.metric("Emplacamentos (piso)", br_int(filtered["emplacamentos_chinesas_min"].sum()))
    c3.metric("Emplacamentos (estimativa)", br_int(filtered["emplacamentos"].sum()))
    c4.metric(
        "Participacao (ult. mes)",
        f"{latest['participacao_total_anfavea'] * 100:.1f}%" if latest is not None else "-",
    )

    metric = st.radio(
        "Metrica",
        ["volume (banda piso-teto)", "participacao (banda piso-teto)"],
        horizontal=True,
    )
    if metric.startswith("volume"):
        y_min, y_max, ylab = (
            "emplacamentos_chinesas_min",
            "emplacamentos",
            "Emplacamentos",
        )
    else:
        y_min, y_max, ylab = (
            "participacao_min",
            "participacao_total_anfavea",
            "Participacao",
        )
    band = filtered.melt(
        id_vars=["ano_mes", "metodo_outras"],
        value_vars=[y_max, y_min],
        var_name="serie",
        value_name="valor",
    )
    band["serie"] = band["serie"].map({y_max: "estimativa (teto)", y_min: "piso confirmado"})
    fig = px.line(
        band,
        x="ano_mes",
        y="valor",
        color="serie",
        markers=True,
        labels={"ano_mes": "Mes", "valor": ylab, "serie": "Serie"},
    )
    st.plotly_chart(fig, use_container_width=True)

    annual = (
        filtered.groupby("ano", as_index=False)
        .agg(
            piso=("emplacamentos_chinesas_min", "sum"),
            estimativa=("emplacamentos", "sum"),
            total_anfavea=("emplacamentos_total_anfavea", "sum"),
        )
        .assign(
            part_piso=lambda df: (df["piso"] / df["total_anfavea"] * 100).round(2),
            part_estimativa=lambda df: (df["estimativa"] / df["total_anfavea"] * 100).round(2),
        )
    )
    st.dataframe(annual, use_container_width=True, hide_index=True)

    st.subheader("Detalhe por marca (inclui BYD, GWM, Omoda nos meses com arquivo por marca)")
    vehicle_groups = sorted(filtered_brand["vehicle_group"].dropna().unique().tolist())
    selected_groups = st.multiselect("Segmento ANFAVEA", vehicle_groups, default=vehicle_groups)
    filtered_brand = filtered_brand[filtered_brand["vehicle_group"].isin(selected_groups)]

    col1, col2 = st.columns(2)
    rank = (
        filtered_brand.groupby("company_or_brand", as_index=False)["emplacamentos"]
        .sum()
        .sort_values("emplacamentos", ascending=False)
    )
    col1.plotly_chart(
        px.bar(rank, x="company_or_brand", y="emplacamentos", labels={"company_or_brand": "Marca"}),
        use_container_width=True,
    )
    col2.plotly_chart(
        px.bar(
            filtered_brand,
            x="ano_mes",
            y="emplacamentos",
            color="company_or_brand",
            labels={"company_or_brand": "Marca", "ano_mes": "Mes"},
        ),
        use_container_width=True,
    )
    st.dataframe(filtered_brand, use_container_width=True, hide_index=True)

with tab_comex:
    filtered_month = filter_period(comex, period)
    filtered_prefix = filter_period(comex_prefix, period)
    filtered_ncm = filter_period(comex_ncm, period)

    # Rotulo legivel do tipo de veiculo a partir do prefixo NCM.
    filtered_prefix = filtered_prefix.assign(
        tipo_ncm=filtered_prefix["ncm_prefixo_consulta"].map(prefix_label)
    )
    filtered_ncm = filtered_ncm.assign(
        tipo_ncm=filtered_ncm["ncm_prefixo_consulta"].map(prefix_label),
        classe_carga_label=filtered_ncm["classe_carga"].map(
            lambda c: CARGO_CLASS_LABELS.get(c, "Sem classe (nao-carga)")
        ),
    )

    prefixes = sorted(filtered_prefix["ncm_prefixo_consulta"].unique().tolist())
    selected_prefixes = st.multiselect(
        "Tipo (prefixo NCM)", prefixes, default=prefixes, format_func=prefix_label
    )
    filtered_prefix = filtered_prefix[
        filtered_prefix["ncm_prefixo_consulta"].isin(selected_prefixes)
    ]
    filtered_ncm = filtered_ncm[filtered_ncm["ncm_prefixo_consulta"].isin(selected_prefixes)]

    st.caption(
        "Metrica principal: **quantidade de veiculos** (NCMs de veiculos completos "
        "8702/8703/8704/8706/8711, medidos em numero de unidades). **8711 = motocicletas**, "
        "que dominam o volume; use o filtro de tipo para separar automoveis de motos. "
        "A dimensao **classe de carga** separa o 8704 em leve (<= 5 t) vs caminhoes (> 5 t), "
        "dumpers e cavalos-mecanicos. Valor FOB e kg ficam como metricas secundarias. "
        "Autopecas (8708) e carrocerias (8707) nao entram na contagem de veiculos."
    )
    dimension = st.selectbox(
        "Dimensao",
        ["tipo_ncm", "codigo_ncm", "classe_carga_label", "ano", "ano_mes"],
        format_func=lambda col: DIMENSION_LABELS.get(col, col),
    )
    measure = st.selectbox(
        "Metrica",
        ["quantidade_veiculos", "valor_fob_usd", "kg_liquido", "quantidade_estatistica"],
        format_func=lambda col: MEASURE_LABELS.get(col, col),
    )
    source = (
        filtered_ncm
        if dimension in ("codigo_ncm", "classe_carga_label")
        else filtered_prefix
    )
    measure_label = MEASURE_LABELS.get(measure, measure)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses", filtered_month["ano_mes"].nunique())
    c2.metric("Veiculos (unidades)", br_int(filtered_prefix["quantidade_veiculos"].sum()))
    c3.metric("Valor FOB", usd_bi(filtered_prefix["valor_fob_usd"].sum()))
    c4.metric("NCMs", filtered_ncm["codigo_ncm"].nunique())

    monthly_selected = (
        filtered_prefix.groupby(["ano_mes", "tipo_ncm"], as_index=False)[measure]
        .sum()
        .sort_values("ano_mes")
    )
    st.plotly_chart(
        px.line(
            monthly_selected,
            x="ano_mes",
            y=measure,
            color="tipo_ncm",
            markers=True,
            labels={"ano_mes": "Mes", measure: measure_label, "tipo_ncm": "Tipo"},
        ),
        use_container_width=True,
    )

    grouped = (
        source.groupby(dimension, dropna=False, as_index=False)[measure]
        .sum()
        .sort_values(measure, ascending=False)
        .head(30)
    )
    st.plotly_chart(
        px.bar(
            grouped,
            x=dimension,
            y=measure,
            labels={
                dimension: DIMENSION_LABELS.get(dimension, dimension),
                measure: measure_label,
            },
        ),
        use_container_width=True,
    )

    heatmap_df = (
        filtered_prefix.groupby(["ano", "tipo_ncm"], as_index=False)[measure]
        .sum()
        .pivot(index="tipo_ncm", columns="ano", values=measure)
        .fillna(0)
    )
    st.plotly_chart(
        px.imshow(
            heatmap_df,
            aspect="auto",
            labels={"x": "Ano", "y": "Tipo (prefixo NCM)", "color": measure_label},
        ),
        use_container_width=True,
    )

    st.dataframe(filtered_ncm, use_container_width=True, hide_index=True)

with tab_estoque:
    st.subheader("Estoque no canal (proxy)")
    st.caption(
        "Diferenca acumulada entre o que **entra** no pais (importacao Comex, unidades) "
        "e o que e **emplacado** (ANFAVEA, marcas chinesas) e uma proxy do estoque parado "
        "no canal (porto, importador, concessionaria). **Indicador direcional, nao exato**: "
        "(1) o Comex e por pais de origem e a ANFAVEA por marca chinesa - populacoes que se "
        "sobrepoem mas nao coincidem (ha marca chinesa ja produzida no Brasil, que emplaca "
        "sem importar, e importacao da China de marcas nao chinesas); (2) ha defasagem de "
        "~1-3 meses entre importar e emplacar; (3) o NCM 8704 mistura picapes e caminhoes."
    )

    segment_name = st.radio("Segmento", list(SEGMENT_MAP), horizontal=True)
    mapping = SEGMENT_MAP[segment_name]

    if "comex_classe" in mapping:
        classes = mapping["comex_classe"]
        imports_source = filter_period(comex_ncm, period).query("classe_carga in @classes")
    else:
        prefixes_sel = mapping["comex_prefix"]
        imports_source = filter_period(comex_prefix, period).query(
            "ncm_prefixo_consulta in @prefixes_sel"
        )
    imports = (
        imports_source.groupby("ano_mes", as_index=False)["quantidade_veiculos"]
        .sum()
        .rename(columns={"quantidade_veiculos": "importacao"})
    )
    regs = (
        filter_period(anfavea_segment, period)
        .query("vehicle_group in @mapping['anfavea']")
        .groupby("ano_mes", as_index=False)
        .agg(emplacamento=("emplacamentos", "sum"), emplacamento_min=("emplacamentos_chinesas_min", "sum"))
    )
    channel = imports.merge(regs, on="ano_mes", how="outer").fillna(0).sort_values("ano_mes")
    channel[["importacao", "emplacamento", "emplacamento_min"]] = channel[
        ["importacao", "emplacamento", "emplacamento_min"]
    ].astype(int)
    channel["gap_mensal"] = channel["importacao"] - channel["emplacamento"]
    channel["estoque_acumulado"] = channel["gap_mensal"].cumsum()

    if channel.empty:
        st.info("Sem dados no periodo selecionado.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Importado (unid.)", br_int(channel["importacao"].sum()))
        c2.metric("Emplacado (estimativa)", br_int(channel["emplacamento"].sum()))
        c3.metric(
            "Saldo acum. (imp - empl)",
            br_int(channel["estoque_acumulado"].iloc[-1]),
        )
        taxa = (
            channel["emplacamento"].sum() / channel["importacao"].sum()
            if channel["importacao"].sum()
            else 0
        )
        c4.metric("Emplacado / importado", f"{taxa * 100:.0f}%")

        st.caption(
            "Leitura do saldo acumulado: **positivo e crescente** = importacao a frente das "
            "vendas, estoque acumulando (ex.: automoveis em 2026, front-loading antes do "
            "imposto). **Negativo** = emplacamento a frente da importacao direta, sinal de "
            "producao local / montagem CKD no Brasil (ex.: caminhoes e comerciais leves, "
            "onde marcas como Effa, Shineray e JAC montam localmente) ou venda de estoque "
            "anterior. Para automoveis antes de 2026, o emplacamento usa o proxy \"Outras "
            "empresas\", que inclui algumas marcas nao chinesas e infla a serie."
        )

        flow = channel.melt(
            id_vars="ano_mes",
            value_vars=["importacao", "emplacamento"],
            var_name="serie",
            value_name="unidades",
        )
        flow["serie"] = flow["serie"].map(
            {"importacao": "Importacao (Comex)", "emplacamento": "Emplacamento (ANFAVEA)"}
        )
        st.plotly_chart(
            px.line(
                flow,
                x="ano_mes",
                y="unidades",
                color="serie",
                markers=True,
                labels={"ano_mes": "Mes", "unidades": "Unidades", "serie": ""},
                title="Fluxo mensal: entra (importacao) x sai (emplacamento)",
            ),
            use_container_width=True,
        )
        st.plotly_chart(
            px.area(
                channel,
                x="ano_mes",
                y="estoque_acumulado",
                labels={"ano_mes": "Mes", "estoque_acumulado": "Saldo acumulado (imp - empl)"},
                title="Saldo acumulado: importacao menos emplacamento (proxy de estoque no canal)",
            ),
            use_container_width=True,
        )

        if "Caminhões" in mapping["anfavea"]:
            trucks_only = (
                filter_period(anfavea_segment, period)
                .query("vehicle_group == 'Caminhões'")
                .groupby("ano_mes", as_index=False)["emplacamentos"]
                .sum()
            )
            imports_trucks = (
                filter_period(comex_ncm, period)
                .query("classe_carga in ['pesado_acima_5t','dumper_fora_estrada','cavalo_mecanico']")
                .groupby("ano_mes", as_index=False)["quantidade_veiculos"]
                .sum()
                .rename(columns={"quantidade_veiculos": "importacao_caminhoes_pesados"})
            )
            trucks = trucks_only.merge(imports_trucks, on="ano_mes", how="outer").fillna(0)
            trucks_long = trucks.melt(
                id_vars="ano_mes",
                value_vars=["importacao_caminhoes_pesados", "emplacamentos"],
                var_name="serie",
                value_name="unidades",
            )
            trucks_long["serie"] = trucks_long["serie"].map(
                {
                    "importacao_caminhoes_pesados": "Importacao caminhoes pesados (Comex 8704 >5t)",
                    "emplacamentos": "Emplacamento caminhoes chineses (ANFAVEA)",
                }
            )
            st.plotly_chart(
                px.line(
                    trucks_long,
                    x="ano_mes",
                    y="unidades",
                    color="serie",
                    markers=True,
                    labels={"ano_mes": "Mes", "unidades": "Unidades", "serie": ""},
                    title="Foco caminhoes: importacao de pesados x emplacamento chines",
                ),
                use_container_width=True,
            )
            st.caption(
                "Emplacamentos chineses de caminhoes por marca (Foton, JAC, Sany, Sinotruk) "
                "so tem detalhe a partir de 2026; antes disso a serie usa a linha agregada "
                "\"Outras empresas\" do grupo Caminhoes, praticamente toda chinesa - proxy "
                "confiavel. Do lado Comex, os caminhoes pesados sao o 8704 acima de 5 t, "
                "mais dumpers e cavalos-mecanicos (estes ultimos despreziveis vindos da China)."
            )

        st.dataframe(channel, use_container_width=True, hide_index=True)

with tab_cpca:
    filtered_cpca = filter_period(cpca, period)
    filtered_metrics = filter_period(cpca_metrics, period)
    metric_options = [
        col
        for col in filtered_cpca.columns
        if col not in {"ano", "mes", "ano_mes"} and filtered_cpca[col].notna().any()
    ]
    selected_cpca_metrics = st.multiselect(
        "Metricas CPCA",
        metric_options,
        default=[m for m in ["narrow_passenger_retail", "nev_narrow_passenger_retail", "nev_passenger_wholesale_estimate"] if m in metric_options],
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses CPCA", filtered_cpca["ano_mes"].nunique())
    if "narrow_passenger_retail" in filtered_cpca:
        c2.metric("Varejo passageiros", br_int(filtered_cpca["narrow_passenger_retail"].sum(skipna=True)))
    if "nev_narrow_passenger_retail" in filtered_cpca:
        c3.metric("NEV varejo", br_int(filtered_cpca["nev_narrow_passenger_retail"].sum(skipna=True)))
    if "nev_passenger_wholesale_estimate" in filtered_cpca:
        c4.metric("NEV atacado estimado", br_int(filtered_cpca["nev_passenger_wholesale_estimate"].sum(skipna=True)))

    cpca_long = filtered_cpca.melt(
        id_vars=["ano", "mes", "ano_mes"],
        value_vars=selected_cpca_metrics,
        var_name="metric_name",
        value_name="value",
    ).dropna(subset=["value"])
    st.plotly_chart(
        px.line(
            cpca_long,
            x="ano_mes",
            y="value",
            color="metric_name",
            markers=True,
            labels={"ano_mes": "Mes", "value": "Veiculos", "metric_name": "Metrica"},
        ),
        use_container_width=True,
    )

    if "nev_retail_penetration_pct" in filtered_cpca.columns:
        penetration = filtered_cpca.dropna(subset=["nev_retail_penetration_pct"])
        if not penetration.empty:
            st.plotly_chart(
                px.bar(
                    penetration,
                    x="ano_mes",
                    y="nev_retail_penetration_pct",
                    labels={"ano_mes": "Mes", "nev_retail_penetration_pct": "Penetracao NEV (%)"},
                ),
                use_container_width=True,
            )

    st.dataframe(filtered_metrics, use_container_width=True, hide_index=True)

with tab_caam:
    st.metric("Evidencias CAAM coletadas", len(caam_catalog))
    if not caam_catalog.empty:
        c1, c2 = st.columns(2)
        c1.plotly_chart(
            px.histogram(caam_catalog, x="article_type", color="evidence_role"),
            use_container_width=True,
        )
        c2.plotly_chart(
            px.bar(
                caam_catalog.groupby("article_type", as_index=False)["image_count"].sum(),
                x="article_type",
                y="image_count",
                labels={"article_type": "Tipo", "image_count": "Imagens brutas"},
            ),
            use_container_width=True,
        )
        st.dataframe(caam_catalog, use_container_width=True, hide_index=True)

with tab_compare:
    anf = filter_period(anfavea, period)
    cx = filter_period(comex, period)
    cp = filter_period(cpca, period)
    compare = anf[["ano_mes", "emplacamentos", "emplacamentos_chinesas_min"]].merge(
        cx[["ano_mes", "quantidade_veiculos", "valor_fob_usd"]],
        on="ano_mes",
        how="inner",
    )
    compare = compare.merge(
        cp[["ano_mes", "narrow_passenger_retail", "nev_narrow_passenger_retail"]],
        on="ano_mes",
        how="left",
    )
    if compare.empty:
        st.info("Nao ha meses sobrepostos no periodo selecionado.")
    else:
        st.caption(
            "Comparacao em volume: veiculos importados da China (Comex) x emplacamentos "
            "de marcas chinesas (ANFAVEA, estimativa). Ambos em unidades."
        )
        st.plotly_chart(
            px.scatter(
                compare,
                x="quantidade_veiculos",
                y="emplacamentos",
                trendline="ols",
                hover_data=["ano_mes"],
                labels={
                    "quantidade_veiculos": "Veiculos importados da China (Comex)",
                    "emplacamentos": "Emplacamentos chineses ANFAVEA (estimativa)",
                },
            ),
            use_container_width=True,
        )
        st.dataframe(compare, use_container_width=True, hide_index=True)
        comparison_long = compare.melt(
            id_vars=["ano_mes"],
            value_vars=[col for col in ["emplacamentos", "narrow_passenger_retail", "nev_narrow_passenger_retail"] if col in compare],
            var_name="serie",
            value_name="veiculos",
        ).dropna()
        st.plotly_chart(
            px.line(comparison_long, x="ano_mes", y="veiculos", color="serie", markers=True),
            use_container_width=True,
        )

with tab_data:
    tables = {
        "gold_anfavea_chinese_registrations_monthly": anfavea,
        "gold_anfavea_chinese_registrations_by_brand_monthly": anfavea_brand,
        "gold_anfavea_chinese_registrations_by_segment_monthly": anfavea_segment,
        "raw_anfavea_origin_brand_monthly": con.execute(
            "select * from raw_anfavea_origin_brand_monthly order by ano_mes"
        ).df(),
        "gold_comex_china_automotive_monthly": comex,
        "gold_comex_china_automotive_by_prefix_monthly": comex_prefix,
        "gold_comex_china_automotive_by_ncm_monthly": comex_ncm,
        "gold_cpca_passenger_market_monthly": cpca,
        "raw_cpca_article_metrics": cpca_metrics,
        "raw_caam_evidence_catalog": caam_catalog,
    }
    table = st.selectbox("Tabela", list(tables))
    data = filter_period(tables[table], period) if "ano_mes" in tables[table].columns else tables[table]
    st.download_button(
        "Baixar CSV",
        data.to_csv(index=False).encode("utf-8"),
        file_name=f"{table}.csv",
        mime="text/csv",
    )
    st.dataframe(data, use_container_width=True, hide_index=True)

with tab_saude:
    st.subheader("Saude dos dados")
    st.caption(
        "Painel de confianca: os dados sao **atuais e validados**? Reune os 51 checks "
        "automaticos de qualidade, a cobertura/frescor de cada fonte e o escopo declarado "
        "da analise. Ignora o filtro de periodo da barra lateral - mostra sempre o estado "
        "completo do pipeline."
    )

    # --- Bloco 1: Qualidade (ops/quality/results/latest.yml) ---
    st.markdown("#### 1. Qualidade")
    quality = load_yaml("ops/quality/results/latest.yml")
    if quality is None:
        st.info(
            "Sem resultado de qualidade. Rode `python scripts/run_quality_checks.py`."
        )
    else:
        summary = quality.get("summary", {})
        total = summary.get("checks", 0)
        passed = summary.get("passed", 0)
        failed = summary.get("failed", 0)
        status = quality.get("status", "?")
        generated_at = str(quality.get("generated_at", "-")).replace("T", " ")

        if status == "pass" and failed == 0:
            st.success(f"**{passed}/{total} checks OK** - ultima verificacao em {generated_at}")
        else:
            st.error(f"**{failed} de {total} checks falharam** - ultima verificacao em {generated_at}")

        c1, c2, c3 = st.columns(3)
        c1.metric("Checks aprovados", f"{passed}/{total}")
        c2.metric("Falhas", failed)
        c3.metric("Status", "OK" if status == "pass" else status.upper())

        checks_df = pd.DataFrame(quality.get("checks", []))
        if not checks_df.empty:
            failures = checks_df[checks_df["status"] != "pass"]
            if not failures.empty:
                st.markdown("**Checks com falha:**")
                st.dataframe(
                    failures[["name", "status", "observed", "expected", "details"]],
                    use_container_width=True,
                    hide_index=True,
                )
            with st.expander(f"Ver todos os {len(checks_df)} checks"):
                st.dataframe(
                    checks_df[["name", "status", "observed", "expected"]],
                    use_container_width=True,
                    hide_index=True,
                )

    # --- Bloco 2: Cobertura e frescor ---
    st.markdown("#### 2. Cobertura e frescor")
    st.caption("Ate quando cada fonte vai e quantos meses/linhas ela cobre.")
    coverage_sources = {
        "ANFAVEA (emplacamentos)": anfavea,
        "Comex Stat (importacao)": comex,
        "CPCA (mercado China)": cpca,
    }
    coverage_rows = []
    for label, df in coverage_sources.items():
        if df.empty or "ano_mes" in df.columns and df["ano_mes"].dropna().empty:
            coverage_rows.append({"Fonte": label, "Primeiro mes": "-", "Ultimo mes": "-", "Meses": 0, "Linhas": 0})
            continue
        meses = df["ano_mes"].dropna()
        coverage_rows.append(
            {
                "Fonte": label,
                "Primeiro mes": meses.min(),
                "Ultimo mes": meses.max(),
                "Meses": meses.nunique(),
                "Linhas": len(df),
            }
        )
    coverage_df = pd.DataFrame(coverage_rows)
    latest_month = max(
        (r["Ultimo mes"] for r in coverage_rows if r["Ultimo mes"] != "-"),
        default="-",
    )
    m1, m2 = st.columns(2)
    m1.metric("Mes mais recente (qualquer fonte)", latest_month)
    m2.metric("Fontes cobertas", len(coverage_rows))
    st.dataframe(coverage_df, use_container_width=True, hide_index=True)

    # --- Bloco 3: Escopo e linhagem ---
    st.markdown("#### 3. Escopo e linhagem")
    scope = load_yaml("ops/metadata/research_scope.yml")
    brands_cfg = load_yaml("ops/metadata/brand_classification.yml")

    focus = None
    ncm_codes = []
    if scope:
        rs = scope.get("research_scope", {})
        focus = rs.get("primary_focus")
        for q in rs.get("questions", []):
            if q.get("ncm_codes"):
                ncm_codes = q["ncm_codes"]
    if focus:
        st.info(f"**Foco principal:** {focus.strip()}")
    if ncm_codes:
        labels = ", ".join(f"`{code}`" for code in ncm_codes)
        st.markdown(f"**NCMs consultados (Comex):** {labels}")
        st.caption(
            "8704 classificado por classe de peso (leve <= 5 t vs caminhoes > 5 t); "
            "87012 = cavalos-mecanicos, incluido por completude (importacao chinesa desprezivel)."
        )

    if brands_cfg:
        brands = brands_cfg.get("brands", [])
        in_scope = sorted(
            b["brand"] for b in brands if b.get("include_in_chinese_cars_scope")
        )
        out_scope = sorted(
            b["brand"] for b in brands if not b.get("include_in_chinese_cars_scope")
        )
        st.markdown(f"**Marcas chinesas no recorte ({len(in_scope)}):** {', '.join(in_scope)}")
        if out_scope:
            st.caption(
                f"Fora do recorte (aparecem em \"Outras empresas\" mas nao sao chinesas): "
                f"{', '.join(out_scope)}"
            )
