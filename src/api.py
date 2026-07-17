import logging
import time

from fastapi import FastAPI, HTTPException, Request
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, ConfigDict, Field

from fastapi import Depends, FastAPI, HTTPException, Request, Response, File, UploadFile

from datetime import datetime

from fastapi import Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database import get_database
from src.database_models import Prediction, User
from src.init_database import initialize_database
from src.user_auth import (
    create_user_session,
    delete_session,
    get_optional_connected_user,
    verify_password,
)

from src.auth import require_authentication

from src.metrics import (
    OCR_FILES_TOTAL,
    OCR_PROCESSING_DURATION_SECONDS,
    OCR_REQUESTS_TOTAL,
)
from src.ocr_service import OCRError, extract_text_from_file
from src.ocr_parser import parse_water_report

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

ALLOWED_OCR_CONTENT_TYPES = {
    "application/pdf",
    "image/png",
    "image/jpeg",
}

MAX_OCR_FILE_SIZE = 1 * 1024 * 1024

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

class OCRResponse(BaseModel):
    filename: str
    content_type: str
    page_count: int
    processing_time_ms: int | None
    extracted_text: str
    extracted_values: dict[str, float | None]

class LoginRequest(BaseModel):
    username: str = Field(
        min_length=3,
        max_length=100,
    )
    password: str = Field(
        min_length=12,
        max_length=200,
    )


class LoginResponse(BaseModel):
    username: str
    session_token: str
    expires_at: datetime


