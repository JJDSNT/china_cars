import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

from china_cars.db import database_path


st.set_page_config(page_title="China Cars", layout="wide")
st.title("China Cars")


def br_int(value: float) -> str:
    return f"{int(value):,}".replace(",", ".")


def usd_bi(value: float) -> str:
    return f"US$ {value / 1_000_000_000:.2f} bi"


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

tab_anfavea, tab_comex, tab_cpca, tab_caam, tab_compare, tab_data = st.tabs(
    ["ANFAVEA", "Comex Stat", "CPCA", "CAAM", "Comparativo", "Dados"]
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

    prefixes = sorted(filtered_prefix["ncm_prefixo_consulta"].unique().tolist())
    selected_prefixes = st.multiselect("Prefixo NCM", prefixes, default=prefixes)
    filtered_prefix = filtered_prefix[
        filtered_prefix["ncm_prefixo_consulta"].isin(selected_prefixes)
    ]
    filtered_ncm = filtered_ncm[filtered_ncm["ncm_prefixo_consulta"].isin(selected_prefixes)]

    st.caption(
        "Metrica principal: **quantidade de veiculos** (NCMs de veiculos completos "
        "8702/8703/8704/8706/87011, medidos em numero de unidades). Valor FOB e kg "
        "ficam como metricas secundarias. Autopecas (8708) e carrocerias (8707) nao "
        "entram na contagem de veiculos."
    )
    dimension = st.selectbox(
        "Dimensao",
        ["ncm_prefixo_consulta", "codigo_ncm", "ano", "ano_mes"],
    )
    measure = st.selectbox(
        "Metrica",
        ["quantidade_veiculos", "valor_fob_usd", "kg_liquido", "quantidade_estatistica"],
    )
    source = filtered_ncm if dimension == "codigo_ncm" else filtered_prefix

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses", filtered_month["ano_mes"].nunique())
    c2.metric("Veiculos (unidades)", br_int(filtered_prefix["quantidade_veiculos"].sum()))
    c3.metric("Valor FOB", usd_bi(filtered_prefix["valor_fob_usd"].sum()))
    c4.metric("NCMs", filtered_ncm["codigo_ncm"].nunique())

    monthly_selected = (
        filtered_prefix.groupby("ano_mes", as_index=False)[measure]
        .sum()
        .sort_values("ano_mes")
    )
    st.plotly_chart(
        px.line(monthly_selected, x="ano_mes", y=measure, markers=True),
        use_container_width=True,
    )

    grouped = (
        source.groupby(dimension, dropna=False, as_index=False)[measure]
        .sum()
        .sort_values(measure, ascending=False)
        .head(30)
    )
    st.plotly_chart(px.bar(grouped, x=dimension, y=measure), use_container_width=True)

    heatmap_df = (
        filtered_prefix.groupby(["ano", "ncm_prefixo_consulta"], as_index=False)[measure]
        .sum()
        .pivot(index="ncm_prefixo_consulta", columns="ano", values=measure)
        .fillna(0)
    )
    st.plotly_chart(
        px.imshow(
            heatmap_df,
            aspect="auto",
            labels={"x": "Ano", "y": "Prefixo NCM", "color": measure},
        ),
        use_container_width=True,
    )

    st.dataframe(filtered_ncm, use_container_width=True, hide_index=True)

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
