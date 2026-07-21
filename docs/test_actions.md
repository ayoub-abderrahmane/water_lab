# C12 — Tests automatisés du modèle d’intelligence artificielle

## 1. Objectif

Les tests automatisés ont pour objectif de vérifier la qualité du modèle Water Lab avant son intégration dans l’application.

Ils couvrent les principales étapes du cycle de machine learning :

1. validation du jeu de données ;
2. préparation des données ;
3. construction du pipeline ;
4. entraînement du modèle ;
5. génération des prédictions ;
6. évaluation des performances ;
7. validation des seuils minimaux ;
8. sauvegarde et rechargement du modèle.

La chaîne doit empêcher la livraison d’un modèle lorsque :

- le jeu de données ne respecte plus le schéma attendu ;
- la cible n’est plus compatible avec une classification binaire ;
- une fuite de données apparaît ;
- le preprocessing ne traite plus les valeurs manquantes ;
- le modèle ne peut plus être entraîné ;
- les probabilités produites sont invalides ;
- les performances sont inférieures aux seuils définis ;
- le modèle sauvegardé ne peut pas être rechargé ;
- le modèle rechargé ne produit plus les mêmes prédictions.

---

## 2. Périmètre des tests

Les tests de C12 portent uniquement sur le modèle d’intelligence artificielle et son pipeline.

Ils concernent les modules suivants :

```text
src/preprocessing.py
src/pipeline.py
src/train.py