import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
import pandas as pd

# ================================
# 🔥 CONFIGURAÇÃO DO FIREBASE 🔥
# ================================
if not firebase_admin._apps:
    cred_info = {
        "type": st.secrets["FIREBASE_TYPE"],
        "project_id": st.secrets["FIREBASE_PROJECT_ID"],
        "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
        "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
        "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
        "client_id": st.secrets["FIREBASE_CLIENT_ID"],
        "auth_uri": st.secrets["FIREBASE_AUTH_URI"],
        "token_uri": st.secrets["FIREBASE_TOKEN_URI"],
        "auth_provider_x509_cert_url": st.secrets["FIREBASE_AUTH_PROVIDER_X509_CERT_URL"],
        "client_x509_cert_url": st.secrets["FIREBASE_CLIENT_X509_CERT_URL"]
    }
    cred = credentials.Certificate(cred_info)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# ================================
# 🚩 CONSTANTES
# ================================
ADMIN_PASSWORD = "admin123"

# ================================
# 🔧 FUNÇÕES AUXILIARES
# ================================
def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    return ""

def carregar_dados():
    docs = db.collection("respostas").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

def carregar_sinonimos():
    docs = db.collection("sinonimos").stream()
    return [{"id": doc.id, **doc.to_dict()} for doc in docs]

def salvar_pergunta(pergunta, resposta):
    db.collection("respostas").document().set({
        "pergunta": pergunta,
        "resposta": resposta
    })

def atualizar_pergunta(id, pergunta, resposta):
    db.collection("respostas").document(id).update({
        "pergunta": pergunta,
        "resposta": resposta
    })

def deletar_pergunta(id):
    db.collection("respostas").document(id).delete()

def salvar_sinonimo(sinonimo, palavra_chave):
    db.collection("sinonimos").document().set({
        "sinonimo": sinonimo,
        "palavra_chave": palavra_chave
    })

def atualizar_sinonimo(id, sinonimo, palavra_chave):
    db.collection("sinonimos").document(id).update({
        "sinonimo": sinonimo,
        "palavra_chave": palavra_chave
    })

def deletar_sinonimo(id):
    db.collection("sinonimos").document(id).delete()

def substituir_sinonimos(texto, sinonimos):
    texto_norm = normalizar_texto(texto)
    for sinon in sinonimos:
        sin = normalizar_texto(sinon["sinonimo"])
        chave = normalizar_texto(sinon["palavra_chave"])
        texto_norm = re.sub(r'\b' + re.escape(sin) + r'\b', chave, texto_norm)
    return texto_norm

# ================================
# 🎨 CONFIGURAÇÃO DA INTERFACE
# ================================
st.set_page_config(page_title="Chatbot Russel 🤖", page_icon="🤖", layout="centered")

