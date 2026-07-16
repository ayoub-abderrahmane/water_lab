# Documentation technique — Water Lab

## 1. Objectif actuel

Water Lab est une application de prédiction de la potabilité de l'eau à partir de neuf mesures physico-chimiques.

À ce stade, le projet permet de :

- préparer le jeu de données ;
- entraîner un modèle XGBoost ;
- suivre les expériences avec MLflow ;
- exposer le modèle avec FastAPI ;
- saisir des mesures depuis une interface Streamlit ;
- exécuter les services avec Docker Compose ;
- exposer des métriques Prometheus et les consulter dans Grafana ;
- produire des logs lors du prétraitement, de l'entraînement et des prédictions.

## 2. Architecture actuelle

```text
Utilisateur
   |
   v
Streamlit
   |
   | requête HTTP POST /predict
   v
FastAPI
   |
   v
Pipeline scikit-learn
   |- imputation médiane
   |- indicateurs de valeurs manquantes
   `- modèle XGBoost

FastAPI -- /metrics --> Prometheus --> Grafana
Entraînement --------> MLflow
Docker Compose ------> orchestration des services
```

Services actuellement présents :

| Service | Rôle | Port local |
|---|---|---:|
| FastAPI | Exposition du modèle | 8000 |
| Streamlit | Interface utilisateur | 8501 |
| MLflow | Suivi des expériences | 5000 |
| Prometheus | Collecte des métriques | 9090 |
| Grafana | Visualisation des métriques | 3000 |
| PostgreSQL | Base prévue pour la suite du projet | 5432 |

PostgreSQL est démarré mais n'est pas encore utilisé par l'application.

## 3. Prétraitement des données

Fichier principal : `src/preprocessing.py`.

Traitements réalisés :

1. vérification de l'existence du fichier CSV ;
2. contrôle des colonnes attendues ;
3. conversion des colonnes en valeurs numériques ;
4. suppression des lignes dont la cible `Potability` est manquante ;
5. contrôle de la cible, limitée aux valeurs `0` et `1` ;
6. conservation des valeurs manquantes dans les variables explicatives ;
7. enregistrement du jeu nettoyé dans `data/processed/`.

Les valeurs manquantes des variables explicatives ne sont pas imputées dans ce fichier. L'imputation est réalisée dans le pipeline après la séparation entre les jeux d'entraînement et de test afin d'éviter une fuite de données.

Les doublons sont comptés mais ne sont pas supprimés.

Commande :

```bash
uv run python -m src.preprocessing
```

## 4. Entraînement du modèle

Fichier principal : `src/train.py`.

Étapes :

1. chargement et contrôle des données ;
2. séparation des variables explicatives et de la cible ;
3. séparation entraînement/test en 80/20 avec stratification ;
4. entraînement du pipeline ;
5. calcul des métriques ;
6. enregistrement des paramètres, métriques et artefacts dans MLflow ;
7. sauvegarde du pipeline avec Joblib.

Pipeline utilisé :

- `SimpleImputer(strategy="median", add_indicator=True)` ;
- `XGBClassifier`.

Derniers résultats obtenus :

| Métrique | Valeur |
|---|---:|
| Accuracy | 0,6143 |
| Precision | 0,5068 |
| Recall | 0,4375 |
| F1-score | 0,4696 |
| ROC-AUC | 0,6337 |

Ces résultats montrent que le modèle fonctionne, mais que ses performances restent modérées, notamment pour la détection de la classe potable.

Commande :

```bash
uv run python -m src.train
```

## 5. Suivi avec MLflow

MLflow conserve :

- les paramètres XGBoost ;
- la stratégie d'imputation ;
- la taille du jeu de données ;
- les métriques d'évaluation ;
- le fichier nettoyé ;
- le pipeline Joblib ;
- le modèle sérialisé au format Cloudpickle.

Interface locale :

```text
http://localhost:5000
```

MLflow est actuellement configuré avec une base SQLite.

## 6. API FastAPI

Fichier principal : `src/api.py`.

Routes disponibles :

| Méthode | Route | Fonction |
|---|---|---|
| GET | `/health` | Vérifie la disponibilité du modèle |
| GET | `/model/info` | Retourne les informations principales du modèle |
| POST | `/predict` | Exécute une prédiction |
| GET | `/metrics/` | Expose les métriques Prometheus |

Documentation Swagger :

```text
http://localhost:8000/docs
```

La route `/metrics` est montée comme une sous-application ASGI. Elle peut ne pas apparaître dans Swagger et être accessible avec une barre finale :

```text
http://localhost:8000/metrics/
```

## 7. Interface Streamlit

L'interface Streamlit collecte les neuf mesures attendues puis appelle la route `POST /predict` de FastAPI.

Elle ne charge pas directement le modèle. Cette séparation permet de conserver FastAPI comme point d'accès unique au modèle.

Interface locale :

```text
http://localhost:8501
```

## 8. Monitoring applicatif

### Prometheus

Prometheus interroge régulièrement la route `/metrics/` et stocke les séries temporelles.

Métriques actuellement exposées :

- nombre de requêtes HTTP ;
- durée des requêtes ;
- nombre de prédictions ;
- nombre d'erreurs de prédiction ;
- nombre de valeurs manquantes reçues ;
- état de chargement du modèle.

Interface locale :

```text
http://localhost:9090
```

Vérification de la cible :

```text
http://localhost:9090/targets
```

### Grafana

Grafana utilise Prometheus comme source de données.

URL de la source depuis le conteneur Grafana :

```text
http://prometheus:9090
```

Interface locale :

```text
http://localhost:3000
```

Les indicateurs à afficher en priorité sont :

- débit de requêtes ;
- erreurs HTTP ;
- temps de réponse ;
- répartition des prédictions.

## 9. Logs applicatifs

Des logs ont été ajoutés dans :

- `src/preprocessing.py` ;
- `src/train.py` ;
- `src/model.py` ;
- `src/api.py`.

Ils permettent de suivre :

- les erreurs de lecture ou de validation du CSV ;
- les anomalies dans la cible ;
- le démarrage et la fin de l'entraînement ;
- les métriques principales ;
- la sauvegarde et le chargement du modèle ;
- les valeurs manquantes reçues ;
- les prédictions et les erreurs associées ;
- les requêtes HTTP traitées par l'API.

Exécution locale :

```bash
uv run python -m src.preprocessing
uv run python -m src.train
```

Consultation des logs de l'API dans Docker :

```bash
docker compose logs -f api
```

Prometheus sert à détecter une anomalie numérique. Les logs servent ensuite à identifier sa cause.

## 10. Exécution avec Docker

Lancer tous les services :

```bash
docker compose up -d --build
```

Vérifier leur état :

```bash
docker compose ps
```

Arrêter les services :

```bash
docker compose down
```

Le code étant copié dans l'image, une reconstruction est nécessaire après une modification, sauf si un volume de développement et le mode `--reload` sont utilisés.

## 11. Limites actuelles

Les éléments suivants ne sont pas encore réalisés :

- authentification par clé API ;
- persistance des prélèvements dans PostgreSQL ;
- routes de gestion des clients et prélèvements ;
- intégration d'OCR.space ;
- tests automatisés ;
- intégration continue avec GitHub Actions ;
- alertes Grafana ;
- dashboard Grafana finalisé et exporté ;
- scénario d'incident documenté ;
- livraison continue.