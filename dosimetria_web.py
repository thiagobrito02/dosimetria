import json
import os
import re
import streamlit as st

# Caminho do JSON
JSON_PATH = "penas_por_artigo.json"

# Funções auxiliares
def carregar_base():
    if not os.path.exists(JSON_PATH):
        return {}
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def ordenar_artigos(artigo_str):
    match = re.match(r"(\d+)", artigo_str)
    return int(match.group(1)) if match else float("inf")

def anos_meses_para_dias(anos, meses):
    return anos * 360 + meses * 30

def dias_para_anos_meses(dias):
    anos = dias // 360
    resto = dias % 360
    meses = resto // 30
    return int(anos), int(meses)

def aplicar_circunstancias(pena_min, pena_max, num_desfavoraveis):
    diferenca_dias = (pena_max - pena_min) * 360
    acrescimo_dias = diferenca_dias * (num_desfavoraveis / 8)
    total_dias = pena_min * 360 + acrescimo_dias
    return dias_para_anos_meses(total_dias)

def aplicar_agravantes_atenuantes(pena_base_dias, agravantes, atenuantes):
    delta_dias = (agravantes - atenuantes) * (pena_base_dias / 6)
    nova_pena = pena_base_dias + delta_dias
    return dias_para_anos_meses(nova_pena)

def aplicar_redutor(pena_provisoria_dias, redutor):
    if redutor <= 0:
        return dias_para_anos_meses(pena_provisoria_dias)
    nova_pena = pena_provisoria_dias * (1 - redutor)
    return dias_para_anos_meses(nova_pena)

def aplicar_majorante(pena_provisoria_dias, majorante):
    if majorante <= 0:
        return dias_para_anos_meses(pena_provisoria_dias)
    nova_pena = pena_provisoria_dias * (1 + majorante)
    return dias_para_anos_meses(nova_pena)

# Início da aplicação
st.set_page_config(page_title="Dosimetria Penal", layout="centered")
st.title("⚖️ Sistema de Dosimetria Penal")

base = carregar_base()
artigos = sorted(base.keys(), key=ordenar_artigos)

if not artigos:
    st.error("Base de artigos não carregada.")
    st.stop()

artigo_escolhido = st.selectbox("Selecione o artigo penal:", artigos)

dados = base.get(artigo_escolhido, {})
crime = dados.get("crime", "")
pena_min = dados.get("pena_min", 0)
pena_max = dados.get("pena_max", 0)

st.markdown(f"**Crime:** {crime}")
st.markdown(f"**Pena mínima:** {pena_min} anos")
st.markdown(f"**Pena máxima:** {pena_max} anos")

st.markdown("### Circunstâncias judiciais")
campos = [
    "Culpabilidade", "Antecedentes", "Conduta social", "Personalidade",
    "Motivos", "Circunstâncias", "Consequências", "Comportamento da vítima"
]

circunstancias = {}
for campo in campos:
    circunstancias[campo] = st.selectbox(campo, ["neutra", "favorável", "desfavorável"], key=campo)

num_desfavoraveis = sum(1 for v in circunstancias.values() if v == "desfavorável")

st.markdown("### Agravantes e Atenuantes")
col1, col2, col3, col4 = st.columns([1, 1, 1, 1])
with col1:
    agravantes = st.slider("Agravantes", 0, 5, 0)
with col2:
    atenuantes = st.slider("Atenuantes", 0, 5, 0)
with col3:
    redutor = st.slider("Redutor (1/6 a 2/3)", 0.00, 0.67, 0.00, step=0.01)
with col4:
    majorante = st.slider("Majorante (1/6 a 2/3)", 0.00, 0.67, 0.00, step=0.01)


if st.button("Calcular Pena"):
    try:
        # Etapa 1: Pena Base
        anos_base, meses_base = aplicar_circunstancias(pena_min, pena_max, num_desfavoraveis)
        base_dias = anos_meses_para_dias(anos_base, meses_base)

        # Etapa 2: Pena Provisória
        anos_prov, meses_prov = aplicar_agravantes_atenuantes(base_dias, agravantes, atenuantes)
        provisoria_dias = anos_meses_para_dias(anos_prov, meses_prov)

        # Etapa 3: Pena Definitiva (Redutor e Majorante aplicados)
        anos_def_red, meses_def_red = aplicar_redutor(provisoria_dias, redutor)
        definitiva_dias = anos_meses_para_dias(anos_def_red, meses_def_red)
        anos_final, meses_final = aplicar_majorante(definitiva_dias, majorante)

        st.success(f"📢 Pena final: **{anos_final} ano(s) e {meses_final} mês(es)**")
    except Exception as e:
        st.error(f"Erro no cálculo: {e}")
