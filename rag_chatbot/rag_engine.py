import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate

def init_llm_and_embeddings(api_key: str):
    base_url = "https://keygateway1.arshnivlabs.com/v1"
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", api_key=api_key, base_url=base_url)
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key, base_url=base_url)
    return llm, embeddings

def process_and_index_pdf(pdf_path: str, api_key: str):
    _, embeddings = init_llm_and_embeddings(api_key)
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)
    
    vectorstore = Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory="./chroma_db"
    )
    return vectorstore

def get_vectorstore(api_key: str):
    _, embeddings = init_llm_and_embeddings(api_key)
    if os.path.exists("./chroma_db"):
        return Chroma(persist_directory="./chroma_db", embedding_function=embeddings)
    return None

from langchain_core.messages import HumanMessage, AIMessage

def answer_query(query: str, api_key: str, chat_history: list = None):
    llm, embeddings = init_llm_and_embeddings(api_key)
    vectorstore = get_vectorstore(api_key)
    
    formatted_history = []
    if chat_history:
        for msg in chat_history:
            if msg["role"] == "user":
                formatted_history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "ai":
                content = msg["content"].split("\n\n*(")[0]
                formatted_history.append(AIMessage(content=content))
                
    if not vectorstore:
        # No documents indexed yet, just answer directly.
        messages = formatted_history + [HumanMessage(content=query)]
        response = llm.invoke(messages)
        return f"{response.content}\n\n*(Given by AI - No documents indexed)*"

    standalone_query = query
    if formatted_history:
        from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
        condense_prompt = ChatPromptTemplate.from_messages([
            ("system", "Given the following chat history and a follow up question, rephrase the follow up question to be a standalone question that can be used to search a document. If it is already standalone, return it as is. DO NOT ANSWER IT, JUST REWRITE IT."),
            MessagesPlaceholder(variable_name="history"),
            ("human", "{question}")
        ])
        standalone_query = (condense_prompt | llm).invoke({
            "history": formatted_history[-4:], # only use last 4 messages for context to save tokens/confusion
            "question": query
        }).content
        
    # Search with relevance scores using standalone query
    results = vectorstore.similarity_search_with_relevance_scores(standalone_query, k=3)
    
    if not results:
        from langchain_core.messages import SystemMessage
        system_msg = SystemMessage(content="CRITICAL INSTRUCTION: You are an AI assistant equipped with a RAG (Retrieval-Augmented Generation) system. You CAN read, access, and search the files the user uploads. If the user asks if you can see, read, or access their file, you MUST reply 'Yes, I can access your file. What specific information would you like me to find?' Do NOT say you cannot access files.")
        messages = [system_msg] + formatted_history + [HumanMessage(content=query)]
        response = llm.invoke(messages)
        return f"{response.content}\n\n*(Given by AI - Output is not relevant to documents)*"
        
    highest_score = results[0][1]
    
    context_text = "\n\n".join([doc.page_content for doc, _ in results])
    
    system_prompt = "You are an AI assistant with access to a document the user uploaded. Here is the most relevant retrieved context from the document:\n\n{context}\n\nAnswer the user's question. If the context contains the answer, use it. Do NOT say you cannot access files or documents."
    
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="history"),
        ("human", "{question}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "context": context_text, 
        "history": formatted_history, 
        "question": query
    })
    
    # 0.3 means 30% relevance
    if highest_score < 0.3:
        return f"{response.content}\n\n*(Given by AI as LLM output is not relevant to retrieved context. Max relevance: {highest_score*100:.1f}%)*"
    else:
        return f"{response.content}\n\n*(Context relevance: {highest_score*100:.1f}%)*"
