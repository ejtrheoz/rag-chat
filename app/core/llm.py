from typing import Dict, List, Optional, Any, Union
from langchain.chat_models import ChatOpenAI
from langchain.schema import AIMessage, HumanMessage, SystemMessage, BaseMessage
from langchain.chains import RetrievalQA, ConversationChain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS
from langchain.memory import ConversationBufferMemory
from app.config import settings
from langchain_community.chat_models import ChatOpenAI
from langchain_openai import OpenAIEmbeddings
import os
import uuid


class LLM:
    model = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.7,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=settings.OPENAI_API_KEY
    )

    loaded_vectorstore = FAISS.load_local(os.path.join("app", "core", "faiss_index"), embeddings, allow_dangerous_deserialization=True)
    retriever = loaded_vectorstore.as_retriever(search_kwargs={"k": 5})
    
    # Dictionary to store conversation memories by session ID
    _memories = {}
    
    @classmethod
    def get_memory(cls, session_id: str = None) -> ConversationBufferMemory:
        """Get or create a memory instance for the specified session"""
        if not session_id:
            session_id = str(uuid.uuid4())
            
        if session_id not in cls._memories:
            cls._memories[session_id] = ConversationBufferMemory(
                memory_key="chat_history",
                return_messages=True
            )
            
        return cls._memories[session_id]
    
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
    def send_message(cls, message: str, session_id: str = None):
        # Get memory for this session
        memory = cls.get_memory(session_id)
        
        # Store the human message in memory
        memory.chat_memory.add_user_message(message)
        
        # Get response from RAG
        response = cls.query_rag(message)
        answer = response["answer"]
        
        # Store the AI response in memory
        memory.chat_memory.add_ai_message(answer)
        
        return {
            "answer": answer,
            "session_id": session_id,
            "source_documents": response["source_documents"]
        }
    
    @classmethod
    def get_conversation_history(cls, session_id: str) -> List[Dict[str, str]]:
        """Get the conversation history for a specific session"""
        if session_id not in cls._memories:
            return []
        
        memory = cls._memories[session_id]
        messages = memory.chat_memory.messages
        
        history = []
        for message in messages:
            if isinstance(message, HumanMessage):
                history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                history.append({"role": "assistant", "content": message.content})
            elif isinstance(message, SystemMessage):
                history.append({"role": "system", "content": message.content})
        
        return history