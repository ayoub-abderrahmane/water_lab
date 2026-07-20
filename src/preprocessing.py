import logging
from pathlib import Path

import pandas as pd

from src.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)

TARGET_COLUMN = "Potability"

COLUMNS = [
    "ph",
    "Hardness",
    "Solids",
    "Chloramines",
    "Sulfate",
    "Conductivity",
    "Organic_carbon",
    "Trihalomethanes",
    "Turbidity",
    TARGET_COLUMN,
]

RAW_DATA_PATH = Path("data/raw/water_potability.csv")
CLEAN_DATA_PATH = Path(
    "data/processed/water_potability_clean.csv"
)


def load_and_clean_data(
    csv_path: Path,
) -> pd.DataFrame:
    """
    Charge et nettoie le dataset sans imputer les valeurs manquantes.
    """
    if not csv_path.exists():
        logger.error("Dataset introuvable : %s", csv_path)
        raise FileNotFoundError(
            f"Fichier introuvable : {csv_path}"
        )

    try:
        dataframe = pd.read_csv(csv_path)
    except Exception:
        logger.exception(
            "Erreur pendant la lecture du CSV : %s",
            csv_path,
        )
        raise

    missing_columns = (
        set(COLUMNS) - set(dataframe.columns)
    )

    if missing_columns:
        logger.error(
            "Colonnes obligatoires absentes : %s",
            sorted(missing_columns),
        )
        raise ValueError(
            "Colonnes manquantes : "
            f"{sorted(missing_columns)}"
        )

    dataframe = dataframe[COLUMNS].copy()

    for column in COLUMNS:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        )

    missing_target_count = int(
        dataframe[TARGET_COLUMN].isna().sum()
    )

    if missing_target_count:
        logger.warning(
            "Lignes avec cible manquante supprimées : %s",
            missing_target_count,
        )
        dataframe = dataframe.dropna(
            subset=[TARGET_COLUMN]
        )

    invalid_targets = (
        set(dataframe[TARGET_COLUMN].unique())
        - {0, 1}
    )

    if invalid_targets:
        logger.error(
            "Valeurs invalides dans la cible : %s",
            sorted(invalid_targets),
        )
        raise ValueError(
            f"Valeurs invalides dans {TARGET_COLUMN} : "
            f"{sorted(invalid_targets)}"
        )

    dataframe[TARGET_COLUMN] = (
        dataframe[TARGET_COLUMN].astype(int)
    )

    logger.info(
        "Dataset nettoyé | lignes=%s | valeurs_manquantes=%s",
        len(dataframe),
        dataframe.isna().sum().to_dict(),
    )

    return dataframe


def split_features_target(
    dataframe: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Sépare les variables explicatives de la cible.
    """
    features = dataframe.drop(
        columns=[TARGET_COLUMN]
    )
    target = dataframe[TARGET_COLUMN]

    return features, target


def save_clean_data(
    dataframe: pd.DataFrame,
    output_path: Path,
) -> None:
    """
    Enregistre le dataset nettoyé sans imputation.
    """
    try:
        output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        dataframe.to_csv(
            output_path,
            index=False,
        )
    except Exception:
        logger.exception(
            "Erreur pendant l'enregistrement : %s",
            output_path,
        )
        raise

    logger.info(
        "Dataset enregistré : %s",
        output_path,
    )


def main() -> None:
    try:
        dataframe = load_and_clean_data(
            RAW_DATA_PATH
        )
        save_clean_data(
            dataframe,
            CLEAN_DATA_PATH,
        )
        print(dataframe.columns.tolist())
        print(dataframe.shape)
    except Exception:
        logger.exception("Échec du preprocessing")
        raise


if __name__ == "__main__":
    main()