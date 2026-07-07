from datetime import datetime

from pydantic import BaseModel


class ResponseRead(BaseModel):
    id: int
    prompt_id: int
    response: str | None = None
    model: str | None = None
    status: str | None = None
    response_length: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
