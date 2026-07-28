# Todo

Checklist vivante du projet. Les cases seront cochees au fur et a mesure de l'avancement.

## API

- [x] Clarifier les regles projet, API et front depuis `choupis` et `shopinx`.
- [x] Importer et cadrer les skills projet dans `docs/skills/`.
- [x] Synchroniser les skills locales avec `/home/appolinaire/starred-skills`: TDD, architecture, revue, RAG.
- [x] Creer les dossiers `api/` et `front/`.
- [x] Importer la skill de mise a jour des plans todo.
- [x] Realigner l'API sur le CDC: FastAPI/Python, POC CSV/Pandas, PostgreSQL differe.
- [x] Remplacer le `Makefile` API par Docker + scripts racine.
- [x] Documenter la vue projet dans `docs/project-overview.md`.
- [x] Documenter les points non clarifies dans `docs/open-questions.md`.
- [x] Ajouter un README projet concis.
- [x] Garder les regles et skills assistant en local via `.gitignore`.
- [ ] Suivre le detail API dans `api/todo.md`.

## CI/CD

- [ ] Inspirer le pipeline des projets `portefolio` et autres references.
- [ ] Ajouter CI API: Docker build, lint, typecheck, tests.
- [ ] Ajouter CD apres clarification de l'environnement cible.

## Front

- [ ] A definir apres le socle API.

## Regles fiscales

- [ ] A definir apres le referentiel comptes GL -> categories RAS.

## RAG / LLM

- [x] Echelon 0: documenter l'architecture RAG cible, les limites et les garde-fous LLM.
- [x] Ajouter les skills locales utiles au RAG: `sentence-transformers`, `chroma`, `llamaindex`.
- [x] Echelon 1: definir le format des documents sources et metadonnees obligatoires.
- [x] Echelon 2: definir la strategie de chunking fiscal par article/section/paragraphe.
- [x] Echelon 3a: preparer 25 questions d'evaluation RAG.
- [x] Echelon 3b: inventorier les fichiers anonymises disponibles pour le corpus RAG.
- [x] Echelon 3c: separer questions pretes au refus et questions en attente de source fiscale.
- [x] Echelon 3d: ajouter un mini corpus interne pour refus, citations, confidentialite et escalade.
- [x] Echelon 3e: valider 5 chunks internes et 12 questions pretes.
- [x] Echelon 3f: rendre le socle RAG generique, fiscalite comme premier domaine seulement.
- [x] Echelon 3g: creer `docs/source-corpus/` et les templates de sources.
- [x] Echelon 3h: ajouter un validateur local qui bloque les sources draft ou incompletes.
- [x] Echelon 3i: ajouter le loader Markdown pour transformer une source validee en blocs RAG.
- [x] Echelon 3j: ajouter l'export Markdown valide vers CSV corpus RAG.
- [ ] Echelon 3k: remplir/valider les squelettes fiscaux puis associer les 13 questions restantes.
- [x] Echelon 4: implementer une recherche locale simple sans LLM.
- [x] Echelon 5a: definir les contrats internes embeddings/index vectoriel sans modele externe.
- [x] Echelon 5b: ajouter un index vectoriel local en memoire pour tests.
- [x] Echelon 5c: brancher un provider embeddings local ou configurable.
- [x] Documenter le flux RAG complet en schemas Mermaid.
- [ ] Echelon 5d: evaluer lexical vs embeddings sur corpus valide.
- [ ] Echelon 6: ajouter recherche hybride et reranking.
- [ ] Echelon 7: brancher un petit modele pour explication uniquement, avec citations.
- [ ] Echelon 8: ajouter evaluation, traces, controles de qualite et securite.

## Rapports

- [ ] A definir apres les premiers controles API.
