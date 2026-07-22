Éco-responsabilité et accessibilité

1. Objectif

Water Lab intègre des objectifs de sobriété technique et d’accessibilité dès la conception.

L’objectif n’est pas d’affirmer une neutralité carbone complète, mais de documenter les choix qui réduisent les calculs, stockages, transferts et obstacles inutiles.

Partie A — Éco-responsabilité

2. Principes retenus

moins de données
→ moins de transfert
→ moins de stockage
→ moins de calcul
→ meilleure efficacité

3. Choix du modèle

XGBoost a été retenu car il est adapté aux données tabulaires, rapide à entraîner, rapide à utiliser et plus proportionné à la tâche qu’un modèle génératif lourd.

4. Modèle chargé une seule fois

Le pipeline est chargé au démarrage de l’API afin d’éviter les rechargements répétés, les accès disque inutiles et l’augmentation du temps de réponse.

5. OCR à la demande

appel uniquement lors d’un import ;

taille limitée à 1 Mio ;

nombre de pages limité ;

formats contrôlés ;

aucun stockage du fichier ;

aucun stockage du texte complet ;

saisie manuelle disponible.

6. Historique limité

L’API retourne uniquement les prédictions les plus récentes afin de réduire la mémoire, le volume HTTP et le temps d’affichage.

La limite concerne la réponse, pas nécessairement la suppression des anciennes données.

7. Image Python slim

FROM python:3.12-slim

Avantages : téléchargement, stockage et surface d’attaque réduits.

8. Cache uv dans la CI

uses: astral-sh/setup-uv@v5
with:
  enable-cache: true

Le cache réduit les téléchargements et le temps d’exécution lorsque uv.lock n’a pas changé.

9. Services séparés

API
Streamlit
PostgreSQL
MLflow
Prometheus
Grafana

La séparation permet de lancer seulement les services nécessaires. Elle ne garantit pas une consommation plus faible si tous les services restent actifs.

10. Minimisation des données

Water Lab ne conserve pas :

le fichier OCR ;

le texte OCR intégral ;

les prédictions invitées ;

des comptes individuels multiples dans la première version.

11. Tableau de synthèse

Choix

Effet technique

XGBoost tabulaire

Modèle proportionné à la tâche

Chargement unique

Moins d’accès disque

OCR à la demande

Aucun calcul permanent

Taille 1 Mio

Moins de mémoire et de réseau

Pas de stockage OCR

Moins de données conservées

Historique limité

Réponses plus légères

Python slim

Image Docker plus légère

Cache uv

Moins de téléchargements

Services séparés

Exécution sélective possible

Mode invité sans sauvegarde

Pas de conservation inutile

12. Limites

aucune mesure énergétique directe ;

impact réel du fournisseur OCR non maîtrisé ;

consommation des conteneurs si tous restent actifs ;

CI distante exécutée à chaque déclenchement.

13. Améliorations possibles

pagination ;

durée de conservation ;

archivage automatique ;

suivi CPU et mémoire ;

comparaison de fournisseurs ;

bilan d’impact.

Partie B — Accessibilité

14. Références

Les objectifs s’appuient sur les principes WCAG, RGAA et les bonnes pratiques de documentation accessible.

15. Interface

Libellés explicites

Chaque champ indique le nom de la mesure et son unité.

Messages d’erreur textuels

La dureté doit être un nombre positif.

Couleur non exclusive

Eau prédite non potable — probabilité 72 %

Navigation cohérente

actions regroupées ;

boutons nommés ;

ordre logique ;

correction avant validation ;

historique réservé au mode connecté.

16. Critères d’acceptation accessibles

Fonction

Critère

Formulaire

Tous les champs possèdent un libellé

Unités

Chaque mesure affiche son unité

Erreurs

Le message décrit le problème

Résultat

Texte et valeur numérique visibles

Couleur

Jamais utilisée seule

OCR

Valeurs modifiables

Navigation

Parcours simple invité/connecté

Historique

Tableau avec en-têtes explicites

Connexion

Champs identifiés et mot de passe masqué

17. Documentation accessible

Les documents utilisent :

un titre principal unique ;

une hiérarchie de titres ;

des paragraphes courts ;

des listes simples ;

des tableaux limités ;

des blocs de code ;

un vocabulaire constant.

À éviter : titres uniquement en majuscules, paragraphes très longs, tableaux trop larges, captures sans description et liens intitulés « cliquez ici ».

18. Visuels

Chaque visuel doit avoir un titre, une légende, une description textuelle, un ordre de lecture logique et un contraste suffisant.

19. Monitoring accessible

Métrique

Valeur

Seuil

Statut

Accuracy

0,614

0,55

Validé

ROC-AUC

0,634

0,58

Validé

Le statut ne doit pas être uniquement vert ou rouge.

20. Tests manuels recommandés

navigation au clavier ;

ordre de tabulation ;

zoom navigateur ;

lisibilité des messages ;

contraste ;

compréhension sans couleur ;

cohérence des titres ;

lecture des tableaux.

21. Limites actuelles

aucun audit RGAA complet ;

aucun test formel avec lecteur d’écran documenté ;

contrôle HTML limité par Streamlit ;

certains graphiques nécessitent une alternative textuelle.

22. Améliorations possibles

audit spécialisé ;

test avec lecteur d’écran ;

contrôle automatisé des contrastes ;

descriptions alternatives ;

amélioration du focus clavier ;

export accessible de l’historique.