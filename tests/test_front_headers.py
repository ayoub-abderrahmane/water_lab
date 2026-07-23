"""Tests de non-régression pour la construction des en-têtes HTTP."""

from front.headers import build_api_headers


def test_headers_without_user_session() -> None:
    """
    Vérifie qu'aucun en-tête de session n'est envoyé
    avant l'authentification de l'utilisateur.
    """
    headers = build_api_headers(
        api_token="technical-token",
    )

    assert headers["Authorization"] == "Bearer technical-token"
    assert "X-User-Session" not in headers


def test_headers_include_current_user_session() -> None:
    """
    Vérifie que la session utilisateur courante est ajoutée
    aux en-têtes après l'authentification.
    """
    headers = build_api_headers(
        api_token="technical-token",
        user_session_token="new-session-token",
    )

    assert headers["Authorization"] == "Bearer technical-token"
    assert headers["X-User-Session"] == "new-session-token"


def test_headers_use_updated_session() -> None:
    """
    Test de non-régression de l'incident E5.

    Les en-têtes doivent être reconstruits avec la nouvelle session,
    sans conserver les valeurs créées avant la connexion.
    """
    headers_before_login = build_api_headers(
        api_token="technical-token",
    )

    headers_after_login = build_api_headers(
        api_token="technical-token",
        user_session_token="new-session-token",
    )

    assert "X-User-Session" not in headers_before_login
    assert (
        headers_after_login["X-User-Session"]
        == "new-session-token"
    )

    assert headers_before_login is not headers_after_login