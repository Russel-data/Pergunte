import streamlit as st
import pandas as pd
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re

ADMIN_PASSWORD = "admin123"
FILE_PATH = "base.xlsx"

# Função para carregar os dados
def load_data():
    try:
        df = pd.read_excel(FILE_PATH)
        df["Palavras-Chave"] = df["Palavras-Chave"].astype(str)
        df["Palavras-Chave"] = df["Palavras-Chave"].apply(lambda x: [normalizar_texto(p) for p in x.split(",")] if isinstance(x, str) else [])
        return df
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo: {e}")
        return pd.DataFrame(columns=["Pergunta", "Resposta", "Palavras-Chave"])

# Função para salvar os dados
def save_data(df):
    try:
        df.to_excel(FILE_PATH, index=False)
        st.success("✅ Alterações salvas com sucesso!")
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

# Carregar os dados diretamente do arquivo
df = load_data()

st.title("Pergunte para o Russel 🤖")
st.divider()
st.subheader("👋 Olá! Eu sou o Russel, sua assistente virtual! 🚀")  
st.write(
    "Fui treinado com as informações que o Wallisson me fornece para tornar seu dia de trabalho mais fácil. "
    "Para obter respostas mais precisas, tente começar sua pergunta com **'REALIZA'**. "
    "Por exemplo: *Realiza USG da cintura pélvica?* 🏥📄\n\n"
    "Estou aqui para te ajudar! Pergunte o que precisar. 😊"
)




modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))

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
        
        resposta = "Desculpe, não posso te ajudar agora."
        for _, row in df.iterrows():
            palavras_chave = row["Palavras-Chave"]
            if isinstance(palavras_chave, list):
                pontuacoes = [fuzz.token_set_ratio(palavra, normalizar_texto(prompt)) for palavra in palavras_chave]
                if max(pontuacoes, default=0) >= 50:
                    resposta = row["Resposta"]
                    break
        
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta.replace("\n", "  \n"))

elif modo == "Administrador":
    st.subheader("🔒 Acesso Restrito")
    senha = st.text_input("Digite a senha:", type="password")
    
    if st.button("Entrar"):
        if senha == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.success("Acesso permitido! ✅")
        else:
            st.error("❌ Senha incorreta!")

    if st.session_state.get("admin_authenticated", False):
        st.header("Modo Administrador")
        st.write("Edite diretamente a tabela abaixo e clique em **Salvar Alterações** para gravar as mudanças.")

        df["Palavras-Chave"] = df["Palavras-Chave"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
        df_editado = st.data_editor(df, num_rows="dynamic")

        if st.button("Salvar Alterações"):
            df_editado["Palavras-Chave"] = df_editado["Palavras-Chave"].apply(lambda x: x.split(", ") if isinstance(x, str) else [])
            save_data(df_editado)
            st.rerun()


