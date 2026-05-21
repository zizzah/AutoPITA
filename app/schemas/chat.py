from pydantic import BaseModel


class ChatQuestion(BaseModel):
    question:str





class ChatResponse(BaseModel):
    answer :str
    sources :list[dict]