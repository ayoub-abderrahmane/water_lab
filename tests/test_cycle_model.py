"""
Tests automatisés du cycle de vie du modèle Water Lab.

Ce fichier couvre uniquement la compétence C12 :

1. validation du jeu de données ;
2. validation de la préparation des données ;
3. validation de l'entraînement ;
4. validation des performances minimales ;
5. validation des prédictions ;
6. validation de la sauvegarde et du rechargement du modèle.

Les tests sont automatisés avec pytest et peuvent être exécutés
localement ou dans une chaîne d'intégration continue.
"""

from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.model_selection import train_test_split

from src.pipeline import build_pipeline
from src.preprocessing import (
    COLUMNS,
    load_and_clean_data,
    split_features_target,
)


DATA_PATH = Path("data/raw/water_potability.csv")

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

TARGET_COLUMN = "Potability"

# Ces seuils sont légèrement inférieurs aux résultats actuels du modèle.
# Ils servent à détecter une baisse importante des performances.
MINIMUM_ACCURACY = 0.55
MINIMUM_ROC_AUC = 0.58


@pytest.fixture(scope="module")
def dataframe() -> pd.DataFrame:
    """
    Charge une seule fois le jeu de données pour tous les tests.

    Le scope "module" évite de relire le fichier CSV avant chaque test.
    """
    return load_and_clean_data(DATA_PATH)


@pytest.fixture(scope="module")
def train_test_data(
    dataframe: pd.DataFrame,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.Series,
    pd.Series,
]:
    """
    Sépare les données en un jeu d'entraînement et un jeu de test.

    La séparation est stratifiée pour conserver une proportion proche
    des classes potable et non potable dans les deux jeux.

    Le random_state fixe rend le test reproductible.
    """
    features, target = split_features_target(dataframe)

    return train_test_split(
        features,
        target,
        test_size=0.20,
        random_state=42,
        stratify=target,
    )


@pytest.fixture(scope="module")
def trained_pipeline(
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
):
    """
    Construit et entraîne une seule fois le pipeline complet.

    Le pipeline comprend notamment :

    - l'imputation des valeurs manquantes ;
    - le modèle de classification XGBoost.

    Cette fixture est réutilisée par les tests d'évaluation,
    de prédiction et de sérialisation.
    """
    x_train, _, y_train, _ = train_test_data

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)

    return pipeline


# -------------------------------------------------------------------
# Validation du jeu de données
# -------------------------------------------------------------------


def test_dataset_file_exists() -> None:
    """
    Vérifie que le fichier source existe.

    Sans ce fichier, la préparation et l'entraînement du modèle
    ne peuvent pas être exécutés.
    """
    assert DATA_PATH.exists(), (
        f"Le jeu de données est introuvable : {DATA_PATH}"
    )


