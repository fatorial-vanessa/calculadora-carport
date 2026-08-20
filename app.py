import math
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Calculadora Carport Fatorial", page_icon="🚗", layout="wide"
)

col_titulo, col_logo = st.columns([4, 1])

with col_titulo:
    st.title("Calculadora de Carport")
    st.write("Selecione o modo de dimensionamento abaixo:")

with col_logo:
    st.image("logofat.png", width=400)

st.divider()

# CONSTANTES TÉCNICAS E LIMITES POR LINHA
ESPESSURA_FIXADOR = 0.0035  # 3.5mm em metros

LIMITES_LINHAS = {
    2: 62.0,  
    3: 52.0,  
    5: 42.0   
}

TERCAS = {
    "2v": {"init": 6.0, "meio": 5.0, "fin": 6.0},
    "1v": {"init": 3.0, "meio": 2.5, "fin": 3.0},
    "pcd": {"init": 4.5, "meio": 3.7, "fin": 4.5},
}

NOMES_KITS = {
    "2v": "Padrão 2 Vagas",
    "1v": "Padrão 1 Vaga",
    "pcd": "Vaga PCD",
}

def calcular_comprimento_mesa(blocks):
    if not blocks:
        return 0.0
    if len(blocks) == 1:
        return TERCAS[blocks[0]]["init"]
    
    comprimento = TERCAS[blocks[0]]["init"]
    comprimento += TERCAS[blocks[-1]]["fin"]
    
    for b in blocks[1:-1]:
        comprimento += TERCAS[b]["meio"]
        
    return comprimento

def detalhar_kits(blocos):
    kits = {
        "Início 2V": 0, "Início 1V": 0, "Início PCD": 0,
        "Meio 2V": 0, "Meio 1V": 0, "Meio PCD": 0,
        "Fim 2V": 0, "Fim 1V": 0, "Fim PCD": 0,
    }
    
    if not blocos:
        return kits
        
    if blocos[0] == "2v": kits["Início 2V"] = 1
    elif blocos[0] == "1v": kits["Início 1V"] = 1
    elif blocos[0] == "pcd": kits["Início PCD"] = 1
    
    if len(blocos) > 1:
        if blocos[-1] == "2v": kits["Fim 2V"] = 1
        elif blocos[-1] == "1v": kits["Fim 1V"] = 1
        elif blocos[-1] == "pcd": kits["Fim PCD"] = 1
        
    if len(blocos) > 2:
        meios = blocos[1:-1]
        kits["Meio 2V"] = meios.count("2v")
        kits["Meio 1V"] = meios.count("1v")
        kits["Meio PCD"] = meios.count("pcd")
        
    return kits

tab_vagas, tab_modulos, tab_projeto = st.tabs(
    ["🅿️ 1. Por Quantidade de Vagas", "☀️ 2. Por Quantidade de Módulos", "📊 3. Completo (Tabela)"]
)

