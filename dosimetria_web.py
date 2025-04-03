import streamlit as st
import json
import os
import re

# Funções utilitárias
def carregar_base(json_path="penas_por_artigo.json"):
    if not os.path.exists(json_path):
        return {}
    with open(json_path, "r", encoding="utf-8") as f:
        return json.load(f)

def carregar_hediondos(path="artigos_hediondos.json"):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("hediondos", [])

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

def calcular_total_meses(anos, meses):
    """Calcula o total de meses a partir de anos e meses."""
    return anos * 12 + meses

def calcular_progressao(pena_anos, pena_meses, reincidente, hediondo):
    dias = anos_meses_para_dias(pena_anos, pena_meses)

    if hediondo:
        if reincidente:
            percentual = 0.6  # 60%
        else:
            percentual = 0.4  # 40%
    else:
        if reincidente:
            percentual = 0.5  # 50%
        else:
            percentual = 0.33  # 1/3

    dias_progressao = dias * percentual
    return dias_para_anos_meses(dias_progressao)

# Início da interface
st.set_page_config(page_title="Dosimetria Penal", layout="centered")
# Abas principais
abas = st.tabs(["📊 Calculadora", "🛠️ Editor de Artigos", "📈 Relatórios"])

with abas[0]:
    st.title("⚖️ Sistema de Dosimetria Penal")
    base = carregar_base()

    if not base:
        st.error("Arquivo JSON não encontrado ou inválido.")
        st.stop()

    artigos = sorted(base.keys(), key=lambda x: int(x.split()[0]) if x.split()[0].isdigit() else float('inf'))
    artigo_escolhido = st.selectbox("Selecione o artigo penal", artigos)

    hediondos = carregar_hediondos()
    eh_hediondo = artigo_escolhido.replace("§", "").replace("º", "").replace(".", "").replace("-", " ").upper() in [h.upper() for h in hediondos]

    if eh_hediondo:
        st.warning("🚨 Crime hediondo detectado conforme Lei 8.072/90.")

    info_artigo = base[artigo_escolhido]

    #pena_min = info_artigo.get("pena_min", 0)
    #pena_max = info_artigo.get("pena_max", 0)"
    pena_min_dict = info_artigo.get("pena_min", {"anos": 0, "meses": 0})
    pena_max_dict = info_artigo.get("pena_max", {"anos": 0, "meses": 0})
    pena_min_dias = anos_meses_para_dias(pena_min_dict["anos"], pena_min_dict["meses"])
    pena_max_dias = anos_meses_para_dias(pena_max_dict["anos"], pena_max_dict["meses"])

    descricao_crime = info_artigo.get("crime", "")

    multa = info_artigo.get("multa")

    st.markdown(f"**Crime:** {descricao_crime}")
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

    dias_multa = 0
    salario_minimo = 0.0

    if multa:
        st.subheader("Pena de Multa")

        st.markdown(f"**Pena prevista de multa:** de {multa['min']} a {multa['max']} dias-multa.")
        dias_multa = st.slider("Quantidade de dias-multa", multa["min"], multa["max"], multa["min"])
        salario_minimo = st.number_input("Valor do salário mínimo vigente (R$)", min_value=0.0, value=1412.0, step=10.0)

    # Seletor de reincidência (fora do botão!)
    st.subheader("Reincidência")
    reincidente = st.radio("O réu é reincidente?", ["Não", "Sim"], key="reincidente")

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

            # Cálculo da multa (se houver)
            if multa and dias_multa and salario_minimo:
                try:
                    valor_multa = dias_multa * (salario_minimo / 30)
                    st.info(f"💰 **Valor da Multa:** R$ {valor_multa:,.2f}")
                except Exception as e:
                    st.warning(f"⚠️ Erro ao processar a multa: {e}")

            total_meses = calcular_total_meses(anos_final, meses_final)

            if reincidente == "Sim" or definitiva_dias > 1460:  # 1460 dias = 4 anos
                regime = "Fechado"
            elif definitiva_dias > 730:  # 2 anos
                regime = "Semiaberto"
            else:
                regime = "Aberto"

            st.info(f"📎 Regime inicial sugerido: **{regime}**")

            anos_progressao, meses_progressao = calcular_progressao(
                            anos_final, meses_final, reincidente, eh_hediondo)

            st.info(f"📍 **Progressão de Regime**: após {anos_progressao} ano(s) e {meses_progressao} mês(es)")

        except Exception as e:
            st.error(f"Erro no cálculo: {e}")  

