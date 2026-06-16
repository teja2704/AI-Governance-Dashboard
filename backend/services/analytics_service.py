from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.database.models import Prompt


def get_analytics(db: Session):

    total_requests = db.query(
        Prompt
    ).count()

    ai_requests = (
        db.query(Prompt)
        .filter(Prompt.response.isnot(None))
        .count()
    )

    manual_requests = (
        total_requests - ai_requests
    )

    success_requests = (
        db.query(Prompt)
        .filter(Prompt.status == "SUCCESS")
        .count()
    )

    failed_requests = (
        db.query(Prompt)
        .filter(Prompt.status == "FAILED")
        .count()
    )

    average_response_length = (
        db.query(
            func.avg(
                Prompt.response_length
            )
        ).scalar()
    )

    average_prompt_length = (
        db.query(
            func.avg(
                func.length(
                    Prompt.prompt
                )
            )
        ).scalar()
    )

    success_rate = (
        round(
            (success_requests / total_requests) * 100,
            2
        )
        if total_requests
        else 0
    )

    failure_rate = (
        round(
            (failed_requests / total_requests) * 100,
            2
        )
        if total_requests
        else 0
    )

    return {
        "total_requests": total_requests,
        "ai_requests": ai_requests,
        "manual_requests": manual_requests,
        "success_requests": success_requests,
        "failed_requests": failed_requests,
        "success_rate": success_rate,
        "failure_rate": failure_rate,
        "average_prompt_length": (
            round(average_prompt_length, 2)
            if average_prompt_length
            else 0
        ),
        "average_response_length": (
            round(average_response_length, 2)
            if average_response_length
            else 0
        )
    }


def get_model_usage(db: Session):

    results = (
        db.query(
            Prompt.model,
            func.count(Prompt.id)
        )
        .group_by(Prompt.model)
        .all()
    )

    return [
        {
            "model": model,
            "count": count
        }
        for model, count in results
    ]


def get_dashboard_kpis(db: Session):

    latest_prompt = (
        db.query(Prompt)
        .order_by(Prompt.id.desc())
        .first()
    )

    # FIXED: Ignore NULL response lengths
    longest_response = (
        db.query(Prompt)
        .filter(
            Prompt.response_length.isnot(None)
        )
        .order_by(
            Prompt.response_length.desc()
        )
        .first()
    )

    model_usage = (
        db.query(
            Prompt.model,
            func.count(Prompt.id)
        )
        .group_by(Prompt.model)
        .all()
    )

    most_used_model = "N/A"

    if model_usage:

        most_used_model = max(
            model_usage,
            key=lambda x: x[1]
        )[0]

    success_requests = (
        db.query(Prompt)
        .filter(
            Prompt.status == "SUCCESS"
        )
        .count()
    )

    failed_requests = (
        db.query(Prompt)
        .filter(
            Prompt.status == "FAILED"
        )
        .count()
    )

    total_requests = (
        success_requests +
        failed_requests
    )

    success_rate = (
        round(
            (success_requests / total_requests) * 100,
            2
        )
        if total_requests
        else 0
    )

    return {
        "most_used_model": most_used_model,

        "latest_prompt": (
            latest_prompt.prompt
            if latest_prompt
            else "N/A"
        ),

        "longest_response": (
            longest_response.response_length
            if longest_response
            else 0
        ),

        "failed_requests": failed_requests,

        "success_rate": success_rate
    }