# ABA 1: DIMENSIONAMENTO POR VAGAS
with tab_vagas:
    st.header("Dimensionamento baseado no Layout do Estacionamento")

    col1, col2 = st.columns(2)
    with col1:
        vagas_comuns = st.number_input("Total de Vagas Padrão (Lineares):", min_value=0, value=1, key="v_comuns")
        vagas_pcd = st.number_input("Total de Vagas PCD (Lineares):", min_value=0, value=0, key="v_pcd")
        
        posicao_pcd_v = "No Fim" 
        
        if vagas_pcd == 1:
            posicao_pcd_v = st.radio(
                "Posição da Vaga PCD:", 
                ["No Início", "No Meio", "No Fim"], 
                horizontal=True, 
                key="v_pcd_pos"
            )
        elif vagas_pcd > 1:
            st.info("ℹ️ Como são várias vagas PCD, o sistema colocará 1 no final e as demais serão distribuídas no meio.")

    with col2:
        largura_str_v = st.text_input("Largura do Módulo (m):", value="1.134", key="v_larg_str")
        try:
            largura_mod = float(largura_str_v.replace(",", "."))
        except ValueError:
            st.error("⚠️ Digite uma largura válida (ex: 1.134).")
            largura_mod = 1.134

        linhas = st.selectbox("Linhas da Mesa:", [2, 3, 5], index=0, key="v_lin")

    if st.button("🚀 Calcular por Vagas", key="btn_vagas"):
        largura_calc = math.ceil(largura_mod * 100) / 100
        limite_atual = LIMITES_LINHAS.get(linhas, 30.0)

        qtd_2v = vagas_comuns // 2
        qtd_1v = vagas_comuns % 2
        
        blocos_padrao = ["2v"] * qtd_2v + ["1v"] * qtd_1v
        
        if vagas_pcd > 0:
            lista_pcds = ["pcd"] * vagas_pcd
            if vagas_pcd == 1:
                if posicao_pcd_v == "No Início":
                    blocos_projeto = lista_pcds + blocos_padrao
                elif posicao_pcd_v == "No Meio":
                    meio = len(blocos_padrao) // 2
                    blocos_projeto = blocos_padrao[:meio] + lista_pcds + blocos_padrao[meio:]
                else:
                    blocos_projeto = blocos_padrao + lista_pcds
            else:
                pcd_fim = ["pcd"]
                pcd_meio = ["pcd"] * (vagas_pcd - 1)
                meio = len(blocos_padrao) // 2
                blocos_projeto = blocos_padrao[:meio] + pcd_meio + blocos_padrao[meio:] + pcd_fim
        else:
            blocos_projeto = blocos_padrao

        
        comprimento_estrutura = calcular_comprimento_mesa(blocos_projeto)

        if comprimento_estrutura == 0:
            st.error("ℹ️Informe pelo menos 1 vaga para realizar o cálculo.")
        elif comprimento_estrutura > limite_atual:
            st.error(f"⛔ **LIMITE EXCEDIDO:** O comprimento da mesa ({comprimento_estrutura:.2f}m) ultrapassou o limite máximo permitido para mesas de **{linhas} linhas**! Reduza a quantidade de vagas.")
        else:
            modulos_por_linha = math.floor((comprimento_estrutura - ESPESSURA_FIXADOR) / (largura_calc + ESPESSURA_FIXADOR))
            total_modulos = modulos_por_linha * linhas
            
            comprimento_ocupado = (modulos_por_linha * largura_calc) + ((modulos_por_linha + 1) * ESPESSURA_FIXADOR)
            sobra_terca = comprimento_estrutura - comprimento_ocupado
            total_fixadores = 2 * (modulos_por_linha + 1) * linhas

            st.divider()

            vagas_lineares_totais = vagas_comuns + vagas_pcd
            if linhas == 5:
                st.info(f"ℹ️ **Arranjo de 5 Linhas (Vagas Duplas):** Como a cobertura de 5 linhas é dupla (carros frente a frente), a estrutura de **{vagas_lineares_totais} vagas lineares** cobrirá **{vagas_lineares_totais * 2} vagas totais**.")

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Módulos (Total)", f"{total_modulos} un")
            m2.metric("Módulos por Linha", f"{modulos_por_linha} un")
            m3.metric("Comprimento da Estrutura", f"{comprimento_estrutura:.2f} m")
            m4.metric("Sobra de Terça / Folga", f"{sobra_terca * 100:.1f} cm")

            st.markdown("---")
            if sobra_terca < 0.05:
                st.error(f"🚨 **ALERTA DE SEGURANÇA:** Sobra de apenas **{sobra_terca * 100:.1f} cm** nas pontas!")
            elif sobra_terca < 0.15:
                st.warning(f"⚠️ **Atenção:** Folga de apenas **{sobra_terca * 100:.1f} cm** nas extremidades.")
            else:
                st.success(f"✅ **Margem Segura:** Folga de **{sobra_terca * 100:.1f} cm** disponível nas terças.")

            st.subheader("📦 Composição de Kits e Componentes")
            st.write(f"🔩 **Total de Fixadores Universais Clampar:** `{total_fixadores}` unidades")

            st.markdown("**Lista de Kits do Projeto:**")
            if len(blocos_projeto) == 1:
                bloco = blocos_projeto[0]
                st.write(f"• **1x Kit Inicial (Completo):** {NOMES_KITS[bloco]} ({TERCAS[bloco]['init']}m)")
            else:
                inicio = blocos_projeto[0]
                fim = blocos_projeto[-1]
                meios = blocos_projeto[1:-1]
                
                st.write(f"• **1x Kit Inicial:** {NOMES_KITS[inicio]} ({TERCAS[inicio]['init']}m)")
                if meios:
                    meio_str = []
                    if meios.count("2v") > 0: meio_str.append(f"{meios.count('2v')}x 2 Vagas")
                    if meios.count("1v") > 0: meio_str.append(f"{meios.count('1v')}x 1 Vaga")
                    if meios.count("pcd") > 0: meio_str.append(f"{meios.count('pcd')}x PCD")
                    st.write("• **Kit(s) Meio:** " + " / ".join(meio_str))
                st.write(f"• **1x Kit Final:** {NOMES_KITS[fim]} ({TERCAS[fim]['fin']}m)")


