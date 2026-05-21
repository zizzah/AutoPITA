from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.schemas.chat import ChatResponse, ChatQuestion
from app.models.user import User
from app.services.rag_service import answer_tax_question

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("", response_model=ChatResponse)
async def chatbox(
    payload: ChatQuestion,
    current_user: User = Depends(get_current_user)
):
    result = await answer_tax_question(payload.question)
    return result