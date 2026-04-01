from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.services.assistant_chat import chat_with_report

router = APIRouter()


class AssistantChatRequest(BaseModel):
    report: dict  # полный JSON отчёта (как AnalyzeResponse)
    question: str


class AssistantChatResponse(BaseModel):
    answer: str


@router.post("/chat", response_model=AssistantChatResponse)
async def assistant_chat(req: AssistantChatRequest):
    """
    Вопрос по отчёту. Ответ строится только по данным отчёта (правдиво).
    Нужен один из ключей: ANTHROPIC_API_KEY, OPENAI_API_KEY, XAI_API_KEY.
    """
    if not req.question.strip():
        raise HTTPException(status_code=422, detail="question не может быть пустым")
    try:
        answer = await chat_with_report(req.report, req.question.strip())
        return AssistantChatResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
