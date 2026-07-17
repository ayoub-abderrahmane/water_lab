import joblib

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

pipeline = joblib.load(
    "models/water_xgboost_pipeline.joblib"
)

imputer = pipeline.named_steps["imputer"]

medians = dict(
    zip(
        FEATURE_COLUMNS,
        imputer.statistics_,
        strict=True,
    )
)

for feature, median in medians.items():
    print(f'"{feature}": {float(median):.6f},')