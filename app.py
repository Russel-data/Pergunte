import streamlit as st
import sqlite3
from fuzzywuzzy import fuzz
from unidecode import unidecode
import re

ADMIN_PASSWORD = "admin123"
DB_PATH = "chatbot.db"

# Função para conectar ao banco e criar a tabela se não existir
def conectar_banco():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS respostas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pergunta TEXT NOT NULL,
        resposta TEXT NOT NULL,
        palavras_chave TEXT NOT NULL
    )
    """)
    conn.commit()
    return conn, cursor

# Função para carregar os dados do banco de dados
def load_data():
    conn, cursor = conectar_banco()
    cursor.execute("SELECT * FROM respostas")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Função para salvar novas perguntas no banco de dados
def save_data(pergunta, resposta, palavras_chave):
    if pergunta and resposta and palavras_chave:  # Garante que os campos não estejam vazios
        conn, cursor = conectar_banco()
        cursor.execute("""
        INSERT INTO respostas (pergunta, resposta, palavras_chave)
        VALUES (?, ?, ?)
        """, (pergunta, resposta, palavras_chave))
        conn.commit()
        conn.close()
        st.success("✅ Pergunta salva com sucesso!")
        st.rerun()  # Atualiza a página para refletir os novos dados
    else:
        st.error("❌ Todos os campos são obrigatórios!")

# Função para atualizar uma pergunta existente
def update_data(id, pergunta, resposta, palavras_chave):
    if pergunta and resposta and palavras_chave:  # Garante que os campos não estejam vazios
        conn, cursor = conectar_banco()
        cursor.execute("""
        UPDATE respostas
        SET pergunta = ?, resposta = ?, palavras_chave = ?
        WHERE id = ?
        """, (pergunta, resposta, palavras_chave, id))
        conn.commit()
        conn.close()
        st.success("✅ Pergunta atualizada com sucesso!")
        st.rerun()  # Atualiza a página para refletir os novos dados
    else:
        st.error("❌ Todos os campos são obrigatórios!")

# Função para excluir uma pergunta
def delete_data(id):
    conn, cursor = conectar_banco()
    cursor.execute("DELETE FROM respostas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    st.success("✅ Pergunta excluída com sucesso!")
    st.rerun()  # Atualiza a página para refletir os novos dados

# Função para normalizar texto (remover acentos e caracteres especiais)
def normalizar_texto(texto):
    if isinstance(texto, str):
        texto = unidecode(texto.lower())
        texto = re.sub(r'[^\w\s]', '', texto)  # Remove caracteres especiais
        texto = re.sub(r'\s+', ' ', texto).strip()  # Remove espaços extras
        return texto
    return ""

# Carregar os dados diretamente do banco
dados = load_data()

# Interface do chat
st.title("Pergunte para o Russel 🤖")
st.divider()
st.subheader("👋 Olá! Eu sou o Russel, sua assistente virtual! 🚀")  
st.write(
    "Fui treinado com as informações que o Wallisson me fornece para tornar seu dia de trabalho mais fácil. "
    "Para obter respostas mais precisas, tente começar sua pergunta com **'REALIZA'**. "
    "Por exemplo: *Realiza USG da cintura pélvica?* 🏥📄\n\n"
    "Estou aqui para te ajudar! Pergunte o que precisar. 😊"
)

# Modo de uso: Colaborador ou Administrador
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
        realiza_exame = False  # Flag para verificar se o exame é realizado
        
        for row in dados:
            id, pergunta, resp, palavras_chave = row
            palavras_chave_lista = palavras_chave.split(", ")
            pontuacoes = [fuzz.token_set_ratio(palavra, normalizar_texto(prompt)) for palavra in palavras_chave_lista]
            if max(pontuacoes, default=0) >= 50:
                resposta = resp
                realiza_exame = True  # Indica que o exame é realizado
                break
        
        # Exibe a resposta
        st.session_state.messages.append({"role": "assistant", "content": resposta})
        with st.chat_message("assistant"):
            st.markdown(resposta.replace("\n", "  \n"))
        
        # Exibe o toast de acordo com a resposta
        if realiza_exame:
            st.toast("✅ Realiza o exame!", icon="✅")  # Toast verde
        else:
            st.toast("❌ Não realiza o exame.", icon="❌")  # Toast vermelho

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
        st.write("Aqui você pode **adicionar**, **editar** ou **excluir** perguntas e respostas.")

        # Formulário para adicionar ou editar perguntas
        st.subheader("Adicionar/Editar Pergunta")
        
        # Selecionar uma pergunta existente para editar
        perguntas_existentes = {row[0]: row[1] for row in dados}  # {id: pergunta}
        id_selecionado = st.selectbox(
            "Selecione uma pergunta para editar ou 'Nova Pergunta' para adicionar:",
            options=["Nova Pergunta"] + list(perguntas_existentes.keys()),
            format_func=lambda x: perguntas_existentes.get(x, "Nova Pergunta")
        )

        if id_selecionado == "Nova Pergunta":
            nova_pergunta = st.text_area("Pergunta:")
            nova_resposta = st.text_area("Resposta:")
            novas_palavras_chave = st.text_input("Palavras-chave (separadas por vírgula):")
            
            if st.button("Salvar Nova Pergunta"):
                save_data(nova_pergunta, nova_resposta, novas_palavras_chave)
        else:
            # Carregar dados da pergunta selecionada
            pergunta_selecionada = [row for row in dados if row[0] == id_selecionado][0]
            nova_pergunta = st.text_area("Pergunta:", value=pergunta_selecionada[1])
            nova_resposta = st.text_area("Resposta:", value=pergunta_selecionada[2])
            novas_palavras_chave = st.text_input("Palavras-chave (separadas por vírgula):", value=pergunta_selecionada[3])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Salvar Alterações"):
                    update_data(id_selecionado, nova_pergunta, nova_resposta, novas_palavras_chave)
            with col2:
                if st.button("Excluir Pergunta"):
                    delete_data(id_selecionado)

