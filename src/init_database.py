"""
Création des tables et du compte principal inovie_lab.
"""

import os

from sqlalchemy import select

from src.database import Base, SessionLocal, engine
from src.database_models import User
from src.user_auth import hash_password


def initialize_database() -> None:
    """
    Crée les tables puis le compte principal s'il n'existe pas.

    Le mot de passe initial provient uniquement de l'environnement.
    """
    username = os.getenv("LAB_USERNAME", "inovie_lab")
    password = os.getenv("LAB_PASSWORD")

    if not password:
        raise RuntimeError(
            "La variable LAB_PASSWORD n'est pas configurée."
        )

    Base.metadata.create_all(bind=engine)

    with SessionLocal.begin() as database:
        existing_user = database.scalar(
            select(User).where(
                User.username == username
            )
        )

        if existing_user is None:
            database.add(
                User(
                    username=username,
                    password_hash=hash_password(password),
                )
            )