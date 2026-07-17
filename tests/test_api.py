import os
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

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