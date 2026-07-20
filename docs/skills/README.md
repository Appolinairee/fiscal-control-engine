# Skills Projet

Ces skills sont importees depuis `choupis` et adaptees comme boite a outils projet. Elles ne remplacent pas les regles obligatoires de `AGENTS.md` et `.agents/rules/`; elles guident des travaux ponctuels.

`shopinx` ne contient pas de dossiers `SKILL.md`: ses apports ont ete repris dans `.agents/rules/`.

| Skill | Usage dans ce projet | Statut |
| --- | --- | --- |
| [shipping-artifacts](shipping-artifacts/SKILL.md) | Produire les docs durables: architecture, variables, tests, automation quand l'IA existe | A utiliser tot |
| [intended-vs-implemented](intended-vs-implemented/SKILL.md) | Auditer l'ecart entre docs fiscales/API et implementation reelle | A utiliser en revue |
| [create-prd](create-prd/SKILL.md) | Transformer le cahier des charges fiscal en PRD exploitable | A adapter au CDC existant |
| [user-stories](user-stories/SKILL.md) | Decouper les fonctionnalites en backlog testable | A utiliser pour planifier |
| [test-scenarios](test-scenarios/SKILL.md) | Formaliser les cas de test metier, limites et refus | A utiliser pour API et controles fiscaux |
| [todo-plan-tracker](todo-plan-tracker/SKILL.md) | Garder `todo.md`, `api/todo.md` et les futurs todos de domaine synchronises | A utiliser a chaque mise a jour de plan |
| [pre-mortem](pre-mortem/SKILL.md) | Identifier les risques avant demo ou mise en production | A utiliser avant livraison |
| [prioritization-frameworks](prioritization-frameworks/SKILL.md) | Arbitrer le backlog si plusieurs chantiers se concurrencent | Usage ponctuel |
| [taste-skill](taste-skill/SKILL.md) | Inspiration frontend uniquement si une interface visuelle est demandee | A filtrer fortement |
| [redesign-skill](redesign-skill/SKILL.md) | Ameliorer une interface existante apres une premiere version | Differe |

Notes:

- Ne pas creer de todo dans `docs/`.
- Les taches restent dans `todo.md` a la racine.
- Pour l'etape API, les skills les plus utiles sont `todo-plan-tracker`, `shipping-artifacts`, `user-stories`, `test-scenarios` et `intended-vs-implemented`.
