from langchain.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain.docstore.document import Document
from app.config import settings
import os

class ChatVectorDB:
    def __init__(self, index_path: str = None):
        self.embeddings = OpenAIEmbeddings(
            model="text-embedding-ada-002",
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        if index_path and os.path.exists(index_path):
            self.index = FAISS.load_local(index_path, self.embeddings, allow_dangerous_deserialization=True)
        else:
            # Create a dummy index so that FAISS.from_texts has something to work with.
            dummy = [""]
            self.index = FAISS.from_texts(dummy, self.embeddings)
            # Clear the dummy text from the index.
        self.index_path = index_path

    def add_chat(self, user_id: str, chat_text: str):
        """
        Add a chat message as a document to the vector db.
        """
        doc = Document(page_content=chat_text, metadata={"user_id": user_id})
        self.index.add_texts([doc.page_content], metadatas=[doc.metadata])
        if self.index_path:
            self.index.save_local(self.index_path)

    def query_chats(self, query: str, k: int = 5):
        """
        Query the vector db for similar chat documents.
        """
        return self.index.similarity_search(query, k=k)

    def get_all_chats(self):
        """
        Return all stored chat documents from the vector DB.
        """
        return list(self.index.docstore._dict.values())