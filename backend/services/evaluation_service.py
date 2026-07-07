import re
from collections import Counter

from sqlalchemy.orm import Session

from backend.config.evaluation_rules import (
    NEAR_EMPTY_RESPONSE_LENGTH,
    SENSITIVE_WORDS,
    max_response_length
)
from backend.database.models import Evaluation, Response


AUTOMATED_EVALUATION_TYPE = "automated"
HUMAN_EVALUATION_TYPE = "human"


def evaluate_response_text(response_text: str | None) -> list[str]:
    text = response_text or ""
    stripped_text = text.strip()
    flags = []

    if len(stripped_text) < NEAR_EMPTY_RESPONSE_LENGTH:
        flags.append("empty_or_near_empty_response")

    if len(text) > max_response_length():
        flags.append("response_too_long")

    lower_text = text.lower()

    for word in SENSITIVE_WORDS:
        if " " in word:
            found = word.lower() in lower_text
        else:
            found = bool(
                re.search(
                    rf"\b{re.escape(word.lower())}\b",
                    lower_text
                )
            )

        if found:
            flags.append(f"banned_word:{word}")

    sentences = [
        re.sub(r"\s+", " ", sentence.strip().lower())
        for sentence in re.split(r"[.!?\n]+", text)
        if sentence.strip()
    ]

    if any(count >= 3 for count in Counter(sentences).values()):
        flags.append("repeated_text")

    return flags


def create_automated_evaluation(
    db: Session,
    response: Response
) -> Evaluation:
    evaluation = Evaluation(
        response_id=response.id,
        evaluation_type=AUTOMATED_EVALUATION_TYPE,
        evaluator_id=None,
        score=None,
        flags=evaluate_response_text(response.response),
        notes=None
    )

    db.add(evaluation)
    db.flush()

    return evaluation


def create_human_evaluation(
    db: Session,
    response_id: int,
    evaluator_id: int,
    score: int,
    notes: str | None
) -> Evaluation:
    evaluation = Evaluation(
        response_id=response_id,
        evaluation_type=HUMAN_EVALUATION_TYPE,
        evaluator_id=evaluator_id,
        score=score,
        flags=None,
        notes=notes
    )

    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)

    return evaluation


def list_evaluations(
    db: Session,
    response_id: int | None = None,
    evaluation_type: str | None = None
) -> list[Evaluation]:
    query = db.query(Evaluation)

    if response_id is not None:
        query = query.filter(
            Evaluation.response_id == response_id
        )

    if evaluation_type is not None:
        query = query.filter(
            Evaluation.evaluation_type == evaluation_type
        )

    return (
        query
        .order_by(Evaluation.created_at.desc())
        .all()
    )
