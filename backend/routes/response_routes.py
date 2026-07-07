from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.database.db import get_db
from backend.schemas.response_schema import ResponseRead
from backend.services.response_service import (
    get_response_by_id,
    list_responses
)


router = APIRouter(
    prefix="/responses",
    tags=["Responses"],
    dependencies=[Depends(get_current_user)]
)


@router.get(
    "/",
    response_model=list[ResponseRead]
)
def read_responses(
    prompt_id: int | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db)
):
    return list_responses(
        db=db,
        prompt_id=prompt_id,
        start_date=start_date,
        end_date=end_date
    )


@router.get(
    "/{response_id}",
    response_model=ResponseRead
)
def read_response(
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

    return response
