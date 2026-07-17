import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")
API_AUTH_TOKEN = os.getenv("API_AUTH_TOKEN")

DEFAULT_VALUES = {
    "ph": 7.035037,
    "Hardness": 196.928061,
    "Solids": 20866.335842,
    "Chloramines": 7.118162,
    "Sulfate": 333.073546,
    "Conductivity": 424.941336,
    "Organic_carbon": 14.214780,
    "Trihalomethanes": 66.565709,
    "Turbidity": 3.969602,
}

DISPLAY_LABELS = {
    "ph": "pH",
    "Hardness": "Dureté",
    "Solids": "Solides dissous",
    "Chloramines": "Chloramines",
    "Sulfate": "Sulfates",
    "Conductivity": "Conductivité",
    "Organic_carbon": "Carbone organique",
    "Trihalomethanes": "Trihalométhanes",
    "Turbidity": "Turbidité",
}

SLIDER_CONFIG = {
    "ph": {
        "label": "pH",
        "min": 0.0,
        "max": 14.0,
        "step": 0.1,
    },
    "Hardness": {
        "label": "Dureté",
        "min": 0.0,
        "max": 500.0,
        "step": 1.0,
    },
    "Solids": {
        "label": "Solides dissous",
        "min": 0.0,
        "max": 60000.0,
        "step": 100.0,
    },
    "Chloramines": {
        "label": "Chloramines",
        "min": 0.0,
        "max": 15.0,
        "step": 0.1,
    },
    "Sulfate": {
        "label": "Sulfates",
        "min": 0.0,
        "max": 500.0,
        "step": 1.0,
    },
    "Conductivity": {
        "label": "Conductivité",
        "min": 0.0,
        "max": 1000.0,
        "step": 1.0,
    },
    "Organic_carbon": {
        "label": "Carbone organique",
        "min": 0.0,
        "max": 30.0,
        "step": 0.1,
    },
    "Trihalomethanes": {
        "label": "Trihalométhanes",
        "min": 0.0,
        "max": 150.0,
        "step": 0.1,
    },
    "Turbidity": {
        "label": "Turbidité",
        "min": 0.0,
        "max": 10.0,
        "step": 0.1,
    },
}

if "user_session_token" not in st.session_state:
    st.session_state["user_session_token"] = None

if "connected_username" not in st.session_state:
    st.session_state["connected_username"] = None

def get_api_headers() -> dict[str, str]:
    """
    Construit les en-têtes utilisés pour appeler l'API.
    """
    headers = {
        "Authorization": f"Bearer {API_AUTH_TOKEN}",
    }

    user_token = st.session_state.get(
        "user_session_token"
    )

    if user_token:
        headers["X-User-Session"] = user_token

    return headers

HEADERS = get_api_headers()

def display_water_warnings(values: dict[str, float]) -> None:
    warnings = []

    if values["ph"] < 6.5 or values["ph"] > 8.5:
        warnings.append(
            "Le pH est en dehors de la plage recommandée de 6,5 à 8,5."
        )

    if values["Turbidity"] > 1.0:
        warnings.append(
            "La turbidité dépasse 1 NTU."
        )

    if values["Solids"] > 1000.0:
        warnings.append(
            "Les solides dissous dépassent 1 000 mg/L."
        )

    if values["Chloramines"] > 3.0:
        warnings.append(
            "Les chloramines dépassent 3 mg/L."
        )

    if values["Sulfate"] > 500.0:
        warnings.append(
            "Les sulfates dépassent 500 mg/L."
        )

    for warning in warnings:
        st.warning(warning)

    st.info(
        "Ces avertissements sont informatifs et ne remplacent pas "
        "une analyse réglementaire en laboratoire."
    )

st.set_page_config(
    page_title="Water Lab",
    page_icon="💧",
)

st.title("Water Lab")
st.write("Prédiction de la potabilité d'un échantillon d'eau")

prediction_tab, ocr_tab, history_tab = st.tabs(
    [
        "Prédiction",
        "Extraction OCR",
        "Historique",
    ]
)

