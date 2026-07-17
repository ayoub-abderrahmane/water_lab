"""
Modèles PostgreSQL de Water Lab.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class User(Base):
    """
    Compte autorisé à enregistrer et consulter les prédictions.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    predictions: Mapped[list["Prediction"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class UserSession(Base):
    """
    Session de connexion temporaire.

    Seul le hash du jeton est enregistré en base.
    """

    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class Prediction(Base):
    """
    Résultat d'une prédiction enregistrée pour un utilisateur connecté.

    Le rapport OCR et son texte complet ne sont pas stockés.
    """

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    ph: Mapped[float | None] = mapped_column(Float)
    hardness: Mapped[float | None] = mapped_column(Float)
    solids: Mapped[float | None] = mapped_column(Float)
    chloramines: Mapped[float | None] = mapped_column(Float)
    sulfate: Mapped[float | None] = mapped_column(Float)
    conductivity: Mapped[float | None] = mapped_column(Float)
    organic_carbon: Mapped[float | None] = mapped_column(Float)
    trihalomethanes: Mapped[float | None] = mapped_column(Float)
    turbidity: Mapped[float | None] = mapped_column(Float)

    predicted_class: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    label: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    potable_probability: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    user: Mapped[User] = relationship(
        back_populates="predictions",
    )