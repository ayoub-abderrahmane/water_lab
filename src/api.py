import logging
import time

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import make_asgi_app
from pydantic import BaseModel, ConfigDict, Field

from src.logging_config import configure_logging
from src.metrics import (
    API_REQUEST_DURATION_SECONDS,
    API_REQUESTS_TOTAL,
    MISSING_INPUT_VALUES_TOTAL,
    MODEL_LOADED,
    PREDICTION_ERRORS_TOTAL,
    PREDICTIONS_TOTAL,
)
from src.model import load_model, predict_water_quality


configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Water Lab API",
    description="API de prédiction de la potabilité de l'eau.",
    version="0.1.0",
)


class WaterSample(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
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
        }
    )

    ph: float | None = Field(default=None)
    Hardness: float | None = Field(default=None, ge=0)
    Solids: float | None = Field(default=None, ge=0)
    Chloramines: float | None = Field(default=None, ge=0)
    Sulfate: float | None = Field(default=None, ge=0)
    Conductivity: float | None = Field(default=None, ge=0)
    Organic_carbon: float | None = Field(default=None, ge=0)
    Trihalomethanes: float | None = Field(default=None, ge=0)
    Turbidity: float | None = Field(default=None, ge=0)


class PredictionResponse(BaseModel):
    predicted_class: int
    label: str
    potable_probability: float


@app.middleware("http")
async def monitor_requests(
    request: Request,
    call_next,
):
    """
    Mesure automatiquement toutes les requêtes HTTP reçues par l'API.
    """
    start_time = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response

    except Exception:
        logger.exception(
            "Erreur non gérée pendant la requête %s %s",
            request.method,
            request.url.path,
        )
        raise

    finally:
        duration = time.perf_counter() - start_time

        status_code = (
            response.status_code
            if response is not None
            else 500
        )

        endpoint = request.url.path

        API_REQUESTS_TOTAL.labels(
            method=request.method,
            endpoint=endpoint,
            status_code=str(status_code),
        ).inc()

        API_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(duration)

        logger.info(
            "Requête terminée | méthode=%s | endpoint=%s | "
            "status=%s | durée=%.4fs",
            request.method,
            endpoint,
            status_code,
            duration,
        )


@app.on_event("startup")
def startup_event() -> None:
    """
    Vérifie que le modèle est disponible au démarrage.
    """
    try:
        load_model()
        MODEL_LOADED.set(1)
        logger.info("Modèle chargé avec succès au démarrage")

    except FileNotFoundError:
        MODEL_LOADED.set(0)
        logger.exception("Modèle introuvable au démarrage")


@app.get("/health")
def health() -> dict[str, str]:
    try:
        load_model()

    except FileNotFoundError as error:
        MODEL_LOADED.set(0)

        logger.error(
            "Échec du contrôle de santé : modèle introuvable"
        )

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    MODEL_LOADED.set(1)

    return {
        "status": "healthy",
        "model": "loaded",
    }


@app.get("/model/info")
def model_info() -> dict[str, str]:
    return {
        "name": "XGBoost Water Potability",
        "version": "0.1.0",
        "imputation": "median",
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
)
def predict(sample: WaterSample) -> PredictionResponse:
    input_data = sample.model_dump()

    for feature_name, value in input_data.items():
        if value is None:
            MISSING_INPUT_VALUES_TOTAL.labels(
                feature=feature_name,
            ).inc()

    try:
        predicted_class, probability = predict_water_quality(
            input_data
        )

    except FileNotFoundError as error:
        MODEL_LOADED.set(0)
        PREDICTION_ERRORS_TOTAL.inc()

        logger.error(
            "Prédiction impossible : modèle introuvable"
        )

        raise HTTPException(
            status_code=503,
            detail=str(error),
        ) from error

    except Exception as error:
        PREDICTION_ERRORS_TOTAL.inc()

        logger.exception(
            "Erreur inattendue pendant la prédiction"
        )

        raise HTTPException(
            status_code=500,
            detail="Erreur interne pendant la prédiction",
        ) from error

    PREDICTIONS_TOTAL.labels(
        predicted_class=str(predicted_class),
    ).inc()

    label = (
        "potable"
        if predicted_class == 1
        else "non potable"
    )

    logger.info(
        "Prédiction effectuée | classe=%s | probabilité=%.4f",
        predicted_class,
        probability,
    )

    return PredictionResponse(
        predicted_class=predicted_class,
        label=label,
        potable_probability=round(probability, 4),
    )


metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)