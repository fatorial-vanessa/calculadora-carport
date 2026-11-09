import math
import io
import subprocess
import sys
import pandas as pd
import streamlit as st

try:
    import openpyxl
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl

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

def exibir_resumo_kits_mesa(blocos_projeto):
    st.markdown("**Lista de Kits desta Mesa:**")
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
            if meios.count("2v") > 0: 
                meio_str.append(f"{meios.count('2v')}x Padrão 2 Vagas ({TERCAS['2v']['meio']}m)")
            if meios.count("1v") > 0: 
                meio_str.append(f"{meios.count('1v')}x Padrão 1 Vaga ({TERCAS['1v']['meio']}m)")
            if meios.count("pcd") > 0: 
                meio_str.append(f"{meios.count('pcd')}x PCD ({TERCAS['pcd']['meio']}m)")
            st.write("• **Kit(s) Meio:** " + " / ".join(meio_str))
        st.write(f"• **1x Kit Final:** {NOMES_KITS[fim]} ({TERCAS[fim]['fin']}m)")

def callback_adicionar_vagas():
    if "res_vagas" in st.session_state and st.session_state["res_vagas"]:
        res = st.session_state["res_vagas"]
        kits_det = detalhar_kits(res["blocos"])
        nova_mesa = {
            "Mesa": res["nome_mesa"],
            "Sobra (cm)": round(res["sobra_terca"] * 100, 1),
            "Modo": "Por Vagas",
            "Linhas": res["linhas"],
            "Vagas Padrão": res["vagas_comuns"],
            "Vagas PCD": res["vagas_pcd"],
            "Módulos": res["total_modulos"],
            "Fixadores": res["total_fixadores"],
        }
        nova_mesa.update(kits_det)
        st.session_state["mesas"].append(nova_mesa)
        st.session_state["linhas_projeto"] = res["linhas"]
        st.session_state["res_vagas"] = None

def callback_adicionar_modulos():
    if "res_modulos" in st.session_state and st.session_state["res_modulos"]:
        res_m = st.session_state["res_modulos"]
        kits_det = detalhar_kits(res_m["blocos"])
        nova_mesa = {
            "Mesa": res_m["nome_mesa"],
            "Sobra (cm)": round(res_m["sobra_terca"] * 100, 1),
            "Modo": "Por Módulos",
            "Linhas": res_m["linhas"],
            "Vagas Padrão": res_m["vagas_padrao"],
            "Vagas PCD": res_m["vagas_pcd"],
            "Módulos": res_m["total_modulos"],
            "Fixadores": res_m["total_fixadores"],
        }
        nova_mesa.update(kits_det)
        st.session_state["mesas"].append(nova_mesa)
        st.session_state["linhas_projeto"] = res_m["linhas"]
        st.session_state["res_modulos"] = None

# Inicialização dos estados no session_state
if "mesas" not in st.session_state:
    st.session_state["mesas"] = []

if "linhas_projeto" not in st.session_state:
    st.session_state["linhas_projeto"] = None

tab_vagas, tab_modulos = st.tabs(
    ["🅿️ 1. Por Quantidade de Vagas", "☀️ 2. Por Quantidade de Módulos"]
)

