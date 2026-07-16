# Compétences et preuves disponibles — état actuel

Ce document présente uniquement les compétences déjà commencées ou partiellement démontrées par l'état actuel du projet.

## C9 — Développer une API exposant un modèle d'IA

### Réalisé

- API développée avec FastAPI ;
- validation des entrées avec Pydantic ;
- route `POST /predict` ;
- route `GET /health` ;
- route `GET /model/info` ;
- documentation OpenAPI générée automatiquement ;
- gestion des erreurs liées au modèle ;
- sources organisées dans le projet.

### Preuves

- capture de `http://localhost:8000/docs` ;
- exemple de requête et de réponse sur `/predict` ;
- code de `src/api.py` ;
- logs d'une prédiction réussie et d'une erreur.

### À compléter

- authentification ;
- tests de tous les endpoints ;
- documentation des règles d'accès ;
- prise en compte explicite des risques OWASP utiles au projet.

## C10 — Intégrer l'API dans une application

### Réalisé

- interface Streamlit fonctionnelle ;
- envoi des mesures à FastAPI par requête HTTP ;
- affichage de la classe prédite et de la probabilité ;
- séparation entre l'interface et le modèle.

### Preuves

- capture du formulaire Streamlit ;
- capture d'un résultat de prédiction ;
- code de `front/app.py` ;
- logs FastAPI montrant l'appel à `/predict`.

### À compléter

- authentification entre Streamlit et FastAPI ;
- tests d'intégration ;
- gestion plus complète des erreurs côté interface.

## C11 — Monitorer un modèle d'IA

### Réalisé

- suivi des expériences avec MLflow ;
- enregistrement des paramètres ;
- enregistrement des métriques ;
- sauvegarde des artefacts ;
- sauvegarde du pipeline entraîné ;
- comparaison possible entre plusieurs runs.

### Métriques suivies

- accuracy ;
- precision ;
- recall ;
- F1-score ;
- ROC-AUC.

### Preuves

- capture d'un run MLflow ;
- tableau des métriques ;
- présence du modèle et des artefacts ;
- code de `src/train.py`.

### Limite actuelle

Le suivi porte surtout sur les métriques calculées pendant l'entraînement. La dérive des données et la performance réelle en production ne sont pas encore suivies.

## C12 — Programmer les tests automatisés d'un modèle d'IA

### État

Non commencé.

Les règles de validation existent déjà dans le code :

- contrôle des colonnes ;
- contrôle de la cible ;
- gestion des valeurs manquantes ;
- vérification du chargement du modèle ;
- vérification des prédictions.

Elles devront être transformées en tests Pytest.

## C13 — Créer une chaîne de livraison continue d'un modèle d'IA

### Réalisé partiellement

- environnement reproductible avec `uv` ;
- pipeline entraînable en ligne de commande ;
- modèle sauvegardé ;
- application conteneurisée.

### À compléter

- workflow GitHub Actions ;
- exécution automatique des tests ;
- entraînement ou validation automatique ;
- construction automatique des images ;
- livraison d'un artefact validé.

## C15 — Concevoir le cadre technique de l'application

### Réalisé

- choix d'une API unique ;
- séparation interface, API et modèle ;
- choix de FastAPI, Streamlit, MLflow, Docker, Prometheus et Grafana ;
- architecture conteneurisée ;
- identification d'une future base PostgreSQL.

### Preuves

- schéma d'architecture ;
- `docker-compose.yml` ;
- Dockerfile ;
- documentation technique.

### Limite actuelle

PostgreSQL est présent dans l'architecture mais n'est pas encore utilisé par l'application.

## C17 — Développer les composants techniques et les interfaces

### Réalisé partiellement

- prétraitement des données ;
- pipeline de machine learning ;
- entraînement et évaluation ;
- API de prédiction ;
- interface Streamlit ;
- gestion d'erreurs ;
- logs applicatifs ;
- métriques Prometheus ;
- exécution avec Docker Compose.

### À compléter

- persistance en base ;
- gestion des profils et droits ;
- OCR ;
- tests ;
- accessibilité de l'interface ;
- sécurisation complète.

## C18 — Automatiser les tests lors du versionnement

### État

Non commencé.

La prochaine étape sera de créer une suite Pytest puis un workflow GitHub Actions exécuté à chaque push et pull request.

## C19 — Créer un processus de livraison continue

### Réalisé partiellement

- images Docker constructibles ;
- services orchestrés avec Docker Compose ;
- lancement reproductible en local.

### À compléter

- automatisation du build ;
- validation par les tests ;
- publication d'une image ;
- procédure de déploiement.

## C20 — Monitorer une application d'IA

### Réalisé partiellement

- route `/metrics/` ;
- métriques de requêtes, durées, erreurs et prédictions ;
- collecte Prometheus ;
- connexion de Grafana à Prometheus ;
- logs dans les composants principaux ;
- orchestration avec Docker Compose.

### Preuves

- capture de `/metrics/` ;
- cible Prometheus en état `UP` ;
- requêtes PromQL ;
- capture Grafana ;
- logs de l'API et du modèle.

### À compléter

- dashboard Grafana finalisé ;
- alertes avec seuils ;
- export du dashboard ;
- documentation des seuils ;
- centralisation éventuelle des logs.

## C21 — Résoudre un incident technique

### État

Non commencé formellement.

Le projet dispose maintenant des éléments nécessaires pour préparer un scénario :

1. détection d'une anomalie dans Grafana ;
2. identification de la route et du statut dans Prometheus ;
3. diagnostic avec les logs ;
4. correction du code ou de la configuration ;
5. vérification ;
6. rédaction d'une fiche d'incident.

## Synthèse

| Compétence | État actuel |
|---|---|
| C9 | En cours |
| C10 | Première version fonctionnelle |
| C11 | Première version fonctionnelle |
| C12 | Non commencé |
| C13 | En cours |
| C15 | Architecture définie |
| C17 | En cours |
| C18 | Non commencé |
| C19 | En cours |
| C20 | En cours |
| C21 | À réaliser |