def message_retriever(retriever, llm, prompt, mensagem):
    
    if(mensagem):
         # Usa o objeto 'retriever' para buscar documentos relevantes relacionados à pergunta.
        result_docs = retriever.invoke(mensagem)  

        # Inicializa uma string vazia para armazenar o contexto da resposta.
        contexto = ""
        for doc in result_docs:  
            # Concatena o conteúdo dos documentos recuperados para formar o contexto.
            contexto += doc.page_content + "\n"  

        # Formata o prompt final, inserindo o contexto e a pergunta do usuário.
        final_prompt = prompt.format(contexto = contexto, pergunta = mensagem)  

        # Usa o modelo de linguagem (LLM) para gerar uma resposta com base no prompt formatado.
        resposta = llm.invoke(final_prompt)  

        # Exibe a resposta da IA na interface do Streamlit.
        return resposta.content
    
    return "Não entendi o que você quis dizer."
