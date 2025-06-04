import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
import pandas as pd
import json
import sys
import traceback
import time

# Configuração da página
st.set_page_config(
    page_title="Chatbot Russel 🤖",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Inicialização do estado da sessão
if "messages" not in st.session_state:
    st.session_state.messages = []
if "admin" not in st.session_state:
    st.session_state.admin = False

# Configurações de cache
@st.cache_resource(ttl=3600)
def init_firebase():
    try:
        if not firebase_admin._apps:
            cred_dict = {
                "type": st.secrets["firebase_credentials"]["type"],
                "project_id": st.secrets["firebase_credentials"]["project_id"],
                "private_key": st.secrets["firebase_credentials"]["private_key"].replace("\\n", "\n"),
                "client_email": st.secrets["firebase_credentials"]["client_email"],
                "auth_uri": st.secrets["firebase_credentials"]["auth_uri"],
                "token_uri": st.secrets["firebase_credentials"]["token_uri"],
                "auth_provider_x509_cert_url": st.secrets["firebase_credentials"]["auth_provider_x509_cert_url"],
                "client_x509_cert_url": st.secrets["firebase_credentials"]["client_x509_cert_url"]
            }
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar com o Firebase: {str(e)}")
        st.error("Detalhes do erro:")
        st.code(traceback.format_exc())
        return None

# Inicializa o Firebase
db = init_firebase()

# --- CONSTANTES --- #
ADMIN_PASSWORD = "admin123"

# --- FUNÇÕES --- #
@st.cache_data(ttl=300)
def normalizar_texto(texto):
    try:
        if isinstance(texto, str):
            texto = unidecode(texto.lower())
            texto = re.sub(r'[^\w\s]', '', texto)
            texto = re.sub(r'\s+', ' ', texto).strip()
            return texto
        return ""
    except Exception as e:
        st.error(f"Erro ao normalizar texto: {str(e)}")
        return ""

@st.cache_data(ttl=60)
def carregar_dados():
    try:
        if db is None:
            return []
        docs = db.collection("respostas").stream()
        dados = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            dados.append(d)
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar dados: {str(e)}")
        return []

@st.cache_data(ttl=60)
def carregar_sinonimos():
    try:
        if db is None:
            return []
        docs = db.collection("sinonimos").stream()
        sinons = []
        for doc in docs:
            d = doc.to_dict()
            d["id"] = doc.id
            sinons.append(d)
        return sinons
    except Exception as e:
        st.error(f"Erro ao carregar sinônimos: {str(e)}")
        return []

def salvar_pergunta(pergunta, resposta):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("respostas").document().set({
            "pergunta": pergunta,
            "resposta": resposta
        })
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pergunta: {str(e)}")
        return False

def atualizar_pergunta(id, pergunta, resposta):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("respostas").document(id).update({
            "pergunta": pergunta,
            "resposta": resposta
        })
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar pergunta: {str(e)}")
        return False

def deletar_pergunta(id):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("respostas").document(id).delete()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar pergunta: {str(e)}")
        return False

def salvar_sinonimo(sinonimo, palavra_chave):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("sinonimos").document().set({
            "sinonimo": sinonimo,
            "palavra_chave": palavra_chave
        })
        return True
    except Exception as e:
        st.error(f"Erro ao salvar sinônimo: {str(e)}")
        return False

def atualizar_sinonimo(id, sinonimo, palavra_chave):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("sinonimos").document(id).update({
            "sinonimo": sinonimo,
            "palavra_chave": palavra_chave
        })
        return True
    except Exception as e:
        st.error(f"Erro ao atualizar sinônimo: {str(e)}")
        return False

def deletar_sinonimo(id):
    if db is None:
        st.error("Erro: Firebase não inicializado")
        return False
    try:
        db.collection("sinonimos").document(id).delete()
        return True
    except Exception as e:
        st.error(f"Erro ao deletar sinônimo: {str(e)}")
        return False

def substituir_sinonimos(texto, sinonimos):
    texto_norm = normalizar_texto(texto)
    for sinon in sinonimos:
        sin = normalizar_texto(sinon["sinonimo"])
        chave = normalizar_texto(sinon["palavra_chave"])
        texto_norm = re.sub(r'\b' + re.escape(sin) + r'\b', chave, texto_norm)
    return texto_norm

# --- APP STREAMLIT --- #
st.title("🤖 Chatbot Russel com Firebase")

modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))

