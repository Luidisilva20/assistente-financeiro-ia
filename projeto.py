import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# 1. CONFIGURAÇÃO DA IA E SYSTEM PROMPT
# ==========================================
CHAVE_API = os.getenv("CHAVE_API") 
genai.configure(api_key=CHAVE_API)

instrucoes_sistema = """
Você é um Assistente Financeiro Educacional empático, claro e objetivo.
Seu objetivo é ajudar iniciantes a entenderem conceitos de economia, produtos financeiros e organização pessoal.

REGRAS OBRIGATÓRIAS (GUARDRAILS):
1. NUNCA recomende ativos específicos de renda variável (ex: "compre a ação da empresa X" ou "invista na criptomoeda Y").
2. Sempre lembre o usuário de que simulações são apenas estimativas educacionais e não garantias de retorno.
3. Se o usuário perguntar algo fora do universo financeiro/econômico, recuse educadamente e traga o assunto de volta para finanças.
4. Formate suas respostas usando tópicos curtos e negrito para facilitar a leitura.
"""

# Inicializa o modelo usando a versão 2.5 
modelo = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=instrucoes_sistema
)

# ==========================================
# 2. LÓGICA DE SIMULAÇÃO (DETERMINÍSTICA)
# ==========================================
def simular_juros_compostos(aporte_inicial, aporte_mensal, taxa_anual, anos):
    taxa_mensal = (1 + taxa_anual / 100) ** (1 / 12) - 1
    meses = anos * 12
    montante = aporte_inicial * (1 + taxa_mensal)**meses
    for _ in range(meses):
        montante += aporte_mensal * (1 + taxa_mensal)**(meses - _)
    return round(montante, 2)

def reiniciar_conversa():
    st.session_state.mensagens = [
        {"role": "assistant", "content": "Como posso te ajudar a organizar suas finanças hoje?"}
    ]

# ==========================================
# 3. INTERFACE E UX (STREAMLIT)
# ==========================================
st.set_page_config(page_title="Seu Assistente Financeiro", page_icon="💰")

# Inicializa a memória da conversa se não existir
if "mensagens" not in st.session_state:
    reiniciar_conversa()

with st.sidebar:
    st.header("📊 Simulador de Investimentos")
    st.write("Arraste ou digite os valores abaixo:")
    
    # Controles interativos
    aporte_inicial = st.number_input("Aporte Inicial (R$)", min_value=0, value=1000, step=100)
    aporte_mensal = st.number_input("Aporte Mensal (R$)", min_value=0, value=200, step=50)
    taxa_anual = st.slider("Taxa de Juros Anual (%)", min_value=1.0, max_value=20.0, value=10.0, step=0.5)
    anos = st.slider("Tempo (Anos)", min_value=1, max_value=30, value=5)
    
    # Botão de simular
    if st.button("Calcular Simulação", type="primary"):
        resultado = simular_juros_compostos(aporte_inicial, aporte_mensal, taxa_anual, anos)
        # Formata o texto para a IA ler e para o usuário ver
        texto_resultado = f"Fiz uma simulação pelo menu lateral! Com R$ {aporte_inicial} iniciais, mais R$ {aporte_mensal} por mês, a {taxa_anual}% ao ano durante {anos} anos, você terá aproximadamente **R$ {resultado}**.\n\n*Lembrando que é uma estimativa educacional!* Quer que eu te explique como os juros compostos fizeram esse dinheiro crescer?"
        st.session_state.mensagens.append({"role": "assistant", "content": texto_resultado})
        
    st.divider() 
    
    # Botão de limpar memória
    st.button("🗑️ Reiniciar Conversa", on_click=reiniciar_conversa)

# --- TELA PRINCIPAL ---
st.title("Olá! Sou seu Assistente Financeiro 🤖")
st.markdown("Posso te ajudar a entender conceitos de economia, tirar dúvidas sobre produtos e simular investimentos.")

st.write("💡 **Perguntas rápidas:**")
col1, col2, col3 = st.columns(3)

# Variável para capturar se o usuário clicou em um botão
prompt_sugestao = None
if col1.button("O que é Tesouro Direto?"): prompt_sugestao = "O que é Tesouro Direto?"
if col2.button("CDB ou Poupança?"): prompt_sugestao = "Qual a diferença entre CDB e Poupança?"
if col3.button("Dicas de reserva extra"): prompt_sugestao = "Como montar uma reserva de emergência?"

st.divider()

# Renderiza as mensagens anteriores na tela
for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ==========================================
# 4. CHAT E INTEGRAÇÃO COM A IA
# ==========================================
# Captura o texto digitado OU o botão clicado
prompt_digitado = st.chat_input("Ex: O que é CDB? ou Simule um investimento...")
prompt_final = prompt_digitado or prompt_sugestao

if prompt_final:
    # Mostra a mensagem do usuário
    st.session_state.mensagens.append({"role": "user", "content": prompt_final})
    with st.chat_message("user"):
        st.markdown(prompt_final)
        
    with st.chat_message("assistant"):
        with st.spinner("Pensando..."):
            try:
                # Junta o histórico para a IA ter contexto 
                historico = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.mensagens])
                
                # Gera a resposta com a API
                resposta_gerada = modelo.generate_content(historico)
                resposta_ia = resposta_gerada.text
                st.markdown(resposta_ia)
                
                # Salva a resposta da IA na memória
                st.session_state.mensagens.append({"role": "assistant", "content": resposta_ia})
            except Exception as e:
                st.error("Ops, tive um problema de conexão com o meu cérebro (API).")
                st.error(f"Detalhe técnico do erro: {e}")