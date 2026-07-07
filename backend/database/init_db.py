from sqlalchemy import inspect

from backend.database.db import SessionLocal, engine
from backend.services.auth_service import ensure_bootstrap_user


def init_db() -> None:
    inspector = inspect(engine)
    table_names = set(inspector.get_table_names())
    required_tables = {
        "prompts",
        "users",
        "responses",
        "evaluations"
    }

    if not required_tables.issubset(table_names):
        raise RuntimeError(
            "Database schema is not initialized. Run `alembic upgrade head`."
        )

    db = SessionLocal()

    try:
        ensure_bootstrap_user(db)
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
