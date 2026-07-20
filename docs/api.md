# Documentation de l’API Water Lab

## 1. Objet

Water Lab API expose un modèle de classification estimant la potabilité d’un échantillon d’eau à partir de mesures physico-chimiques.

L’API fournit également :

- une extraction OCR de rapports PDF ou images ;
- une authentification technique ;
- une authentification du compte laboratoire ;
- une gestion de sessions temporaires ;
- une sauvegarde conditionnelle des prédictions ;
- un historique des résultats ;
- des métriques Prometheus ;
- une route de contrôle de santé.

L’application constitue une aide à l’analyse. Le résultat produit par le modèle ne remplace pas une validation réglementaire ou une expertise de laboratoire.

---

## 2. Architecture

```text
Application cliente
        |
        v
API FastAPI
        |
        +------------------+
        |                  |
        v                  v
Pipeline IA            OCR.space
        |
        v
PostgreSQL
```

### Responsabilités

| Composant | Responsabilité |
|---|---|
| Application cliente | Saisie, dépôt de fichier et affichage |
| FastAPI | Validation, authentification et orchestration |
| Pydantic | Validation des données entrantes et sortantes |
| Pipeline IA | Prédiction de la potabilité |
| OCR.space | Extraction du texte des documents |
| Parseur OCR | Association du texte aux mesures |
| PostgreSQL | Utilisateurs, sessions et prédictions |
| SQLAlchemy | Accès à la base de données |
| Prometheus | Collecte des métriques |

L’API est le seul composant autorisé à accéder directement au modèle, à PostgreSQL et au service OCR.

---

## 3. URL et version

Version actuelle : `0.1.0`

Adresse locale habituelle : `http://localhost:8000`

Documentation Swagger : `http://localhost:8000/docs`

Schéma OpenAPI : `http://localhost:8000/openapi.json`

---

## 4. Variables d’environnement

| Variable | Fonction |
|---|---|
| `API_AUTH_TOKEN` | Jeton technique de l’API |
| `DATABASE_URL` | Connexion SQLAlchemy à PostgreSQL |
| `POSTGRES_DB` | Nom de la base |
| `POSTGRES_USER` | Utilisateur PostgreSQL |
| `POSTGRES_PASSWORD` | Mot de passe PostgreSQL |
| `OCR_SPACE_API_KEY` | Clé du service OCR.space |
| `LAB_USERNAME` | Nom du compte laboratoire |
| `LAB_PASSWORD` | Mot de passe initial du laboratoire |
| `USER_SESSION_DURATION_HOURS` | Durée d’une session |

Les secrets ne doivent pas être placés directement dans le code ni versionnés dans Git.

---

## 5. Modèle d’authentification

L’API utilise deux niveaux distincts d’authentification.

### 5.1 Authentification technique

Les routes sensibles exigent :

```http
Authorization: Bearer <API_AUTH_TOKEN>
```

Ce jeton autorise une application cliente à appeler l’API. Il ne représente pas un utilisateur précis.

### 5.2 Authentification utilisateur

La route `/auth/login` vérifie le compte du laboratoire et retourne un jeton temporaire.

Le jeton est ensuite transmis avec :

```http
X-User-Session: <session_token>
```

La session utilisateur permet :

- de sauvegarder une prédiction ;
- de consulter l’historique ;
- de distinguer le mode invité du mode connecté.

### 5.3 Stockage des identifiants

Le mot de passe utilisateur n’est pas stocké en clair. Seul son hash Argon2 est enregistré dans PostgreSQL.

Le jeton de session est retourné au client, mais seul son hash SHA-256 est conservé dans la base.

### 5.4 Expiration et révocation

Chaque session possède une date d’expiration.

La route `/auth/logout` permet de supprimer immédiatement la session avant son expiration naturelle.

---

## 6. Inventaire des points de terminaison

| Méthode | Route | Jeton technique | Session utilisateur | Fonction |
|---|---|---:|---:|---|
| `GET` | `/health` | Non | Non | Vérifier le modèle |
| `GET` | `/model/info` | Oui | Non | Informations du modèle |
| `POST` | `/predict` | Oui | Facultative | Réaliser une prédiction |
| `POST` | `/ocr` | Oui | Non | Extraire un document |
| `POST` | `/auth/login` | Oui | Non | Créer une session |
| `POST` | `/auth/logout` | Oui | Obligatoire | Supprimer une session |
| `GET` | `/predictions/history` | Oui | Obligatoire | Consulter l’historique |
| `GET` | `/metrics` | Oui | Non | Métriques Prometheus |

---

## 7. `GET /health`

### Fonction

Vérifie que le fichier du modèle est disponible et peut être chargé.

### Authentification

Aucune.

### Réponse réussie

```json
{
  "status": "healthy",
  "model": "loaded"
}
```

### Erreur

Si le modèle est introuvable : `503 Service Unavailable`.

---

## 8. `GET /model/info`

### Fonction

