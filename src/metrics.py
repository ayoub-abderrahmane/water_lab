from prometheus_client import Counter, Gauge, Histogram

API_REQUESTS_TOTAL = Counter(
    "water_lab_api_requests_total",
    "Nombre total de requêtes reçues par l'API",
    ["method", "endpoint", "status_code"],
)

API_REQUEST_DURATION_SECONDS = Histogram(
    "water_lab_api_request_duration_seconds",
    "Durée de traitement des requêtes API",
    ["method", "endpoint"],
)

PREDICTIONS_TOTAL = Counter(
    "water_lab_predictions_total",
    "Nombre total de prédictions",
    ["predicted_class"],
)

PREDICTION_ERRORS_TOTAL = Counter(
    "water_lab_prediction_errors_total",
    "Nombre total d'erreurs de prédiction",
)

MODEL_LOADED = Gauge(
    "water_lab_model_loaded",
    "Indique si le modèle est chargé : 1 oui, 0 non",
)

MISSING_INPUT_VALUES_TOTAL = Counter(
    "water_lab_missing_input_values_total",
    "Nombre de valeurs manquantes reçues par variable",
    ["feature"],
)

TRAINING_RUNS_TOTAL = Counter(
    "water_lab_training_runs_total",
    "Nombre total d'entraînements exécutés",
    ["status"],
)