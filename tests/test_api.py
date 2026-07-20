import os
from types import SimpleNamespace

os.environ.setdefault(
    "DATABASE_URL",
    "sqlite+pysqlite:///:memory:",
)

TEST_TOKEN = os.getenv(
    "API_AUTH_TOKEN",
    "test-token",
)

os.environ.setdefault(
    "API_AUTH_TOKEN",
    TEST_TOKEN,
)

import pytest
from fastapi.testclient import TestClient

from datetime import datetime, timedelta, timezone

from src.database import get_database
from src.user_auth import get_optional_connected_user

TEST_TOKEN = os.getenv("API_AUTH_TOKEN", "test-token")
os.environ.setdefault("API_AUTH_TOKEN", TEST_TOKEN)

from src.api import app  # noqa: E402
from src.ocr_service import OCRError  # noqa: E402


client = TestClient(app)

AUTH_HEADERS = {
    "Authorization": f"Bearer {TEST_TOKEN}",
}

VALID_PAYLOAD = {
    "ph": 7.2,
    "Hardness": 190.0,
    "Solids": 21000.0,
    "Chloramines": 7.0,
    "Sulfate": 330.0,
    "Conductivity": 420.0,
    "Organic_carbon": 14.0,
    "Trihalomethanes": 65.0,
    "Turbidity": 4.0,
}

class FakeScalarResult:
    """Résultat simulé de SQLAlchemy pour database.scalars()."""

    def __init__(self, items: list) -> None:
        self.items = items

    def all(self) -> list:
        return self.items


class FakeDatabase:
    """
    Session SQLAlchemy simulée.

    Elle permet de tester l'API sans écrire dans PostgreSQL.
    """

    def __init__(
        self,
        scalar_result=None,
        scalars_result: list | None = None,
    ) -> None:
        self.scalar_result = scalar_result
        self.scalars_result = scalars_result or []
        self.added_objects = []
        self.commit_called = False

    def scalar(self, statement):
        return self.scalar_result

    def scalars(self, statement) -> FakeScalarResult:
        return FakeScalarResult(self.scalars_result)

    def add(self, instance) -> None:
        self.added_objects.append(instance)

    def commit(self) -> None:
        self.commit_called = True


@pytest.fixture(autouse=True)
def reset_dependency_overrides():
    """
    Supprime les dépendances simulées après chaque test.

    Cela évite qu'un test influence les suivants.
    """
    yield
    app.dependency_overrides.clear()

def test_predict_without_token_is_rejected() -> None:
    response = client.post("/predict", json=VALID_PAYLOAD)
    assert response.status_code == 401


def test_predict_with_invalid_token_is_rejected() -> None:
    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers={"Authorization": "Bearer mauvais-jeton"},
    )
    assert response.status_code == 401


def test_predict_with_valid_token_succeeds() -> None:
    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200

    result = response.json()
    assert result["predicted_class"] in {0, 1}
    assert result["label"] in {"potable", "non potable"}
    assert 0.0 <= result["potable_probability"] <= 1.0


def test_predict_rejects_negative_value() -> None:
    payload = VALID_PAYLOAD.copy()
    payload["Hardness"] = -1.0

    response = client.post(
        "/predict",
        json=payload,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_predict_rejects_invalid_type() -> None:
    payload = VALID_PAYLOAD.copy()
    payload["Sulfate"] = "valeur-invalide"

    response = client.post(
        "/predict",
        json=payload,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_model_info_requires_authentication() -> None:
    response = client.get("/model/info")
    assert response.status_code == 401


def test_model_info_with_valid_token_succeeds() -> None:
    response = client.get(
        "/model/info",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert response.json()["name"] == "XGBoost Water Potability"


def test_metrics_requires_authentication() -> None:
    response = client.get("/metrics")
    assert response.status_code == 401


def test_metrics_with_valid_token_succeeds() -> None:
    response = client.get(
        "/metrics",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert "water_lab_" in response.text


def test_ocr_rejects_unsupported_file_type() -> None:
    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "document.txt",
                b"contenu",
                "text/plain",
            )
        },
    )

    assert response.status_code == 415


def test_ocr_rejects_empty_file() -> None:
    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "document.png",
                b"",
                "image/png",
            )
        },
    )

    assert response.status_code == 400


def test_ocr_rejects_file_larger_than_one_mebibyte() -> None:
    oversized_content = b"0" * ((1 * 1024 * 1024) + 1)

    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "document.png",
                oversized_content,
                "image/png",
            )
        },
    )

    assert response.status_code == 413


