from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_prediction_endpoint() -> None:
    payload = {
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

    response = client.post("/predict", json=payload)

    assert response.status_code == 200

    result = response.json()

    assert result["predicted_class"] in [0, 1]
    assert 0 <= result["potable_probability"] <= 1


def test_prediction_with_missing_values() -> None:
    payload = {
        "ph": None,
        "Hardness": 190.0,
        "Solids": 21000.0,
        "Chloramines": 7.0,
        "Sulfate": None,
        "Conductivity": 420.0,
        "Organic_carbon": 14.0,
        "Trihalomethanes": None,
        "Turbidity": 4.0,
    }

    response = client.post("/predict", json=payload)

    assert response.status_code == 200