st.markdown(
    """
    <style>
    .chat-message {
        max-width: 70%;
        padding: 10px 15px;
        margin: 5px 10px;
        border-radius: 20px;
        font-size: 16px;
        line-height: 1.4;
        white-space: pre-wrap;
        word-wrap: break-word;
        box-shadow: 0 1px 1px rgb(0 0 0 / 0.1);
    }
    .user-message {
        background-color: #DCF8C6;
        margin-left: auto;
        border-bottom-right-radius: 0;
    }
    .bot-message {
        background-color: #FFFFFF;
        margin-right: auto;
        border-bottom-left-radius: 0;
    }
    .chat-container {
        display: flex;
        flex-direction: column;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ================================
# 🚀 APP PRINCIPAL
# ================================
st.title("🤖 Chatbot Russel com Firebase")

modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))

# ====================================
# 👨‍💻 MODO COLABORADOR
# ====================================
if modo == "Colaborador":
    st.subheader("👋 Bem-vindo! Pergunte algo para o Russel")

    dados = carregar_dados()
    sinonimos = carregar_sinonimos()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        css_class = "user-message" if message["role"] == "user" else "bot-message"
        st.markdown(
            f'<div class="chat-message {css_class}">{message["content"].replace("\n", "<br>")}</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

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
        st.experimental_rerun()

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []

# ====================================
# 🔒 MODO ADMINISTRADOR
# ====================================
elif modo == "Administrador":
    st.subheader("🔒 Área Administrativa")

    if "admin" not in st.session_state:
        st.session_state.admin = False

    if not st.session_state.admin:
        senha = st.text_input("Digite a senha:", type="password")
        if st.button("Entrar"):
            if senha == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.success("✅ Acesso liberado!")
            else:
                st.error("❌ Senha incorreta!")
    else:
        st.success("🔓 Acesso como Administrador")
        if st.button("🚪 Sair"):
            st.session_state.admin = False
            st.experimental_rerun()

        st.header("📋 Gerenciar Perguntas e Respostas")

        dados = carregar_dados()
        df = pd.DataFrame(dados)
        if not df.empty:
            st.dataframe(df[["pergunta", "resposta"]])

        op = st.selectbox("Escolha ação:", ["Nova Pergunta", "Editar Pergunta", "Deletar Pergunta"])

        if op == "Nova Pergunta":
            pergunta = st.text_area("Pergunta:")
            resposta = st.text_area("Resposta:")
            if st.button("💾 Salvar Nova Pergunta"):
                if pergunta.strip() and resposta.strip():
                    salvar_pergunta(pergunta.strip(), resposta.strip())
                    st.success("Pergunta salva!")
                    st.experimental_rerun()
                else:
                    st.error("Pergunta e resposta não podem ficar vazias.")

        elif op == "Editar Pergunta":
            ids = [d["id"] for d in dados]
            sel_id = st.selectbox("Selecione pergunta para editar:", ids)
            sel_item = next((x for x in dados if x["id"] == sel_id), None)
            if sel_item:
                pergunta = st.text_area("Pergunta:", value=sel_item["pergunta"])
                resposta = st.text_area("Resposta:", value=sel_item["resposta"])
                if st.button("💾 Atualizar Pergunta"):
                    if pergunta.strip() and resposta.strip():
                        atualizar_pergunta(sel_id, pergunta.strip(), resposta.strip())
                        st.success("Pergunta atualizada!")
                        st.experimental_rerun()
                    else:
                        st.error("Pergunta e resposta não podem ficar vazias.")

        elif op == "Deletar Pergunta":
            ids = [d["id"] for d in dados]
            sel_id = st.selectbox("Selecione pergunta para deletar:", ids)
            if st.button("🗑️ Deletar Pergunta"):
                deletar_pergunta(sel_id)
                st.success("Pergunta deletada!")
                st.experimental_rerun()

        st.divider()
        st.header("📚 Gerenciar Sinônimos")

        sinonimos = carregar_sinonimos()
        df_sinons = pd.DataFrame(sinonimos)
        if not df_sinons.empty:
            st.dataframe(df_sinons)

        op2 = st.selectbox("Escolha ação para Sinônimos:", ["Novo Sinônimo", "Editar Sinônimo", "Deletar Sinônimo"])

        if op2 == "Novo Sinônimo":
            sin_entrada = st.text_input("Novo Sinônimo:")
            chave_entrada = st.text_input("Palavra-chave correspondente:")
            if st.button("💾 Salvar Sinônimo"):
                if sin_entrada.strip() and chave_entrada.strip():
                    salvar_sinonimo(sin_entrada.strip(), chave_entrada.strip())
                    st.success("Sinônimo salvo!")
                    st.experimental_rerun()
                else:
                    st.error("Preencha os dois campos.")

        elif op2 == "Editar Sinônimo":
            ids = [s["id"] for s in sinonimos]
            sel_id = st.selectbox("Selecione sinônimo para editar:", ids)
            sel_item = next((x for x in sinonimos if x["id"] == sel_id), None)
            if sel_item:
                sin_entrada = st.text_input("Sinônimo:", value=sel_item["sinonimo"])
                chave_entrada = st.text_input("Palavra-chave:", value=sel_item["palavra_chave"])
                if st.button("💾 Atualizar Sinônimo"):
                    if sin_entrada.strip() and chave_entrada.strip():
                        atualizar_sinonimo(sel_id, sin_entrada.strip(), chave_entrada.strip())
                        st.success("Sinônimo atualizado!")
                        st.experimental_rerun()
                    else:
                        st.error("Preencha os dois campos.")

        elif op2 == "Deletar Sinônimo":
            ids = [s["id"] for s in sinonimos]
            sel_id = st.selectbox("Selecione sinônimo para deletar:", ids)
            if st.button("🗑️ Deletar Sinônimo"):
                deletar_sinonimo(sel_id)
                st.success("Sinônimo deletado!")
                st.experimental_rerun()

        st.divider()
