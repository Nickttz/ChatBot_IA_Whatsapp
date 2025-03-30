from dotenv import load_dotenv
import os
import whatsappflask as wf
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
import pandas as pd

# Carregar variáveis de ambiente
try:
    load_dotenv()
    google_api_key = os.getenv("GOOGLE_API_KEY")
except Exception:
    raise ValueError("Erro: GOOGLE_API_KEY não foi encontrada no .env")

# Criar modelo do Google Gemini
llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro", google_api_key=google_api_key)

# Ler arquivo CSV
try:
    df = pd.read_csv("base-dados.csv", delimiter=";")
except FileNotFoundError:
    raise FileNotFoundError("Erro: O arquivo 'base-dados.csv' não foi encontrado.")
except pd.errors.EmptyDataError:
    raise ValueError("Erro: O arquivo CSV está vazio.")
except pd.errors.ParserError:
    raise ValueError("Erro: Erro ao processar o arquivo CSV.")

# Converter para um arquivo feather
try:
    df.to_feather("base.feather")
except Exception as e:
    raise RuntimeError(f"Erro ao converter CSV para Feather: {e}")

# Colocar os dados do arquivo feather em uma lista
try:
    documents = [
        Document(page_content=f"Pergunta: {row['pergunta']}\nResposta: {row['resposta']}")
        for _, row in df.iterrows()
    ]
except KeyError as e:
    raise KeyError(f"Erro: Coluna {e} não encontrada no DataFrame. Verifique o CSV.")

#  Criar embeddings do Hugging Face
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

#  Criar o FAISS vectorstore corretamente
try:
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vectorstore = FAISS.from_documents(documents, embeddings)
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 3}) # Recupera os 3 mais relevantes
except Exception as e:
    raise RuntimeError(f"Erro ao criar vectorstore: {e}")

# Prompt para instrucionar a I.A
prompt = ChatPromptTemplate.from_messages([
        ("system", "Responda apenas com base nas informações fornecidas. " 
                   "Se a informação não estiver no contexto, diga que não sabe sobre o assunto. "
                   "Se a pergunta for diferente de um texto, como uma imagem ou figurinha, ou o texto for vazio, diga que não entendeu. "
                   "Caso haja na pergunta algo escrito bom dia, boa tarde ou boa noite, responda educadamente da mesma forma. "
                   "Se houver uma pergunta sendo a junção de várias informações do contexto, responda-a com elas de forma parafraseada. "
                   "Sempre seja educado em suas respostas"),
        ("human", "{contexto}\n\nPergunta: {pergunta}")
    ])

app = Flask(__name__)

@app.route("/bot", methods=["POST"])
def whatsapp_message():
   
    try:
        # Recuperar a mensagem do usuário
        mensagem = request.values.get("Body", "")

        if not mensagem:
            return "Erro: Nenhuma mensagem recebida", 400

        # Instanciar a resposta do chatbot
        mensagem_resp = MessagingResponse()

        # Recuperar a resposta do bot
        resposta_bot = wf.message_retriever(retriever, llm, prompt, mensagem)

        msg = mensagem_resp.message()
        msg.body(resposta_bot)

        return str(mensagem_resp)
    
    except Exception as e:
        return f"Erro interno no servidor: {e}", 500
    
if __name__ == "__main__":
    app.run(port=5000, debug=True)