def test_ocr_returns_text_and_extracted_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ocr_text = """
    Rapport d'analyse d'eau
    pH : 7,6
    Conductivité : 650 µS/cm
    Turbidité : 0,7 NTU
    Dureté : 25,3 °f
    Sulfates : 210 mg/L
    """

    fake_result = SimpleNamespace(
        text=ocr_text,
        page_count=1,
        processing_time_ms=120,
    )

    monkeypatch.setattr(
        "src.api.extract_text_from_file",
        lambda **kwargs: fake_result,
    )

    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "rapport.png",
                b"image-factice",
                "image/png",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()
    values = result["extracted_values"]

    assert result["filename"] == "rapport.png"
    assert result["page_count"] == 1
    assert result["processing_time_ms"] == 120
    assert values["ph"] == pytest.approx(7.6)
    assert values["Conductivity"] == pytest.approx(650.0)
    assert values["Turbidity"] == pytest.approx(0.7)
    assert values["Hardness"] == pytest.approx(253.0)
    assert values["Sulfate"] == pytest.approx(210.0)
    assert values["Chloramines"] is None


def test_ocr_service_error_returns_502(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_ocr_error(**kwargs):
        raise OCRError("Service OCR indisponible")

    monkeypatch.setattr(
        "src.api.extract_text_from_file",
        raise_ocr_error,
    )

    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "rapport.png",
                b"image-factice",
                "image/png",
            )
        },
    )

    assert response.status_code == 502
    assert "Service OCR indisponible" in response.json()["detail"]


def test_unknown_route_returns_404() -> None:
    response = client.get(
        "/route-inexistante",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 404

def test_health_returns_model_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "src.api.load_model",
        lambda: object(),
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "model": "loaded",
    }


def test_health_returns_503_when_model_is_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def raise_file_not_found():
        raise FileNotFoundError(
            "Modèle introuvable."
        )

    monkeypatch.setattr(
        "src.api.load_model",
        raise_file_not_found,
    )

    response = client.get("/health")

    assert response.status_code == 503
    assert "Modèle introuvable" in response.json()["detail"]

def test_login_without_api_token_is_rejected() -> None:
    response = client.post(
        "/auth/login",
        json={
            "username": "inovie_lab",
            "password": "mot-de-passe-test",
        },
    )

    assert response.status_code == 401


def test_login_with_invalid_credentials_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_user = SimpleNamespace(
        id=1,
        username="inovie_lab",
        password_hash="hash-test",
        is_active=True,
    )

    fake_database = FakeDatabase(
        scalar_result=fake_user,
    )

    def override_database():
        yield fake_database

    app.dependency_overrides[
        get_database
    ] = override_database

    monkeypatch.setattr(
        "src.api.verify_password",
        lambda password, password_hash: False,
    )

    response = client.post(
        "/auth/login",
        headers=AUTH_HEADERS,
        json={
            "username": "inovie_lab",
            "password": "mauvais-mot-de-passe",
        },
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Identifiants incorrects."
    )


