import logging
from functools import lru_cache
from pathlib import Path

import joblib
import pandas as pd
from sklearn.pipeline import Pipeline

from src.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

MODEL_PATH = Path("models/water_xgboost_pipeline.joblib")

FEATURE_COLUMNS = [
    "ph",
    "Hardness",
    "Solids",
    "Chloramines",
    "Sulfate",
    "Conductivity",
    "Organic_carbon",
    "Trihalomethanes",
    "Turbidity",
]


@lru_cache(maxsize=1)
def load_model() -> Pipeline:
    """
    Charge le pipeline entraîné une seule fois.
    """
    if not MODEL_PATH.exists():
        logger.error("Modèle introuvable : %s", MODEL_PATH)

        raise FileNotFoundError(
            "Modèle introuvable. "
            "Exécute d'abord : uv run python -m src.train"
        )

    try:
        pipeline = joblib.load(MODEL_PATH)
    except Exception:
        logger.exception(
            "Erreur pendant le chargement du modèle : %s",
            MODEL_PATH,
        )
        raise

    logger.info("Modèle chargé avec succès : %s", MODEL_PATH)

    return pipeline


def predict_water_quality(
    input_data: dict[str, float | None],
) -> tuple[int, float]:
    """
    Réalise une prédiction et retourne la classe et la probabilité.
    """
    missing_features = [
        feature
        for feature, value in input_data.items()
        if value is None
    ]

    if missing_features:
        logger.warning(
            "Valeurs manquantes reçues : %s",
            missing_features,
        )

    try:
        pipeline = load_model()

        dataframe = pd.DataFrame(
            [input_data],
            columns=FEATURE_COLUMNS,
        )

        prediction = int(pipeline.predict(dataframe)[0])
        probability = float(
            pipeline.predict_proba(dataframe)[0][1]
        )

    except Exception:
        logger.exception("Erreur pendant la prédiction")
        raise

    logger.info(
        "Prédiction terminée | classe=%s | probabilité=%.4f",
        prediction,
        probability,
    )

    return prediction, probability