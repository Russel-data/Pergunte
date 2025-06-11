import streamlit as st
import sqlite3
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
import pandas as pd

# --- CONFIG SQLITE --- #
DB_PATH = "chatbot.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS respostas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pergunta TEXT NOT NULL,
            resposta TEXT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sinonimos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sinonimo TEXT NOT NULL,
            palavra_chave TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- CONSTANTES --- #
ADMIN_PASSWORD = "admin123"

# --- FUNÇÕES AUXILIARES --- #

def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    return ""

def carregar_dados():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, pergunta, resposta FROM respostas")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "pergunta": r[1], "resposta": r[2]} for r in rows]

def carregar_sinonimos():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, sinonimo, palavra_chave FROM sinonimos")
    rows = cur.fetchall()
    conn.close()
    return [{"id": r[0], "sinonimo": r[1], "palavra_chave": r[2]} for r in rows]

def salvar_pergunta(pergunta, resposta):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO respostas (pergunta, resposta) VALUES (?, ?)", (pergunta, resposta))
    conn.commit()
    conn.close()

def atualizar_pergunta(id, pergunta, resposta):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE respostas SET pergunta = ?, resposta = ? WHERE id = ?", (pergunta, resposta, id))
    conn.commit()
    conn.close()

def deletar_pergunta(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM respostas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def salvar_sinonimo(sinonimo, palavra_chave):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO sinonimos (sinonimo, palavra_chave) VALUES (?, ?)", (sinonimo, palavra_chave))
    conn.commit()
    conn.close()

def atualizar_sinonimo(id, sinonimo, palavra_chave):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("UPDATE sinonimos SET sinonimo = ?, palavra_chave = ? WHERE id = ?", (sinonimo, palavra_chave, id))
    conn.commit()
    conn.close()

def deletar_sinonimo(id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("DELETE FROM sinonimos WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def substituir_sinonimos(texto, sinonimos):
    texto_norm = normalizar_texto(texto)
    for sinon in sinonimos:
        sin = normalizar_texto(sinon["sinonimo"])
        chave = normalizar_texto(sinon["palavra_chave"])
        texto_norm = re.sub(r'\b' + re.escape(sin) + r'\b', chave, texto_norm)
    return texto_norm

# --- INTERFACE STREAMLIT --- #

st.set_page_config(page_title="Chatbot Russel", page_icon="🤖", layout="wide")

# CSS Moderno
st.markdown("""
<style>
/* Geral */
body, .block-container {
    background-color: #f0f2f6;
    color: #262730;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* Título */
h1 {
    color: #1f2937;
    font-weight: 700;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
    color: white;
}
[data-testid="stSidebar"] .css-1d391kg {
    color: white;
}
[data-testid="stSidebar"] .css-1d391kg div, 
[data-testid="stSidebar"] .css-1d391kg label {
    color: white;
}

/* Botões */
.stButton > button {
    background-color: #2563eb;
    color: white;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    transition: background-color 0.3s ease;
    border: none;
}
.stButton > button:hover {
    background-color: #1e40af;
    color: #e0e7ff;
}

/* Inputs */
input[type="text"], textarea, .stTextInput>div>div>input, .stTextArea>div>div>textarea {
    border-radius: 8px !important;
    border: 1.5px solid #d1d5db !important;
    padding: 8px !important;
    font-size: 16px !important;
    transition: border-color 0.3s ease;
}
input[type="text"]:focus, textarea:focus, .stTextInput>div>div>input:focus, .stTextArea>div>div>textarea:focus {
    border-color: #2563eb !important;
    outline: none !important;
}

/* Chat bubbles */
.chat-container {
    display: flex;
    flex-direction: column;
    max-width: 700px;
    margin: 0 auto 20px auto;
    padding: 10px;
    background-color: #ffffff;
    border-radius: 12px;
    box-shadow: 0 8px 24px rgb(0 0 0 / 0.1);
    min-height: 400px;
    overflow-y: auto;
}
.chat-message {
    max-width: 75%;
    padding: 12px 18px;
    margin: 6px 12px;
    border-radius: 20px;
    font-size: 17px;
    line-height: 1.5;
    white-space: pre-wrap;
    word-wrap: break-word;
    box-shadow: 0 3px 8px rgb(0 0 0 / 0.12);
    transition: background-color 0.3s ease;
}
.user-message {
    background: linear-gradient(135deg, #81e6d9, #38b2ac);
    color: white;
    align-self: flex-end;
    border-bottom-right-radius: 4px;
}
.bot-message {
    background: linear-gradient(135deg, #e0e7ff, #a5b4fc);
    color: #1e293b;
    align-self: flex-start;
    border-bottom-left-radius: 4px;
}

/* Headers e divisores */
h2, h3 {
    color: #334155;
}
hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 15px 0;
}

/* Dataframes */
.stDataFrame {
    border-radius: 12px !important;
    overflow: hidden;
    box-shadow: 0 4px 14px rgb(0 0 0 / 0.1);
}

/* Mensagem de erro e sucesso */
.stAlert {
    border-radius: 10px !important;
}

/* Scroll chat */
.chat-container::-webkit-scrollbar {
    width: 8px;
}
.chat-container::-webkit-scrollbar-thumb {
    background-color: #2563eb;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🤖 Russel - Chatbot CDI g")

# Sidebar para navegação
modo = st.sidebar.selectbox("Modo de Acesso", ("Colaborador", "Administrador"))

if modo == "Colaborador":
    st.subheader("👋 Olá! Em que posso ajudar?")

    dados = carregar_dados()
    sinonimos = carregar_sinonimos()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Container chat com scroll
    chat_container = st.container()
    with chat_container:
        st.markdown('<div class="chat-container">', unsafe_allow_html=True)
        for message in st.session_state.messages:
            css_class = "user-message" if message["role"] == "user" else "bot-message"
            st.markdown(f'<div class="chat-message {css_class}">{message["content"].replace("\n", "<br>")}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    prompt = st.chat_input("Digite sua pergunta aqui...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        prompt_norm = substituir_sinonimos(prompt, sinonimos)

        resposta = "❌ Desculpe, no momento não posso ajudar, pergunte para o Wallisson quem sabe na próxima eu possa."
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

    if "admin" not in st.session_state:
        st.session_state.admin = False

    if not st.session_state.admin:
        senha = st.text_input("Digite a senha:", type="password", placeholder="Senha do administrador")
        if st.button("Entrar"):
            if senha == ADMIN_PASSWORD:
                st.session_state.admin = True
                st.success("✅ Acesso liberado!")
                st.rerun()
            else:
                st.error("❌ Senha incorreta!")
    else:
        st.success("🔐 Você está na área administrativa!")
        st.header("📋 Gerenciar Perguntas e Respostas")

        dados = carregar_dados()
        df = pd.DataFrame(dados)
        if not df.empty:
            st.dataframe(df[["pergunta", "resposta"]], use_container_width=True)

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
                    st.error("Preencha pergunta e resposta.")

        elif op == "Editar Pergunta":
            if dados:
                escolha = st.selectbox("Selecione pergunta para editar:", [f"{d['id']} - {d['pergunta']}" for d in dados])
                id_edit = int(escolha.split(" - ")[0])
                item = next((x for x in dados if x["id"] == id_edit), None)
                if item:
                    pergunta_edit = st.text_area("Pergunta:", value=item["pergunta"])
                    resposta_edit = st.text_area("Resposta:", value=item["resposta"])
                    if st.button("💾 Atualizar Pergunta"):
                        if pergunta_edit.strip() and resposta_edit.strip():
                            atualizar_pergunta(id_edit, pergunta_edit.strip(), resposta_edit.strip())
                            st.success("Pergunta atualizada!")
                            st.rerun()
                        else:
                            st.error("Preencha pergunta e resposta.")
            else:
                st.info("Nenhuma pergunta cadastrada.")

        elif op == "Deletar Pergunta":
            if dados:
                escolha = st.selectbox("Selecione pergunta para deletar:", [f"{d['id']} - {d['pergunta']}" for d in dados])
                id_del = int(escolha.split(" - ")[0])
                if st.button("🗑️ Confirmar exclusão"):
                    deletar_pergunta(id_del)
                    st.success("Pergunta deletada!")
                    st.rerun()
            else:
                st.info("Nenhuma pergunta cadastrada.")

        st.markdown("---")
        st.header("📚 Gerenciar Sinônimos")

        sinonimos = carregar_sinonimos()
        df_sinon = pd.DataFrame(sinonimos)
        if not df_sinon.empty:
            st.dataframe(df_sinon[["sinonimo", "palavra_chave"]], use_container_width=True)

        op_sin = st.selectbox("Ação Sinônimos:", ["Novo Sinônimo", "Editar Sinônimo", "Deletar Sinônimo"])

        if op_sin == "Novo Sinônimo":
            sin = st.text_input("Sinônimo:")
            chave = st.text_input("Palavra-Chave para substituir:")
            if st.button("💾 Salvar Sinônimo"):
                if sin.strip() and chave.strip():
                    salvar_sinonimo(sin.strip(), chave.strip())
                    st.success("Sinônimo salvo!")
                    st.rerun()
                else:
                    st.error("Preencha sinônimo e palavra-chave.")

        elif op_sin == "Editar Sinônimo":
            if sinonimos:
                escolha_sin = st.selectbox("Selecione sinônimo para editar:", [f"{s['id']} - {s['sinonimo']}" for s in sinonimos])
                id_sin = int(escolha_sin.split(" - ")[0])
                item_sin = next((x for x in sinonimos if x["id"] == id_sin), None)
                if item_sin:
                    sin_edit = st.text_input("Sinônimo:", value=item_sin["sinonimo"])
                    chave_edit = st.text_input("Palavra-Chave:", value=item_sin["palavra_chave"])
                    if st.button("💾 Atualizar Sinônimo"):
                        if sin_edit.strip() and chave_edit.strip():
                            atualizar_sinonimo(id_sin, sin_edit.strip(), chave_edit.strip())
                            st.success("Sinônimo atualizado!")
                            st.rerun()
                        else:
                            st.error("Preencha sinônimo e palavra-chave.")
            else:
                st.info("Nenhum sinônimo cadastrado.")

        elif op_sin == "Deletar Sinônimo":
            if sinonimos:
                escolha_sin = st.selectbox("Selecione sinônimo para deletar:", [f"{s['id']} - {s['sinonimo']}" for s in sinonimos])
                id_sin_del = int(escolha_sin.split(" - ")[0])
                if st.button("🗑️ Confirmar exclusão Sinônimo"):
                    deletar_sinonimo(id_sin_del)
                    st.success("Sinônimo deletado!")
                    st.rerun()
            else:
                st.info("Nenhum sinônimo cadastrado.")

        if st.button("🔒 Sair da Administração"):
            st.session_state.admin = False
            st.rerun()