def test_login_with_valid_credentials_returns_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_user = SimpleNamespace(
        id=1,
        username="inovie_lab",
        password_hash="hash-test",
        is_active=True,
    )

    fake_database = FakeDatabase(
        scalar_result=fake_user,
    )

    def override_database():
        yield fake_database

    app.dependency_overrides[
        get_database
    ] = override_database

    monkeypatch.setattr(
        "src.api.verify_password",
        lambda password, password_hash: True,
    )

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(hours=8)
    )

    monkeypatch.setattr(
        "src.api.create_user_session",
        lambda database, user: (
            "session-token-test",
            expires_at,
        ),
    )

    response = client.post(
        "/auth/login",
        headers=AUTH_HEADERS,
        json={
            "username": "inovie_lab",
            "password": "mot-de-passe-test",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["username"] == "inovie_lab"
    assert (
        result["session_token"]
        == "session-token-test"
    )
    assert "expires_at" in result

def test_logout_without_user_session_is_rejected() -> None:
    response = client.post(
        "/auth/logout",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422


def test_logout_deletes_user_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_database = FakeDatabase()

    def override_database():
        yield fake_database

    app.dependency_overrides[
        get_database
    ] = override_database

    captured_values = {}

    def fake_delete_session(
        database,
        session_token: str,
    ) -> None:
        captured_values["database"] = database
        captured_values["session_token"] = (
            session_token
        )

    monkeypatch.setattr(
        "src.api.delete_session",
        fake_delete_session,
    )

    response = client.post(
        "/auth/logout",
        headers={
            **AUTH_HEADERS,
            "X-User-Session": "session-token-test",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Déconnexion effectuée.",
    }

    assert (
        captured_values["database"]
        is fake_database
    )
    assert (
        captured_values["session_token"]
        == "session-token-test"
    )   

def test_history_without_user_session_is_rejected() -> None:
    fake_database = FakeDatabase()

    def override_database():
        yield fake_database

    def override_connected_user():
        return None

    app.dependency_overrides[
        get_database
    ] = override_database

    app.dependency_overrides[
        get_optional_connected_user
    ] = override_connected_user

    response = client.get(
        "/predictions/history",
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 401
    assert (
        response.json()["detail"]
        == "Connexion utilisateur requise."
    )


def test_history_returns_connected_user_predictions() -> None:
    connected_user = SimpleNamespace(
        id=1,
        username="inovie_lab",
    )

    prediction_date = datetime.now(timezone.utc)

    fake_prediction = SimpleNamespace(
        id=42,
        user_id=1,
        source="manuel",
        created_at=prediction_date,
        ph=7.2,
        hardness=190.0,
        solids=21000.0,
        chloramines=7.0,
        sulfate=330.0,
        conductivity=420.0,
        organic_carbon=14.0,
        trihalomethanes=65.0,
        turbidity=4.0,
        predicted_class=1,
        label="potable",
        potable_probability=0.78,
    )

    fake_database = FakeDatabase(
        scalars_result=[fake_prediction],
    )

    def override_database():
        yield fake_database

    def override_connected_user():
        return connected_user

    app.dependency_overrides[
        get_database
    ] = override_database

    app.dependency_overrides[
        get_optional_connected_user
    ] = override_connected_user

    response = client.get(
        "/predictions/history",
        headers={
            **AUTH_HEADERS,
            "X-User-Session": "session-token-test",
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert len(result) == 1
    assert result[0]["id"] == 42
    assert result[0]["source"] == "manuel"
    assert result[0]["ph"] == pytest.approx(7.2)
    assert result[0]["predicted_class"] == 1
    assert result[0]["label"] == "potable"
    assert result[0][
        "potable_probability"
    ] == pytest.approx(0.78)

def test_guest_prediction_is_not_saved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_database = FakeDatabase()

    def override_database():
        yield fake_database

    def override_connected_user():
        return None

    app.dependency_overrides[
        get_database
    ] = override_database

    app.dependency_overrides[
        get_optional_connected_user
    ] = override_connected_user

    monkeypatch.setattr(
        "src.api.predict_water_quality",
        lambda input_data: (1, 0.8123),
    )

    response = client.post(
        "/predict",
        json=VALID_PAYLOAD,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 200
    assert fake_database.added_objects == []
    assert fake_database.commit_called is False


def test_connected_prediction_is_saved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    connected_user = SimpleNamespace(
        id=1,
        username="inovie_lab",
    )

    fake_database = FakeDatabase()

    def override_database():
        yield fake_database

    def override_connected_user():
        return connected_user

    app.dependency_overrides[
        get_database
    ] = override_database

    app.dependency_overrides[
        get_optional_connected_user
    ] = override_connected_user

    monkeypatch.setattr(
        "src.api.predict_water_quality",
        lambda input_data: (1, 0.8123),
    )

    response = client.post(
        "/predict",
        params={"source": "ocr"},
        json=VALID_PAYLOAD,
        headers={
            **AUTH_HEADERS,
            "X-User-Session": "session-token-test",
        },
    )

    assert response.status_code == 200
    assert len(fake_database.added_objects) == 1
    assert fake_database.commit_called is True

    saved_prediction = (
        fake_database.added_objects[0]
    )

    assert saved_prediction.user_id == 1
    assert saved_prediction.source == "ocr"
    assert saved_prediction.predicted_class == 1
    assert saved_prediction.label == "potable"
    assert (
        saved_prediction.potable_probability
        == pytest.approx(0.8123)
    )

def test_predict_rejects_unknown_property() -> None:
    payload = VALID_PAYLOAD.copy()
    payload["administrateur"] = True

    response = client.post(
        "/predict",
        json=payload,
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422