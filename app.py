import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
import pandas as pd

# --- CONFIG FIREBASE --- #
FIREBASE_CRED_PATH = "C:\\Users\\User\\Desktop\\INT\\inteligencia\\pergunte-russel-firebase-adminsdk-fbsvc-93db4386e2.json"

if not firebase_admin._apps:
    cred = credentials.Certificate(FIREBASE_CRED_PATH)
    firebase_admin.initialize_app(cred)

db = firestore.client()

# --- CONSTANTES --- #
ADMIN_PASSWORD = "admin123"

# --- FUNÇÕES --- #

def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    return ""

def carregar_dados():
    docs = db.collection("respostas").stream()
    dados = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        dados.append(d)
    return dados

def carregar_sinonimos():
    docs = db.collection("sinonimos").stream()
    sinons = []
    for doc in docs:
        d = doc.to_dict()
        d["id"] = doc.id
        sinons.append(d)
    return sinons

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

# --- APP STREAMLIT --- #

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
    """, unsafe_allow_html=True
)

st.title("🤖 Chatbot Russel com Firebase")

modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))

if modo == "Colaborador":
    st.subheader("👋 Bem-vindo! Pergunte algo para o Russel")

    dados = carregar_dados()
    sinonimos = carregar_sinonimos()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    st.markdown('<div class="chat-container">', unsafe_allow_html=True)

    for message in st.session_state.messages:
        if message["role"] == "user":
            st.markdown(
                f'<div class="chat-message user-message">{message["content"].replace("\n", "<br>")}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-message bot-message">{message["content"].replace("\n", "<br>")}</div>',
                unsafe_allow_html=True,
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

        st.rerun()

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []

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
            st.rerun()

        st.header("📋 Gerenciar Perguntas e Respostas")

        dados = carregar_dados()
        df = pd.DataFrame(dados)
        if not df.empty:
            df_display = df[["pergunta", "resposta"]]
            st.dataframe(df_display)

        op = st.selectbox("Escolha ação:", ["Nova Pergunta", "Editar Pergunta", "Deletar Pergunta"])

        if op == "Nova Pergunta":
            pergunta = st.text_area("Pergunta:")
            resposta = st.text_area("Resposta:")
            if st.button("💾 Salvar Nova Pergunta"):
                if pergunta.strip() and resposta.strip():
                    salvar_pergunta(pergunta.strip(), resposta.strip())
                    st.success("Pergunta salva!")
                    st.rerun()
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
                        st.rerun()
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
                        st.rerun()
                    else:
                        st.error("Preencha os dois campos.")

        elif op2 == "Deletar Sinônimo":
            ids = [s["id"] for s in sinonimos]
            sel_id = st.selectbox("Selecione sinônimo para deletar:", ids)
            if st.button("🗑️ Deletar Sinônimo"):
                deletar_sinonimo(sel_id)
                st.success("Sinônimo deletado!")
                st.rerun()
        st.divider()
