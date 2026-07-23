"""Fonctions utilitaires pour construire les en-têtes de l'API."""

from typing import Optional


def build_api_headers(
    api_token: str,
    user_session_token: Optional[str] = None,
) -> dict[str, str]:
    """
    Construit les en-têtes HTTP utilisés par le frontend.

    Args:
        api_token:
            Jeton technique permettant d'accéder à l'API.

        user_session_token:
            Jeton de session de l'utilisateur connecté.
            Il est absent avant la connexion.

    Returns:
        Un nouveau dictionnaire d'en-têtes HTTP.
    """
    headers = {
        "Authorization": f"Bearer {api_token}",
    }

    if user_session_token:
        headers["X-User-Session"] = user_session_token

    return headers