import re


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


def normalize_number(value: str) -> float:
    """
    Convertit un nombre issu de l'OCR en nombre Python.

    Exemple :
    7,6 devient 7.6.
    """
    cleaned_value = value.replace(" ", "").replace(",", ".")
    return float(cleaned_value)


def extract_value(
    text: str,
    patterns: list[str],
) -> float | None:
    """
    Retourne la première valeur trouvée parmi plusieurs expressions.
    """
    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if match:
            return normalize_number(match.group(1))

    return None


def parse_water_report(
    extracted_text: str,
) -> dict[str, float | None]:
    """
    Extrait les neuf variables attendues par le modèle.

    Une variable absente du document reçoit la valeur None.
    """
    ph = extract_value(
        extracted_text,
        [
            r"\bpH\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    hardness = extract_value(
        extracted_text,
        [
            r"Duret[ée]\s*:\s*([0-9]+(?:[.,][0-9]+)?)\s*°?\s*f",
            r"Hardness\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    # Conversion des degrés français en mg/L de CaCO3.
    if hardness is not None and re.search(
        r"Duret[ée].*?°?\s*f",
        extracted_text,
        flags=re.IGNORECASE,
    ):
        hardness *= 10

    solids = extract_value(
        extracted_text,
        [
            r"Solides?\s+dissous\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Total\s+dissolved\s+solids\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
            r"\bTDS\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"\bSolids\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    chloramines = extract_value(
        extracted_text,
        [
            r"Chloramines?\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Chloramine\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    sulfate = extract_value(
        extracted_text,
        [
            r"Sulfates?\s*(?:\(SO4[-–—]*\))?\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
            r"\bSulfate\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    conductivity = extract_value(
        extracted_text,
        [
            r"Conductivit[ée]\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Conductivity\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    organic_carbon = extract_value(
        extracted_text,
        [
            r"Carbone\s+organique\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
            r"Carbone\s+organique\s+total\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
            r"\bTOC\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Organic\s+carbon\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    trihalomethanes = extract_value(
        extracted_text,
        [
            r"Trihalom[ée]thanes?\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
            r"\bTHM\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Trihalomethanes?\s*:\s*"
            r"([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    turbidity = extract_value(
        extracted_text,
        [
            r"Turbidit[ée]\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
            r"Turbidity\s*:\s*([0-9]+(?:[.,][0-9]+)?)",
        ],
    )

    return {
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