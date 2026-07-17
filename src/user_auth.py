"""
Authentification du compte laboratoire et gestion des sessions.
"""

import hashlib
import os
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Header, HTTPException
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from src.database import SessionLocal
from src.database_models import User, UserSession


password_hasher = PasswordHash.recommended()

SESSION_DURATION_HOURS = int(
    os.getenv("USER_SESSION_DURATION_HOURS", "8")
)


def hash_password(password: str) -> str:
    """Crée un hash sécurisé du mot de passe."""
    return password_hasher.hash(password)


def verify_password(
    password: str,
    password_hash: str,
) -> bool:
    """Compare un mot de passe avec son hash."""
    return password_hasher.verify(
        password,
        password_hash,
    )


def hash_session_token(token: str) -> str:
    """
    Hash un jeton de session avant son stockage en base.
    """
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


def create_user_session(
    database: Session,
    user: User,
) -> tuple[str, datetime]:
    """
    Crée un jeton aléatoire temporaire pour l'utilisateur.
    """
    raw_token = secrets.token_urlsafe(32)

    expires_at = datetime.now(UTC) + timedelta(
        hours=SESSION_DURATION_HOURS
    )

    database.add(
        UserSession(
            user_id=user.id,
            token_hash=hash_session_token(raw_token),
            expires_at=expires_at,
        )
    )

    database.commit()

    return raw_token, expires_at


def get_user_from_session_token(
    database: Session,
    token: str,
) -> User | None:
    """
    Retourne l'utilisateur associé à une session valide.
    """
    now = datetime.now(UTC)

    statement = (
        select(User)
        .join(
            UserSession,
            UserSession.user_id == User.id,
        )
        .where(
            UserSession.token_hash
            == hash_session_token(token),
            UserSession.expires_at > now,
            User.is_active.is_(True),
        )
    )

    return database.scalar(statement)


def get_optional_connected_user(
    x_user_session: str | None = Header(
        default=None,
        alias="X-User-Session",
    ),
) -> User | None:
    """
    Retourne l'utilisateur connecté lorsque le jeton est valide.

    Sans jeton, la requête continue en mode invité.
    Un jeton invalide ou expiré est refusé.
    """
    if not x_user_session:
        return None

    with SessionLocal() as database:
        user = get_user_from_session_token(
            database,
            x_user_session,
        )

        if user is None:
            raise HTTPException(
                status_code=401,
                detail=(
                    "La session utilisateur est invalide "
                    "ou expirée."
                ),
            )

        database.expunge(user)
        return user


def delete_session(
    database: Session,
    raw_token: str,
) -> None:
    """Supprime une session lors de la déconnexion."""
    database.execute(
        delete(UserSession).where(
            UserSession.token_hash
            == hash_session_token(raw_token)
        )
    )

    database.commit()