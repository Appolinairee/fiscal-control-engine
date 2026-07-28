# Todo API

Checklist operationnelle du chantier API. Les cases seront cochees au fur et a mesure.

## Socle Python

- [x] Mettre a jour les skills locales de standards: TDD, architecture, revue de code, revue adversariale.
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

## Domaine `rag-source`

- [x] Definir le format documentaire dans `docs/rag-source-format.md`.
- [x] Creer les objets metier typés pour les sources fiscales RAG.
- [x] Distinguer documents anonymises et uploads utilisateur.
- [x] Bloquer l'indexation des uploads utilisateur tant qu'ils ne sont pas valides.
- [x] Definir le contrat interne de chunk fiscal sans route HTTP.
- [x] Implementer le chunking par blocs article/section/paragraphe avec fenetre de mots en secours.
- [x] Preparer 25 questions d'evaluation RAG dans `docs/reference/rag-evaluation-questions.csv`.
- [x] Inventorier les fichiers disponibles dans `docs/rag-corpus-inventory.md`.
- [x] Creer `docs/reference/rag-question-expectations.csv` avec 3 refus prets et 22 questions en attente de source.
- [x] Ajouter `docs/reference/rag-mini-corpus.csv` pour les procedures internes non fiscales.
- [x] Associer les questions internes pretes a des chunks attendus.
- [x] Valider le mini corpus: 5 blocs, 5 chunk refs, 12 attentes pretes, 13 sources fiscales manquantes.
- [x] Generaliser les objets internes RAG avec aliases de compatibilite `Fiscal...`.
- [x] Ajouter une recherche lexicale locale sans LLM ni embeddings.
- [x] Ajouter un loader CSV generique pour mini corpus RAG.
- [x] Valider le flux local corpus -> chunks -> recherche.
- [x] Creer `docs/source-corpus/` avec templates generiques et squelettes fiscaux.
- [x] Ajouter un validateur local des sources Markdown: draft, placeholders et metadonnees manquantes.
- [x] Verifier que les 3 squelettes fiscaux sont detectes et non indexables.
- [x] Ajouter un loader Markdown qui transforme une source validee en blocs RAG.
- [x] Verifier le scan reel: 3 sources Markdown, 0 indexable, 3 bloquees.
- [x] Ajouter l'export Markdown valide vers `docs/reference/rag-source-corpus.generated.csv`.
- [x] Verifier l'export reel: 3 sources scannees, 0 source exportee, 0 bloc exporte, 3 sources bloquees.
- [x] Definir les contrats internes embeddings/index vectoriel sans modele externe.
- [x] Ajouter un index vectoriel local en memoire pour tests.
- [x] Ajouter un provider embeddings deterministe pour tests.
- [x] Valider le pipeline chunks -> embeddings -> index vectoriel local.
- [x] Brancher un provider embeddings local ou configurable via `sentence-transformers`.
- [x] Ajouter une factory de provider embeddings configuree par nom.
- [x] Documenter le flux RAG complet dans `docs/rag-flow-mermaid.md`.
- [ ] Remplir/valider les squelettes fiscaux puis associer les 13 questions restantes.

## Couche FastAPI Future

- [x] Initialiser FastAPI autour du coeur metier.
- [x] Configurer le prefixe global `/api`.
- [x] Ajouter `GET /api/health`.
- [ ] Reporter les routes `account_mapping` apres stabilisation de la logique interne.
- [ ] Creer `GET /api/account-mappings`.
- [ ] Creer `POST /api/account-mappings/import-from-files` avec chemins securises ou source configuree.

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
- [x] Ajouter les tests unitaires du domaine `rag_source`.
- [x] Ajouter les tests unitaires du chunker fiscal.
- [x] Ajouter les tests unitaires prouvant le support de sources RAG non fiscales.
- [x] Ajouter les tests unitaires du loader de corpus RAG.
- [x] Ajouter les tests unitaires du retriever lexical.
- [x] Ajouter le test de flux local RAG sans LLM.
- [x] Ajouter les tests unitaires du validateur de sources RAG Markdown.
- [x] Ajouter les tests unitaires du loader Markdown de sources RAG.
- [x] Ajouter les tests unitaires de l'export Markdown vers CSV corpus RAG.
- [x] Ajouter les tests unitaires du provider embeddings deterministe.
- [x] Ajouter les tests unitaires de l'index vectoriel memoire.
- [x] Ajouter le test de pipeline vectoriel local.
- [x] Ajouter les tests unitaires du provider `sentence-transformers` optionnel.
- [x] Ajouter les tests unitaires de la factory embeddings.
- [x] Ajouter les tests unitaires sur les fixtures CSV representatives.
- [x] Ajouter le test health.
- [ ] Ajouter les tests unitaires du router `account_mapping` quand les routes seront reprises.
- [x] Verifier l'import des 139 comptes GL.
- [x] Verifier que 138 comptes obtiennent un libelle depuis le plan comptable.
- [x] Verifier que `44910002` ressort comme compte sans libelle.
- [x] Executer les tests metier/import disponibles localement: `PYTHONPATH=. python3 -m pytest app/account_mapping/tests -q` avec 33 tests passes.
- [x] Executer les tests chunker disponibles localement: `PYTHONPATH=. python3 -m pytest app/rag_source/tests/test_chunker.py -q` avec 5 tests passes.
- [x] Executer les tests RAG source disponibles localement: `PYTHONPATH=. python3 -m pytest app/rag_source/tests -q` avec 43 tests passes.
- [x] Executer tous les tests API disponibles localement: `PYTHONPATH=. python3 -m pytest -q` avec 77 tests passes.
- [x] Executer le lint API localement: `PYTHONPATH=. python3 -m ruff check app`.
- [x] Executer le typecheck API localement: `PYTHONPATH=. python3 -m mypy app`.
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