# ABA 2: DIMENSIONAMENTO POR MÓDULOS
with tab_modulos:
    st.header("Dimensionamento baseado na Quantidade de Módulos")

    col1, col2 = st.columns(2)
    with col1:
        total_modulos_m = st.number_input(
            "Total de Módulos:", min_value=1, value=1, key="m_tot"
        )
        
        incluir_pcd_m = st.radio(
            "Incluir Vagas PCD?", ["Não", "Sim"], horizontal=True, key="m_pcd_radio"
        )
        
        pcd_qtd = 0
        posicao_pcd = "No Fim"
        
        if incluir_pcd_m == "Sim":
            pcd_qtd = st.number_input(
                "Quantidade de Vagas PCD:", min_value=1, max_value=10, value=1, key="m_pcd_qtd"
            )
            
            if pcd_qtd == 1:
                posicao_pcd = st.radio(
                    "Posição da Vaga PCD:", 
                    ["No Início", "No Meio", "No Fim"], 
                    horizontal=True, 
                    key="m_pcd_pos"
                )
            else:
                st.info("ℹ️ Como são várias vagas PCD, o sistema colocará 1 no final e as demais serão distribuídas no meio.")

    with col2:
        largura_str_m = st.text_input(
            "Largura do Módulo (m):", value="1.134", key="m_larg_str"
        )
        try:
            largura_mod_m = float(largura_str_m.replace(",", "."))
        except ValueError:
            largura_mod_m = 1.134

        linhas_m = st.selectbox(
            "Arranjo de Linhas da Mesa:", [2, 3, 5], index=0, key="m_lin"
        )

    if st.button("🚀 Calcular por Módulos", key="btn_modulos"):
        st.divider()
        limite_atual_m = LIMITES_LINHAS.get(linhas_m, 30.0)

        resto = total_modulos_m % linhas_m
        if resto != 0:
            modulos_considerados = math.ceil(total_modulos_m / linhas_m) * linhas_m
            st.warning(
                f"⚠️ **Ajuste de Arranjo:** A quantidade digitada ({total_modulos_m}) não é múltipla de {linhas_m} (linhas da mesa). "
                f"Para que a estrutura não fique com 'buracos', o cálculo considerou o espaço físico para **{modulos_considerados} módulos**."
            )
        else:
            modulos_considerados = total_modulos_m

        largura_calc_m = math.ceil(largura_mod_m * 100) / 100
        modulos_por_linha_m = modulos_considerados // linhas_m

        comprimento_minimo_mesa = (modulos_por_linha_m * largura_calc_m) + (
            (modulos_por_linha_m + 1) * ESPESSURA_FIXADOR
        )

        if comprimento_minimo_mesa > limite_atual_m:
            st.error(f"⛔ **LIMITE EXCEDIDO:** Essa quantidade de módulos exige um comprimento mínimo de ({comprimento_minimo_mesa:.2f}m), ultrapassando o limite máximo permitido para mesas de **{linhas_m} linhas**!")
        else:
            melhor_comprimento = float('inf')
            melhor_combinacao = []
            
            limite_kits = math.ceil(comprimento_minimo_mesa / 2.0) + 15
            
            for q_2v in range(limite_kits):
                for q_1v in [0, 1]:  
                    blocos = ["2v"] * q_2v + ["1v"] * q_1v
                    
                    if pcd_qtd > 0:
                        lista_pcds = ["pcd"] * pcd_qtd
                        if pcd_qtd == 1:
                            if posicao_pcd == "No Início":
                                blocos = lista_pcds + blocos
                            elif posicao_pcd == "No Meio":
                                if len(blocos) > 0:
                                    meio = len(blocos) // 2
                                    blocos = blocos[:meio] + lista_pcds + blocos[meio:]
                                else:
                                    blocos = lista_pcds
                            else:
                                blocos = blocos + lista_pcds
                        else:
                            pcd_fim = ["pcd"]
                            pcd_meio = ["pcd"] * (pcd_qtd - 1)
                            
                            if len(blocos) > 0:
                                meio = len(blocos) // 2
                                blocos = blocos[:meio] + pcd_meio + blocos[meio:] + pcd_fim
                            else:
                                blocos = pcd_meio + pcd_fim

                    if not blocos: continue
                    
                    comp_teste = calcular_comprimento_mesa(blocos)
                    if comp_teste >= comprimento_minimo_mesa and comp_teste < melhor_comprimento:
                        melhor_comprimento = comp_teste
                        melhor_combinacao = blocos

            if not melhor_combinacao:
                q_2v_fallback = math.ceil(comprimento_minimo_mesa / 6.0)
                melhor_combinacao = ["2v"] * q_2v_fallback
                if pcd_qtd > 0:
                    melhor_combinacao.extend(["pcd"] * pcd_qtd)
                melhor_comprimento = calcular_comprimento_mesa(melhor_combinacao)

            sobra_terca_m = melhor_comprimento - comprimento_minimo_mesa
            total_fixadores_m = 2 * (modulos_por_linha_m + 1) * linhas_m
            
            vagas_geradas_padrao_lineares = (melhor_combinacao.count("2v") * 2) + melhor_combinacao.count("1v")
            vagas_pcd_geradas = melhor_combinacao.count("pcd")
            vagas_lineares_totais_m = vagas_geradas_padrao_lineares + vagas_pcd_geradas

            if linhas_m == 5:
                st.info(
                    f"ℹ️ **Arranjo de 5 Linhas (Vagas Duplas):** Você gerou **{vagas_lineares_totais_m} vagas lineares**, "
                    f"o que equivale a **{vagas_lineares_totais_m * 2} vagas totais no estacionamento**."
                )
                label_vagas = "Vagas (Totais/Lineares)"
                valor_vagas = f"{vagas_lineares_totais_m * 2} / {vagas_lineares_totais_m}"
            else:
                label_vagas = "Vagas Geradas"
                valor_vagas = f"{vagas_lineares_totais_m} un"

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Módulos/Linha", f"{modulos_por_linha_m} un")
            m2.metric("Comprimento", f"{melhor_comprimento:.2f} m")
            m3.metric(label_vagas, valor_vagas)
            m4.metric("Sobra de Terça", f"{sobra_terca_m * 100:.1f} cm")

            if linhas_m != 5:
                st.caption(f"Detalhes: {vagas_geradas_padrao_lineares} Padrão | {vagas_pcd_geradas} PCD")

            st.markdown("---")

            if sobra_terca_m < 0.05:
                st.error(f"🚨 **ALERTA DE SEGURANÇA:** Sobra de apenas **{sobra_terca_m * 100:.1f} cm** nas pontas!")
            elif sobra_terca_m < 0.15:
                st.warning(f"⚠️ **Atenção:** Folga de **{sobra_terca_m * 100:.1f} cm** nas terças.")
            else:
                st.success(f"✅ **Margem Segura:** Folga de **{sobra_terca_m * 100:.1f} cm** disponível nas terças.")

            st.subheader("📦 Composição de Kits e Componentes")
            
            st.markdown(f"🔩 **Total de Fixadores Universais Clampar:** {total_fixadores_m} unidades")
            if len(melhor_combinacao) == 1:
                st.write(f"• **1x Kit Inicial (Completo):** {NOMES_KITS[melhor_combinacao[0]]}")
            else:
                inicio = melhor_combinacao[0]
                fim = melhor_combinacao[-1]
                meios = melhor_combinacao[1:-1]
                
                st.write(f"• **1x Kit Inicial:** {NOMES_KITS[inicio]}")
                if meios:
                    meio_str = []
                    if meios.count("2v") > 0: meio_str.append(f"{meios.count('2v')}x 2 Vagas")
                    if meios.count("1v") > 0: meio_str.append(f"{meios.count('1v')}x 1 Vaga")
                    if meios.count("pcd") > 0: meio_str.append(f"{meios.count('pcd')}x PCD")
                    st.write("• **Kit(s) Meio:** " + " / ".join(meio_str))
                
                st.write(f"• **1x Kit Final:** {NOMES_KITS[fim]}")


