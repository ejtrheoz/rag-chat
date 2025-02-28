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
from app.core.chat_vector_db import ChatVectorDB
import nltk
from nltk.tokenize import word_tokenize
from transformers import pipeline





class LLM:
    model = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.1,
        openai_api_key=settings.OPENAI_API_KEY
    )
    
    embeddings = OpenAIEmbeddings(
        model="text-embedding-ada-002",
        openai_api_key=settings.OPENAI_API_KEY
    )

    loaded_vectorstore = FAISS.load_local(os.path.join("app", "core", "faiss_index"), embeddings, allow_dangerous_deserialization=True)
    retriever = loaded_vectorstore.as_retriever(search_kwargs={"k": 5})

    chat_vector_db = ChatVectorDB(index_path=os.path.join("app", "core", "chat_vector_index"))

    
    # Dictionary to store conversation memories by session ID
    _memories = {}
    
    @classmethod
    def get_memory(cls, user_id: str) -> ConversationBufferMemory:
        """Get or create a memory instance for the specified user"""
        if user_id not in cls._memories:
            cls._memories[user_id] = ConversationBufferMemory(
                memory_key="history",  # changed from "chat_history" to "history"
                return_messages=True
            )
            
        return cls._memories[user_id]
    
    @classmethod
    def generate_prompt(cls, preferences_context: Optional[str] = None):
        template = """Answer the question based only on the following context 
        and without bullet points containing only short answers using your knowledge from database:
        {context}

        Question: {question}
        Answer:
        """

        if preferences_context:
            template += "Preferences: " + preferences_context

        prompt = PromptTemplate(
            template=template,
            input_variables=["context", "question"]
        )

        return prompt
    
    @classmethod
    def query_rag(cls, question: str, preferences_context: Optional[str] = None):
        rag_chain = RetrievalQA.from_chain_type(
            llm=cls.model,
            chain_type="stuff",
            retriever=cls.retriever,
            return_source_documents=True,
            chain_type_kwargs={"prompt": cls.generate_prompt(preferences_context)}
        )

        result = rag_chain({"query": question})
        return {
            "answer": result["result"],
            "source_documents": [(doc.page_content, doc.metadata) for doc in result["source_documents"]]
        }

    @classmethod
    def send_message(cls, message: str, user_id: str, preferences_context: Optional[str] = None):
        # Get memory for this user
        memory = cls.get_memory(user_id)
        
        # Store the human message in memory
        memory.chat_memory.add_user_message(message)
        
        # Get response from RAG
        response = cls.query_rag(message, preferences_context)
        answer = response["answer"]
        
        # Store the AI response in memory
        memory.chat_memory.add_ai_message(answer)

        combined = f"User: {message}\nAssistant: {answer}"
        # print(cls.chat_vector_db.get_all_chats())

        if any(keyword in message.lower() for keyword in ["like", "prefer"]):
            cls.chat_vector_db.add_chat(user_id, message)

        
        return {
            "answer": answer,
            "user_id": user_id,
            "source_documents": response["source_documents"]
        }
    
    @classmethod
    def get_user_preferences(cls, user_id: str, query: str, k: int = 5):
        """
        Query the chat vector database for documents related to the user's preferences,
        filter out specific unwanted messages, and return only unique page content.
        """
        chat_vector_db = ChatVectorDB(index_path=os.path.join("app", "core", "chat_vector_index"))
        results = chat_vector_db.query_chats(query, k=k)
        user_results = [doc for doc in results if doc.metadata.get("user_id") == user_id]
        # Extract just the page_content
        content_list = [doc.page_content for doc in user_results]
        
        # Filter out unwanted messages, e.g. messages that exactly equal "what i like"
        filtered = [msg for msg in content_list if msg.strip().lower() != "what i like"]
        
        # Optionally remove duplicates
        unique_messages = list(dict.fromkeys(filtered))
        content_str = "\n".join(unique_messages)
        return content_str
    
    @classmethod
    def detect_preference(cls, sentence: str) -> bool:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        candidate_labels = ["preference", "other"]

        result = classifier(sentence, candidate_labels)
        # If the top label is "preference", we detect a preference
        return result["labels"][0] == "preference"

    