# ==============================================================================
# ABA 1: DIMENSIONAMENTO POR VAGAS
# ==============================================================================
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
        nome_mesa_v = st.text_input("Nome/Identificação da Mesa (Opcional):", placeholder="Ex: Mesa Estacionamento A", key="v_nome_mesa")

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
            st.error("ℹ️ Informe pelo menos 1 vaga para realizar o cálculo.")
            st.session_state["res_vagas"] = None
        elif comprimento_estrutura > limite_atual:
            st.error(f"⛔ **LIMITE EXCEDIDO:** O comprimento da mesa ({comprimento_estrutura:.2f}m) ultrapassou o limite máximo permitido para mesas de **{linhas} linhas**! Reduza a quantidade de vagas.")
            st.session_state["res_vagas"] = None
        else:
            modulos_por_linha = math.floor((comprimento_estrutura - ESPESSURA_FIXADOR) / (largura_calc + ESPESSURA_FIXADOR))
            total_modulos = modulos_por_linha * linhas
            comprimento_ocupado = (modulos_por_linha * largura_calc) + ((modulos_por_linha + 1) * ESPESSURA_FIXADOR)
            sobra_terca = comprimento_estrutura - comprimento_ocupado
            total_fixadores = 2 * (modulos_por_linha + 1) * linhas

            st.session_state["res_vagas"] = {
                "blocos": blocos_projeto,
                "comprimento": comprimento_estrutura,
                "total_modulos": total_modulos,
                "modulos_por_linha": modulos_por_linha,
                "sobra_terca": sobra_terca,
                "total_fixadores": total_fixadores,
                "vagas_comuns": vagas_comuns,
                "vagas_pcd": vagas_pcd,
                "linhas": linhas,
                "nome_mesa": nome_mesa_v if nome_mesa_v else f"Mesa {len(st.session_state['mesas']) + 1}"
            }

    if st.session_state.get("res_vagas"):
        res = st.session_state["res_vagas"]
        st.divider()

        vagas_totais = res["vagas_comuns"] + res["vagas_pcd"]
        if res["linhas"] == 5:
            st.info(f"ℹ️ **Arranjo de 5 Linhas (Vagas Duplas):** A estrutura de **{vagas_totais} vagas lineares** cobrirá **{vagas_totais * 2} vagas totais**.")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Módulos (Total)", f"{res['total_modulos']} un")
        m2.metric("Módulos por Linha", f"{res['modulos_por_linha']} un")
        m3.metric("Comprimento da Estrutura", f"{res['comprimento']:.2f} m")
        m4.metric("Sobra de Terça / Folga", f"{res['sobra_terca'] * 100:.1f} cm")

        st.markdown("---")
        if res["sobra_terca"] < 0.05:
            st.error(f"🚨 **ALERTA DE SEGURANÇA:** Sobra de apenas **{res['sobra_terca'] * 100:.1f} cm** nas pontas!")
        elif res["sobra_terca"] < 0.15:
            st.warning(f"⚠️ **Atenção:** Folga de apenas **{res['sobra_terca'] * 100:.1f} cm** nas extremidades.")
        else:
            st.success(f"✅ **Margem Segura:** Folga de **{res['sobra_terca'] * 100:.1f} cm** disponível nas terças.")

        st.subheader("📦 Composição de Kits e Componentes")
        st.write(f"🔩 **Total de Fixadores Universais Clampar:** `{res['total_fixadores']}` unidades")
        
        exibir_resumo_kits_mesa(res["blocos"])

        col_add, _ = st.columns([1, 2])
        with col_add:
            # Trava de Segurança
            if st.session_state["linhas_projeto"] is not None and res["linhas"] != st.session_state["linhas_projeto"]:
                st.error(f"⛔ **Adição Bloqueada:** O projeto atual está travado em mesas de **{st.session_state['linhas_projeto']} Linhas**. Para adicionar mesas de **{res['linhas']} Linhas**, limpe o projeto atual.")
            else:
                st.button(
                    "➕ Adicionar Esta Mesa ao Projeto", 
                    type="primary", 
                    key="btn_add_vagas", 
                    on_click=callback_adicionar_vagas
                )


