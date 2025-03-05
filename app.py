import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re

# Definir a senha do administrador
ADMIN_PASSWORD = "admin123"

# Carregar a planilha
def load_data():
    try:
        df = pd.read_excel("base.xlsx")
        df["Palavras-Chave"] = df["Palavras-Chave"].astype(str)
        df["Palavras-Chave"] = df["Palavras-Chave"].apply(lambda x: [normalizar_texto(p) for p in x.split(",")] if isinstance(x, str) else [])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return pd.DataFrame()

# Salvar a planilha
def save_data(df):
    try:
        df.to_excel("base.xlsx", index=False)
        st.success("Dados salvos com sucesso!")
        st.cache_data.clear()  # Limpa o cache
    except Exception as e:
        st.error(f"Erro ao salvar o arquivo: {e}")

# Função para normalizar texto
def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    return ""

# Função para encontrar resposta por palavras-chave
def encontrar_resposta_por_palavras_chave(prompt, df):
    prompt = normalizar_texto(prompt)
    melhor_pontuacao = 0
    melhor_resposta = None

    for _, row in df.iterrows():
        palavras_chave = row["Palavras-Chave"]
        if not isinstance(palavras_chave, list):
            continue
        pontuacoes = [fuzz.token_set_ratio(palavra, prompt) for palavra in palavras_chave]
        pontuacao = max(pontuacoes) if pontuacoes else 0
        if pontuacao > melhor_pontuacao and pontuacao >= 50:
            melhor_pontuacao = pontuacao
            melhor_resposta = row["Resposta"]
    return melhor_resposta if melhor_resposta else "Desculpe, não entendi. Pode reformular a pergunta?"

# Interface do app
st.title("Pergunte para o Russel 🤖")
modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))
df = load_data()

if df.empty:
    st.error("O arquivo está vazio ou não pôde ser carregado. Verifique o arquivo.")
    st.stop()

colunas_necessarias = ["Pergunta", "Resposta", "Palavras-Chave"]
for coluna in colunas_necessarias:
    if coluna not in df.columns:
        st.error(f"O arquivo não contém a coluna '{coluna}'. Verifique o arquivo.")
        st.stop()

if modo == "Colaborador":
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("\n", "  \n"))
    prompt = st.chat_input("Digite sua mensagem...")
    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        response = encontrar_resposta_por_palavras_chave(prompt, df)
        st.session_state.messages.append({"role": "assistant", "content": response})
        with st.chat_message("assistant"):
            st.markdown(response.replace("\n", "  \n"))

elif modo == "Administrador":
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False
    if not st.session_state.admin_authenticated:
        st.subheader("🔒 Acesso Restrito")
        senha = st.text_input("Digite a senha:", type="password")
        if st.button("Entrar"):
            if senha == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("Acesso permitido! ✅")
            else:
                st.error("❌ Senha incorreta!")
    if st.session_state.admin_authenticated:
        st.header("Modo Administrador")
        st.write("Edite diretamente a tabela abaixo e clique em salvar para atualizar os dados.")

        df["Palavras-Chave"] = df["Palavras-Chave"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        df_editado = st.data_editor(df, num_rows="dynamic")
        if st.button("Salvar Alterações"):
            df_editado["Palavras-Chave"] = df_editado["Palavras-Chave"].apply(lambda x: x.split(", ") if isinstance(x, str) else [])
            save_data(df_editado)
            st.success("Alterações salvas com sucesso!")