with history_tab:
    st.subheader("Historique des prédictions")

    if not st.session_state["user_session_token"]:
        st.info(
            "Connectez-vous au compte inovie_lab pour "
            "consulter l'historique."
        )

    else:
        try:
            response = requests.get(
                f"{API_URL}/predictions/history",
                headers=get_api_headers(),
                timeout=10,
            )

            if response.status_code == 401:
                st.session_state[
                    "user_session_token"
                ] = None

                st.session_state[
                    "connected_username"
                ] = None

                st.warning(
                    "La session a expiré. "
                    "Reconnectez-vous."
                )

            else:
                response.raise_for_status()
                history = response.json()

        except requests.RequestException as error:
            st.error(
                "Impossible de charger l'historique : "
                f"{error}"
            )

        else:
            if not history:
                st.info(
                    "Aucune prédiction enregistrée."
                )
            else:
                rows = []

                for item in history:
                    rows.append(
                        {
                            "Date": item["created_at"],
                            "Source": item["source"],
                            "Résultat": item["label"],
                            "Probabilité potable": (
                                item[
                                    "potable_probability"
                                ]
                            ),
                            "pH": item["ph"],
                            "Dureté": item["Hardness"],
                            "Solides dissous": (
                                item["Solids"]
                            ),
                            "Chloramines": (
                                item["Chloramines"]
                            ),
                            "Sulfates": item["Sulfate"],
                            "Conductivité": (
                                item["Conductivity"]
                            ),
                            "Carbone organique": (
                                item["Organic_carbon"]
                            ),
                            "Trihalométhanes": (
                                item["Trihalomethanes"]
                            ),
                            "Turbidité": (
                                item["Turbidity"]
                            ),
                        }
                    )

                st.dataframe(
                    rows,
                    use_container_width=True,
                    hide_index=True,
                )

# ------------------------------------------------------------------
# Prédiction manuelle
# ------------------------------------------------------------------

with prediction_tab:
    st.subheader("Saisie manuelle des mesures")

    ph = st.slider(
        "pH",
        0.0,
        14.0,
        DEFAULT_VALUES["ph"],
        0.1,
    )

    hardness = st.slider(
        "Dureté en mg/L de CaCO₃",
        0.0,
        500.0,
        DEFAULT_VALUES["Hardness"],
        1.0,
    )

    solids = st.slider(
        "Solides dissous en mg/L",
        0.0,
        60000.0,
        DEFAULT_VALUES["Solids"],
        100.0,
    )

    chloramines = st.slider(
        "Chloramines en mg/L",
        0.0,
        15.0,
        DEFAULT_VALUES["Chloramines"],
        0.1,
    )

    sulfate = st.slider(
        "Sulfates en mg/L",
        0.0,
        500.0,
        DEFAULT_VALUES["Sulfate"],
        1.0,
    )

    conductivity = st.slider(
        "Conductivité en µS/cm",
        0.0,
        1000.0,
        DEFAULT_VALUES["Conductivity"],
        1.0,
    )

    organic_carbon = st.slider(
        "Carbone organique en mg/L",
        0.0,
        30.0,
        DEFAULT_VALUES["Organic_carbon"],
        0.1,
    )

    trihalomethanes = st.slider(
        "Trihalométhanes en µg/L",
        0.0,
        150.0,
        DEFAULT_VALUES["Trihalomethanes"],
        0.1,
    )

    turbidity = st.slider(
        "Turbidité en NTU",
        0.0,
        10.0,
        DEFAULT_VALUES["Turbidity"],
        0.1,
    )

    submitted = st.button(
        "Analyser",
        type="primary",
        key="manuel_prediction",
    )

    if submitted:
        if not API_AUTH_TOKEN:
            st.error(
                "Le jeton d'authentification de l'API "
                "n'est pas configuré."
            )
            st.stop()

        payload = {
            "ph": ph,
            "Hardness": hardness,
            "Solids": solids,
            "Chloramines": chloramines,
            "Sulfate": sulfate,
            "Conductivity": conductivity,
            "Organic_carbon": organic_carbon,
            "Trihalomethanes": trihalomethanes,
            "Turbidity": turbidity,
        }

        display_water_warnings(payload)


        try:
            response = requests.post(
            f"{API_URL}/predict",
            params={"source": "manuel"},
            json=payload,
            headers=get_api_headers(),
            timeout=10,
        )

            if response.status_code == 401:
                st.error("Le jeton d'authentification est invalide.")
                st.stop()

            response.raise_for_status()
            prediction_result = response.json()

        except requests.RequestException as error:
            st.error(
                f"Erreur de communication avec l'API : {error}"
            )

        else:
            st.success(
                f"Résultat : {prediction_result['label']}"
            )
            st.metric(
                "Probabilité de potabilité",
                (
                    f"{prediction_result['potable_probability']:.2%}"
                ),
            )