Retourne les principales informations relatives au modèle.

### Authentification

Jeton technique obligatoire.

```http
Authorization: Bearer <API_AUTH_TOKEN>
```

### Réponse réussie

```json
{
  "name": "XGBoost Water Potability",
  "version": "0.1.0",
  "imputation": "median"
}
```

---

## 9. `POST /predict`

### Fonction

Exécute une prédiction de potabilité.

### Authentification

Jeton technique obligatoire. La session utilisateur est facultative.

```http
Authorization: Bearer <API_AUTH_TOKEN>
X-User-Session: <session_token>
```

Sans `X-User-Session`, la prédiction fonctionne mais n’est pas enregistrée. Avec une session valide, elle est sauvegardée dans PostgreSQL.

### Paramètre de requête

| Paramètre | Valeurs | Valeur par défaut |
|---|---|---|
| `source` | `manuel` ou `ocr` | `manuel` |

### Corps attendu

```json
{
  "ph": 7.2,
  "Hardness": 190.0,
  "Solids": 21000.0,
  "Chloramines": 7.0,
  "Sulfate": 330.0,
  "Conductivity": 420.0,
  "Organic_carbon": 14.0,
  "Trihalomethanes": 65.0,
  "Turbidity": 4.0
}
```

### Réponse réussie

```json
{
  "predicted_class": 1,
  "label": "potable",
  "potable_probability": 0.8123
}
```

### Erreurs

| Code | Situation |
|---:|---|
| `401` | Jeton technique absent ou incorrect |
| `422` | Type ou contrainte invalide |
| `500` | Erreur inattendue de prédiction |
| `503` | Modèle introuvable |

---

## 10. `POST /ocr`

### Fonction

Extrait le texte d’un rapport et recherche les neuf mesures utilisées par le modèle.

### Authentification

Jeton technique obligatoire.

### Formats acceptés

- PDF ;
- PNG ;
- JPEG.

### Taille maximale

`1 Mio`, soit `1 048 576 octets`.

### Exemple avec `curl`

```bash
curl -X POST \
  "http://localhost:8000/ocr" \
  -H "Authorization: Bearer <API_AUTH_TOKEN>" \
  -F "file=@rapport.pdf"
```

### Erreurs

| Code | Situation |
|---:|---|
| `400` | Fichier vide |
| `401` | Jeton absent ou invalide |
| `413` | Fichier supérieur à 1 Mio |
| `415` | Format non accepté |
| `422` | Champ `file` absent |
| `502` | Erreur du service OCR.space |

---

## 11. `POST /auth/login`

### Fonction

Authentifie le compte du laboratoire et crée une session temporaire.

### Authentification

Jeton technique obligatoire.

### Corps attendu

```json
{
  "username": "inovie_lab",
  "password": "mot-de-passe-du-laboratoire"
}
```

### Contraintes

| Champ | Contraintes |
|---|---|
| `username` | Entre 3 et 100 caractères |
| `password` | Entre 12 et 200 caractères |

### Réponse réussie

```json
{
  "username": "inovie_lab",
  "session_token": "jeton-temporaire",
  "expires_at": "2026-07-20T23:00:00+00:00"
}
```

### Erreurs

| Code | Situation |
|---:|---|
| `401` | Jeton technique invalide |
| `401` | Identifiants utilisateur incorrects |
| `422` | Corps ou longueur des champs invalide |

---

## 12. `POST /auth/logout`

### Fonction

Supprime la session utilisateur correspondante.

### Authentification

```http
Authorization: Bearer <API_AUTH_TOKEN>
X-User-Session: <session_token>
```

### Réponse réussie

```json
{
  "message": "Déconnexion effectuée."
}
```

### Erreurs

| Code | Situation |
|---:|---|
| `401` | Jeton technique invalide |
| `422` | En-tête `X-User-Session` absent |

---

## 13. `GET /predictions/history`

### Fonction

Retourne les prédictions du compte actuellement connecté.

### Authentification

Jeton technique et session utilisateur obligatoires.

```http
Authorization: Bearer <API_AUTH_TOKEN>
X-User-Session: <session_token>
```

### Règles d’autorisation

- la requête ne reçoit pas d’identifiant utilisateur ;
- l’utilisateur est déterminé à partir de la session ;
- la requête SQL filtre sur l’identifiant du compte connecté ;
- les résultats sont classés du plus récent au plus ancien ;
- la réponse est limitée à 100 prédictions.

### Erreurs

| Code | Situation |
|---:|---|
| `401` | Jeton technique incorrect |
| `401` | Session absente, invalide ou expirée |

---

## 14. `GET /metrics`

### Fonction

Expose les métriques au format Prometheus.

### Authentification

Jeton technique obligatoire.

### Documentation Swagger

Cette route est volontairement masquée de Swagger avec :

```python
include_in_schema=False
```

Le corps contient notamment des métriques préfixées par `water_lab_`.

---

## 15. Codes HTTP utilisés

