User stories et parcours utilisateurs

1. Contexte métier

Les analyses réalisées sur papier peuvent être perdues, difficiles à retrouver et entraîner une double saisie. Water Lab permet de saisir directement les analyses dans l’application, de lancer une prédiction et de conserver un historique lorsque l’utilisateur est connecté.

2. Profils utilisateurs

Profil

Besoin principal

Utilisateur invité

Réaliser une prédiction ponctuelle sans compte

Laboratoire connecté

Sauvegarder et retrouver les analyses

Équipe technique

Maintenir l’API, le modèle et les services

3. Justification des modes d’accès

Mode invité

aucune création de compte ;

aucune donnée conservée ;

accès immédiat à la prédiction ;

adapté à une démonstration ou à un test.

Limites : pas de sauvegarde, pas d’historique et pas de traçabilité à long terme.

Mode laboratoire connecté

sauvegarde automatique ;

historique centralisé ;

réduction de la double saisie ;

moins de risque de perte qu’avec le papier ;

continuité entre saisie, prédiction et consultation.

Compte laboratoire unique

Le compte unique réduit la complexité, évite une gestion complète des rôles, limite les données personnelles et fournit un historique partagé.

4. User stories

ID

User story

Besoin métier

Critères d’acceptation

US1

En tant qu’utilisateur, je souhaite renseigner manuellement les mesures d’un échantillon afin d’obtenir une estimation de sa potabilité.

Exploiter le modèle sans connaissance technique.

Les neuf mesures sont visibles ; les unités sont indiquées ; les valeurs invalides sont refusées ; la classe et la probabilité sont affichées.

US2

En tant qu’utilisateur, je souhaite déposer un rapport PDF ou une image afin d’extraire automatiquement les mesures et de réduire la saisie manuelle.

Gagner du temps et limiter les erreurs de ressaisie.

Les formats PDF, PNG et JPEG sont acceptés ; la taille est contrôlée ; les valeurs extraites sont modifiables ; la prédiction ne part qu’après validation humaine.

US3

En tant que visiteur, je souhaite utiliser l’application sans créer de compte afin d’effectuer une prédiction ponctuelle.

Permettre un usage rapide.

Le mode invité est clairement indiqué ; la prédiction est disponible ; aucune donnée n’est sauvegardée ; l’historique est inaccessible.

US4

En tant que membre du laboratoire, je souhaite me connecter avec le compte laboratoire afin de conserver et retrouver les analyses réalisées.

Sécuriser l’accès aux fonctions de sauvegarde.

Les identifiants invalides sont refusés ; une session temporaire est créée ; le mot de passe est hashé ; la déconnexion supprime la session.

US5

En tant qu’utilisateur connecté, je souhaite consulter l’historique des prédictions afin de retrouver les résultats précédents.

Assurer la traçabilité.

Les résultats récents apparaissent en premier ; chaque ligne contient la date, la source, les mesures, le résultat et la probabilité ; une session valide est obligatoire.

US6

En tant qu’utilisateur du laboratoire, je souhaite enregistrer directement mes analyses dans l’application afin d’éviter la double saisie, de limiter la perte d’informations et de retrouver les résultats dans un historique centralisé.

Remplacer les notes papier dispersées.

Les prédictions connectées sont sauvegardées ; la date, la source, les mesures et le résultat sont conservés ; les analyses peuvent être retrouvées sans ressaisie ; les prédictions invitées ne sont pas enregistrées.

5. Critères d’accessibilité

libellés explicites ;

unités visibles ;

messages d’erreur textuels ;

information non transmise uniquement par couleur ;

navigation cohérente ;

titres structurés ;

contraste lisible ;

correction possible avant validation ;

boutons nommés par leur action.

6. Parcours utilisateur invité

Accueil
→ choisir le mode invité
→ choisir saisie manuelle ou OCR
→ renseigner ou vérifier les valeurs
→ lancer la prédiction
→ afficher la classe et la probabilité
→ ne pas sauvegarder
→ fin

7. Parcours utilisateur connecté

Accueil
→ connexion au compte laboratoire
→ création d’une session temporaire
→ choisir saisie manuelle ou OCR
→ vérifier les valeurs
→ lancer la prédiction
→ sauvegarder dans PostgreSQL
→ afficher le résultat
→ consulter l’historique
→ se déconnecter

8. Parcours OCR

Choisir un fichier
→ contrôler format et taille
→ envoyer à l’API
→ appeler OCR.space
→ parser le texte
→ afficher les mesures
→ corriger ou compléter
→ lancer la prédiction

9. Règles métier principales

neuf mesures sont attendues par le modèle ;

l’utilisateur doit vérifier les valeurs OCR ;

une prédiction invitée n’est pas sauvegardée ;

une prédiction connectée est rattachée au compte laboratoire ;

l’historique est limité aux résultats récents ;

une session expirée est refusée ;

la déconnexion révoque la session.

10. Critères de validation globaux

les deux modes d’accès fonctionnent ;

les neuf mesures sont saisissables ;

l’OCR préremplit les champs ;

les champs OCR restent modifiables ;

les erreurs sont compréhensibles ;

la prédiction renvoie une classe et une probabilité ;

les données invitées ne sont pas stockées ;

les données connectées apparaissent dans l’historique ;

l’historique n’est pas accessible sans session ;

la déconnexion supprime l’accès à l’historique.

11. Limites

compte laboratoire unique ;

pas de gestion avancée des rôles ;

pas de suppression d’utilisateur dans l’interface ;

pas de recherche multi-critères avancée ;

modèle non adapté à une décision sanitaire autonome.