# ------------------------------------------------------------------
# Extraction OCR puis prédiction
# ------------------------------------------------------------------

with ocr_tab:
    st.subheader("Analyser un rapport de laboratoire")

    st.write(
        "Formats acceptés : PDF, PNG et JPEG. "
        "Taille maximale : 1 Mo."
    )

    uploaded_file = st.file_uploader(
        "Sélectionner un rapport de laboratoire",
        type=["pdf", "png", "jpg", "jpeg"],
        accept_multiple_files=False,
        key="ocr_uploaded_file",
    )

    if uploaded_file is not None:
        st.write(
            f"Fichier sélectionné : {uploaded_file.name}"
        )

        if st.button(
            "Extraire les mesures",
            type="primary",
            key="ocr_extract_button",
        ):
            if not API_AUTH_TOKEN:
                st.error(
                    "Le jeton de l'API n'est pas configuré."
                )
                st.stop()

            try:
                with st.spinner(
                    "Extraction des mesures en cours..."
                ):
                    response = requests.post(
                        f"{API_URL}/ocr",
                        headers=get_api_headers(),
                        files={
                            "file": (
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                uploaded_file.type,
                            )
                        },
                        timeout=45,
                    )   

                if response.status_code == 401:
                    st.error(
                        "Le jeton d'authentification est invalide."
                    )
                    st.stop()

                if response.status_code == 413:
                    st.error(
                        "Le fichier dépasse la taille autorisée."
                    )
                    st.stop()

                if response.status_code == 415:
                    st.error(
                        "Le format du fichier n'est pas accepté."
                    )
                    st.stop()

                if response.status_code == 502:
                    detail = response.json().get(
                        "detail",
                        "Le service OCR est indisponible.",
                    )
                    st.error(detail)
                    st.stop()

                response.raise_for_status()
                ocr_result = response.json()

            except requests.Timeout:
                st.error(
                    "Le traitement OCR a dépassé le délai prévu."
                )

            except requests.RequestException as error:
                st.error(
                    "Erreur de communication avec l'API : "
                    f"{error}"
                )

            else:
                extracted_values = ocr_result[
                    "extracted_values"
                ]

                missing_features = []

                for feature, default_value in DEFAULT_VALUES.items():
                    extracted_value = extracted_values.get(feature)

                    if extracted_value is None:
                        selected_value = default_value
                        missing_features.append(feature)
                    else:
                        selected_value = float(extracted_value)

                    st.session_state[
                        f"ocr_{feature}"
                    ] = selected_value

                st.session_state["ocr_completed"] = True
                st.session_state[
                    "ocr_missing_features"
                ] = missing_features
                st.session_state[
                    "ocr_extracted_text"
                ] = ocr_result["extracted_text"]
                st.session_state[
                    "ocr_page_count"
                ] = ocr_result["page_count"]
                st.session_state[
                    "ocr_processing_time_ms"
                ] = ocr_result["processing_time_ms"]

                st.success(
                    "Extraction terminée avec succès."
                )

    if st.session_state.get("ocr_completed", False):
        missing_features = st.session_state.get(
            "ocr_missing_features",
            [],
        )

        if missing_features:
            missing_labels = [
                DISPLAY_LABELS[feature]
                for feature in missing_features
            ]

            st.warning(
                "Toutes les mesures nécessaires n'ont pas été "
                "détectées. Les valeurs suivantes ont été "
                "complétées avec des valeurs par défaut : "
                + ", ".join(missing_labels)
                + ". Vérifiez-les avant de lancer la prédiction."
            )
        else:
            st.success(
                "Les neuf mesures attendues ont été détectées."
            )

        st.write(
            "Nombre de pages traitées : "
            f"{st.session_state.get('ocr_page_count', 0)}"
        )

        processing_time = st.session_state.get(
            "ocr_processing_time_ms"
        )

        if processing_time is not None:
            st.write(
                f"Durée OCR : {processing_time} ms"
            )

        st.subheader("Vérification des mesures")

        slider_values = {}

        for feature, config in SLIDER_CONFIG.items():
            current_value = float(
                st.session_state.get(
                    f"ocr_{feature}",
                    DEFAULT_VALUES[feature],
                )
            )

            current_value = max(
                config["min"],
                min(config["max"], current_value),
            )

            slider_values[feature] = st.slider(
                config["label"],
                min_value=float(config["min"]),
                max_value=float(config["max"]),
                value=current_value,
                step=float(config["step"]),
                key=f"slider_{feature}",
            )

        if st.button(
            "Lancer la prédiction",
            type="primary",
            key="ocr_prediction_button",
        ):
            
            payload = slider_values

            display_water_warnings(payload)

            try:
                with st.spinner(
                    "Calcul de la prédiction..."
                ):
                    response = requests.post(
                    f"{API_URL}/predict",
                    params={"source": "ocr"},
                    json=slider_values,
                    headers=get_api_headers(),
                    timeout=10,
                )

                if response.status_code == 401:
                    st.error(
                        "Le jeton d'authentification est invalide."
                    )
                    st.stop()

                response.raise_for_status()
                prediction_result = response.json()

            except requests.RequestException as error:
                st.error(
                    "Erreur pendant la prédiction : "
                    f"{error}"
                )

            else:
                st.success(
                    f"Résultat : {prediction_result['label']}"
                )

                st.metric(
                    "Probabilité de potabilité",
                    (
                        f"{prediction_result[
                            'potable_probability'
                        ]:.2%}"
                    ),
                )

        with st.expander("Afficher le texte extrait"):
            st.text_area(
                "Texte OCR",
                value=st.session_state.get(
                    "ocr_extracted_text",
                    "",
                ),
                height=300,
                disabled=True,
            )

            st.download_button(
                label="Télécharger le texte extrait",
                data=st.session_state.get(
                    "ocr_extracted_text",
                    "",
                ),
                file_name="texte_ocr.txt",
                mime="text/plain",
            )