class PredictionHistoryItem(BaseModel):
    id: int
    source: str
    created_at: datetime

    ph: float | None
    Hardness: float | None
    Solids: float | None
    Chloramines: float | None
    Sulfate: float | None
    Conductivity: float | None
    Organic_carbon: float | None
    Trihalomethanes: float | None
    Turbidity: float | None

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

        if endpoint != "/metrics":
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
    Vérifie que le modèle et la db sont disponible au démarrage.
    """
    initialize_database()
    logger.info("Base de données initialisée")

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


@app.get(
    "/model/info",
    dependencies=[Depends(require_authentication)],
)
def model_info() -> dict[str, str]:
    return {
        "name": "XGBoost Water Potability",
        "version": "0.1.0",
        "imputation": "median",
    }


@app.post(
    "/predict",
    response_model=PredictionResponse,
    dependencies=[Depends(require_authentication)],
)
def predict(
    sample: WaterSample,
    source: str = "manuel",
    connected_user: User | None = Depends(
        get_optional_connected_user
    ),
    database: Session = Depends(get_database),
) -> PredictionResponse:
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

    if connected_user is not None:
        if source not in {"manuel", "ocr"}:
            source = "manuel"

        database.add(
            Prediction(
                user_id=connected_user.id,
                source=source,
                ph=input_data["ph"],
                hardness=input_data["Hardness"],
                solids=input_data["Solids"],
                chloramines=input_data["Chloramines"],
                sulfate=input_data["Sulfate"],
                conductivity=input_data["Conductivity"],
                organic_carbon=input_data[
                    "Organic_carbon"
                ],
                trihalomethanes=input_data[
                    "Trihalomethanes"
                ],
                turbidity=input_data["Turbidity"],
                predicted_class=predicted_class,
                label=label,
                potable_probability=round(
                    probability,
                    4,
                ),
            )
        )

        database.commit()

        logger.info(
            "Prédiction enregistrée | utilisateur=%s",
            connected_user.username,
        )

    return PredictionResponse(
        predicted_class=predicted_class,
        label=label,
        potable_probability=round(probability, 4),
    )

@app.post(
    "/auth/login",
    response_model=LoginResponse,
    dependencies=[Depends(require_authentication)],
)
def login(
    credentials: LoginRequest,
    database: Session = Depends(get_database),
) -> LoginResponse:
    """
    Connecte le compte laboratoire.

    La route retourne un jeton de session temporaire.
    """
    user = database.scalar(
        select(User).where(
            User.username == credentials.username
        )
    )

    invalid_credentials = (
        user is None
        or not user.is_active
        or not verify_password(
            credentials.password,
            user.password_hash,
        )
    )

    if invalid_credentials:
        raise HTTPException(
            status_code=401,
            detail="Identifiants incorrects.",
        )

    token, expires_at = create_user_session(
        database,
        user,
    )

    return LoginResponse(
        username=user.username,
        session_token=token,
        expires_at=expires_at,
    )


@app.post(
    "/auth/logout",
    dependencies=[Depends(require_authentication)],
)
def logout(
    x_user_session: str = Header(
        alias="X-User-Session",
    ),
    database: Session = Depends(get_database),
) -> dict[str, str]:
    """Supprime la session utilisateur."""
    delete_session(
        database,
        x_user_session,
    )

    return {
        "message": "Déconnexion effectuée.",
    }

@app.get(
    "/predictions/history",
    response_model=list[PredictionHistoryItem],
    dependencies=[Depends(require_authentication)],
)
def prediction_history(
    connected_user: User | None = Depends(
        get_optional_connected_user
    ),
    database: Session = Depends(get_database),
) -> list[PredictionHistoryItem]:
    """
    Retourne l'historique du compte connecté.
    """
    if connected_user is None:
        raise HTTPException(
            status_code=401,
            detail="Connexion utilisateur requise.",
        )

    predictions = database.scalars(
        select(Prediction)
        .where(
            Prediction.user_id == connected_user.id
        )
        .order_by(
            Prediction.created_at.desc()
        )
        .limit(100)
    ).all()

    return [
        PredictionHistoryItem(
            id=item.id,
            source=item.source,
            created_at=item.created_at,
            ph=item.ph,
            Hardness=item.hardness,
            Solids=item.solids,
            Chloramines=item.chloramines,
            Sulfate=item.sulfate,
            Conductivity=item.conductivity,
            Organic_carbon=item.organic_carbon,
            Trihalomethanes=item.trihalomethanes,
            Turbidity=item.turbidity,
            predicted_class=item.predicted_class,
            label=item.label,
            potable_probability=(
                item.potable_probability
            ),
        )
        for item in predictions
    ]


@app.post(
    "/ocr",
    response_model=OCRResponse,
    dependencies=[Depends(require_authentication)],
)
async def extract_document_text(
    file: UploadFile = File(...),
) -> OCRResponse:
    """
    Extrait le texte d'un fichier PDF, PNG ou JPEG avec OCR.space.
    """
    filename = file.filename or "document"

    content_type = (
        file.content_type
        or "application/octet-stream"
    )

    if content_type not in ALLOWED_OCR_CONTENT_TYPES:
        OCR_REQUESTS_TOTAL.labels(
            status="invalid_format",
        ).inc()

        raise HTTPException(
            status_code=415,
            detail=(
                "Format non pris en charge. "
                "Formats autorisés : PDF, PNG et JPEG."
            ),
        )

    file_content = await file.read()

    if not file_content:
        OCR_REQUESTS_TOTAL.labels(
            status="empty_file",
        ).inc()

        raise HTTPException(
            status_code=400,
            detail="Le fichier transmis est vide.",
        )

    if len(file_content) > MAX_OCR_FILE_SIZE:
        OCR_REQUESTS_TOTAL.labels(
            status="file_too_large",
        ).inc()

        raise HTTPException(
            status_code=413,
            detail="Le fichier dépasse la limite de 1 Mo.",
        )

    OCR_FILES_TOTAL.labels(
        content_type=content_type,
    ).inc()

    start_time = time.perf_counter()

    try:
        result = extract_text_from_file(
            file_content=file_content,
            filename=filename,
            content_type=content_type,
        )

    except OCRError as error:
        OCR_REQUESTS_TOTAL.labels(
            status="error",
        ).inc()

        logger.warning(
            "Échec du traitement OCR | fichier=%s | erreur=%s",
            filename,
            error,
        )

        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    finally:
        duration = time.perf_counter() - start_time

        OCR_PROCESSING_DURATION_SECONDS.observe(
            duration
        )

    OCR_REQUESTS_TOTAL.labels(
        status="success",
    ).inc()

    extracted_values = parse_water_report(
        result.text
    )

    return OCRResponse(
        filename=filename,
        content_type=content_type,
        page_count=result.page_count,
        processing_time_ms=result.processing_time_ms,
        extracted_text=result.text,
        extracted_values=extracted_values,
    )
@app.get(
    "/metrics",
    include_in_schema=False,
    dependencies=[Depends(require_authentication)],
)
def metrics() -> Response:
    """
    Expose les métriques Prometheus.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )