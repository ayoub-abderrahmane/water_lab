# Water Lab

## 1. Présentation du projet

Water Lab est un projet réalisé dans le cadre d’un bachelor en développement en intelligence artificielle.

L’objectif est de développer une application capable d’estimer la potabilité d’un échantillon d’eau à partir de neuf mesures physico-chimiques.

Le projet comprend actuellement :

- un pipeline de préparation des données ;
- un modèle de classification XGBoost ;
- une API REST développée avec FastAPI ;
- une interface utilisateur développée avec Streamlit ;
- un suivi des expérimentations avec MLflow ;
- un monitoring applicatif avec Prometheus et Grafana ;
- une conteneurisation avec Docker Compose ;
- une journalisation des principales étapes de préparation, d’entraînement et de prédiction.

Le projet est développé sous WSL2.

## 2. Besoin du commanditaire

Le besoin identifié est de fournir à un laboratoire ou à une structure chargée du contrôle de la qualité de l’eau un outil simple permettant :

- de saisir les mesures physico-chimiques d’un échantillon ;
- d’obtenir rapidement une estimation de sa potabilité ;
- de consulter le résultat et la probabilité calculée par le modèle ;
- de suivre le fonctionnement technique du service ;
- de préparer l’intégration future du stockage des analyses ;
- de préparer l’intégration future d’un service OCR pour extraire automatiquement les informations de rapports de laboratoire.

L’application ne remplace pas une analyse réglementaire réalisée en laboratoire. Elle constitue un outil d’aide à l’analyse basé sur un modèle de Machine Learning.

## 3. Architecture actuelle

L’architecture actuelle comprend :

- une interface Streamlit pour saisir les mesures ;
- une API FastAPI pour exposer le modèle ;
- une authentification par jeton Bearer ;
- un modèle XGBoost sérialisé avec Joblib ;
- un serveur MLflow pour suivre les paramètres, métriques et artefacts ;
- Prometheus pour collecter les métriques de l’API ;
- Grafana pour visualiser les indicateurs ;
- PostgreSQL dans l’environnement Docker, sans utilisation applicative à ce stade.

Flux principal :

```text
Utilisateur
    |
    v
Interface Streamlit
    |
    v
Requête HTTP authentifiée
    |
    v
API FastAPI
    |
    v
Pipeline de prétraitement
    |
    v
Modèle XGBoost
    |
    v
Classe prédite et probabilité de potabilité
```

## 4. Jeu de données

### 4.1 Composition

Le jeu de données contient :

- 3 276 observations ;
- 9 caractéristiques physico-chimiques ;
- une cible binaire nommée `Potability`.

Les variables utilisées sont :

- `ph` : niveau de pH ;
- `Hardness` : dureté de l’eau ;
- `Solids` : quantité de solides dissous ;
- `Chloramines` : concentration en chloramines ;
- `Sulfate` : concentration en sulfates ;
- `Conductivity` : conductivité ;
- `Organic_carbon` : quantité de carbone organique ;
- `Trihalomethanes` : concentration en trihalométhanes ;
- `Turbidity` : turbidité.

La cible prend deux valeurs :

- `0` : eau considérée comme non potable ;
- `1` : eau considérée comme potable.

Le fichier doit être placé dans :

```text
data/raw/water_potability.csv
```

### 4.2 Valeurs manquantes

Le jeu de données contient des valeurs manquantes, notamment dans les colonnes suivantes :

- `ph` ;
- `Sulfate` ;
- `Trihalomethanes`.

Ces valeurs ne sont pas remplacées directement dans le fichier nettoyé.

L’imputation est intégrée dans le pipeline Scikit-learn et exécutée après la séparation entre les jeux d’entraînement et de test.

La stratégie utilisée est :

```python
SimpleImputer(
    strategy="median",
    add_indicator=True,
)
```

La médiane est utilisée car elle est moins sensible aux valeurs extrêmes que la moyenne.

### 4.3 Préparation des données

Le script de prétraitement vérifie :

- la présence du fichier CSV ;
- la présence des colonnes attendues ;
- la conversion des colonnes en valeurs numériques ;
- l’absence de valeurs manquantes dans la cible ;
- la présence exclusive des valeurs `0` et `1` dans la cible ;
- le nombre de valeurs manquantes restantes.

Les doublons sont comptabilisés dans les logs, mais ne sont pas supprimés automatiquement.

Le fichier nettoyé est enregistré dans :

```text
data/processed/water_potability_clean.csv
```

## 5. Cible et métriques d’évaluation

L’objectif métier principal est de détecter les échantillons potentiellement non potables.

La classe métier prioritaire est :

```text
0 = non potable
```

Une erreur critique consiste à prédire qu’un échantillon est potable alors qu’il est réellement non potable.

Le rappel de la classe `0` permet de mesurer la proportion d’échantillons réellement non potables correctement détectés.

Exemple :

```python
recall_non_potable = recall_score(
    y_test,
    predictions,
    pos_label=0,
    zero_division=0,
)
```

