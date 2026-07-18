import logging
import os
import time
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split

from src.logging_config import configure_logging
from src.pipeline import XGBOOST_PARAMS, build_pipeline
from src.preprocessing import (
    load_and_clean_data,
    split_features_target,
)

configure_logging()
logger = logging.getLogger(__name__)

DATA_PATH = Path("data/raw/water_potability.csv")
PROCESSED_DATA_PATH = Path(
    "data/processed/water_potability_clean.csv"
)
MODEL_PATH = Path("models/water_xgboost_pipeline.joblib")

MLFLOW_TRACKING_URI = os.getenv(
    "MLFLOW_TRACKING_URI",
    "sqlite:///mlflow.db",
)

MLFLOW_EXPERIMENT_NAME = "water_lab_xgboost"

MINIMUM_ACCURACY = 0.55
MINIMUM_ROC_AUC = 0.58


def validate_model_metrics(
    metrics: dict[str, float],
) -> None:
    """
    Vérifie que les performances minimales du modèle sont respectées.

    Une RuntimeError est levée lorsqu'une métrique est inférieure
    au seuil attendu. Dans une chaîne d'intégration continue,
    cette exception provoque l'échec du workflow et empêche
    le packaging ou le déploiement d'un modèle insuffisant.
    """
    validation_errors = []

    if metrics["accuracy"] < MINIMUM_ACCURACY:
        validation_errors.append(
            "Accuracy insuffisante : "
            f"{metrics['accuracy']:.4f}. "
            f"Minimum attendu : {MINIMUM_ACCURACY:.4f}."
        )

    if metrics["roc_auc"] < MINIMUM_ROC_AUC:
        validation_errors.append(
            "ROC-AUC insuffisant : "
            f"{metrics['roc_auc']:.4f}. "
            f"Minimum attendu : {MINIMUM_ROC_AUC:.4f}."
        )

    if validation_errors:
        raise RuntimeError(
            "Validation du modèle échouée. "
            + " ".join(validation_errors)
        )

    logger.info(
        "Validation réussie | accuracy=%.4f >= %.4f | "
        "roc_auc=%.4f >= %.4f",
        metrics["accuracy"],
        MINIMUM_ACCURACY,
        metrics["roc_auc"],
        MINIMUM_ROC_AUC,
    )

def main() -> None:
    start_time = time.perf_counter()

    logger.info("Début de l'entraînement")

    try:
        dataframe = load_and_clean_data(DATA_PATH)

        PROCESSED_DATA_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        dataframe.to_csv(
            PROCESSED_DATA_PATH,
            index=False,
        )

        features, target = split_features_target(dataframe)

        x_train, x_test, y_train, y_test = train_test_split(
            features,
            target,
            test_size=0.2,
            random_state=42,
            stratify=target,
        )

        logger.info(
            "Découpage effectué | train=%s | test=%s",
            len(x_train),
            len(x_test),
        )

        mlflow.set_tracking_uri(MLFLOW_TRACKING_URI)
        mlflow.set_experiment(MLFLOW_EXPERIMENT_NAME)

        pipeline = build_pipeline()

        with mlflow.start_run() as run:
            pipeline.fit(x_train, y_train)

            predictions = pipeline.predict(x_test)
            probabilities = pipeline.predict_proba(
                x_test
            )[:, 1]

            metrics = {
                "accuracy": accuracy_score(
                    y_test,
                    predictions,
                ),
                "precision": precision_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),
                "recall": recall_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),
                "f1_score": f1_score(
                    y_test,
                    predictions,
                    zero_division=0,
                ),
                "roc_auc": roc_auc_score(
                    y_test,
                    probabilities,
                ),
            }

            mlflow.log_params(XGBOOST_PARAMS)
            mlflow.log_param(
                "imputation_strategy",
                "median",
            )
            mlflow.log_param(
                "missing_indicator",
                True,
            )
            mlflow.log_param("test_size", 0.2)
            mlflow.log_param(
                "dataset_rows",
                len(dataframe),
            )
            mlflow.log_metrics(metrics)

            validate_model_metrics(metrics)

            MODEL_PATH.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            joblib.dump(pipeline, MODEL_PATH)

            mlflow.log_artifact(
                str(PROCESSED_DATA_PATH)
            )
            mlflow.log_artifact(str(MODEL_PATH))

            mlflow.sklearn.log_model(
                sk_model=pipeline,
                name="model",
                serialization_format="cloudpickle",
            )

            logger.info(
                "Run MLflow terminé | run_id=%s",
                run.info.run_id,
            )

        duration = time.perf_counter() - start_time

        logger.info(
            "Entraînement terminé | durée=%.2fs | "
            "accuracy=%.4f | recall=%.4f | roc_auc=%.4f",
            duration,
            metrics["accuracy"],
            metrics["recall"],
            metrics["roc_auc"],
        )

        

        logger.info("Modèle sauvegardé : %s", MODEL_PATH)

    except Exception:
        logger.exception("Échec de l'entraînement")
        raise


if __name__ == "__main__":
    main()