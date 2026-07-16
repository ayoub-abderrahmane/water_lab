from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

XGBOOST_PARAMS = {
    "n_estimators": 300,
    "learning_rate": 0.05,
    "max_depth": 6,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "eval_metric": "logloss",
    # Compense le déséquilibre 61/39 (n_négatifs / n_positifs ≈ 1.56)
    "scale_pos_weight": 1.56,
    "random_state": 42
}


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                    add_indicator=True,
                ),
            ),
            (
                "classifier",
                XGBClassifier(**XGBOOST_PARAMS),
            ),
        ]
    )