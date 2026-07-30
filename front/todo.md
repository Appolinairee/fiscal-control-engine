# Todo Front

Checklist operationnelle du chantier front. Les cases seront cochees au fur et a mesure.

## Socle Next.js

- [x] Initialiser le projet front en Next.js.
- [x] Ajouter les scripts de dev, lint, typecheck et tests.
- [x] Definir la structure de base: `app`, `api`, `components`, `config`, `store`, `types`, `utils`.
- [x] Installer les dependances UI necessaires pour le dashboard.
- [x] Ramener le socle Shopinx utile: API core, hooks generiques, utils, styles, polices, icons et composants base ciblés.
- [ ] Surveiller l'audit npm Next/PostCSS/Sharp: derniere version stable `next@16.2.12` encore signalee par `npm audit --omit=dev`.
- [x] Valider le socle: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build`.

## Dashboard Agent

- [x] Implementer une topbar fixe inspiree du design fourni.
- [ ] Afficher le nom produit `Harmonizer` avec le sous-titre `Agent fiscal`.
- [ ] Ajouter une icone menu seule, sans listing ni navigation pour l'instant.
- [ ] Ajouter une action `+` visuelle, sans logique pour l'instant.
- [ ] Ajouter le bloc profil utilisateur a droite.
- [ ] Ajouter une recherche visuelle avec placeholder, sans logique pour l'instant.
- [x] Structurer la topbar en composants lisibles: brand, bouton icone, profil, recherche.
- [x] Remplacer l'avatar provisoire par la photo profil Shopinx `default-profile.jpeg`.
- [x] Poser le shell dashboard sur fond blanc sans rounded global provisoire.
- [x] Preparer ensuite le layout 3 colonnes: infos/stats, agent premium dominant, donnees/graphes.
- [x] Centrer le premier bloc agent light premium dans la colonne du milieu.
- [x] Ajouter les faux etats de travail agent sans sources detaillees pour l'instant.
- [x] Structurer le prompt agent en shell unique avec textarea blanc et barre d'etat basse integree.
- [x] Laisser les colonnes laterales vides avec seulement les separateurs.
- [ ] Prevoir la table de travail en panneau bas masque.

## Integration Agent Excel

- [x] Decoupler upload et analyse: l'upload valide seulement format/taille et retourne vite.
- [x] Pendant l'upload, afficher un etat visible: fichier en cours, poids, attente API.
- [x] Apres upload reussi, afficher les infos utiles: nom fichier, taille, feuilles detectees.
- [x] Afficher les erreurs upload lisibles: format refuse, fichier trop lourd, fichier illisible, API indisponible.
- [ ] Laisser l'utilisateur choisir la feuille si plusieurs feuilles sont detectees.
- [x] Lancer automatiquement la pre-analyse deterministe apres upload reussi, sans afficher de reponse agent.
- [x] Conserver la pre-analyse en contexte interne sans bloc visible avant soumission.
- [x] Garder l'agent en attente tant qu'aucun message utilisateur n'est soumis.
- [x] A la soumission utilisateur, garder le chat fixe en bas et afficher la reponse agent en haut.
- [x] A la soumission utilisateur, deplacer le fichier de l'input vers la conversation haute.
- [x] Autoriser une question agent sans fichier Excel attache.
- [x] Garder le prompt centre a l'etat initial, puis fixe en bas des qu'il y a du contenu.
- [x] Definir les scrolls: colonne agent en scroll interne, reponse en haut, prompt fixe en bas.
- [x] Afficher un loading intelligent avec etapes d'execution haut niveau.
- [x] Ne pas afficher les métriques deterministes comme une reponse agent.
- [ ] Afficher les resultats de mapping et anomalies.

## Rapports

- [ ] Preparer l'interface de generation/consultation de rapport.
