from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime, UTC

from .base import Base


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