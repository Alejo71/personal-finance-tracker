import os

from sqlmodel import SQLModel, create_engine


def _database_url() -> str:
    if configured_url := os.getenv("DATABASE_URL"):
        return configured_url
    if host := os.getenv("DB_HOST"):
        user = os.getenv("DB_USER", "postgres")
        password = os.getenv("DB_PASSWORD", "postgres")
        name = os.getenv("DB_NAME", "personal_finance_tracker")
        port = os.getenv("DB_PORT", "5432")
        return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
    return "sqlite:///./finance.db"


DATABASE_URL = _database_url()
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, echo=False, connect_args=connect_args)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
