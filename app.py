# -*- coding: utf-8 -*-
"""
Dashboard de Vagas — TI / Engenharia de Software (Versão Otimizada)

Instalar dependências:
    pip install streamlit pandas openpyxl plotly

Rodar:
    streamlit run app.py
"""
from collections import Counter
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Vagas TI — Dashboard",
    page_icon="💼",
    layout="wide",
)

# ---------------- ESTILIZAÇÃO (CSS customizado) ----------------
st.markdown("""
<style>
    html, body, [class*="css"]  { font-family: 'Segoe UI', Arial, sans-serif; }
    .main { background-color: #F8FAFC; }

    /* Títulos */
    .dash-title { font-size: 32px; font-weight: 700; color: #1B2A4A; margin-bottom: 4px; }
    .dash-subtitle { color: #6C757D; margin-bottom: 24px; font-size: 16px; }

    /* Cards de KPI */
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        border-left: 5px solid var(--kpi-color, #2E86AB);
        margin-bottom: 10px;
    }
    .kpi-label { font-size: 13px; color: #6C757D; margin-bottom: 4px; font-weight: 500; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #1B2A4A; }

    /* Containers de Gráficos */
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background: white;
        border-radius: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
        padding: 8px;
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

TEMPLATE = "plotly_white"
BASE_DIR = Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
XLSX_PATH = BASE_DIR / "vagas_ti_engenharia_software.xlsx"


def parse_salario(texto: str):
    """Extrai o valor médio do salário caso seja um número único ou uma faixa (ex: R$ 2.200 a R$ 2.500)."""
    if pd.isna(texto) or "Não divulgado" in str(texto):
        return None
    
    # Encontra todos os números com possíveis separadores de milhar/decimal
    numeros = re.findall(r'R\$\s*([\d\.\,]+)', str(texto))
    
    valores = []
    for num in numeros:
        # Limpa o formato para float python
        num_clean = num.replace('.', '').replace(',', '.')
        try:
            valores.append(float(num_clean))
        except ValueError:
            pass
            
    if valores:
        return sum(valores) / len(valores)  # Média se for faixa
    return None


# ---------------- CARREGAMENTO E LIMPEZA DOS DADOS ----------------
@st.cache_data
def load_data(path: Path) -> pd.DataFrame:
    if not path.exists():
        st.error(f"Arquivo não encontrado: `{path.name}`. Certifique-se de que o arquivo Excel está no mesmo diretório.")
        st.stop()

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

    # Extrai a carga horária semanal numérica
    df["carga_horaria"] = (
        df["carga_horaria_txt"]
        .astype(str)
        .str.extract(r"(\d+)", expand=False)
        .astype(float)
    )

    # Parser numérico de salário
    df["valor_salario_num"] = df["valor_salario"].apply(parse_salario)

    return df


df = load_data(XLSX_PATH)

# Header Principal
st.markdown('<div class="dash-title">Dashboard de Vagas — TI / Engenharia de Software</div>', unsafe_allow_html=True)
st.markdown('<div class="dash-subtitle">Fintechs · E-commerce / Marketplace · Software Houses / Consultorias de TI</div>', unsafe_allow_html=True)


# ---------------- SIDEBAR: FILTROS E RESET ----------------
st.sidebar.header("Filtros")

all_nichos = sorted(df["nicho"].dropna().unique().tolist())
all_contratos = sorted(df["contrato"].dropna().unique().tolist())
all_cargas = sorted(df["carga_horaria"].dropna().unique().tolist())
all_interesses = sorted(df["interesse"].dropna().unique().tolist())

if "selected_nichos" not in st.session_state:
    st.session_state["selected_nichos"] = all_nichos
if "selected_contratos" not in st.session_state:
    st.session_state["selected_contratos"] = all_contratos
if "selected_cargas" not in st.session_state:
    st.session_state["selected_cargas"] = all_cargas
if "selected_interesses" not in st.session_state:
    st.session_state["selected_interesses"] = all_interesses

def reset_filters():
    st.session_state["selected_nichos"] = all_nichos
    st.session_state["selected_contratos"] = all_contratos
    st.session_state["selected_cargas"] = all_cargas
    st.session_state["selected_interesses"] = all_interesses

st.sidebar.button("🔄 Resetar Filtros", on_click=reset_filters, use_container_width=True)
st.sidebar.write("---")

nichos = st.sidebar.multiselect("Nicho de mercado", options=all_nichos, key="selected_nichos")
contratos = st.sidebar.multiselect("Tipo de contrato", options=all_contratos, key="selected_contratos")
cargas = st.sidebar.multiselect(
    "Carga horária semanal",
    options=all_cargas,
    format_func=lambda x: f"{int(x)}h" if pd.notnull(x) else "N/A",
    key="selected_cargas"
)
interesses = st.sidebar.multiselect("Interessante para mim?", options=all_interesses, key="selected_interesses")

# Aplicação dos Filtros
d = df[
    df["nicho"].isin(nichos)
    & df["contrato"].isin(contratos)
    & df["carga_horaria"].isin(cargas)
    & df["interesse"].isin(interesses)
]

# ---------------- TRATAMENTO DE FILTRO VAZIO ----------------
if d.empty:
    st.warning("⚠️ Nenhuma vaga encontrada para a combinação de filtros selecionada.")
    st.stop()

# ---------------- CÁLCULO DOS KPIs ----------------
salarios_validos = d["valor_salario_num"].dropna()
if len(salarios_validos) > 0:
    salario_medio_val = salarios_validos.mean()
    media_salario_txt = f"R$ {salario_medio_val:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
else:
    media_salario_txt = "—"

kpi_data = [
    ("Vagas filtradas", len(d), "#2E86AB"),
    ("Empresas ativas", d["empresa"].nunique(), "#3AAA6B"),
    ("Interessantes (Sim)", int((d["interesse"] == "Sim").sum()), "#E8A93E"),
    ("Carga média semanal", f"{d['carga_horaria'].mean():.0f}h" if d['carga_horaria'].notnull().any() else "—", "#8E44AD"),
    ("Salário médio divulgado", media_salario_txt, "#D9534F"),
]

cols_kpi = st.columns(5)
for col, (label, value, cor) in zip(cols_kpi, kpi_data):
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="--kpi-color:{cor}">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
        </div>
        """, unsafe_allow_html=True)

