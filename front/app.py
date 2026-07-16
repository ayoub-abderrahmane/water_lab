import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://api:8000")

st.set_page_config(
    page_title="Water Lab",
    page_icon="💧",
)

st.title("Water Lab")
st.write("Prédiction de la potabilité d'un échantillon d'eau")

with st.form("prediction_form"):
    ph = st.number_input("pH", value=7.0)
    hardness = st.number_input("Dureté", value=190.0)
    solids = st.number_input("Solides dissous", value=21000.0)
    chloramines = st.number_input("Chloramines", value=7.0)
    sulfate = st.number_input("Sulfates", value=330.0)
    conductivity = st.number_input("Conductivité", value=420.0)
    organic_carbon = st.number_input("Carbone organique", value=14.0)
    trihalomethanes = st.number_input("Trihalométhanes", value=65.0)
    turbidity = st.number_input("Turbidité", value=4.0)

    submitted = st.form_submit_button("Analyser")

if submitted:
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

    try:
        response = requests.post(
            f"{API_URL}/predict",
            json=payload,
            timeout=10,
        )
        response.raise_for_status()
        result = response.json()

        st.success(f"Résultat : {result['label']}")
        st.metric(
            "Probabilité de potabilité",
            f"{result['potable_probability']:.2%}",
        )
    except requests.RequestException as error:
        st.error(f"Erreur de communication avec l'API : {error}")