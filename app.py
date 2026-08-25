# -*- coding: utf-8 -*-
"""
Dashboard de Vagas — TI / Engenharia de Software (Streamlit, arquivo único)

Instalar dependências:
    pip install streamlit pandas openpyxl plotly

Rodar:
    streamlit run app.py
"""
import os
import re

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Vagas TI — Dashboard", layout="wide")

# ---------------- ESTILIZAÇÃO (CSS customizado) ----------------
st.markdown("""
<style>
    html, body, [class*="css"]  { font-family: 'Segoe UI', Arial, sans-serif; }
    .main { background-color: #F4F6F8; }

    /* Título */
    .dash-title { font-size: 30px; font-weight: 700; color: #1B2A4A; margin-bottom: 2px; }
    .dash-subtitle { color: #6C757D; margin-bottom: 24px; }

    /* Cards de KPI */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        border-left: 6px solid var(--kpi-color, #2E86AB);
    }
    .kpi-label { font-size: 13px; color: #6C757D; margin-bottom: 4px; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #1B2A4A; }

    /* Cards de gráfico */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        padding: 4px;
    }

    /* Sidebar */
    section[data-testid="stSidebar"] { background-color: #1B2A4A; }
    section[data-testid="stSidebar"] * { color: #F4F6F8 !important; }

    /* Tabela */
    div[data-testid="stDataFrame"] { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

CORES_NICHO = {
    "Fintechs": "#2E86AB",
    "E-commerce / Marketplace": "#3AAA6B",
    "Software Houses / Consultorias de TI": "#E8A93E",
}

XLSX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vagas_ti_engenharia_software.xlsx")


# ---------------- CARREGAMENTO E LIMPEZA DOS DADOS ----------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name="Vagas TI")

    df = df.rename(columns={
        "Nicho de mercado": "nicho",
        "Nome da empresa": "empresa",
        "Título da vaga": "titulo",
        "Salário divulgado?": "salario_divulgado",
        "Valor do salário": "valor_salario",
        "Texto da vaga / palavras-chave mais pedidas": "palavras_chave",
        "Cargo": "cargo",
        "Modalidade": "modalidade",
        "Tipo de contrato": "contrato",
        "Carga horária semanal": "carga_horaria_txt",
        "Interessante para mim?": "interesse",
        "Justificativa": "justificativa",
    })

    # Extrai a carga horária semanal como número (ex: "30h" -> 30)
    df["carga_horaria"] = (
        df["carga_horaria_txt"]
        .astype(str)
        .apply(lambda x: int(re.sub(r"\D", "", x)) if re.search(r"\d", x) else None)
    )

    return df


df = load_data(XLSX_PATH)

st.markdown('<div class="dash-title">Dashboard de Vagas — TI / Engenharia de Software</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Fintechs · E-commerce / Marketplace · Software Houses / Consultorias de TI</div>', unsafe_allow_html=True)

# ---------------- SIDEBAR: FILTROS ----------------
st.sidebar.header("Filtros")

nichos = st.sidebar.multiselect(
    "Nicho de mercado (grupos)",
    sorted(df["nicho"].unique()),
    default=sorted(df["nicho"].unique()),
)
contratos = st.sidebar.multiselect(
    "Tipo de contrato",
    sorted(df["contrato"].unique()),
    default=sorted(df["contrato"].unique()),
)
cargas = st.sidebar.multiselect(
    "Carga horária semanal",
    sorted(df["carga_horaria"].dropna().unique()),
    default=sorted(df["carga_horaria"].dropna().unique()),
    format_func=lambda x: f"{int(x)}h",
)
interesses = st.sidebar.multiselect(
    "Interessante para mim?",
    sorted(df["interesse"].unique()),
    default=sorted(df["interesse"].unique()),
)

d = df[
    df["nicho"].isin(nichos)
    & df["contrato"].isin(contratos)
    & df["carga_horaria"].isin(cargas)
    & df["interesse"].isin(interesses)
]

# ---------------- KPIs (cards estilizados) ----------------
kpi_data = [
    ("Vagas filtradas", len(d), "#2E86AB"),
    ("Empresas", d["empresa"].nunique(), "#3AAA6B"),
    ("Interessantes (Sim)", int((d["interesse"] == "Sim").sum()), "#E8A93E"),
    ("Carga média semanal", f"{d['carga_horaria'].mean():.0f}h" if len(d) else "—", "#8E44AD"),
]
cols_kpi = st.columns(4)
for col, (label, value, cor) in zip(cols_kpi, kpi_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:{cor}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")
st.write("")

# ---------------- GRÁFICOS ----------------
TEMPLATE = "plotly_white"

col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        if len(d):
            agrupado = d.groupby(["carga_horaria", "nicho"]).size().reset_index(name="qtd_vagas")
            agrupado["carga_horaria_lbl"] = agrupado["carga_horaria"].astype(int).astype(str) + "h"
            fig = px.bar(
                agrupado, x="carga_horaria_lbl", y="qtd_vagas", color="nicho", barmode="group",
                title="Vagas por carga horária semanal, agrupadas por nicho",
                labels={"carga_horaria_lbl": "Carga horária", "qtd_vagas": "Qtd. de vagas", "nicho": "Nicho"},
                color_discrete_map=CORES_NICHO,
            )
            fig.update_layout(template=TEMPLATE, legend_title_text="")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Nenhuma vaga para os filtros selecionados.")

with col2:
    with st.container(border=True):
        if len(d):
            agrupado2 = d.groupby(["contrato", "nicho"]).size().reset_index(name="qtd_vagas")
            fig2 = px.bar(
                agrupado2, x="contrato", y="qtd_vagas", color="nicho", barmode="group",
                title="Vagas por tipo de contrato, agrupadas por nicho",
                labels={"contrato": "Contrato", "qtd_vagas": "Qtd. de vagas", "nicho": "Nicho"},
                color_discrete_map=CORES_NICHO,
            )
            fig2.update_layout(template=TEMPLATE, legend_title_text="")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nenhuma vaga para os filtros selecionados.")

col3, col4 = st.columns(2)
with col3:
    with st.container(border=True):
        if len(d):
            fig3 = px.pie(
                d, names="interesse", title="Distribuição de interesse (Sim/Não)", hole=0.45,
                color="interesse", color_discrete_map={"Sim": "#3AAA6B", "Não": "#D9534F"},
            )
            fig3.update_layout(template=TEMPLATE)
            st.plotly_chart(fig3, use_container_width=True)

with col4:
    with st.container(border=True):
        if len(d):
            fig4 = px.bar(
                d.groupby("modalidade").size().reset_index(name="qtd_vagas"),
                x="modalidade", y="qtd_vagas", title="Vagas por modalidade",
                labels={"modalidade": "Modalidade", "qtd_vagas": "Qtd. de vagas"},
                color="modalidade", color_discrete_sequence=px.colors.qualitative.Set2,
            )
            fig4.update_layout(template=TEMPLATE, showlegend=False)
            st.plotly_chart(fig4, use_container_width=True)

st.write("")
st.markdown('<div class="dash-subtitle" style="font-size:18px; font-weight:700; color:#1B2A4A;">Tabela de vagas filtradas</div>', unsafe_allow_html=True)
st.dataframe(
    d[[
        "nicho", "empresa", "titulo", "contrato", "carga_horaria_txt", "modalidade",
        "salario_divulgado", "valor_salario", "interesse", "justificativa",
    ]],
    use_container_width=True,
    hide_index=True,
)