st.write("")

# ---------------- GRÁFICOS ----------------
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        agrupado = d.groupby(["carga_horaria", "nicho"]).size().reset_index(name="qtd_vagas")
        agrupado = agrupado.sort_values("carga_horaria")
        agrupado["carga_horaria_lbl"] = agrupado["carga_horaria"].astype(int).astype(str) + "h"
        
        fig = px.bar(
            agrupado, x="carga_horaria_lbl", y="qtd_vagas", color="nicho", barmode="group",
            title="Vagas por Carga Horária Semanal",
            labels={"carga_horaria_lbl": "Carga horária", "qtd_vagas": "Qtd. de vagas", "nicho": "Nicho"},
            color_discrete_map=CORES_NICHO,
        )
        fig.update_layout(template=TEMPLATE, legend_title_text="", margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)

with col2:
    with st.container(border=True):
        agrupado2 = d.groupby(["contrato", "nicho"]).size().reset_index(name="qtd_vagas")
        fig2 = px.bar(
            agrupado2, x="contrato", y="qtd_vagas", color="nicho", barmode="group",
            title="Vagas por Tipo de Contrato",
            labels={"contrato": "Contrato", "qtd_vagas": "Qtd. de vagas", "nicho": "Nicho"},
            color_discrete_map=CORES_NICHO,
        )
        fig2.update_layout(template=TEMPLATE, legend_title_text="", margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig2, use_container_width=True)

col3, col4 = st.columns(2)

with col3:
    with st.container(border=True):
        fig3 = px.pie(
            d, names="interesse", title="Distribuição de Interesse (Sim/Não)", hole=0.45,
            color="interesse", color_discrete_map={"Sim": "#3AAA6B", "Não": "#D9534F"},
        )
        fig3.update_layout(template=TEMPLATE, margin=dict(t=40, b=20, l=10, r=10))
        st.plotly_chart(fig3, use_container_width=True)

with col4:
    with st.container(border=True):
        words = []
        for text in d["palavras_chave"].dropna():
            tokens = [t.strip().title() for t in re.split(r"[,/;\n]", str(text)) if len(t.strip()) > 1]
            words.extend(tokens)
        
        if words:
            top_words = pd.DataFrame(Counter(words).most_common(8), columns=["Tecnologia", "Qtd"])
            fig4 = px.bar(
                top_words, x="Qtd", y="Tecnologia", orientation="h",
                title="Top 8 Tecnologias Pedidas nas Vagas",
                labels={"Qtd": "Ocorrências", "Tecnologia": ""},
                color_discrete_sequence=["#2E86AB"]
            )
            fig4.update_layout(template=TEMPLATE, yaxis=dict(autorange="reversed"), margin=dict(t=40, b=20, l=10, r=10))
            st.plotly_chart(fig4, use_container_width=True)

# ---------------- TABELA DE DADOS ----------------
st.write("")
st.markdown('<div class="dash-subtitle" style="font-size:18px; font-weight:700; color:#1B2A4A;">Tabela de Vagas Filtradas</div>', unsafe_allow_html=True)

st.dataframe(
    d[[
        "nicho", "empresa", "titulo", "contrato", "carga_horaria_txt", "modalidade",
        "salario_divulgado", "valor_salario", "interesse", "justificativa",
    ]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "nicho": st.column_config.TextColumn("Nicho"),
        "empresa": st.column_config.TextColumn("Empresa"),
        "titulo": st.column_config.TextColumn("Título da Vaga"),
        "contrato": st.column_config.TextColumn("Contrato"),
        "carga_horaria_txt": st.column_config.TextColumn("Carga Horária"),
        "modalidade": st.column_config.TextColumn("Modalidade"),
        "salario_divulgado": st.column_config.TextColumn("Salário Divulgado?"),
        "valor_salario": st.column_config.TextColumn("Valor do Salário"),
        "interesse": st.column_config.TextColumn("Interessante?"),
        "justificativa": st.column_config.TextColumn("Justificativa"),
    }
)