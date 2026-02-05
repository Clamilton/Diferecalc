import streamlit as st
import pandas as pd

# Configuração da Página
st.set_page_config(page_title="Calc Tributária", layout="centered")

# --- Inicialização da Memória (Session State) ---
if 'fator_inversao' not in st.session_state:
    st.session_state.fator_inversao = 1

# Inicializa o valor do input se não existir
if 'valor_digitado' not in st.session_state:
    st.session_state.valor_digitado = "0,00"

# --- Funções Auxiliares ---

def formatar_brl(valor):
    """Transforma float 1500.50 em string '1.500,50'"""
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def converter_input_br(valor_texto):
    """Limpa string '1.500,50' para float 1500.50"""
    if not valor_texto: return 0.0
    try:
        # Remove pontos de milhar e troca vírgula por ponto decimal
        limpo = valor_texto.replace(".", "").replace(",", ".")
        return float(limpo)
    except ValueError:
        return 0.0

# --- CALLBACK: A mágica da auto-formatação ---
def atualizar_input():
    # Pega o que o usuário digitou
    texto_atual = st.session_state.valor_digitado
    # Converte para número real
    valor_float = converter_input_br(texto_atual)
    # Formata de volta para o padrão Bonito (1.000,00) e atualiza o input
    st.session_state.valor_digitado = formatar_brl(valor_float)

def calcular_distribuicao_completa(valor_total, variacao_pct, inverter_logica):
    taxa_pis = 1.65
    taxa_cofins = 7.60
    taxa_total = taxa_pis + taxa_cofins
    fator_pis = taxa_pis / taxa_total
    
    # 1. Base (Média)
    base_media = round(valor_total / 3, 2)
    valor_variacao = round(base_media * (variacao_pct / 100), 2)
    
    # 2. Definição dos Totais com Lógica de Inversão
    total_m1 = base_media
    
    if not inverter_logica:
        total_m2 = round(base_media - valor_variacao, 2)
        tipo_distribuicao = "📉 Padrão: Mês 2 Baixo / Mês 3 Alto"
    else:
        total_m2 = round(base_media + valor_variacao, 2)
        tipo_distribuicao = "📈 Invertido: Mês 2 Alto / Mês 3 Baixo"
        
    total_m3 = round(valor_total - (total_m1 + total_m2), 2)
    
    totais_mensais = [total_m1, total_m2, total_m3]
    meses_label = ["Mês 1 (Média)", "Mês 2 (Variação)", "Mês 3 (Ajuste Final)"]
    
    dados_finais = []
    
    for i, total_mes in enumerate(totais_mensais):
        v_pis = round(total_mes * fator_pis, 2)
        v_cofins = round(total_mes - v_pis, 2)
        
        dados_finais.append({
            "Mês": meses_label[i],
            "Valor PIS (1,65%)": formatar_brl(v_pis),
            "Valor COFINS (7,60%)": formatar_brl(v_cofins),
            "Total do Mês": formatar_brl(total_mes),
            "_total_raw": total_mes,
            "_pis_raw": v_pis,
            "_cofins_raw": v_cofins
        })
        
    return dados_finais, tipo_distribuicao

# --- Interface ---
st.title("📊 Distribuidor de Crédito")
st.markdown("Cálculo com alternância de padrão para evitar malha fina.")

with st.container(border=True):
    col1, col2 = st.columns(2)
    with col1:
        # Input vinculado ao Session State com Callback
        st.text_input(
            "Valor Total do Crédito (R$)", 
            key="valor_digitado",  # Vincula à variável na memória
            on_change=atualizar_input, # Roda a função de formatação ao dar Enter
            help="Digite o valor e aperte Enter. Ex: 1000 vira 1.000,00"
        )
        
        # Converte para usar no cálculo
        valor_input = converter_input_br(st.session_state.valor_digitado)
        
    with col2:
        pct_input = st.number_input("Variação (%)", value=12.3, step=0.1, format="%.2f")

# Botão de Ação
if st.button("Calcular Distribuição (Alternar Padrão)", type="primary"):
    
    if valor_input == 0:
        st.warning("Por favor, digite um valor maior que zero.")
    else:
        # Alterna o fator de inversão
        st.session_state.fator_inversao *= -1
        usar_inversao = (st.session_state.fator_inversao == -1)
        
        dados, status_msg = calcular_distribuicao_completa(valor_input, pct_input, usar_inversao)
        
        df_visual = pd.DataFrame(dados)[["Mês", "Valor PIS (1,65%)", "Valor COFINS (7,60%)", "Total do Mês"]]
        
        # Feedback Visual
        if usar_inversao:
            st.info(status_msg, icon="🔄")
        else:
            st.success(status_msg, icon="✅")
        
        st.subheader("Resultado (Copie e Cole)")
        st.dataframe(df_visual, use_container_width=True, hide_index=True)
        
        # Prova Real
        total_geral = sum([d['_total_raw'] for d in dados])
        dif = total_geral - valor_input
        
        st.markdown("---")
        if abs(dif) < 0.01:
            st.caption(f"Validação Matemática: R$ {formatar_brl(total_geral)} (Perfeito)")
        else:
            st.error(f"Erro de arredondamento: {dif}")