| Code | Signification |
|---:|---|
| `200` | Requête réussie |
| `400` | Fichier vide ou requête incorrecte |
| `401` | Authentification requise ou invalide |
| `404` | Route inexistante |
| `413` | Fichier trop volumineux |
| `415` | Format non pris en charge |
| `422` | Données ou en-tête obligatoires invalides |
| `500` | Erreur interne de prédiction |
| `502` | Erreur du fournisseur OCR |
| `503` | Modèle indisponible |

---

## 16. Persistance des données

### Tables

| Table | Contenu |
|---|---|
| `users` | Compte et hash du mot de passe |
| `user_sessions` | Hash du jeton et expiration |
| `predictions` | Mesures, résultat, source et date |

### Données non conservées

L’API ne conserve pas :

- le mot de passe en clair ;
- le jeton de session en clair dans la base ;
- le fichier PDF ou image ;
- le texte OCR complet ;
- les prédictions réalisées en mode invité.

---

## 17. Sécurité OWASP

### API1 — Broken Object Level Authorization

L’historique est filtré par l’utilisateur dérivé de la session. Aucun identifiant d’utilisateur n’est fourni directement par le client.

### API2 — Broken Authentication

Mesures appliquées :

- jeton technique Bearer ;
- compte utilisateur ;
- hash Argon2 ;
- session temporaire ;
- hash du jeton ;
- expiration ;
- déconnexion côté serveur.

### API3 — Broken Object Property Level Authorization

Les modèles Pydantic définissent les propriétés entrantes et sortantes. L’ajout de `extra="forbid"` permet de refuser explicitement les propriétés inconnues.

### API4 — Unrestricted Resource Consumption

Mesures appliquées :

- taille maximale de 1 Mo ;
- un fichier par requête ;
- formats limités ;
- délai maximal OCR ;
- métriques de durée et de volume.

### API5 — Broken Function Level Authorization

Les routes sensibles sont protégées. L’historique exige en plus une session utilisateur.

### API6 — Unrestricted Access to Sensitive Business Flows

L’OCR est protégé par authentification et limite de taille. Une limitation de fréquence reste à ajouter.

### API7 — Server-Side Request Forgery

L’utilisateur transmet un fichier et non une URL. L’adresse OCR.space est définie côté serveur.

### API8 — Security Misconfiguration

Mesures appliquées :

- secrets externalisés ;
- image Docker ;
- dépendances verrouillées ;
- erreurs contrôlées ;
- route `/metrics` masquée de Swagger.

### API9 — Improper Inventory Management

Les routes, méthodes et niveaux d’accès sont inventoriés dans cette documentation.

### API10 — Unsafe Consumption of APIs

L’appel à OCR.space utilise HTTPS, une clé côté serveur, un délai maximal, une vérification du statut, une gestion des erreurs et une vérification humaine du résultat.

---

## 18. Tests automatisés

Les tests couvrent :

| Domaine | Scénarios |
|---|---|
| Santé | Modèle présent ou absent |
| Authentification technique | Jeton absent, invalide ou valide |
| Prédiction | Succès, type invalide, valeur négative |
| Persistance | Invité non sauvegardé, connecté sauvegardé |
| Connexion | Mauvais et bons identifiants |
| Déconnexion | En-tête absent et suppression |
| Historique | Session absente et résultat valide |
| OCR | Format, taille, fichier vide, succès et erreur |
| Monitoring | Accès à `/metrics` |
| Routage | Route inconnue |

Les appels OCR réels sont simulés avec `monkeypatch`.

---

## 19. Lancement de l’API

Avec uv :

```bash
uv run uvicorn src.api:app \
  --host 0.0.0.0 \
  --port 8000
```

En développement :

```bash
uv run uvicorn src.api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --reload
```

Avec Docker Compose :

```bash
docker compose up -d --build
```

Vérification :

```bash
docker compose ps
```

Logs :

```bash
docker compose logs -f api
```

---

## 20. Limites actuelles

- un seul compte laboratoire ;
- absence de rôles utilisateur ;
- absence de limitation de fréquence ;
- absence de blocage après plusieurs échecs de connexion ;
- absence de HTTPS dans l’environnement local ;
- route d’API non préfixée par une version ;
- dépendance au service OCR.space ;
- absence de contrôle approfondi de la signature réelle des fichiers ;
- modèle insuffisant pour une décision sanitaire autonome.

---

## 21. Conclusion

Water Lab API expose le modèle de potabilité dans une architecture séparant le client, les services métier, la base de données et les services externes.

Les routes sensibles sont protégées par un jeton technique. Les fonctions de sauvegarde et d’historique utilisent en complément une session utilisateur temporaire.

Les données sont validées par Pydantic. Les mots de passe et les jetons ne sont pas conservés en clair. Les documents OCR sont limités en type et en taille et ne sont pas stockés.

La documentation recense les huit points de terminaison, leurs données, leurs codes de réponse et leurs règles d’accès.