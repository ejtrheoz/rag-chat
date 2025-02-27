from fastapi import APIRouter, Request
from app.config import settings
from langchain_core.messages import HumanMessage
from app.core.llm import LLM


router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/answer")
async def echo_message(request: Request):
    data = await request.json()
    message = data.get("message", "")
    response = LLM.send_message(message)
    answer = response["answer"]
    
    print(f"{LLM._memories}")

    return {"response": f"Bot: {answer}"}