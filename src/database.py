"""
Configuration de la connexion PostgreSQL.

La session SQLAlchemy est ouverte pour une opération, puis fermée.
"""

import os
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "La variable DATABASE_URL n'est pas configurée."
    )


engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Classe de base des modèles SQLAlchemy."""


def get_database() -> Generator[Session, None, None]:
    """
    Fournit une session de base de données à une route FastAPI.

    La session est toujours fermée après le traitement.
    """
    database = SessionLocal()

    try:
        yield database
    finally:
        database.close()