def test_dataset_is_not_empty(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie que le jeu de données contient des observations.

    Un fichier vide ne doit jamais être accepté pour entraîner
    ou évaluer le modèle.
    """
    assert not dataframe.empty
    assert len(dataframe) > 0


def test_dataset_contains_expected_columns(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie la présence et l'ordre des colonnes attendues.

    Une colonne manquante, supplémentaire ou déplacée pourrait
    rendre les données incompatibles avec le pipeline.
    """
    assert list(dataframe.columns) == COLUMNS


def test_target_contains_only_binary_values(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie que la cible contient uniquement les classes 0 et 1.

    Dans ce projet :

    - 0 signifie non potable ;
    - 1 signifie potable.
    """
    target_values = set(
        dataframe[TARGET_COLUMN].unique()
    )

    assert target_values.issubset({0, 1})


def test_target_has_no_missing_values(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie qu'aucune valeur de la cible n'est manquante.

    Une observation sans classe connue ne peut pas être utilisée
    pour un entraînement supervisé.
    """
    missing_target_count = (
        dataframe[TARGET_COLUMN]
        .isna()
        .sum()
    )

    assert missing_target_count == 0


def test_feature_columns_are_numeric(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie que toutes les variables du modèle sont numériques.

    Le pipeline et XGBoost attendent des valeurs numériques.
    """
    features = dataframe[FEATURE_COLUMNS]

    for column in FEATURE_COLUMNS:
        assert pd.api.types.is_numeric_dtype(
            features[column]
        ), f"La colonne {column} n'est pas numérique."


def test_features_and_target_are_separated(
    dataframe: pd.DataFrame,
) -> None:
    """
    Vérifie que la cible n'est pas incluse dans les variables.

    Cela empêche une fuite de données qui donnerait directement
    la réponse attendue au modèle pendant son entraînement.
    """
    features, target = split_features_target(
        dataframe
    )

    assert TARGET_COLUMN not in features.columns
    assert list(features.columns) == FEATURE_COLUMNS
    assert len(features) == len(target)


# -------------------------------------------------------------------
# Validation de la préparation des données
# -------------------------------------------------------------------


def test_pipeline_contains_imputer() -> None:
    """
    Vérifie que le pipeline contient une étape d'imputation.

    Cette étape remplace les valeurs manquantes par les médianes
    apprises uniquement sur le jeu d'entraînement.
    """
    pipeline = build_pipeline()

    assert "imputer" in pipeline.named_steps


def test_pipeline_contains_classifier() -> None:
    """
    Vérifie que le pipeline contient un modèle de classification.

    Le nom exact de l'étape finale peut varier. Le test vérifie donc
    que le pipeline possède au moins deux étapes et qu'une étape finale
    est bien présente après l'imputation.
    """
    pipeline = build_pipeline()

    assert len(pipeline.steps) >= 2

    final_step_name, final_estimator = (
        pipeline.steps[-1]
    )

    assert final_step_name != "imputer"
    assert hasattr(final_estimator, "fit")
    assert hasattr(final_estimator, "predict")


def test_imputer_removes_missing_values(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que l'imputation supprime les valeurs manquantes.

    Le test prend quelques observations du jeu de test,
    ajoute volontairement des valeurs manquantes puis applique
    l'imputer entraîné.
    """
    _, x_test, _, _ = train_test_data

    sample = x_test.head(5).copy()

    sample.loc[
        sample.index[0],
        "ph",
    ] = np.nan

    sample.loc[
        sample.index[1],
        "Sulfate",
    ] = np.nan

    sample.loc[
        sample.index[2],
        "Trihalomethanes",
    ] = np.nan

    imputer = trained_pipeline.named_steps[
        "imputer"
    ]

    transformed_sample = imputer.transform(sample)

    assert not np.isnan(
        transformed_sample
    ).any()


def test_imputer_has_learned_one_median_per_feature(
    trained_pipeline,
) -> None:
    """
    Vérifie que l'imputer a appris une médiane pour chaque variable.

    La propriété statistics_ est créée pendant l'entraînement.
    Elle contient les valeurs utilisées pour remplacer les données
    manquantes.
    """
    imputer = trained_pipeline.named_steps[
        "imputer"
    ]

    assert hasattr(imputer, "statistics_")

    assert len(
        imputer.statistics_
    ) == len(FEATURE_COLUMNS)

    assert not np.isnan(
        imputer.statistics_
    ).any()


# -------------------------------------------------------------------
# Validation de l'entraînement
# -------------------------------------------------------------------


def test_pipeline_can_be_trained(
    trained_pipeline,
) -> None:
    """
    Vérifie que l'entraînement du pipeline se termine correctement.

    Après l'entraînement, le modèle final doit posséder l'attribut
    classes_, ce qui indique qu'il a appris les classes de la cible.
    """
    final_estimator = trained_pipeline.steps[-1][1]

    assert hasattr(final_estimator, "classes_")

    learned_classes = set(
        final_estimator.classes_
    )

    assert learned_classes == {0, 1}


def test_training_uses_expected_feature_order(
    trained_pipeline,
) -> None:
    """
    Vérifie que le pipeline a été entraîné avec les neuf variables
    dans l'ordre attendu.

    L'ordre des colonnes doit rester stable entre l'entraînement
    et les prédictions en production.
    """
    assert hasattr(
        trained_pipeline,
        "feature_names_in_",
    )

    assert list(
        trained_pipeline.feature_names_in_
    ) == FEATURE_COLUMNS


# -------------------------------------------------------------------
# Validation de l'évaluation
# -------------------------------------------------------------------


def test_model_accuracy_is_above_minimum(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que l'accuracy du modèle reste supérieure au seuil minimal.

    Ce test est un test de non-régression. Il doit échouer si une
    modification réduit fortement les performances du modèle.
    """
    _, x_test, _, y_test = train_test_data

    predictions = trained_pipeline.predict(
        x_test
    )

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    assert accuracy >= MINIMUM_ACCURACY, (
        f"Accuracy insuffisante : {accuracy:.4f}. "
        f"Minimum attendu : {MINIMUM_ACCURACY:.4f}."
    )


def test_model_roc_auc_is_above_minimum(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que le ROC-AUC reste supérieur au seuil minimal.

    Le ROC-AUC mesure la capacité du modèle à distinguer les classes
    potable et non potable sur différents seuils de décision.
    """
    _, x_test, _, y_test = train_test_data

    probabilities = (
        trained_pipeline.predict_proba(
            x_test
        )[:, 1]
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    assert roc_auc >= MINIMUM_ROC_AUC, (
        f"ROC-AUC insuffisant : {roc_auc:.4f}. "
        f"Minimum attendu : {MINIMUM_ROC_AUC:.4f}."
    )


# -------------------------------------------------------------------
# Validation des prédictions
# -------------------------------------------------------------------


def test_model_returns_valid_classes(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que le modèle retourne uniquement les classes 0 et 1.
    """
    _, x_test, _, _ = train_test_data

    predictions = trained_pipeline.predict(
        x_test.head(20)
    )

    assert set(predictions).issubset({0, 1})


def test_model_returns_valid_probabilities(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que les probabilités sont comprises entre 0 et 1.

    La somme des probabilités des deux classes doit également
    être égale à 1 pour chaque observation.
    """
    _, x_test, _, _ = train_test_data

    probabilities = (
        trained_pipeline.predict_proba(
            x_test.head(20)
        )
    )

    assert np.all(probabilities >= 0)
    assert np.all(probabilities <= 1)

    assert np.allclose(
        probabilities.sum(axis=1),
        1.0,
    )


def test_model_predicts_with_missing_values(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
) -> None:
    """
    Vérifie que le pipeline peut prédire avec des valeurs manquantes.

    L'imputer doit remplacer ces valeurs avant que l'échantillon
    soit transmis au modèle.
    """
    _, x_test, _, _ = train_test_data

    sample = x_test.head(1).copy()

    sample.loc[
        sample.index[0],
        "ph",
    ] = np.nan

    sample.loc[
        sample.index[0],
        "Sulfate",
    ] = np.nan

    sample.loc[
        sample.index[0],
        "Trihalomethanes",
    ] = np.nan

    prediction = trained_pipeline.predict(
        sample
    )

    assert len(prediction) == 1
    assert prediction[0] in {0, 1}


# -------------------------------------------------------------------
# Validation de la sauvegarde du modèle
# -------------------------------------------------------------------


def test_model_can_be_saved_and_reloaded(
    trained_pipeline,
    train_test_data: tuple[
        pd.DataFrame,
        pd.DataFrame,
        pd.Series,
        pd.Series,
    ],
    tmp_path: Path,
) -> None:
    """
    Vérifie que le pipeline peut être sauvegardé puis rechargé.

    Le modèle rechargé doit produire exactement les mêmes prédictions
    que le modèle présent en mémoire.

    tmp_path est un dossier temporaire créé automatiquement par pytest.
    Il est supprimé après l'exécution du test.
    """
    _, x_test, _, _ = train_test_data

    temporary_model_path = (
        tmp_path / "water_model_test.joblib"
    )

    joblib.dump(
        trained_pipeline,
        temporary_model_path,
    )

    assert temporary_model_path.exists()

    reloaded_pipeline = joblib.load(
        temporary_model_path
    )

    sample = x_test.head(20)

    original_predictions = (
        trained_pipeline.predict(sample)
    )

    reloaded_predictions = (
        reloaded_pipeline.predict(sample)
    )

    assert np.array_equal(
        original_predictions,
        reloaded_predictions,
    )