Les métriques actuellement suivies sont :

- accuracy ;
- precision ;
- recall de la classe `1` ;
- F1-score ;
- ROC-AUC.

Les améliorations prévues sont :

- ajout du recall de la classe `0` ;
- ajout de la matrice de confusion ;
- suivi du nombre d’eaux non potables classées à tort comme potables ;
- étude d’un seuil de décision adapté au risque métier.

## 6. Prérequis

Le projet nécessite :

- Git ;
- Docker ;
- Docker Compose ;
- WSL2 sous Windows dans l’environnement de développement actuel.

Pour une exécution locale hors Docker :

- Python 3.12 ;
- `uv`.

## 7. Installation

### 7.1 Cloner le projet

```bash
git clone <URL_DU_DEPOT>
cd water_lab
```

### 7.2 Préparer le jeu de données

Placer le fichier CSV dans :

```text
data/raw/water_potability.csv
```

### 7.3 Préparer le modèle

Le modèle utilisé par l’API doit être présent dans :

```text
models/water_xgboost_pipeline.joblib
```

S’il n’existe pas, lancer :

```bash
uv run python -m src.train
```

### 7.4 Créer le fichier `.env`

Créer un fichier `.env` à la racine du projet :

```env
API_AUTH_TOKEN=remplacer_par_un_jeton_securise
```

Générer un jeton avec :

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Le fichier `.env` ne doit pas être versionné.

Ajouter dans `.gitignore` :

```gitignore
.env
```

## 8. Configuration du jeton Prometheus

La route `/metrics` est protégée par le même jeton Bearer que les autres routes sécurisées de l’API.

Créer le fichier suivant :

```text
monitoring/prometheus_token.txt
```

Le fichier doit contenir uniquement le jeton, sans le préfixe `Bearer`.

Exemple :

```text
abc123
```

La valeur doit être strictement identique à celle déclarée dans `.env` :

```env
API_AUTH_TOKEN=abc123
```

Le fichier `monitoring/prometheus_token.txt` contient une donnée sensible.

Ajouter dans `.gitignore` :

```gitignore
monitoring/prometheus_token.txt
```

Si le fichier a déjà été ajouté à Git :

```bash
git rm --cached monitoring/prometheus_token.txt
```

Dans `monitoring/prometheus.yml`, Prometheus lit le jeton avec :

```yaml
authorization:
  type: Bearer
  credentials_file: /etc/prometheus/api_token
```

Dans `docker-compose.yml`, le fichier est monté en lecture seule :

```yaml
volumes:
  - ./monitoring/prometheus_token.txt:/etc/prometheus/api_token:ro
```

## 9. Démarrage de l’application

Construire et démarrer les services :

```bash
docker compose up -d --build
```

Vérifier l’état des conteneurs :

```bash
docker compose ps
```

Services disponibles :

- API FastAPI : `http://localhost:8000`
- Documentation Swagger : `http://localhost:8000/docs`
- Interface Streamlit : `http://localhost:8501`
- MLflow : `http://localhost:5000`
- Prometheus : `http://localhost:9090`
- Grafana : `http://localhost:3000`

Arrêter les services :

```bash
docker compose down
```

Supprimer également les volumes :

```bash
docker compose down -v
```

Attention : cette dernière commande supprime les données persistantes associées aux volumes Docker.

## 10. Utilisation de Streamlit

Ouvrir :

```text
http://localhost:8501
```

L’interface permet de saisir les neuf mesures physico-chimiques d’un échantillon.

Après validation du formulaire, Streamlit envoie une requête HTTP à FastAPI.

Le résultat contient :

- la classe prédite ;
- le libellé `potable` ou `non potable` ;
- la probabilité estimée pour la classe potable.

L’authentification entre Streamlit et FastAPI est actuellement automatique grâce au jeton configuré côté serveur.

## 11. Utilisation de l’API

### 11.1 Vérifier l’état du service

Route :

```http
GET /health
```

Commande :

```bash
curl http://localhost:8000/health
```

Réponse attendue :

```json
{
  "status": "healthy",
  "model": "loaded"
}
```

Cette route est publique.

### 11.2 Consulter les informations du modèle

Route :

```http
GET /model/info
```

Commande :

```bash
curl   -H "Authorization: Bearer VOTRE_JETON"   http://localhost:8000/model/info
```

Exemple de réponse :

```json
{
  "name": "XGBoost Water Potability",
  "version": "0.1.0",
  "imputation": "median"
}
```

### 11.3 Lancer une prédiction

Route :

```http
POST /predict
```

Commande :

```bash
curl -X POST   http://localhost:8000/predict   -H "Authorization: Bearer VOTRE_JETON"   -H "Content-Type: application/json"   -d '{
    "ph": 7.2,
    "Hardness": 190,
    "Solids": 21000,
    "Chloramines": 7,
    "Sulfate": 330,
    "Conductivity": 420,
    "Organic_carbon": 14,
    "Trihalomethanes": 65,
    "Turbidity": 4
  }'
```

