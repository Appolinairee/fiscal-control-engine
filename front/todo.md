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
- [ ] Preparer ensuite le layout 3 colonnes: infos/stats, agent premium dominant, donnees/graphes.
- [ ] Prevoir la table de travail en panneau bas masque.

## Integration Agent Excel

- [ ] Afficher la liste des feuilles Excel.
- [ ] Afficher les colonnes detectees.
- [ ] Afficher le profiling d'une feuille.
- [ ] Afficher les resultats de mapping et anomalies.

## Rapports

- [ ] Preparer l'interface de generation/consultation de rapport.
