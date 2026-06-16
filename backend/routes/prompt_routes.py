from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.db import get_db

from backend.schemas.prompt_schema import (
    PromptCreate,
    PromptResponse,
    GenerateRequest,
    GenerateResponse,
    HistoryResponse
)

from backend.services.prompt_service import (
    create_prompt,
    get_all_prompts,
    create_prompt_with_response,
    get_prompt_history
)

from backend.services.llm_service import generate_response


router = APIRouter(
    prefix="/prompts",
    tags=["Prompts"]
)


@router.post(
    "/",
    response_model=PromptResponse
)
def create_new_prompt(
    prompt: PromptCreate,
    db: Session = Depends(get_db)
):

    return create_prompt(
        db,
        prompt.prompt
    )


@router.get("/")
def read_prompts(
    db: Session = Depends(get_db)
):

    return get_all_prompts(db)


@router.post(
    "/generate",
    response_model=GenerateResponse
)
def generate_ai_response(
    request: GenerateRequest,
    db: Session = Depends(get_db)
):

    try:

        ai_response = generate_response(
            request.prompt
        )

        status = "SUCCESS"

    except Exception as e:

        ai_response = str(e)

        status = "FAILED"

    create_prompt_with_response(
        db=db,
        prompt_text=request.prompt,
        response_text=ai_response,
        model_name="gemini-2.5-flash",
        status=status
    )

    return GenerateResponse(
        prompt=request.prompt,
        response=ai_response
    )


@router.get(
    "/history",
    response_model=list[HistoryResponse]
)
def history(
    db: Session = Depends(get_db)
):

    return get_prompt_history(db)