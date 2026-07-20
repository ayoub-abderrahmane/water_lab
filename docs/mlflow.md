# Monitoring du modèle Water Lab avec MLflow

## 1. Objectif

La chaîne de monitoring permet de suivre les entraînements du modèle de classification de potabilité.

Elle doit permettre :

- d’enregistrer les paramètres du modèle ;
- de mesurer ses performances ;
- de comparer plusieurs entraînements ;
- de tracer les versions et dates d’exécution ;
- de conserver les fichiers produits ;
- d’identifier une dégradation des résultats ;
- de refuser un modèle inférieur aux seuils minimaux.

Le monitoring présenté ici concerne le modèle de machine learning.  
Le monitoring applicatif de FastAPI est traité séparément avec Prometheus et Grafana.

---

## 2. Outil sélectionné

L’outil retenu est MLflow Tracking.

### Critères de choix

| Critère | Justification |
|---|---|
| Suivi complet des expériences | MLflow centralise les paramètres, métriques, dates, statuts et artefacts de chaque entraînement. |
| Compatibilité technique | MLflow s’intègre avec Python, scikit-learn et XGBoost sans modifier l’architecture principale du projet. |
| Déploiement local | MLflow peut être exécuté dans Docker et utiliser SQLite dans l’environnement de test. |
| Restitution | L’interface web permet de consulter et de comparer les runs. |
| Versionnement | Le code de configuration et de journalisation est conservé dans Git. |
| Maîtrise des données | L’instance est auto-hébergée et ne nécessite pas l’envoi des résultats vers une plateforme SaaS. |

---

## 3. Architecture de la chaîne

```text
Dataset
   ↓
Prétraitement
   ↓
Séparation entraînement/test
   ↓
Entraînement XGBoost
   ↓
Calcul des métriques
   ↓
Enregistrement dans MLflow
   ├── paramètres
   ├── métriques
   ├── informations du run
   └── artefacts
   ↓
Interface web MLflow