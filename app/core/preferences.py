import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from app.core.chat_vector_db import ChatVectorDB
from transformers import pipeline
import os

nltk.download('stopwords')
nltk.download('punkt')

class Preferences:
    
    stop_words = set(stopwords.words('english'))

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
        filtered = [msg for msg in content_list if cls.filter_message(msg) != "like"]

        # Optionally remove duplicates
        unique_messages = list(dict.fromkeys(filtered))
        content_str = "\n".join(unique_messages)
        return content_str
    
    @classmethod
    def filter_message(cls, msg):
        word_tokens = word_tokenize(msg.lower())
        filtered_words = [w for w in word_tokens if not w in cls.stop_words]
        return " ".join(filtered_words)

    @classmethod
    def detect_preference(cls, sentence: str) -> bool:
        classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        candidate_labels = ["preference", "other"]

        result = classifier(sentence, candidate_labels)
        # If the top label is "preference", we detect a preference
        return result["labels"][0] == "preference"