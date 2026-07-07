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

all_periods = sorted(set(anfavea["ano_mes"]).union(set(comex["ano_mes"])))
period = st.sidebar.select_slider(
    "Periodo",
    options=all_periods,
    value=(all_periods[0], all_periods[-1]),
)

tab_anfavea, tab_comex, tab_compare, tab_data = st.tabs(
    ["ANFAVEA", "Comex Stat", "Comparativo", "Dados"]
)

with tab_anfavea:
    filtered = filter_period(anfavea, period)
    filtered_brand = filter_period(anfavea_brand, period)

    brands = sorted(filtered_brand["company_or_brand"].dropna().unique().tolist())
    vehicle_groups = sorted(filtered_brand["vehicle_group"].dropna().unique().tolist())
    selected_brands = st.multiselect("Marca", brands, default=brands)
    selected_groups = st.multiselect("Segmento ANFAVEA", vehicle_groups, default=vehicle_groups)

    filtered_brand = filtered_brand[
        filtered_brand["company_or_brand"].isin(selected_brands)
        & filtered_brand["vehicle_group"].isin(selected_groups)
    ]
    filtered = (
        filtered_brand.groupby(["ano", "mes", "ano_mes"], as_index=False)["emplacamentos"]
        .sum()
        .merge(
            anfavea[["ano", "mes", "ano_mes", "emplacamentos_total_anfavea"]],
            on=["ano", "mes", "ano_mes"],
            how="left",
        )
    )
    filtered["participacao_total_anfavea"] = (
        filtered["emplacamentos"] / filtered["emplacamentos_total_anfavea"]
    )

    latest = filtered.iloc[-1] if not filtered.empty else None
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses", len(filtered))
    c2.metric("Emplacamentos", br_int(filtered["emplacamentos"].sum()))
    c3.metric(
        "Participacao media",
        f"{filtered['participacao_total_anfavea'].mean() * 100:.2f}%",
    )
    c4.metric("Ultimo mes", latest["ano_mes"] if latest is not None else "-")

    metric = st.radio(
        "Metrica",
        ["emplacamentos", "participacao_total_anfavea"],
        horizontal=True,
    )
    fig = px.line(
        filtered,
        x="ano_mes",
        y=metric,
        markers=True,
        labels={
            "ano_mes": "Mes",
            "emplacamentos": "Emplacamentos",
            "participacao_total_anfavea": "Participacao",
        },
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    annual = (
        filtered.groupby("ano", as_index=False)
        .agg(
            emplacamentos=("emplacamentos", "sum"),
            total_anfavea=("emplacamentos_total_anfavea", "sum"),
        )
        .assign(participacao=lambda df: df["emplacamentos"] / df["total_anfavea"])
    )
    col1.dataframe(annual, use_container_width=True, hide_index=True)

    rank = (
        filtered_brand.groupby("company_or_brand", as_index=False)["emplacamentos"]
        .sum()
        .sort_values("emplacamentos", ascending=False)
    )
    col2.plotly_chart(
        px.bar(rank, x="company_or_brand", y="emplacamentos", labels={"company_or_brand": "Marca"}),
        use_container_width=True,
    )

    st.plotly_chart(
        px.bar(
            filtered_brand,
            x="ano_mes",
            y="emplacamentos",
            color="company_or_brand",
            facet_row="vehicle_group" if filtered_brand["vehicle_group"].nunique() > 1 else None,
            labels={"company_or_brand": "Marca", "ano_mes": "Mes"},
        ),
        use_container_width=True,
    )

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

    dimension = st.selectbox(
        "Dimensao",
        ["ncm_prefixo_consulta", "codigo_ncm", "ano", "ano_mes"],
    )
    measure = st.selectbox(
        "Metrica",
        ["valor_fob_usd", "kg_liquido", "quantidade_estatistica"],
    )
    source = filtered_ncm if dimension == "codigo_ncm" else filtered_prefix

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Meses", filtered_month["ano_mes"].nunique())
    c2.metric("Valor FOB", usd_bi(filtered_prefix["valor_fob_usd"].sum()))
    c3.metric("Kg liquido", f"{filtered_prefix['kg_liquido'].sum() / 1_000_000:.1f} mi kg")
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

with tab_compare:
    anf = filter_period(anfavea, period)
    cx = filter_period(comex, period)
    compare = anf[["ano_mes", "emplacamentos"]].merge(
        cx[["ano_mes", "valor_fob_usd"]],
        on="ano_mes",
        how="inner",
    )
    if compare.empty:
        st.info("Nao ha meses sobrepostos no periodo selecionado.")
    else:
        compare["valor_fob_usd_bi"] = compare["valor_fob_usd"] / 1_000_000_000
        st.plotly_chart(
            px.scatter(
                compare,
                x="valor_fob_usd_bi",
                y="emplacamentos",
                trendline="ols",
                hover_data=["ano_mes"],
                labels={
                    "valor_fob_usd_bi": "Comex FOB US$ bi",
                    "emplacamentos": "Emplacamentos ANFAVEA",
                },
            ),
            use_container_width=True,
        )
        st.dataframe(compare, use_container_width=True, hide_index=True)

with tab_data:
    tables = {
        "gold_anfavea_chinese_registrations_monthly": anfavea,
        "gold_anfavea_chinese_registrations_by_brand_monthly": anfavea_brand,
        "gold_comex_china_automotive_monthly": comex,
        "gold_comex_china_automotive_by_prefix_monthly": comex_prefix,
        "gold_comex_china_automotive_by_ncm_monthly": comex_ncm,
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

