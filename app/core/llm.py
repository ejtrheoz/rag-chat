from typing import Dict, List, Optional, Any, Union
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from app.config import settings
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
from app.config import settings
import os


class LLM:
    model = ChatOpenAI(
        model_name="gpt-4o-mini",  # Use model_name parameter
        temperature=0.7,  # You can also specify temperature
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=settings.OPENAI_API_KEY
    )

    loaded_vectorstore = FAISS.load_local(os.path.join("app", "core", "faiss_index"), embeddings, allow_dangerous_deserialization=True)
    retriever = loaded_vectorstore.as_retriever(search_kwargs={"k": 5})
    
    @classmethod
    def generate_prompt(cls):
        template = """Answer the question based only on the following context and without bullet points containing only short answers:
        {context}

        Question: {question}
        Answer:"""

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        return prompt
    

    @classmethod
    def query_rag(cls, question: str):
        rag_chain = RetrievalQA.from_chain_type(
            llm=cls.model,
            chain_type="stuff",
            retriever=cls.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": cls.generate_prompt()}
        )

        result = rag_chain({"query": question})
        return {
            "answer": result["result"],
            "source_documents": [(doc.page_content, doc.metadata) for doc in result["source_documents"]]
        }

    @classmethod
    def send_rag_message(cls, message: str):
        response = cls.query_rag(message)
        return response["answer"]


    @classmethod
    def send_message(cls, message: str):
        response = cls.model.invoke([HumanMessage(content=message)])
        return response.content
    
    