# ABA 3: PROJETO COMPLETO (TABELA)
with tab_projeto:
    st.header("Gestor de Projetos: Adicionar Mesas")

    if "mesas" not in st.session_state:
        st.session_state["mesas"] = []

    with st.expander("➕ Adicionar Nova Mesa ao Projeto", expanded=True):
        modo = st.radio("Método de entrada para esta mesa:", ["Por Vagas", "Por Módulos"], horizontal=True, key="p_modo")

        col_cfg1, col_cfg2 = st.columns(2)
        with col_cfg1:
            largura_str_p = st.text_input("Largura do Módulo (m):", value="1.134", key="p_larg_str")
            try:
                largura_mod_p = float(largura_str_p.replace(",", "."))
            except ValueError:
                largura_mod_p = 1.134
            largura_calc_p = math.ceil(largura_mod_p * 100) / 100

        with col_cfg2:
            linhas_p = st.selectbox("Linhas da Mesa:", [2, 3, 5], index=0, key="p_lin")

        st.markdown("---")

        if modo == "Por Vagas":
            c1, c2 = st.columns(2)
            with c1:
                v_reg = st.number_input("Vagas Regulares (Padrão)", min_value=0, value=1, key="p_vreg")
            with c2:
                v_pcd = st.number_input("Vagas PCD", min_value=0, value=0, key="p_vpcd")
                posicao_pcd_p = "No Fim"
                
                if v_pcd == 1:
                    posicao_pcd_p = st.radio("Posição da Vaga PCD:", ["No Início", "No Meio", "No Fim"], horizontal=True, key="p_vpcd_pos_vagas")
                elif v_pcd > 1:
                    st.info("ℹ️ Como são várias vagas PCD, o sistema colocará 1 no final e as demais serão distribuídas no meio.")
                    
            v_mod = 0
        else:
            c1, c2 = st.columns(2)
            with c1:
                v_mod = st.number_input("Qtd. Módulos", min_value=1, value=1, key="p_vmod")
                v_reg = 0
                
            with c2:
                incluir_pcd_p = st.radio("Incluir Vagas PCD?", ["Não", "Sim"], horizontal=True, key="p_pcd_radio")
                
                v_pcd = 0
                posicao_pcd_p = "No Fim"
                
                if incluir_pcd_p == "Sim":
                    v_pcd = st.number_input("Quantidade de Vagas PCD:", min_value=1, max_value=10, value=1, key="p_pcd_qtd")
                    if v_pcd == 1:
                        posicao_pcd_p = st.radio("Posição da Vaga PCD:", ["No Início", "No Meio", "No Fim"], horizontal=True, key="p_pcd_pos")

        nome_mesa = st.text_input("Nome da Mesa (Opcional)", placeholder="Ex: Estacionamento Visitantes", key="p_nome")

        if st.button("Adicionar Mesa", type="primary"):
            blocos_finais = []
            modulos_finais = 0
            vagas_reg_finais = 0
            comprimento_final = 0.0
            modulos_por_linha = 0
            limite_atual_p = LIMITES_LINHAS.get(linhas_p, 30.0)

            if modo == "Por Vagas":
                qtd_2v = v_reg // 2
                qtd_1v = v_reg % 2
                
                blocos_padrao = ["2v"] * qtd_2v + ["1v"] * qtd_1v
                
                if v_pcd > 0:
                    lista_pcds = ["pcd"] * v_pcd
                    if v_pcd == 1:
                        if posicao_pcd_p == "No Início":
                            blocos_finais = lista_pcds + blocos_padrao
                        elif posicao_pcd_p == "No Meio":
                            meio = len(blocos_padrao) // 2
                            blocos_finais = blocos_padrao[:meio] + lista_pcds + blocos_padrao[meio:]
                        else:
                            blocos_finais = blocos_padrao + lista_pcds
                    else:
                        pcd_fim = ["pcd"]
                        pcd_meio = ["pcd"] * (v_pcd - 1)
                        meio = len(blocos_padrao) // 2
                        blocos_finais = blocos_padrao[:meio] + pcd_meio + blocos_padrao[meio:] + pcd_fim
                else:
                    blocos_finais = blocos_padrao

                comprimento_final = calcular_comprimento_mesa(blocos_finais)
                modulos_por_linha = math.floor((comprimento_final - ESPESSURA_FIXADOR) / (largura_calc_p + ESPESSURA_FIXADOR))
                modulos_finais = modulos_por_linha * linhas_p
                vagas_reg_finais = v_reg

            else: 
                resto = v_mod % linhas_p
                modulos_considerados = math.ceil(v_mod / linhas_p) * linhas_p if resto != 0 else v_mod
                modulos_por_linha = modulos_considerados // linhas_p
                comp_min = (modulos_por_linha * largura_calc_p) + ((modulos_por_linha + 1) * ESPESSURA_FIXADOR)
                
                melhor_comp = float('inf')
                limite_kits = math.ceil(comp_min / 2.0) + 15
                
                for q_2v in range(limite_kits):
                    for q_1v in [0, 1]:
                        blocos = ["2v"] * q_2v + ["1v"] * q_1v
                        
                        if v_pcd > 0:
                            lista_pcds = ["pcd"] * v_pcd
                            if v_pcd == 1:
                                if posicao_pcd_p == "No Início":
                                    blocos = lista_pcds + blocos
                                elif posicao_pcd_p == "No Meio":
                                    if len(blocos) > 0:
                                        meio = len(blocos) // 2
                                        blocos = blocos[:meio] + lista_pcds + blocos[meio:]
                                    else:
                                        blocos = lista_pcds
                                else:
                                    blocos = blocos + lista_pcds
                            else:
                                pcd_fim = ["pcd"]
                                pcd_meio = ["pcd"] * (v_pcd - 1)
                                if len(blocos) > 0:
                                    meio = len(blocos) // 2
                                    blocos = blocos[:meio] + pcd_meio + blocos[meio:] + pcd_fim
                                else:
                                    blocos = pcd_meio + pcd_fim

                        if not blocos: continue
                        
                        c_teste = calcular_comprimento_mesa(blocos)
                        if c_teste >= comp_min and c_teste < melhor_comp:
                            melhor_comp = c_teste
                            blocos_finais = blocos

                if not blocos_finais:
                    q_2v_fallback = math.ceil(comp_min / 6.0)
                    blocos_finais = ["2v"] * q_2v_fallback
                    if v_pcd > 0:
                        blocos_finais.extend(["pcd"] * v_pcd)

                comprimento_final = calcular_comprimento_mesa(blocos_finais)
                modulos_finais = v_mod
                vagas_reg_finais = (blocos_finais.count("2v") * 2) + blocos_finais.count("1v")

            if comprimento_final > limite_atual_p:
                st.error(f"⛔ **MESA NÃO ADICIONADA:** O comprimento calculado ({comprimento_final:.2f}m) excede o limite máximo para mesas de **{linhas_p} linhas**.")
            else:
                comprimento_ocupado = (modulos_por_linha * largura_calc_p) + ((modulos_por_linha + 1) * ESPESSURA_FIXADOR)
                sobra_terca = comprimento_final - comprimento_ocupado
                sobra_cm = round(sobra_terca * 100, 1)
                
                kits_detalhados = detalhar_kits(blocos_finais)
                
                mesa_nome_final = nome_mesa if nome_mesa else f"Mesa {len(st.session_state['mesas']) + 1}"
                total_fixadores = (modulos_por_linha + 1) * 2 * linhas_p

                nova_mesa = {
                    "Mesa": mesa_nome_final,
                    "Sobra (cm)": sobra_cm,
                    "Modo": modo,
                    "Linhas": linhas_p,
                    "Vagas Padrão": vagas_reg_finais,
                    "Vagas PCD": v_pcd,
                    "Módulos": modulos_finais,
                    "Fixadores": total_fixadores,
                }
                nova_mesa.update(kits_detalhados)
                
                st.session_state["mesas"].append(nova_mesa)
                st.success(f"✅ {mesa_nome_final} adicionada! Sobra: {sobra_cm} cm.")

    st.subheader("📋 Resumo do Projeto")
    if len(st.session_state["mesas"]) > 0:
        df_projeto = pd.DataFrame(st.session_state["mesas"])
        
        mesas_erro = df_projeto[df_projeto["Sobra (cm)"] < 5.0]
        mesas_alerta = df_projeto[(df_projeto["Sobra (cm)"] >= 5.0) & (df_projeto["Sobra (cm)"] < 15.0)]
        
        if not mesas_erro.empty:
            st.error(f"🚨 **ALERTA DE SEGURANÇA:** As seguintes mesas estão com folga muito baixa (< 5cm): {', '.join(mesas_erro['Mesa'].tolist())}")
            
        if not mesas_alerta.empty:
            st.warning(f"⚠️ **Atenção:** As seguintes mesas estão com folga de atenção (< 15cm): {', '.join(mesas_alerta['Mesa'].tolist())}")
        
        df_visualizacao = df_projeto.astype(str)
        
        col_mapping = {
            "Mesa": ("Informações da Mesa", "Nome"),
            "Sobra (cm)": ("Informações da Mesa", "Sobra (cm)"),
            "Modo": ("Informações da Mesa", "Modo"),
            "Linhas": ("Informações da Mesa", "Linhas"),
            "Vagas Padrão": ("Informações da Mesa", "Vagas Pad."),
            "Vagas PCD": ("Informações da Mesa", "Vagas PCD"),
            "Módulos": ("Informações da Mesa", "Módulos"),
            "Fixadores": ("Informações da Mesa", "Fixadores"),
            "Início 2V": ("✅ Kit Início", "2 Vagas"),
            "Início 1V": ("✅ Kit Início", "1 Vaga"),
            "Início PCD": ("✅ Kit Início", "PCD"),
            "Meio 2V": ("🔗 Kits Meio", "2 Vagas"),
            "Meio 1V": ("🔗 Kits Meio", "1 Vaga"),
            "Meio PCD": ("🔗 Kits Meio", "PCD"),
            "Fim 2V": ("🏁 Kit Fim", "2 Vagas"),
            "Fim 1V": ("🏁 Kit Fim", "1 Vaga"),
            "Fim PCD": ("🏁 Kit Fim", "PCD")
        }
        
        df_visualizacao.columns = pd.MultiIndex.from_tuples(
            [col_mapping.get(c, ("Outros", c)) for c in df_visualizacao.columns]
        )
        
        df_visualizacao.index = range(1, len(df_visualizacao) + 1)
        
        st.dataframe(df_visualizacao, width="stretch")

        st.markdown("---")
        st.subheader("📦 Total de Kits Desse Projeto:")
        
        # Iniciais
        if df_projeto["Início 2V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Início 2V'].sum()}x Kit Inicial:** 2 Vagas completo (6.0m)")
        if df_projeto["Início 1V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Início 1V'].sum()}x Kit Inicial:** 1 Vaga completo (3.0m)")
        if df_projeto["Início PCD"].sum() > 0:
            st.markdown(f"• **{df_projeto['Início PCD'].sum()}x Kit Inicial:** 1 vaga PCD completo (3.8m)")
            
        # Meios
        if df_projeto["Meio 2V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Meio 2V'].sum()}x Kit Meio:** 2 Vagas complemento (6.0m)")
        if df_projeto["Meio 1V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Meio 1V'].sum()}x Kit Meio:** 1 Vaga complemento (3.0m)")
        if df_projeto["Meio PCD"].sum() > 0:
            st.markdown(f"• **{df_projeto['Meio PCD'].sum()}x Kit Meio:** 1 vaga PCD complemento (3.8m)")
            
        # Finais
        if df_projeto["Fim 2V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Fim 2V'].sum()}x Kit Final:** 2 Vagas complemento (6.0m)")
        if df_projeto["Fim 1V"].sum() > 0:
            st.markdown(f"• **{df_projeto['Fim 1V'].sum()}x Kit Final:** 1 Vaga complemento (3.0m)")
        if df_projeto["Fim PCD"].sum() > 0:
            st.markdown(f"• **{df_projeto['Fim PCD'].sum()}x Kit Final:** 1 vaga PCD complemento (3.8m)")
            
        st.markdown("<br>", unsafe_allow_html=True) 

        col_btn1, col_btn2 = st.columns([1, 5])
        with col_btn1:
            if st.button("🗑️ Limpar Projeto"):
                st.session_state["mesas"] = []
                st.rerun()
    else:
        st.info("Nenhuma mesa adicionada ao projeto ainda.")