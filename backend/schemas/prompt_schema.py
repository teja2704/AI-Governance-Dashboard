from pydantic import BaseModel


class PromptCreate(BaseModel):
    prompt: str


class PromptResponse(BaseModel):
    id: int
    prompt: str

    class Config:
        from_attributes = True


# NEW

class GenerateRequest(BaseModel):
    prompt: str


class GenerateResponse(BaseModel):
    prompt: str
    response: str
    
from datetime import datetime

class HistoryResponse(BaseModel):

    id: int
    prompt: str
    response: str | None = None
    model: str | None = None
    status: str | None = None
    timestamp: datetime

    class Config:
        from_attributes = True