from langchain.chat_models import ChatOpenAI
from app.config import settings
from langchain.chat_models import init_chat_model


model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=settings.OPENAI_API_KEY)