# ==============================================================================
# ABA 2: DIMENSIONAMENTO POR MÓDULOS
# ==============================================================================
with tab_modulos:
    st.header("Dimensionamento baseado na Quantidade de Módulos")

    col1, col2 = st.columns(2)
    with col1:
        total_modulos_m = st.number_input("Total de Módulos:", min_value=1, value=1, key="m_tot")
        
        modo_calculo_m = st.radio(
            "Modo de Encaixe dos Kits:",
            ["Manual (Com/Sem PCD)", "Otimizado Automático (Best Fit)"],
            horizontal=True,
            key="m_modo_calc"
        )
        
        pcd_qtd = 0
        posicao_pcd = "No Fim"
        
        if modo_calculo_m == "Manual (Com/Sem PCD)":
            incluir_pcd_m = st.radio("Incluir Vagas PCD?", ["Não", "Sim"], horizontal=True, key="m_pcd_radio")
            if incluir_pcd_m == "Sim":
                pcd_qtd = st.number_input("Quantidade de Vagas PCD:", min_value=1, max_value=10, value=1, key="m_pcd_qtd")
                if pcd_qtd == 1:
                    posicao_pcd = st.radio("Posição da Vaga PCD:", ["No Início", "No Meio", "No Fim"], horizontal=True, key="m_pcd_pos")
                else:
                    st.info("ℹ️ Como são várias vagas PCD, o sistema colocará 1 no final e as demais serão distribuídas no meio.")

    with col2:
        largura_str_m = st.text_input("Largura do Módulo (m):", value="1.134", key="m_larg_str")
        try:
            largura_mod_m = float(largura_str_m.replace(",", "."))
        except ValueError:
            largura_mod_m = 1.134

        linhas_m = st.selectbox("Arranjo de Linhas da Mesa:", [2, 3, 5], index=0, key="m_lin")
        nome_mesa_m = st.text_input("Nome/Identificação da Mesa (Opcional):", placeholder="Ex: Mesa Cobertura B", key="m_nome_mesa")

    if st.button("🚀 Calcular por Módulos", key="btn_modulos"):
        limite_atual_m = LIMITES_LINHAS.get(linhas_m, 30.0)

        resto = total_modulos_m % linhas_m
        modulos_considerados = math.ceil(total_modulos_m / linhas_m) * linhas_m if resto != 0 else total_modulos_m
        largura_calc_m = math.ceil(largura_mod_m * 100) / 100
        modulos_por_linha_m = modulos_considerados // linhas_m

        comprimento_minimo_mesa = (modulos_por_linha_m * largura_calc_m) + ((modulos_por_linha_m + 1) * ESPESSURA_FIXADOR)

        if comprimento_minimo_mesa > limite_atual_m:
            st.error(f"⛔ **LIMITE EXCEDIDO:** Essa quantidade de módulos exige um comprimento mínimo de ({comprimento_minimo_mesa:.2f}m), ultrapassando o limite máximo permitido para mesas de **{linhas_m} linhas**!")
            st.session_state["res_modulos"] = None
        else:
            melhor_comprimento = float('inf')
            melhor_combinacao = []
            limite_kits = math.ceil(comprimento_minimo_mesa / 2.0) + 15

            if modo_calculo_m == "Otimizado Automático (Best Fit)":
                for q_2v in range(limite_kits):
                    for q_1v in [0, 1]:  
                        for q_pcd in range(limite_kits):
                            if q_2v == 0 and q_1v == 0 and q_pcd == 0: continue
                            blocos = ["2v"] * q_2v + ["pcd"] * q_pcd + ["1v"] * q_1v
                            comp_teste = calcular_comprimento_mesa(blocos)
                            if comp_teste >= comprimento_minimo_mesa and comp_teste < melhor_comprimento:
                                melhor_comprimento = comp_teste
                                melhor_combinacao = blocos
            else:
                for q_2v in range(limite_kits):
                    for q_1v in [0, 1]:  
                        blocos = ["2v"] * q_2v + ["1v"] * q_1v
                        if pcd_qtd > 0:
                            lista_pcds = ["pcd"] * pcd_qtd
                            if pcd_qtd == 1:
                                if posicao_pcd == "No Início": blocos = lista_pcds + blocos
                                elif posicao_pcd == "No Meio":
                                    meio = len(blocos) // 2 if blocos else 0
                                    blocos = blocos[:meio] + lista_pcds + blocos[meio:]
                                else: blocos = blocos + lista_pcds
                            else:
                                pcd_fim = ["pcd"]
                                pcd_meio = ["pcd"] * (pcd_qtd - 1)
                                meio = len(blocos) // 2 if blocos else 0
                                blocos = blocos[:meio] + pcd_meio + blocos[meio:] + pcd_fim

                        if not blocos: continue
                        comp_teste = calcular_comprimento_mesa(blocos)
                        if comp_teste >= comprimento_minimo_mesa and comp_teste < melhor_comprimento:
                            melhor_comprimento = comp_teste
                            melhor_combinacao = blocos

            if not melhor_combinacao:
                q_2v_fallback = math.ceil(comprimento_minimo_mesa / 6.0)
                melhor_combinacao = ["2v"] * q_2v_fallback
                if pcd_qtd > 0 and modo_calculo_m == "Manual (Com/Sem PCD)":
                    melhor_combinacao.extend(["pcd"] * pcd_qtd)
                melhor_comprimento = calcular_comprimento_mesa(melhor_combinacao)

            sobra_terca_m = melhor_comprimento - comprimento_minimo_mesa
            total_fixadores_m = 2 * (modulos_por_linha_m + 1) * linhas_m
            
            vagas_geradas_padrao = (melhor_combinacao.count("2v") * 2) + melhor_combinacao.count("1v")
            vagas_geradas_pcd = melhor_combinacao.count("pcd")

            st.session_state["res_modulos"] = {
                "blocos": melhor_combinacao,
                "comprimento": melhor_comprimento,
                "total_modulos": total_modulos_m,
                "modulos_por_linha": modulos_por_linha_m,
                "sobra_terca": sobra_terca_m,
                "total_fixadores": total_fixadores_m,
                "vagas_padrao": vagas_geradas_padrao,
                "vagas_pcd": vagas_geradas_pcd,
                "linhas": linhas_m,
                "resto_ajuste": resto,
                "nome_mesa": nome_mesa_m if nome_mesa_m else f"Mesa {len(st.session_state['mesas']) + 1}"
            }

    if st.session_state.get("res_modulos"):
        res_m = st.session_state["res_modulos"]
        st.divider()

        if res_m["resto_ajuste"] != 0:
            st.warning(f"⚠️ **Ajuste de Arranjo:** A quantidade digitada não é múltipla de {res_m['linhas']}. O cálculo considerou o espaço físico para **{res_m['modulos_por_linha'] * res_m['linhas']} módulos**.")

        vagas_totais_lineares = res_m["vagas_padrao"] + res_m["vagas_pcd"]
        if res_m["linhas"] == 5:
            st.info(f"ℹ️ **Arranjo de 5 Linhas (Vagas Duplas):** Foram geradas **{vagas_totais_lineares} vagas lineares** ({vagas_totais_lineares * 2} vagas totais no estacionamento).")
            label_vagas = "Vagas (Totais/Lineares)"
            valor_vagas = f"{vagas_totais_lineares * 2} / {vagas_totais_lineares}"
        else:
            label_vagas = "Vagas Geradas"
            valor_vagas = f"{vagas_totais_lineares} un"

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Módulos/Linha", f"{res_m['modulos_por_linha']} un")
        m2.metric("Comprimento", f"{res_m['comprimento']:.2f} m")
        m3.metric(label_vagas, valor_vagas)
        m4.metric("Sobra de Terça", f"{res_m['sobra_terca'] * 100:.1f} cm")

        st.markdown("---")

        if res_m["sobra_terca"] < 0.05:
            st.error(f"🚨 **ALERTA DE SEGURANÇA:** Sobra de apenas **{res_m['sobra_terca'] * 100:.1f} cm** nas pontas!")
        elif res_m["sobra_terca"] < 0.15:
            st.warning(f"⚠️ **Atenção:** Folga de **{res_m['sobra_terca'] * 100:.1f} cm** nas terças.")
        else:
            st.success(f"✅ **Margem Segura:** Folga de **{res_m['sobra_terca'] * 100:.1f} cm** disponível nas terças.")

        st.subheader("📦 Composição de Kits e Componentes")
        st.markdown(f"🔩 **Total de Fixadores Universais Clampar:** `{res_m['total_fixadores']}` unidades")
        
        exibir_resumo_kits_mesa(res_m["blocos"])

        col_add_m, _ = st.columns([1, 2])
        with col_add_m:
            if st.session_state["linhas_projeto"] is not None and res_m["linhas"] != st.session_state["linhas_projeto"]:
                st.error(f"⛔ **Adição Bloqueada:** O projeto atual está travado em mesas de **{st.session_state['linhas_projeto']} Linhas**. Para adicionar mesas de **{res_m['linhas']} Linhas**, limpe o projeto atual.")
            else:
                st.button(
                    "➕ Adicionar Esta Mesa ao Projeto", 
                    type="primary", 
                    key="btn_add_modulos", 
                    on_click=callback_adicionar_modulos
                )

