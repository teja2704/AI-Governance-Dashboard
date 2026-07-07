from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database.db import get_db
from backend.database.models import User
from backend.schemas.evaluation_schema import (
    EvaluationRead,
    HumanEvaluationCreate
)
from backend.services.evaluation_service import (
    AUTOMATED_EVALUATION_TYPE,
    HUMAN_EVALUATION_TYPE,
    create_human_evaluation,
    list_evaluations
)
from backend.services.response_service import get_response_by_id


router = APIRouter(
    prefix="/evaluations",
    tags=["Evaluations"],
    dependencies=[Depends(get_current_user)]
)


@router.post(
    "/",
    response_model=EvaluationRead
)
def create_evaluation(
    request: HumanEvaluationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    response = get_response_by_id(
        db,
        request.response_id
    )

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found."
        )

    return create_human_evaluation(
        db=db,
        response_id=request.response_id,
        evaluator_id=current_user.id,
        score=request.score,
        notes=request.notes
    )


@router.get(
    "/",
    response_model=list[EvaluationRead]
)
def read_evaluations(
    response_id: int | None = Query(default=None),
    evaluation_type: str | None = Query(
        default=None,
        pattern=f"^({AUTOMATED_EVALUATION_TYPE}|{HUMAN_EVALUATION_TYPE})$"
    ),
    db: Session = Depends(get_db)
):
    return list_evaluations(
        db=db,
        response_id=response_id,
        evaluation_type=evaluation_type
    )


@router.get(
    "/{response_id}",
    response_model=list[EvaluationRead]
)
def read_response_evaluations(
    response_id: int,
    db: Session = Depends(get_db)
):
    response = get_response_by_id(
        db,
        response_id
    )

    if response is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Response not found."
        )

    return list_evaluations(
        db=db,
        response_id=response_id
    )
