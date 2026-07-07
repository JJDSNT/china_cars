import duckdb
import plotly.express as px
import streamlit as st

from china_cars.db import database_path


st.set_page_config(page_title="China Cars", layout="wide")
st.title("China Cars")

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

tab_anfavea, tab_comex, tab_data = st.tabs(["ANFAVEA", "Comex Stat", "Dados"])

with tab_anfavea:
    latest = anfavea.iloc[-1]
    ytd = anfavea[anfavea["ano"].eq(latest["ano"])]
    c1, c2, c3 = st.columns(3)
    c1.metric("Ultimo mes", latest["ano_mes"])
    c2.metric("Emplacamentos no mes", f"{int(latest['emplacamentos']):,}".replace(",", "."))
    c3.metric("Acumulado 2026", f"{int(ytd['emplacamentos'].sum()):,}".replace(",", "."))

    fig = px.line(
        anfavea,
        x="ano_mes",
        y="emplacamentos",
        markers=True,
        labels={"ano_mes": "Mes", "emplacamentos": "Emplacamentos"},
    )
    st.plotly_chart(fig, use_container_width=True)

    annual = (
        anfavea.groupby("ano", as_index=False)
        .agg(
            emplacamentos=("emplacamentos", "sum"),
            total_anfavea=("emplacamentos_total_anfavea", "sum"),
        )
        .assign(participacao=lambda df: df["emplacamentos"] / df["total_anfavea"])
    )
    st.dataframe(annual, use_container_width=True, hide_index=True)

    fig_brand = px.bar(
        anfavea_brand,
        x="ano_mes",
        y="emplacamentos",
        color="company_or_brand",
        labels={"ano_mes": "Mes", "emplacamentos": "Emplacamentos", "company_or_brand": "Marca"},
    )
    st.plotly_chart(fig_brand, use_container_width=True)

with tab_comex:
    latest = comex.iloc[-1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Ultimo mes", latest["ano_mes"])
    c2.metric("FOB no mes", f"US$ {latest['valor_fob_usd']/1e9:.2f} bi")
    c3.metric("Kg liquido no mes", f"{latest['kg_liquido']/1e6:.1f} mi kg")

    fig = px.line(
        comex,
        x="ano_mes",
        y="valor_fob_usd",
        markers=True,
        labels={"ano_mes": "Mes", "valor_fob_usd": "Valor FOB US$"},
    )
    st.plotly_chart(fig, use_container_width=True)

    prefix_options = sorted(comex_prefix["ncm_prefixo_consulta"].unique().tolist())
    selected_prefix = st.multiselect("NCM", prefix_options, default=prefix_options)
    filtered_prefix = comex_prefix[comex_prefix["ncm_prefixo_consulta"].isin(selected_prefix)]
    fig_prefix = px.bar(
        filtered_prefix,
        x="ano_mes",
        y="valor_fob_usd",
        color="ncm_prefixo_consulta",
        labels={
            "ano_mes": "Mes",
            "valor_fob_usd": "Valor FOB US$",
            "ncm_prefixo_consulta": "Prefixo NCM",
        },
    )
    st.plotly_chart(fig_prefix, use_container_width=True)
    st.dataframe(filtered_prefix, use_container_width=True, hide_index=True)

with tab_data:
    table = st.selectbox(
        "Tabela",
        [
            "gold_anfavea_chinese_registrations_monthly",
            "gold_anfavea_chinese_registrations_by_brand_monthly",
            "gold_comex_china_automotive_monthly",
            "gold_comex_china_automotive_by_prefix_monthly",
            "gold_comex_china_automotive_by_ncm_monthly",
        ],
    )
    data = {
        "gold_anfavea_chinese_registrations_monthly": anfavea,
        "gold_anfavea_chinese_registrations_by_brand_monthly": anfavea_brand,
        "gold_comex_china_automotive_monthly": comex,
        "gold_comex_china_automotive_by_prefix_monthly": comex_prefix,
        "gold_comex_china_automotive_by_ncm_monthly": comex_ncm,
    }[table]
    st.dataframe(data, use_container_width=True, hide_index=True)