Exemple de réponse :

```json
{
  "predicted_class": 0,
  "label": "non potable",
  "potable_probability": 0.3271
}
```

La probabilité correspond à la probabilité estimée par le modèle pour la classe `1`, c’est-à-dire la classe potable.

### 11.4 Codes de réponse principaux

- `200` : requête traitée avec succès ;
- `401` : jeton absent ou invalide ;
- `405` : mauvaise méthode HTTP ;
- `422` : données d’entrée invalides ;
- `500` : erreur interne ;
- `503` : modèle indisponible.

## 12. Utilisation de MLflow

MLflow est utilisé pour suivre :

- les paramètres XGBoost ;
- la stratégie d’imputation ;
- la taille du jeu de données ;
- les métriques d’évaluation ;
- le modèle sérialisé ;
- le fichier de données nettoyé.

Ouvrir :

```text
http://localhost:5000
```

L’expérience utilisée est :

```text
water_lab_xgboost
```

## 13. Utilisation de Prometheus

Prometheus collecte les métriques exposées par FastAPI sur :

```http
GET /metrics
```

Ouvrir Prometheus :

```text
http://localhost:9090
```

Vérifier les cibles :

```text
http://localhost:9090/targets
```

La cible `water_lab_api` doit être en état `UP`.

Métriques disponibles :

```promql
water_lab_api_requests_total
```

```promql
water_lab_api_request_duration_seconds
```

```promql
water_lab_predictions_total
```

```promql
water_lab_prediction_errors_total
```

```promql
water_lab_missing_input_values_total
```

```promql
water_lab_model_loaded
```

Exemple de débit de requêtes :

```promql
sum(
  rate(
    water_lab_api_requests_total[5m]
  )
)
```

Exemple d’erreurs serveur :

```promql
sum(
  rate(
    water_lab_api_requests_total{
      status_code=~"5.."
    }[5m]
  )
)
```

## 14. Utilisation de Grafana

Ouvrir Grafana :

```text
http://localhost:3000
```

La source de données Prometheus doit utiliser l’adresse interne Docker :

```text
http://prometheus:9090
```

Ne pas utiliser :

```text
http://localhost:9090
```

Indicateurs à afficher en priorité :

- nombre de requêtes ;
- requêtes par seconde ;
- erreurs HTTP ;
- temps de réponse ;
- nombre de prédictions ;
- répartition des classes prédites ;
- disponibilité du modèle.

## 15. Logs

Le projet utilise le module Python `logging`.

Des logs sont présents dans :

- `preprocessing.py` ;
- `train.py` ;
- `model.py` ;
- `api.py`.

Ils permettent de suivre :

- le chargement du jeu de données ;
- les anomalies de colonnes ;
- les valeurs manquantes ;
- le démarrage et la fin de l’entraînement ;
- les métriques principales ;
- la sauvegarde du modèle ;
- le chargement du modèle ;
- les prédictions ;
- les erreurs HTTP et internes.

Consulter les logs de l’API :

```bash
docker compose logs api
```

Suivre les logs en direct :

```bash
docker compose logs -f api
```

Exécuter le prétraitement :

```bash
uv run python -m src.preprocessing
```

Lancer l’entraînement :

```bash
uv run python -m src.train
```

## 16. Sécurité

L’application utilise actuellement un jeton Bearer unique.

Les fichiers suivants doivent rester locaux :

```text
.env
monitoring/prometheus_token.txt
```

Le fichier `.gitignore` doit contenir au minimum :

```gitignore
.env
monitoring/prometheus_token.txt
__pycache__/
*.pyc
.venv/
mlruns/
logs/
```

Un fichier `.env.example` peut être versionné :

```env
API_AUTH_TOKEN=
```

Ne jamais versionner une vraie clé API.

## 17. Limites actuelles

À ce stade :

- l’application utilise un jeton Bearer unique ;
- Streamlit transmet automatiquement ce jeton à FastAPI ;
- il n’existe pas encore de gestion multi-clients ;
- PostgreSQL est démarré mais n’est pas encore utilisé par l’application ;
- l’intégration OCR n’est pas encore développée ;
- les prélèvements ne sont pas encore historisés ;
- les tests automatisés ne sont pas encore finalisés ;
- la CI/CD n’est pas encore mise en place ;
- les alertes Grafana ne sont pas encore configurées ;
- le modèle fournit une estimation statistique et ne remplace pas une validation réglementaire en laboratoire.

## 18. Accessibilité de la documentation

Cette documentation applique les principes suivants :

- hiérarchie régulière des titres ;
- phrases courtes ;
- listes structurées ;
- absence d’information transmise uniquement par la couleur ;
- absence d’emoji décoratif ;
- commandes isolées dans des blocs de code ;
- vocabulaire technique accompagné d’un contexte ;
- structure compatible avec la navigation au clavier et les lecteurs d’écran.