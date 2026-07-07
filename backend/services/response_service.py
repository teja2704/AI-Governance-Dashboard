from datetime import date, datetime, time

from sqlalchemy.orm import Session

from backend.database.models import Response
from backend.services.evaluation_service import create_automated_evaluation


def create_response(
    db: Session,
    prompt_id: int,
    response_text: str | None,
    model_name: str,
    status: str
) -> Response:
    response = Response(
        prompt_id=prompt_id,
        response=response_text,
        model=model_name,
        status=status,
        response_length=len(response_text)
        if response_text
        else 0
    )

    db.add(response)
    db.flush()

    create_automated_evaluation(
        db,
        response
    )

    return response


def get_response_by_id(
    db: Session,
    response_id: int
) -> Response | None:
    return (
        db.query(Response)
        .filter(Response.id == response_id)
        .first()
    )


def list_responses(
    db: Session,
    prompt_id: int | None = None,
    start_date: date | None = None,
    end_date: date | None = None
) -> list[Response]:
    query = db.query(Response)

    if prompt_id is not None:
        query = query.filter(Response.prompt_id == prompt_id)

    if start_date is not None:
        query = query.filter(
            Response.created_at >= datetime.combine(
                start_date,
                time.min
            )
        )

    if end_date is not None:
        query = query.filter(
            Response.created_at <= datetime.combine(
                end_date,
                time.max
            )
        )

    return (
        query
        .order_by(Response.created_at.desc())
        .all()
    )