# ==============================================================================
# TABELA E RESUMO DO PROJETO (FIXO NA PARTE INFERIOR)
# ==============================================================================
st.divider()
st.header("📊 Resumo Consolidado do Projeto")

if st.session_state["linhas_projeto"] is not None:
    st.info(f"🔒 **Arranjo do Projeto Atual:** Mesas de **{st.session_state['linhas_projeto']} Linhas**")

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
    
    st.dataframe(df_visualizacao, use_container_width=True, hide_index=True)

    col_exp1, col_exp2, _ = st.columns([1, 1, 2])

    csv_data = df_projeto.to_csv(index=False).encode("utf-8-sig")
    with col_exp1:
        st.download_button(
            label="📥 Baixar Tabela (CSV)",
            data=csv_data,
            file_name="resumo_carport.csv",
            mime="text/csv",
        )
        
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df_projeto.to_excel(writer, sheet_name="Resumo Carport", index=False)
    excel_data = buffer.getvalue()

    with col_exp2:
        st.download_button(
            label="📊 Baixar Tabela (Excel)",
            data=excel_data,
            file_name="resumo_carport.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    col_del1, col_del2 = st.columns([2, 1])
    with col_del1:
        nomes_mesas = [m["Mesa"] for m in st.session_state["mesas"]]
        mesa_para_remover = st.selectbox("Selecione uma mesa para remover do projeto:", nomes_mesas, key="sel_del_mesa")
    with col_del2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        if st.button("❌ Remover Mesa Selecionada", type="secondary"):
            st.session_state["mesas"] = [m for m in st.session_state["mesas"] if m["Mesa"] != mesa_para_remover]
            if len(st.session_state["mesas"]) == 0:
                st.session_state["linhas_projeto"] = None
            st.rerun()

    st.markdown("---")
    st.subheader("📦 Totais Consolidados do Projeto")
    
    total_modulos_projeto = df_projeto["Módulos"].sum()
    st.metric("☀️ Total de Módulos (Painéis) do Projeto", f"{total_modulos_projeto} unidades")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**🟢 Kits Início:**")
        if df_projeto["Início 2V"].sum() > 0: st.write(f"• **{df_projeto['Início 2V'].sum()}x** Kit Inicial 2 Vagas (6.0m)")
        if df_projeto["Início 1V"].sum() > 0: st.write(f"• **{df_projeto['Início 1V'].sum()}x** Kit Inicial 1 Vaga (3.0m)")
        if df_projeto["Início PCD"].sum() > 0: st.write(f"• **{df_projeto['Início PCD'].sum()}x** Kit Inicial PCD (4.5m)")

    with c2:
        st.markdown("**🔗 Kits Meio:**")
        if df_projeto["Meio 2V"].sum() > 0: st.write(f"• **{df_projeto['Meio 2V'].sum()}x** Kit Meio 2 Vagas (5.0m)")
        if df_projeto["Meio 1V"].sum() > 0: st.write(f"• **{df_projeto['Meio 1V'].sum()}x** Kit Meio 1 Vaga (2.5m)")
        if df_projeto["Meio PCD"].sum() > 0: st.write(f"• **{df_projeto['Meio PCD'].sum()}x** Kit Meio PCD (3.7m)")

    with c3:
        st.markdown("**🏁 Kits Fim:**")
        if df_projeto["Fim 2V"].sum() > 0: st.write(f"• **{df_projeto['Fim 2V'].sum()}x** Kit Final 2 Vagas (6.0m)")
        if df_projeto["Fim 1V"].sum() > 0: st.write(f"• **{df_projeto['Fim 1V'].sum()}x** Kit Final 1 Vaga (3.0m)")
        if df_projeto["Fim PCD"].sum() > 0: st.write(f"• **{df_projeto['Fim PCD'].sum()}x** Kit Final PCD (4.5m)")

    st.markdown(f"🔩 **Total Geral de Fixadores:** `{df_projeto['Fixadores'].sum()}` unidades")

    st.markdown("<br>", unsafe_allow_html=True)
    col_btn1, _ = st.columns([1, 5])
    with col_btn1:
        if st.button("🗑️ Limpar Todo o Projeto", type="secondary"):
            st.session_state["mesas"] = []
            st.session_state["linhas_projeto"] = None
            if "res_vagas" in st.session_state: st.session_state["res_vagas"] = None
            if "res_modulos" in st.session_state: st.session_state["res_modulos"] = None
            st.rerun()
else:
    st.info("Nenhuma mesa adicionada ao projeto ainda. Realize um cálculo acima e clique em '➕ Adicionar Esta Mesa ao Projeto'.")
