from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime
from datetime import datetime, UTC

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
