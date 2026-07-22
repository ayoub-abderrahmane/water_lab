Guide utilisateur — Water Lab

1. Présentation

Water Lab estime la potabilité d’un échantillon d’eau à partir de mesures physico-chimiques.

L’application propose :

une saisie manuelle ;

un import de rapport avec OCR ;

un mode invité ;

un mode laboratoire connecté ;

un historique des prédictions enregistrées.

Le résultat fourni est une estimation issue d’un modèle d’intelligence artificielle. Il ne remplace pas une validation sanitaire ou réglementaire.

2. Accéder à l’application

Interface Streamlit : http://localhost:8501
API FastAPI : http://localhost:8000
Documentation API : http://localhost:8000/docs

Les ports peuvent varier selon la configuration Docker Compose.

3. Choisir un mode d’accès

Mode invité

Disponible pour une prédiction ponctuelle, une démonstration ou un test sans conservation.

En mode invité : saisie manuelle, OCR et prédiction sont disponibles ; aucune donnée n’est sauvegardée et l’historique est inaccessible.

Mode laboratoire

Disponible pour conserver les analyses, retrouver les prédictions précédentes et éviter la double saisie.

4. Se connecter

ouvrir l’écran de connexion ;

renseigner le nom d’utilisateur ;

renseigner le mot de passe ;

sélectionner Se connecter.

En cas de succès, une session temporaire est créée, l’historique devient accessible et les nouvelles prédictions peuvent être sauvegardées.

5. Réaliser une prédiction manuelle

Mesure

Champ technique

pH

ph

Dureté

Hardness

Solides dissous

Solids

Chloramines

Chloramines

Sulfates

Sulfate

Conductivité

Conductivity

Carbone organique

Organic_carbon

Trihalométhanes

Trihalomethanes

Turbidité

Turbidity

Procédure :

ouvrir le formulaire ;

renseigner les mesures ;

respecter les unités ;

corriger les erreurs signalées ;

lancer la prédiction ;

lire la classe et la probabilité.

6. Utiliser l’OCR

Formats acceptés :

PDF
PNG
JPEG

Limites :

1 Mio maximum
3 pages maximum dans le périmètre retenu

Procédure :

ouvrir l’écran OCR ;

choisir un fichier ;

lancer l’extraction ;

vérifier les valeurs détectées ;

corriger les valeurs incorrectes ;

compléter les valeurs absentes ;

lancer la prédiction.

Le fichier et le texte complet ne sont pas stockés par Water Lab.

7. Comprendre le résultat

0 = eau prédite non potable
1 = eau prédite potable

La probabilité indique le niveau estimé par le modèle pour la classe potable. Elle ne constitue pas une certification.

8. Sauvegarde des prédictions

Mode invité

La prédiction n’est pas sauvegardée.

Mode connecté

La prédiction est enregistrée avec la date, la source, les neuf mesures, la classe, le libellé et la probabilité.

9. Consulter l’historique

L’historique est réservé au compte connecté et affiche les prédictions les plus récentes.

Chaque ligne peut contenir :

la date ;

la source ;

les mesures ;

le résultat ;

la probabilité.

10. Se déconnecter

sélectionner Déconnexion ;

attendre la confirmation ;

vérifier que l’historique n’est plus accessible.

11. Messages d’erreur courants

Situation

Action

Authentification requise

Vérifier la configuration de l’application

Session invalide ou expirée

Se reconnecter

Valeur invalide

Corriger le champ

Format non supporté

Utiliser PDF, PNG ou JPEG

Fichier trop volumineux

Réduire le fichier

Service OCR indisponible

Utiliser la saisie manuelle

Modèle indisponible

Contacter l’équipe technique

Base indisponible

Contacter l’équipe technique

12. Bonnes pratiques

vérifier les unités ;

contrôler chaque valeur OCR ;

ne pas utiliser le résultat comme seule décision sanitaire ;

se déconnecter après utilisation ;

ne pas partager le mot de passe hors de l’équipe autorisée ;

utiliser la saisie manuelle si le rapport est illisible.

13. Accessibilité

titres structurés ;

libellés explicites ;

unités visibles ;

boutons nommés par leur action ;

messages d’erreur textuels ;

information non transmise uniquement par couleur ;

navigation simple ;

correction possible avant validation.

14. Confidentialité

Water Lab conserve uniquement les prédictions réalisées en mode connecté. Les fichiers OCR et leur texte complet ne sont pas stockés.

15. Limites du modèle

Le modèle est meilleur qu’un choix aléatoire et atteint les seuils techniques du projet, mais reste insuffisant pour une décision critique autonome.

16. Signaler un problème

Transmettre :

date et heure
mode invité ou connecté
écran concerné
type de fichier
action réalisée
message d’erreur