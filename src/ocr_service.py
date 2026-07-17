import logging
import os
import time
from dataclasses import dataclass

import requests

logger = logging.getLogger(__name__)

OCR_SPACE_URL = "https://api.ocr.space/parse/image"
OCR_SPACE_API_KEY = os.getenv("OCR_SPACE_API_KEY")

OCR_TIMEOUT_SECONDS = 30


@dataclass
class OCRResult:
    text: str
    processing_time_ms: int | None
    page_count: int


class OCRError(Exception):
    """
    Erreur métier déclenchée lorsque le traitement OCR échoue.
    """


def extract_text_from_file(
    file_content: bytes,
    filename: str,
    content_type: str,
) -> OCRResult:
    """
    Envoie un document à OCR.space et retourne le texte extrait.
    """
    if not OCR_SPACE_API_KEY:
        logger.error("La clé OCR.space n'est pas configurée")
        raise OCRError(
            "La clé OCR.space n'est pas configurée sur le serveur."
        )

    start_time = time.perf_counter()

    try:
        response = requests.post(
            OCR_SPACE_URL,
            headers={
                "apikey": OCR_SPACE_API_KEY,
            },
            files={
                "file": (
                    filename,
                    file_content,
                    content_type,
                ),
            },
            data={
                "language": "fre",
                "isOverlayRequired": "false",
                "OCREngine": "2",
            },
            timeout=OCR_TIMEOUT_SECONDS,
        )

        response.raise_for_status()

    except requests.Timeout as error:
        logger.warning(
            "Délai OCR.space dépassé | fichier=%s",
            filename,
        )
        raise OCRError(
            "Le service OCR n'a pas répondu dans le délai prévu."
        ) from error

    except requests.RequestException as error:
        logger.exception(
            "Erreur de communication avec OCR.space | fichier=%s",
            filename,
        )
        raise OCRError(
            "Impossible de communiquer avec le service OCR."
        ) from error

    try:
        payload = response.json()
    except ValueError as error:
        logger.error(
            "Réponse OCR.space non JSON | fichier=%s",
            filename,
        )
        raise OCRError(
            "Le service OCR a retourné une réponse invalide."
        ) from error

    if payload.get("IsErroredOnProcessing"):
        error_message = payload.get("ErrorMessage")

        if isinstance(error_message, list):
            error_message = " ".join(
                str(message)
                for message in error_message
            )

        logger.warning(
            "Traitement OCR refusé | fichier=%s | erreur=%s",
            filename,
            error_message,
        )

        raise OCRError(
            error_message
            or "Le traitement OCR a échoué."
        )

    parsed_results = payload.get("ParsedResults") or []

    extracted_pages = []

    for parsed_result in parsed_results:
        parsed_text = parsed_result.get("ParsedText")

        if parsed_text:
            extracted_pages.append(parsed_text.strip())

    extracted_text = "\n\n".join(extracted_pages).strip()

    if not extracted_text:
        logger.warning(
            "Aucun texte extrait | fichier=%s",
            filename,
        )
        raise OCRError(
            "Aucun texte exploitable n'a été détecté."
        )

    duration_ms = int(
        (time.perf_counter() - start_time) * 1000
    )

    processing_time = payload.get(
        "ProcessingTimeInMilliseconds"
    )

    try:
        processing_time_ms = int(
            float(processing_time)
        )
    except (TypeError, ValueError):
        processing_time_ms = duration_ms

    logger.info(
        "OCR terminé | fichier=%s | pages=%s | durée_ms=%s",
        filename,
        len(extracted_pages),
        duration_ms,
    )

    return OCRResult(
        text=extracted_text,
        processing_time_ms=processing_time_ms,
        page_count=len(extracted_pages),
    )