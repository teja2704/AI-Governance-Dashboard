from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class HumanEvaluationCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    response_id: int
    score: int = Field(ge=1, le=5)
    notes: str | None = None


class EvaluationRead(BaseModel):
    id: int
    response_id: int
    evaluation_type: str
    evaluator_id: int | None = None
    score: int | None = None
    flags: list[str] | None = None
    notes: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True