if modo == "Colaborador":
    st.subheader("👋 Bem-vindo! Pergunte algo para o Russel")

    dados = carregar_dados()
    sinonimos = carregar_sinonimos()

    # Exibe mensagens
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.write(f"**Você:** {message['content']}")
        else:
            st.write(f"**Russel:** {message['content']}")

    # Input para nova mensagem
    prompt = st.chat_input("Digite sua pergunta...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})

        prompt_norm = substituir_sinonimos(prompt, sinonimos)

        resposta = "❌ Desculpe, não encontrei uma resposta."
        for item in dados:
            pergunta_norm = substituir_sinonimos(item["pergunta"], sinonimos)
            score = fuzz.token_set_ratio(normalizar_texto(prompt_norm), normalizar_texto(pergunta_norm))
            if score >= 70:
                resposta = item["resposta"]
                break

        st.session_state.messages.append({"role": "assistant", "content": resposta})
        st.rerun()

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []
        st.rerun()

elif modo == "Administrador":
    st.subheader("🔒 Área Administrativa")

    if not st.session_state.admin:
        senha = st.text_input("Digite a senha:", type="password")
        if st.button("Entrar"):
            if senha == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.success("✅ Acesso liberado!")
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    else:
        st.success("🔓 Acesso como Administrador")
        if st.button("🚪 Sair"):
            st.session_state.admin = False
            st.rerun()

        st.header("📋 Gerenciar Perguntas e Respostas")

        dados = carregar_dados()
        if dados:
            df = pd.DataFrame(dados)
            df_display = df[["pergunta", "resposta"]]
            st.dataframe(df_display)

        op = st.selectbox("Escolha ação:", ["Nova Pergunta", "Editar Pergunta", "Deletar Pergunta"])

        if op == "Nova Pergunta":
            pergunta = st.text_area("Pergunta:")
            resposta = st.text_area("Resposta:")
            if st.button("💾 Salvar Nova Pergunta"):
                if pergunta.strip() and resposta.strip():
                    if salvar_pergunta(pergunta.strip(), resposta.strip()):
                        st.success("Pergunta salva!")
                        st.rerun()
                else:
                    st.error("Pergunta e resposta não podem ficar vazias.")

        elif op == "Editar Pergunta":
            if dados:
                ids = [d["id"] for d in dados]
                sel_id = st.selectbox("Selecione pergunta para editar:", ids)
                sel_item = next((x for x in dados if x["id"] == sel_id), None)
                if sel_item:
                    pergunta = st.text_area("Pergunta:", value=sel_item["pergunta"])
                    resposta = st.text_area("Resposta:", value=sel_item["resposta"])
                    if st.button("💾 Atualizar Pergunta"):
                        if pergunta.strip() and resposta.strip():
                            if atualizar_pergunta(sel_id, pergunta.strip(), resposta.strip()):
                                st.success("Pergunta atualizada!")
                                st.rerun()
                        else:
                            st.error("Pergunta e resposta não podem ficar vazias.")

        elif op == "Deletar Pergunta":
            if dados:
                ids = [d["id"] for d in dados]
                sel_id = st.selectbox("Selecione pergunta para deletar:", ids)
                if st.button("🗑️ Deletar Pergunta"):
                    if deletar_pergunta(sel_id):
                        st.success("Pergunta deletada!")
                        st.rerun()

        st.divider()

        st.header("📚 Gerenciar Sinônimos")

        sinonimos = carregar_sinonimos()
        if sinonimos:
            df_sinons = pd.DataFrame(sinonimos)
            st.dataframe(df_sinons)

        op2 = st.selectbox("Escolha ação para Sinônimos:", ["Novo Sinônimo", "Editar Sinônimo", "Deletar Sinônimo"])

        if op2 == "Novo Sinônimo":
            sin_entrada = st.text_input("Novo Sinônimo:")
            chave_entrada = st.text_input("Palavra-chave correspondente:")
            if st.button("💾 Salvar Sinônimo"):
                if sin_entrada.strip() and chave_entrada.strip():
                    if salvar_sinonimo(sin_entrada.strip(), chave_entrada.strip()):
                        st.success("Sinônimo salvo!")
                        st.rerun()
                else:
                    st.error("Preencha os dois campos.")

        elif op2 == "Editar Sinônimo":
            if sinonimos:
                ids = [s["id"] for s in sinonimos]
                sel_id = st.selectbox("Selecione sinônimo para editar:", ids)
                sel_item = next((x for x in sinonimos if x["id"] == sel_id), None)
                if sel_item:
                    sin_entrada = st.text_input("Sinônimo:", value=sel_item["sinonimo"])
                    chave_entrada = st.text_input("Palavra-chave:", value=sel_item["palavra_chave"])
                    if st.button("💾 Atualizar Sinônimo"):
                        if sin_entrada.strip() and chave_entrada.strip():
                            if atualizar_sinonimo(sel_id, sin_entrada.strip(), chave_entrada.strip()):
                                st.success("Sinônimo atualizado!")
                                st.rerun()
                        else:
                            st.error("Preencha os dois campos.")

        elif op2 == "Deletar Sinônimo":
            if sinonimos:
                ids = [s["id"] for s in sinonimos]
                sel_id = st.selectbox("Selecione sinônimo para deletar:", ids)
                if st.button("🗑️ Deletar Sinônimo"):
                    if deletar_sinonimo(sel_id):
                        st.success("Sinônimo deletado!")
                        st.rerun()
