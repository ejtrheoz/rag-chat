from fastapi import APIRouter, Request
from app.config import settings
from langchain_core.messages import HumanMessage
from app.core.llm import LLM
from fastapi import Depends
from app.users.dependencies import get_current_user
from app.users.models import Users

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

@router.post("/answer")
async def send_message(request: Request, current_user: Users = Depends(get_current_user)):
    data = await request.json()
    message = data.get("message", "")

    if LLM.detect_preference(message):
        print("Detected preference")
        preferences = LLM.get_user_preferences(str(current_user.id), "Get messages where user says what he likes and ignore such messages as 'what i like'", k=100)
        response = LLM.send_message(message, str(current_user.id), preferences)
        LLM.chat_vector_db.add_chat(str(current_user.id), message)
        print(preferences)
    else:
        response = LLM.send_message(message, str(current_user.id))

    
    answer = response["answer"]



    return {"response": f"Bot: {answer}"}