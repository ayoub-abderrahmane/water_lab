# Sécurité de l’API Water Lab — OWASP API Security Top 10

## 1. Objectif

Ce document présente les dix principaux risques de sécurité définis par l’OWASP pour les API, leur application au projet Water Lab, les protections déjà présentes et les améliorations à prévoir.

L’OWASP, Open Worldwide Application Security Project, publie des référentiels de sécurité applicative. Pour Water Lab, la référence pertinente est l’OWASP API Security Top 10, édition 2023.

## 2. Périmètre

Routes analysées :

- `GET /health` ;
- `GET /model/info` ;
- `POST /predict` ;
- `POST /ocr` ;
- `GET /metrics`.

Technologies concernées :

- FastAPI ;
- Pydantic ;
- authentification Bearer ;
- OCR.space ;
- Prometheus ;
- Docker Compose.

## 3. Protections déjà présentes

- authentification Bearer sur les routes sensibles ;
- secrets stockés dans les variables d’environnement ;
- validation des entrées avec Pydantic ;
- modèles de réponse explicites ;
- formats OCR limités à PDF, PNG et JPEG ;
- taille maximale des fichiers fixée à 1 Mio ;
- timeout sur les appels à OCR.space ;
- gestion des erreurs HTTP ;
- journalisation ;
- métriques Prometheus ;
- documentation Swagger ;
- appel d’OCR.space uniquement depuis l’API ;
- adresse OCR.space définie côté serveur.

## 4. Les dix risques OWASP

### API1:2023 — Broken Object Level Authorization

Ce risque apparaît lorsqu’un utilisateur peut consulter ou modifier l’objet d’un autre utilisateur en changeant son identifiant.

Dans Water Lab, ce risque est actuellement limité, car aucune route ne manipule encore des clients ou prélèvements stockés par identifiant.

À prévoir lors de l’ajout de PostgreSQL :

- vérifier que l’utilisateur possède l’objet demandé ;
- ne pas se contenter de vérifier que l’identifiant existe ;
- ajouter des tests d’accès croisé ;
- utiliser des identifiants difficiles à deviner lorsque cela est pertinent.

**Statut :** non applicable actuellement, mais à traiter avec les futures routes CRUD.

### API2:2023 — Broken Authentication

Ce risque concerne une authentification faible, contournable ou mal protégée.

Mesures présentes :

- jeton Bearer obligatoire sur `/predict`, `/ocr`, `/model/info` et `/metrics` ;
- comparaison du jeton avec `secrets.compare_digest` ;
- secret placé dans `.env` ;
- fichiers sensibles exclus de Git.

Limites :

- un seul jeton partagé ;
- aucune expiration ;
- aucune gestion individuelle des utilisateurs ;
- aucune rotation automatique.

À prévoir :

- jetons individuels ;
- expiration et rotation ;
- limitation des tentatives ;
- journalisation des échecs sans enregistrer les secrets.

**Statut :** partiellement couvert.

### API3:2023 — Broken Object Property Level Authorization

Ce risque apparaît lorsqu’une API accepte ou expose des propriétés non prévues.

Mesures présentes :

- `WaterSample` définit les neuf variables autorisées ;
- `PredictionResponse` et `OCRResponse` limitent les champs renvoyés ;
- la clé OCR.space n’est jamais renvoyée.

Amélioration recommandée dans `WaterSample` :

```python
model_config = ConfigDict(
    extra="forbid",
)
```

Cette option refuse les propriétés supplémentaires.

**Statut :** majoritairement couvert.

### API4:2023 — Unrestricted Resource Consumption

Ce risque concerne la consommation excessive de mémoire, processeur, réseau ou quota externe.

Mesures présentes :

- fichiers limités à 1 Mio ;
- types limités à PDF, PNG et JPEG ;
- timeout réseau ;
- un fichier par requête ;
- métriques sur le nombre et la durée des appels OCR.

À prévoir :

- rate limiting ;
- quota par client ;
- alertes sur le quota OCR.space ;
- limites CPU et mémoire Docker ;
- contrôle du contenu réel du fichier.

**Statut :** partiellement couvert.

### API5:2023 — Broken Function Level Authorization

Ce risque apparaît lorsqu’un utilisateur accède à une fonction réservée à un autre rôle.

Mesures présentes :

- `/health` est publique ;
- les autres routes sensibles sont protégées.

Limite :

- tous les utilisateurs authentifiés disposent du même niveau d’accès.

À prévoir :

- rôles administrateur, utilisateur et monitoring ;
- jeton spécifique pour Prometheus ;
- tests d’autorisation par rôle.

**Statut :** partiellement couvert.

### API6:2023 — Unrestricted Access to Sensitive Business Flows

Ce risque concerne l’automatisation abusive d’une fonction métier légitime.

Dans Water Lab, des appels massifs à `/ocr` peuvent consommer le quota OCR.space.

