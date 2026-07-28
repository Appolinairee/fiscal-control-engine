# Bank Files Harmonizer

Agent de revue fiscale pre-declaratif pour harmoniser les fichiers comptables et preparer des controles TVA/RAS deterministes.

## Objectif

Le projet analyse les donnees du Grand Livre avant depot fiscal afin d'aider le responsable financier a reperer les incoherences possibles. Le systeme ne remplace ni le cabinet fiscal ni la decision humaine.

## Strategie Actuelle

- Construire d'abord le coeur metier interne.
- Garder FastAPI, PostgreSQL, RAG et frontend autour du coeur, pas dedans.
- Limiter Pandas a l'import et a la normalisation des fichiers.
- Garder les tests unitaires comme priorite immediate.
- Reporter les routes API avancees et les tests d'integration.

## Stack Cible

- API: Python FastAPI.
- Import/POC: Python + Pandas + CSV/Excel.
- Frontend: React + Tailwind CSS.
- Base cible: PostgreSQL apres validation du POC.
- RAG cible: ChromaDB.
- LLM: explication uniquement, jamais decision fiscale.

## Structure

```text
api/      coeur Python, future API FastAPI, tests unitaires
docs/     cahier des charges, sources Excel, referentiels metier
front/    frontend Next.js
```

## Commandes

Les commandes projet passent par Docker et les scripts racine:

```bash
npm run api:build
npm run api:dev
npm run api:test
npm run api:lint
npm run api:typecheck
```

Frontend:

```bash
cd front
npm install
npm run dev
```

Ouvrir ensuite `http://localhost:3000`.

Controles front:

```bash
cd front
npm run lint
npm run typecheck
npm run build
```

Dans cet environnement local, Docker n'est pas disponible. Les tests unitaires actuellement executables:

```bash
cd api
PYTHONPATH=. python3 -m pytest app/account_mapping/tests -q
```

## Documents Utiles

- [Vue projet](docs/project-overview.md)
- [Sources Excel](docs/excel-sources.md)
- [Questions ouvertes](docs/open-questions.md)
- [Plan API](api/todo.md)
- [Plan Front](front/todo.md)
