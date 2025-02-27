from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os
from langchain.chat_models import init_chat_model
from app.config import settings

from app.chat.router import router as chat_router
from app.core.llm import model

current_dir = os.path.dirname(os.path.abspath(__file__))
templates_path = os.path.join(current_dir, "templates")

model = init_chat_model("gpt-4o-mini", model_provider="openai", api_key=settings.OPENAI_API_KEY)



app = FastAPI()

app.include_router(chat_router)

templates = Jinja2Templates(directory=templates_path)

@app.get("/", response_class=HTMLResponse)
async def read_chat(request: Request):
    return templates.TemplateResponse("chat.html", {"request": request})