Mesures présentes :

- authentification ;
- limite de taille ;
- métriques.

À prévoir :

- nombre maximal de requêtes par minute ;
- quota journalier ;
- blocage temporaire en cas d’abus ;
- alerte avant épuisement du quota.

**Statut :** à améliorer.

### API7:2023 — Server-Side Request Forgery

Une attaque SSRF force le serveur à appeler une adresse choisie par l’utilisateur.

Le risque est faible actuellement :

- l’utilisateur envoie un fichier, pas une URL ;
- l’adresse OCR.space est fixe ;
- aucune URL utilisateur n’est transmise à `requests.post`.

À conserver :

- ne pas accepter d’URL distante sans validation ;
- utiliser une liste blanche de domaines ;
- bloquer les adresses locales et privées ;
- contrôler les redirections.

**Statut :** faible dans l’architecture actuelle.

### API8:2023 — Security Misconfiguration

Ce risque regroupe les mauvaises configurations de production.

Mesures présentes :

- secrets hors du code ;
- fichiers sensibles exclus de Git ;
- `/metrics` masquée de Swagger ;
- erreurs HTTP contrôlées ;
- application conteneurisée.

À prévoir :

- HTTPS en production ;
- désactivation de `--reload` et du mode debug ;
- politique CORS restrictive ;
- versions de dépendances fixées ;
- analyse des dépendances ;
- mots de passe non standards pour Grafana et PostgreSQL ;
- services internes non exposés publiquement.

**Statut :** partiellement couvert.

### API9:2023 — Improper Inventory Management

Ce risque apparaît lorsque les routes, versions et services ne sont pas correctement recensés.

Mesures présentes :

- Swagger recense les routes publiques ;
- version `0.1.0` déclarée ;
- routes regroupées dans FastAPI.

À prévoir :

- inventaire des routes et niveaux d’accès ;
- préfixe de version, par exemple `/api/v1` ;
- suppression des routes obsolètes ;
- documentation des environnements ;
- inventaire des ports et services Docker.

**Statut :** partiellement couvert.

### API10:2023 — Unsafe Consumption of APIs

Ce risque concerne la confiance excessive accordée à une API tierce.

Water Lab consomme OCR.space.

Mesures présentes :

- appel HTTPS ;
- clé envoyée côté serveur ;
- timeout ;
- vérification du statut HTTP ;
- conversion JSON protégée ;
- vérification de `IsErroredOnProcessing` ;
- gestion du texte vide ;
- erreurs du fournisseur transformées en erreurs contrôlées ;
- vérification humaine des valeurs OCR avant prédiction.

À prévoir :

- validation plus stricte de la structure JSON ;
- limite sur la taille de la réponse ;
- nombre de tentatives limité ;
- surveillance des changements de contrat OCR.space ;
- solution de repli en cas d’indisponibilité.

**Statut :** bien pris en compte, avec améliorations possibles.

## 5. Tests de sécurité attendus

Les tests doivent vérifier :

- absence de jeton ;
- mauvais jeton ;
- bon jeton ;
- types invalides ;
- valeurs négatives ;
- propriétés supplémentaires ;
- fichier vide ;
- format interdit ;
- fichier supérieur à 1 Mio ;
- erreur OCR.space ;
- accès à `/metrics` ;
- accès à `/model/info` ;
- plage de probabilité entre 0 et 1 ;
- absence de secret dans les réponses.

Les appels à OCR.space doivent être simulés afin de ne pas utiliser le quota réel et de rendre les tests reproductibles.

## 6. Priorités

1. Ajouter les tests de sécurité.
2. Ajouter `extra="forbid"` à `WaterSample`.
3. Mettre en place un rate limiting.
4. Séparer les rôles et les jetons.
5. Configurer HTTPS et CORS pour la production.
6. Ajouter une analyse automatique des dépendances.
7. Surveiller le quota OCR.space.
8. Documenter l’inventaire des routes et services.

## 7. Conclusion

Water Lab possède déjà plusieurs protections importantes : authentification, validation Pydantic, limite de taille, liste blanche des formats, timeout, gestion des erreurs, logs et métriques.

Les principales améliorations concernent la limitation du nombre de requêtes, la gestion de plusieurs utilisateurs, la séparation des rôles et la configuration de production.

## 8. Sources officielles

- [OWASP API Security Top 10 — édition 2023](https://owasp.org/API-Security/editions/2023/fr/0x00-header/)
- [Liste des dix risques OWASP API Security 2023](https://owasp.org/API-Security/editions/2023/fr/0x11-t10/)
- [API4 — Consommation de ressources non restreinte](https://owasp.org/API-Security/editions/2023/fr/0xa4-unrestricted-resource-consumption/)
- [API10 — Consommation non sécurisée d’API](https://owasp.org/API-Security/editions/2023/en/0xaa-unsafe-consumption-of-apis/)