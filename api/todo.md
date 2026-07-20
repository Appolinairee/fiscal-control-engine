# Todo API

Checklist operationnelle du chantier API. Les cases seront cochees au fur et a mesure.

## Socle Python

- [x] Initialiser `api/` comme projet Python propre.
- [x] Ajouter la structure `app/` avec domaines, configuration et tests.
- [x] Ajouter les dependances de base: FastAPI, Pydantic, Pandas, lecteur Excel, pytest, lint/typecheck.
- [x] Ajouter un module de configuration et `api/.env.example`.
- [x] Ajouter Docker comme environnement de developpement reproductible.
- [x] Ajouter les scripts racine `package.json` pour dev, lint, typecheck et tests API.
- [x] Supprimer le `Makefile` API au profit de Docker + scripts racine.
- [ ] Generer le lockfile `uv.lock` via Docker apres premier build API. Bloque localement: Docker absent.

## Coeur Metier Stable

- [x] Creer les objets metier typés: compte GL, compte du plan comptable, mapping compte, statut de classification.
- [x] Creer les contrats de service independants de FastAPI et de la base.
- [x] Creer une interface de stockage `AccountMappingRepository`.
- [x] Ajouter une implementation initiale fichier ou memoire du repository.
- [x] Garder PostgreSQL comme implementation future sans changer les contrats metier.
- [x] Documenter les points non clarifies dans `docs/open-questions.md`.

## Import et Normalisation

- [x] Documenter les fichiers Excel, feuilles, colonnes et roles dans `docs/excel-sources.md`.
- [x] Documenter la vue projet dans `docs/project-overview.md`.
- [x] Encapsuler la lecture Excel/CSV dans un service d'import dedie.
- [x] Limiter Pandas a la lecture, au nettoyage et a la jointure initiale des fichiers.
- [x] Transformer les lignes importees en objets metier typés.
- [x] Preparer un jeu de donnees CSV representatif depuis les fichiers Excel.

## Domaine `account-mapping`

- [x] Creer le domaine `account_mapping`.
- [x] Creer le service de jointure comptes GL + plan comptable.
- [x] Creer le service de classification RAS preliminaire avec justification et niveau de confiance.
- [x] Isoler les constantes metier du mapping dans un module `constants.py`.
- [x] Sortir les regles et textes RAS vers `docs/reference/ras-classification-rules.csv`.
- [x] Charger le referentiel RAS via la configuration API.
- [x] Creer les schemas Pydantic et contrats de reponse explicites.

## Couche FastAPI

- [x] Initialiser FastAPI autour du coeur metier.
- [x] Configurer le prefixe global `/api`.
- [x] Ajouter `GET /api/health`.
- [x] Creer `GET /api/account-mappings`.
- [x] Creer `POST /api/account-mappings/import-from-files`.

## Tests et Verification

- [x] Cadrer la strategie actuelle: tests unitaires uniquement pour le moment.
- [x] Ajouter les tests des objets metier et contrats.
- [x] Ajouter les tests unitaires du service d'import CSV.
- [x] Renforcer les tests unitaires sur les cas limites: fichier vide, extension non supportee, libelle vide, doublons plan comptable.
- [ ] Reporter les tests d'integration Excel/Docker a une phase ulterieure.
- [x] Ajouter les tests unitaires du repository fichier ou memoire.
- [x] Ajouter les tests unitaires du service `account_mapping`.
- [x] Ajouter les tests unitaires du classifieur RAS preliminaire.
- [x] Ajouter les tests unitaires du loader de referentiel RAS.
- [x] Ajouter les tests unitaires sur les fixtures CSV representatives.
- [x] Ajouter le test health.
- [x] Ajouter les tests unitaires du router `account_mapping`.
- [x] Verifier l'import des 139 comptes GL.
- [x] Verifier que 138 comptes obtiennent un libelle depuis le plan comptable.
- [x] Verifier que `44910002` ressort comme compte sans libelle.
- [x] Executer les tests metier/import/router disponibles localement: `PYTHONPATH=. python3 -m pytest app/account_mapping/tests -q` avec 35 tests passes.
- [x] Verifier la compilation Python: `PYTHONPATH=. python3 -m compileall app tests`.
- [ ] Executer lint, typecheck et tests API via Docker. Bloque localement: Docker absent.

## CI/CD Future

- [ ] Etudier les pipelines existants dans `portefolio` et autres projets de reference.
- [ ] Ajouter une CI API: build Docker, lint, typecheck, tests.
- [ ] Ajouter une CI front quand le socle front existe.
- [ ] Ajouter les controles de secrets et fichiers sensibles avant merge.
- [ ] Ajouter une strategie CD apres validation de l'environnement cible.

## Migration Infrastructure Future

- [ ] Introduire PostgreSQL uniquement apres validation du POC CSV/Pandas.
- [ ] Ajouter une implementation PostgreSQL de `AccountMappingRepository`.
- [ ] Ajouter les migrations versionnees, par exemple avec Alembic si SQLAlchemy est retenu.
- [ ] Conserver les endpoints et contrats existants pendant la migration.
