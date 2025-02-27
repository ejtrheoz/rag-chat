# from config import settings
import getpass
import os
from langchain_core.messages import HumanMessage
from langchain.chat_models import init_chat_model

api_key  = "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"

model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=api_key)
response = model.invoke([HumanMessage(content="Hi! I'm Bob")])

print(response.content)