with abas[1]:  # 🛠️ Editor de Artigos
    st.subheader("🛠️ Editor da Base de Artigos")

    artigos_lista = sorted(base.keys(), key=lambda x: int(x.split()[0]) if x.split()[0].isdigit() else float('inf'))
    #artigo_edit = st.selectbox("Selecione ou digite o artigo para editar ou criar", [""] + artigos_lista)
    artigo_edit = st.text_input("Digite o número do artigo para editar ou criar")

    
    novo_crime = st.text_input("Descrição do crime", value=base.get(artigo_edit, {}).get("crime", "") if artigo_edit else "")
    pena_texto = st.text_input("Pena (ex: Reclusão de 2 a 8 anos)", value=base.get(artigo_edit, {}).get("pena", "") if artigo_edit else "")

    col1, col2 = st.columns(2)
    with col1:
        pena_min_anos = st.number_input("Pena mínima (anos)", 0, 100, base.get(artigo_edit, {}).get("pena_min", {}).get("anos", 0) if artigo_edit else 0)
        pena_max_anos = st.number_input("Pena máxima (anos)", 0, 100, base.get(artigo_edit, {}).get("pena_max", {}).get("anos", 0) if artigo_edit else 0)
    with col2:
        pena_min_meses = st.number_input("Pena mínima (meses)", 0, 11, base.get(artigo_edit, {}).get("pena_min", {}).get("meses", 0) if artigo_edit else 0)
        pena_max_meses = st.number_input("Pena máxima (meses)", 0, 11, base.get(artigo_edit, {}).get("pena_max", {}).get("meses", 0) if artigo_edit else 0)

    st.markdown("#### Multa (opcional)")
    colm1, colm2 = st.columns(2)
    with colm1:
        multa_min = st.number_input("Mínimo de dias-multa", 0, 10000, base.get(artigo_edit, {}).get("multa", {}).get("min", 0) if artigo_edit else 0)
    with colm2:
        multa_max = st.number_input("Máximo de dias-multa", 0, 10000, base.get(artigo_edit, {}).get("multa", {}).get("max", 0) if artigo_edit else 0)

    # Ações
    colb1, colb2, colb3 = st.columns(3)
    with colb1:
        if st.button("💾 Salvar ou Atualizar"):
            if artigo_edit.strip():
                base[artigo_edit] = {
                    "crime": novo_crime,
                    "pena": pena_texto,
                    "pena_min": {"anos": pena_min_anos, "meses": pena_min_meses},
                    "pena_max": {"anos": pena_max_anos, "meses": pena_max_meses},
                }
                if multa_min > 0 or multa_max > 0:
                    base[artigo_edit]["multa"] = {"min": multa_min, "max": multa_max}
                with open("penas_por_artigo.json", "w", encoding="utf-8") as f:
                    json.dump(base, f, indent=2, ensure_ascii=False)
                st.success(f"Artigo {artigo_edit} salvo com sucesso.")
    with colb2:
        if st.button("❌ Excluir Artigo") and artigo_edit in base:
            del base[artigo_edit]
            with open("penas_por_artigo.json", "w", encoding="utf-8") as f:
                json.dump(base, f, indent=2, ensure_ascii=False)
            st.warning(f"Artigo {artigo_edit} excluído com sucesso.")
    with colb3:
        if st.button("🔄 Recarregar Base"):
            base.update(carregar_base())
            st.info("Base recarregada.")
       

with abas[2]:
    st.title("📈 Relatórios")
    st.write("Aqui você pode visualizar relatórios e estatísticas.")
    