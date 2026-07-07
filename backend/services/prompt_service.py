from sqlalchemy.orm import Session

from backend.database.models import Prompt


def create_prompt(db: Session, prompt_text: str):
    
    prompt = Prompt(
        prompt=prompt_text
    )

    db.add(prompt)
    db.commit()
    db.refresh(prompt)

    return prompt



def get_all_prompts(db: Session):

    return db.query(Prompt).all()


def create_prompt_with_response(
    db: Session,
    prompt_text: str,
    response_text: str,
    model_name: str,
    status: str
):

    prompt = Prompt(
        prompt=prompt_text,
        response=response_text,
        model=model_name,
        response_length=len(response_text)
        if response_text else 0,
        status=status
    )

    db.add(prompt)

    db.commit()

    db.refresh(prompt)

    return prompt


def get_prompt_history(db: Session):

    return (
        db.query(Prompt)
        .order_by(Prompt.id.desc())
        .limit(20)
        .all()
    )
