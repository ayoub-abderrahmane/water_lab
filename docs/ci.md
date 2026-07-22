Chaîne d’intégration et de livraison continues

1. Objectif

La chaîne CI/CD de Water Lab automatise les contrôles techniques réalisés lors du versionnement des sources.

Elle permet de :

recréer un environnement Python propre ;

installer les dépendances verrouillées ;

exécuter les tests automatisés ;

calculer la couverture du code ;

entraîner et valider le modèle ;

publier le modèle entraîné comme artefact ;

construire l’image Docker de l’application ;

vérifier que l’image est exploitable ;

préparer un livrable prêt à être déployé.

La chaîne ne remplace pas la revue humaine. Elle sert de porte de contrôle avant la fusion dans main et avant toute livraison.

2. Outils utilisés

Outil

Rôle

GitHub

Hébergement du dépôt distant

GitHub Actions

Exécution de la chaîne CI/CD

YAML

Description du workflow

uv

Installation de Python et des dépendances

Pytest

Exécution des tests

pytest-cov

Calcul de la couverture

Joblib

Sérialisation du modèle

Docker

Packaging de l’application

actions/upload-artifact

Publication des rapports et modèles

GitHub Actions a été retenu car il est directement intégré au dépôt GitHub du projet, conserve l’historique des exécutions et permet de versionner la configuration avec le code.

3. Fichier de configuration

Le workflow est stocké dans :

.github/workflows/continuous-delivery.yml

4. Déclencheurs

on:
  push:
    branches:
      - main
      - develop

  pull_request:
    branches:
      - main

  workflow_dispatch:

Déclencheur

Objectif

Push sur develop

Contrôler les développements en cours

Push sur main

Valider la branche principale

Pull request vers main

Tester avant fusion

Déclenchement manuel

Relancer la chaîne à la demande

5. Organisation des jobs

validate-and-test
        ↓
train-and-validate
        ↓
package
        ↓
deploy

Chaque job dépend du précédent grâce à needs. Si un job échoue, les jobs suivants ne sont pas exécutés.

6. Job de validation et de test

Ce job récupère le dépôt, installe uv, installe Python 3.12, installe les dépendances, configure les variables de test, exécute les tests, génère un rapport de couverture et publie ce rapport comme artefact.

validate-and-test:
  name: Valider les données et tester l’application
  runs-on: ubuntu-latest

  steps:
    - name: Récupérer le dépôt
      uses: actions/checkout@v4

    - name: Installer uv
      uses: astral-sh/setup-uv@v5
      with:
        enable-cache: true

    - name: Installer Python
      run: uv python install 3.12

    - name: Installer les dépendances
      run: uv sync --locked --dev

    - name: Exécuter les tests
      env:
        API_AUTH_TOKEN: test-token
        DATABASE_URL: sqlite+pysqlite:///./test_water_lab.db
      run: |
        uv run pytest tests \
          -v \
          --cov=src \
          --cov-report=term-missing \
          --cov-report=html

    - name: Publier le rapport de couverture
      if: always()
      uses: actions/upload-artifact@v4
      with:
        name: rapport-couverture
        path: htmlcov/
        if-no-files-found: ignore

Les variables de test évitent d’utiliser les secrets ou la base de données de l’environnement réel.

7. Job d’entraînement et de validation

uv run python -m src.train

Le script charge et nettoie le dataset, entraîne le pipeline XGBoost, calcule les métriques, vérifie les seuils minimaux, sauvegarde le modèle et journalise l’expérience dans MLflow.

Seuils actuels :

Accuracy minimale : 0,55
ROC-AUC minimal : 0,58

Le fichier attendu est :

models/water_xgboost_pipeline.joblib

8. Packaging Docker

package:
  name: Construire l’image Docker
  runs-on: ubuntu-latest
  needs: train-and-validate

  steps:
    - name: Récupérer le dépôt
      uses: actions/checkout@v4

    - name: Construire l’image Docker
      run: |
        docker build \
          -t water-lab-api:${{ github.sha }} \
          .

    - name: Vérifier l’image
      run: |
        docker image inspect \
          water-lab-api:${{ github.sha }}

Le SHA relie l’image à une version exacte du code.

9. Conservation de l’image Docker

- name: Exporter l’image Docker
  run: |
    docker save \
      --output water-lab-api.tar \
      water-lab-api:${{ github.sha }}

- name: Publier l’image Docker
  uses: actions/upload-artifact@v4
  with:
    name: image-docker-water-lab
    path: water-lab-api.tar
    if-no-files-found: error
    retention-days: 30

Chargement local :

docker load --input water-lab-api.tar
docker image ls water-lab-api

10. Livraison et déploiement

Dans la version actuelle :

tests validés
→ modèle validé
→ image Docker construite
→ artefacts publiés
→ fusion dans main
→ livrable prêt à être déployé

La construction d’une image Docker ne signifie pas qu’un déploiement distant a eu lieu. Un véritable déploiement nécessite le transfert de l’image, le lancement du conteneur sur une cible, la configuration des variables et la vérification de /health.

11. Exécution locale

uv sync --locked --dev

API_AUTH_TOKEN=test-token \
DATABASE_URL=sqlite+pysqlite:///./test_water_lab.db \
uv run pytest tests -v

API_AUTH_TOKEN=test-token \
DATABASE_URL=sqlite+pysqlite:///./test_water_lab.db \
uv run pytest tests \
  -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html

Le rapport HTML est créé dans htmlcov/index.html.

12. Consultation des résultats

Dans GitHub :

ouvrir le dépôt ;

ouvrir l’onglet Actions ;

sélectionner le workflow ;

ouvrir l’exécution liée au commit ;

consulter les jobs et les logs ;

télécharger les artefacts en bas de la page.

13. Analyse d’un échec

ouvrir le premier job rouge ;

ouvrir la première étape en erreur ;

lire le message complet ;

reproduire localement la même commande ;

corriger ;

relancer les tests ;

créer un nouveau commit ;

pousser la correction.

14. Fichiers versionnés

.github/workflows/continuous-delivery.yml
Dockerfile
docker-compose.yml
pyproject.toml
uv.lock
src/
tests/
README.md
docs/

Fichiers générés à ne pas versionner :

.coverage
htmlcov/
.pytest_cache/
test_water_lab.db

15. Limites actuelles

le déploiement distant n’est pas automatisé ;

l’image Docker doit être exportée ou publiée dans un registre pour être conservée ;

les variables sensibles doivent être gérées avec les secrets GitHub ;

un test de démarrage du conteneur pourrait compléter le build.