with st.sidebar:
    st.header("Session")

    if not st.session_state["user_session_token"]:
        st.info(
            "Mode invité : les prédictions ne sont "
            "pas enregistrées."
        )

        with st.form("login_form"):
            username = st.text_input(
                "Nom du compte",
                value="inovie_lab",
            )

            password = st.text_input(
                "Mot de passe",
                type="password",
            )

            login_submitted = st.form_submit_button(
                "Se connecter"
            )

        if login_submitted:
            try:
                response = requests.post(
                    f"{API_URL}/auth/login",
                    headers={
                        "Authorization": (
                            f"Bearer {API_AUTH_TOKEN}"
                        )
                    },
                    json={
                        "username": username,
                        "password": password,
                    },
                    timeout=10,
                )

                response.raise_for_status()
                login_result = response.json()

            except requests.RequestException:
                st.error(
                    "Identifiants incorrects ou API "
                    "indisponible."
                )

            else:
                st.session_state[
                    "user_session_token"
                ] = login_result["session_token"]

                st.session_state[
                    "connected_username"
                ] = login_result["username"]

                st.rerun()

    else:
        st.success(
            "Connecté : "
            + st.session_state["connected_username"]
        )

        if st.button("Se déconnecter"):
            try:
                requests.post(
                    f"{API_URL}/auth/logout",
                    headers=get_api_headers(),
                    timeout=10,
                )
            finally:
                st.session_state[
                    "user_session_token"
                ] = None

                st.session_state[
                    "connected_username"
                ] = None

                st.rerun()