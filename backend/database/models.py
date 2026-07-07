from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text
)
from datetime import datetime, UTC

from sqlalchemy.orm import relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(150),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="evaluator"
    )


class Prompt(Base):
    __tablename__ = "prompts"

    id = Column(Integer, primary_key=True, index=True)

    prompt = Column(Text, nullable=False)

    response = Column(Text)

    model = Column(String(100))

    timestamp = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC)
    )

    response_length = Column(Integer)

    status = Column(
        String(20),
        default="SUCCESS"
    )

    responses = relationship(
        "Response",
        back_populates="prompt"
    )


class Response(Base):
    __tablename__ = "responses"

    id = Column(Integer, primary_key=True, index=True)

    prompt_id = Column(
        Integer,
        ForeignKey("prompts.id"),
        nullable=False,
        index=True
    )

    response = Column(Text)

    model = Column(String(100))

    status = Column(
        String(20),
        default="SUCCESS"
    )

    response_length = Column(Integer)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True
    )

    prompt = relationship(
        "Prompt",
        back_populates="responses"
    )

    evaluations = relationship(
        "Evaluation",
        back_populates="response"
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id = Column(Integer, primary_key=True, index=True)

    response_id = Column(
        Integer,
        ForeignKey("responses.id"),
        nullable=False,
        index=True
    )

    evaluation_type = Column(
        String(20),
        nullable=False,
        index=True
    )

    evaluator_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True,
        index=True
    )

    score = Column(Integer)

    flags = Column(JSON)

    notes = Column(Text)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        index=True
    )

    response = relationship(
        "Response",
        back_populates="evaluations"
    )

    evaluator = relationship(
        "User",
        back_populates="evaluations"
    )
