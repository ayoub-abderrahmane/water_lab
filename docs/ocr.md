Intégration du service OCR.space

1. Objectif

Water Lab permet d’importer un rapport d’analyse d’eau au format PDF ou image afin d’extraire automatiquement les mesures physico-chimiques nécessaires au modèle.

L’OCR réduit la ressaisie manuelle, mais ne remplace pas la validation humaine.

fichier
→ contrôle du format et de la taille
→ envoi à OCR.space
→ récupération du texte
→ parsing des mesures
→ affichage dans des champs modifiables
→ validation humaine
→ prédiction

2. Service retenu

Critère

Valeur utilisée dans le projet

Authentification

Clé API

Coût de développement

Offre gratuite

Taille maximale appliquée

1 Mio par fichier

Pages maximales retenues

3 pages

Quota gratuit documenté dans le projet

500 requêtes par IP et par jour

Formats acceptés par Water Lab

PDF, PNG, JPEG

Expiration du jeton

La clé gratuite utilisée n’a pas de date d’expiration annoncée

Fonction principale

Reconnaissance optique de caractères

Ces limites correspondent au périmètre documenté pour Water Lab et doivent être revérifiées si le fournisseur modifie son offre.

3. Données attendues

ph
Hardness
Solids
Chloramines
Sulfate
Conductivity
Organic_carbon
Trihalomethanes
Turbidity

Libellé du rapport

Champ technique

pH

ph

Dureté

Hardness

Conductivité

Conductivity

Sulfates

Sulfate

Turbidité

Turbidity

4. Contrôles avant l’appel externe

L’API contrôle :

la présence d’un fichier ;

le type MIME ;

l’extension ;

la taille maximale ;

le contenu vide ;

le nombre de pages lorsque cette information est disponible.

Formats autorisés :

application/pdf
image/png
image/jpeg

Taille maximale : 1 Mio.

5. Authentification

OCR_SPACE_API_KEY=...

La clé ne doit pas être écrite dans le code, versionnée dans Git, affichée dans les logs ou renvoyée dans une réponse HTTP.

Exemple .env.example :

OCR_SPACE_API_KEY=

6. Flux technique

Streamlit
→ POST /ocr
→ authentification Bearer
→ validation du fichier
→ service OCR
→ OCR.space
→ texte extrait
→ parseur Water Lab
→ réponse JSON
→ champs Streamlit modifiables

7. Réponse attendue

{
  "page_count": 1,
  "processing_time_ms": 120,
  "extracted_values": {
    "ph": 7.6,
    "Hardness": 253.0,
    "Sulfate": 210.0,
    "Conductivity": 650.0,
    "Turbidity": 0.7,
    "Chloramines": null
  }
}

Une valeur absente n’est jamais inventée.

8. Validation humaine

L’utilisateur peut corriger une valeur mal lue, compléter une valeur absente, vérifier les unités, annuler l’opération et lancer la prédiction uniquement après vérification.

9. Gestion des erreurs

Cas

Réponse attendue

Fichier absent

HTTP 400

Fichier vide

HTTP 400

Format non supporté

HTTP 415

Fichier supérieur à 1 Mio

HTTP 413

Clé OCR absente

Erreur de configuration

Service OCR indisponible

HTTP 502

Réponse illisible

Message d’erreur contrôlé

Valeurs incomplètes

Champs à null et correction manuelle

La saisie manuelle reste disponible si OCR.space est indisponible.

10. Tests automatisés

Test de taille maximale

def test_ocr_rejects_file_larger_than_one_mebibyte() -> None:
    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "rapport.pdf",
                b"x" * (1024 * 1024 + 1),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413

Test avec monkeypatch

def test_ocr_returns_text_and_extracted_values(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_result = SimpleNamespace(
        text="pH : 7,6\nConductivité : 650",
        page_count=1,
        processing_time_ms=120,
    )

    monkeypatch.setattr(
        "src.api.extract_text_from_file",
        lambda **kwargs: fake_result,
    )

    response = client.post(
        "/ocr",
        headers=AUTH_HEADERS,
        files={
            "file": (
                "rapport.png",
                b"image-factice",
                "image/png",
            )
        },
    )

    assert response.status_code == 200
    assert response.json()["extracted_values"]["ph"] == 7.6

monkeypatch rend le test rapide, reproductible, indépendant du réseau et sans consommation du quota.

11. Sécurité

route protégée par Bearer token ;

clé OCR stockée dans l’environnement ;

taille et type des fichiers contrôlés ;

fichiers non conservés après traitement ;

texte OCR complet non sauvegardé ;

erreurs externes transformées en réponses contrôlées ;

aucune clé dans les logs ;

validation humaine avant prédiction.

12. Sobriété

appel OCR uniquement à la demande ;

limite de taille à 1 Mio ;

nombre de pages limité ;

absence de stockage du fichier ;

absence de stockage du texte intégral ;

saisie manuelle disponible ;

tests simulés sans appel externe.

13. Procédure d’utilisation

ouvrir l’application ;

choisir l’import OCR ;

sélectionner un PDF, PNG ou JPEG ;

vérifier la limite de taille ;

lancer l’extraction ;

lire les valeurs détectées ;

corriger les erreurs ;

compléter les valeurs absentes ;

lancer la prédiction ;

consulter le résultat.

14. Limites connues

qualité dépendante du document source ;

erreurs possibles sur les scans flous ;

mise en page variable ;

unités parfois à convertir ;

dépendance à un service externe ;

quota gratuit limité ;

validation humaine obligatoire.