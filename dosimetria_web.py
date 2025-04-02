import streamlit as st
import json
import os

# Funções utilitárias
def carregar_base(json_path="penas_por_artigo.json"):
    if not os.path.exists(json_path):
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

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

def aplicar_redutor(pena_dias, redutor):
    if redutor <= 0:
        return dias_para_anos_meses(pena_dias)
    nova_pena = pena_dias * (1 - redutor)
    return dias_para_anos_meses(nova_pena)

def aplicar_majorante(pena_dias, majorante):
    if majorante <= 0:
        return dias_para_anos_meses(pena_dias)
    nova_pena = pena_dias * (1 + majorante)
    return dias_para_anos_meses(nova_pena)

# Início da interface
st.set_page_config(page_title="Dosimetria Penal", layout="centered")
st.title("⚖️ Sistema de Dosimetria Penal")
base = carregar_base()

if not base:
    st.error("Arquivo JSON não encontrado ou inválido.")
    st.stop()

artigos = sorted(base.keys(), key=lambda x: int(x.split()[0]) if x.split()[0].isdigit() else float('inf'))
artigo_escolhido = st.selectbox("Selecione o artigo penal", artigos)

info_artigo = base[artigo_escolhido]
#pena_min = info_artigo.get("pena_min", 0)
#pena_max = info_artigo.get("pena_max", 0)"
pena_min_dict = info_artigo.get("pena_min", {"anos": 0, "meses": 0})
pena_max_dict = info_artigo.get("pena_max", {"anos": 0, "meses": 0})
pena_min_dias = anos_meses_para_dias(pena_min_dict["anos"], pena_min_dict["meses"])
pena_max_dias = anos_meses_para_dias(pena_max_dict["anos"], pena_max_dict["meses"])

descricao_crime = info_artigo.get("crime", "")

st.markdown(f"**Crime:** {descricao_crime}")
st.markdown(f"**Pena cominada:** {pena_min_dict['anos']}a{pena_min_dict['meses']}m até {pena_max_dict['anos']}a{pena_max_dict['meses']}m")
st.markdown(f"**Pena mínima:** {pena_min_dict['anos']} ano(s) e {pena_min_dict['meses']} mês(es)")
st.markdown(f"**Pena máxima:** {pena_max_dict['anos']} ano(s) e {pena_max_dict['meses']} mês(es)")


# Circunstâncias judiciais (Art. 59 do CP)
st.subheader("Circunstâncias Judiciais (Art. 59 CP)")
campos = [
    "Culpabilidade", "Antecedentes", "Conduta social", "Personalidade",
    "Motivos", "Circunstâncias", "Consequências", "Comportamento da vítima"
]

circunstancias = []
for campo in campos:
    valor = st.selectbox(f"{campo}:", ["neutra", "favorável", "desfavorável"], key=campo)
    if valor == "desfavorável":
        circunstancias.append(campo)

# Se for tráfico, incluir mais 2 circunstâncias (Art. 42 da Lei de Drogas)
if "tráfico" in descricao_crime.lower():
    st.subheader("Circunstâncias Específicas (Art. 42 Lei de Drogas)")
    for campo in ["Natureza da substância", "Quantidade da substância"]:
        valor = st.selectbox(f"{campo}:", ["neutra", "favorável", "desfavorável"], key=campo)
        if valor == "desfavorável":
            circunstancias.append(campo)

# Agravantes, Atenuantes, Redutor, Majorante
st.subheader("Outros Fatores")

col1, col2 = st.columns(2)
with col1:
    agravantes = st.slider("Nº de agravantes", 0, 5, 0)
with col2:
    atenuantes = st.slider("Nº de atenuantes", 0, 5, 0)

col3, col4 = st.columns(2)
with col3:
    redutor = st.slider("Redutor (de 1/6 a 2/3)", 0.0, 0.67, 0.0, step=0.01)
with col4:
    majorante = st.slider("Majorante (de 1/6 a 2/3)", 0.0, 0.67, 0.0, step=0.01)

# Botão de cálculo
if st.button("Calcular Pena"):
    try:
        desfavoraveis = len(circunstancias)
        #anos_base, meses_base = aplicar_circunstancias(pena_min, pena_max, desfavoraveis)"
        anos_base, meses_base = aplicar_circunstancias(pena_min_dias / 360, pena_max_dias / 360, desfavoraveis)
        base_dias = anos_meses_para_dias(anos_base, meses_base)

        anos_prov, meses_prov = aplicar_agravantes_atenuantes(base_dias, agravantes, atenuantes)
        provisoria_dias = anos_meses_para_dias(anos_prov, meses_prov)

        anos_def, meses_def = aplicar_redutor(provisoria_dias, redutor)
        definitiva_dias = anos_meses_para_dias(anos_def, meses_def)

        anos_final, meses_final = aplicar_majorante(definitiva_dias, majorante)

        st.success(f"📌 **Pena Final:** {anos_final} ano(s) e {meses_final} mês(es)")

    except Exception as e:
        st.error(f"Erro no cálculo: {e}")