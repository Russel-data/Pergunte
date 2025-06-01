import streamlit as st
import sqlite3
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re
import pandas as pd

st.set_page_config(page_title="Chatbot Russel 🤖", page_icon="🤖", layout="centered")

ADMIN_PASSWORD = "admin123"
DB_PATH = "chatbot.db"

# Funções de banco de dados
def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT NOT NULL,
        resposta TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn, cursor

def load_data():
    conn, cursor = conectar_banco()
    cursor.execute("SELECT * FROM respostas")
    rows = cursor.fetchall()
    conn.close()
    return rows

def save_data(pergunta, resposta):
    conn, cursor = conectar_banco()
    cursor.execute("""
    INSERT INTO respostas (pergunta, resposta)
    VALUES (?, ?)
    """, (pergunta, resposta))
    conn.commit()
    conn.close()
    st.success("✅ Pergunta salva com sucesso!")
    st.rerun()

def update_data(id, pergunta, resposta):
    conn, cursor = conectar_banco()
    cursor.execute("""
    UPDATE respostas
    SET pergunta = ?, resposta = ?
    WHERE id = ?
    """, (pergunta, resposta, id))
    conn.commit()
    conn.close()
    st.success("✅ Pergunta atualizada com sucesso!")
    st.rerun()

def delete_data(id):
    conn, cursor = conectar_banco()
    cursor.execute("DELETE FROM respostas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    st.success("✅ Pergunta excluída com sucesso!")
    st.rerun()

# Normalização
def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)
        texto = re.sub(r'\s+', ' ', texto).strip()
        return texto
    return ""

# Dados
dados = load_data()

# Interface
st.title("🤖 Pergunte para o Russel")
st.divider()

modo = st.sidebar.radio("Selecione o modo:", ("Colaborador", "Administrador"))

# ====================== COLABORADOR ========================
if modo == "Colaborador":
    st.subheader("👋 Bem-vindo! Eu sou o Russel, sua assistente virtual.")
    st.info(
        "💡 Dica: Para respostas mais precisas, comece sua pergunta com **'Realiza'**, "
        "por exemplo: *Realiza exame de abdômen?*"
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"].replace("\n", "  \n"))

    prompt = st.chat_input("Digite sua pergunta...")

    if prompt:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        resposta = "❌ Desculpe, não encontrei uma resposta."
        realiza = False

        for row in dados:
            id, pergunta, resp = row
            similaridade = fuzz.token_set_ratio(normalizar_texto(prompt), normalizar_texto(pergunta))
            if similaridade >= 70:
                resposta = resp
                realiza = True
                break

        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta.replace("\n", "  \n"))

        if realiza:
            st.toast("✅ Realiza o exame!", icon="✅")
        else:
            st.toast("❌ Não realiza o exame.", icon="❌")

    if st.button("🗑️ Limpar conversa"):
        st.session_state.messages = []

# ====================== ADMINISTRADOR ========================
elif modo == "Administrador":
    st.subheader("🔒 Área Administrativa")
    senha = st.text_input("Digite a senha:", type="password")

    if st.button("Entrar"):
        if senha == ADMIN_PASSWORD:
            st.session_state.admin = True
            st.success("✅ Acesso liberado!")
        else:
            st.error("❌ Senha incorreta!")

    if st.session_state.get("admin", False):
        st.divider()
        st.header("📋 Gerenciamento de Perguntas")

        perguntas_dict = {row[0]: row[1] for row in dados}
        id_selecionado = st.selectbox(
            "Selecione uma pergunta ou 'Nova Pergunta':",
            options=["Nova Pergunta"] + list(perguntas_dict.keys()),
            format_func=lambda x: perguntas_dict.get(x, "Nova Pergunta")
        )

        if id_selecionado == "Nova Pergunta":
            pergunta = st.text_area("Pergunta:")
            resposta = st.text_area("Resposta:")

            if st.button("💾 Salvar"):
                save_data(pergunta, resposta)
        else:
            row = [r for r in dados if r[0] == id_selecionado][0]
            pergunta = st.text_area("Pergunta:", value=row[1])
            resposta = st.text_area("Resposta:", value=row[2])

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Atualizar"):
                    update_data(id_selecionado, pergunta, resposta)
            with col2:
                if st.button("🗑️ Excluir"):
                    if st.confirm("Tem certeza que deseja excluir?"):
                        delete_data(id_selecionado)

        st.divider()
        st.subheader("📑 Banco de Dados Atual")
        df = pd.DataFrame(dados, columns=["ID", "Pergunta", "Resposta"])
        st.dataframe(df, use_container_width=True)

        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Exportar para CSV",
            csv,
            "banco_perguntas.csv",
            "text/csv",
            key='download-csv'
        )
