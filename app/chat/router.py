from fastapi import APIRouter, Request
from app.config import settings
from langchain_core.messages import HumanMessage
from app.core.llm import model 

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/answer")
async def echo_message(request: Request):
    data = await request.json()
    message = data.get("message", "")
    response = model.invoke([HumanMessage(content=message)])
    # echo message back as Bot's answer
    return {"response": f"Bot: {response.content}"}