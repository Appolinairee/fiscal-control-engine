# Sources Excel

Ce document decrit le role des fichiers Excel actuellement fournis et les colonnes attendues pour les premiers traitements.

## Vue d'ensemble

| Fichier | Role | Utilisation maintenant | Utilisation plus tard |
| --- | --- | --- | --- |
| `docs/Plan Comptable/Compte du Grand Livre.xlsx` | Liste distincte des comptes presents dans le Grand Livre | Source des comptes a cartographier | Peut etre regenere depuis le GL detaille |
| `docs/Plan Comptable/plan comptable.XLSX` | Referentiel compte -> libelle | Enrichir les comptes GL avec leur libelle | Source de reference pour toute qualification comptable |
| `docs/GL BF00.xlsx` | Grand Livre detaille | Reference et verification | Source des controles TVA/RAS transactionnels |

## Flux de l'etape actuelle

```text
Compte du Grand Livre.xlsx
        +
plan comptable.XLSX
        =
mapping comptes GL enrichis avec libelles
```

Cette etape ne detecte pas encore les anomalies fiscales. Elle prepare le referentiel des comptes a qualifier.

## Flux futur

```text
GL BF00.xlsx
        +
mapping comptes fiscalises
        +
regles TVA/RAS
        =
anomalies fiscales detectees
```

## `Compte du Grand Livre.xlsx`

- Feuille utile: `Feuil1`
- Dimension observee: `A1:A140`
- Colonne obligatoire:
  - `Compte`
- Role:
  - Fournir la liste des comptes distincts utilises dans le Grand Livre.
  - Eviter de parcourir le GL detaille pendant la premiere cartographie.
- Regles d'import:
  - Ignorer l'en-tete `Compte`.
  - Nettoyer les espaces.
  - Conserver les comptes alphanumeriques comme texte, par exemple `16000BSP`.
  - Supprimer les doublons en conservant le premier ordre d'apparition.

## `plan comptable.XLSX`

- Feuille utile: `Sheet1`
- Dimension observee: `A1:B20971`
- Colonnes obligatoires:
  - Colonne A: numero de compte. L'en-tete est vide dans le fichier source.
  - Colonne B: `Texte descr.cpt gén.`
- Role:
  - Fournir le libelle comptable de chaque compte.
- Regles d'import:
  - Lire la colonne A comme texte.
  - Lire `Texte descr.cpt gén.` comme libelle.
  - Nettoyer les espaces.
  - Rejeter les lignes sans numero de compte.
  - Rejeter ou signaler les lignes sans libelle.

## `GL BF00.xlsx`

- Feuilles observees:
  - `Feuil1`: extrait/pivot partiel.
  - `Compte`: liste partielle de comptes.
  - `Sheet1`: Grand Livre detaille.
  - `Sheet1 (2)`: copie apparente de `Sheet1`.
- Feuille utile pour les controles futurs:
  - `Sheet1`
- Colonnes observees utiles:
  - `Nº pièce`
  - `Compte`
  - `Domaine d'activité`
  - `Type de pièce`
  - `Date pièce`
  - `Période comptable`
  - `Clé comptabilisation`
  - `Montant devise document`
  - `Devise pièce`
  - `Code TVA`
  - `Texte`
  - `Centre de profit`
  - `Devise interne`
- Role:
  - Servir aux controles transactionnels TVA/RAS apres stabilisation du mapping comptes.
- Regles d'import futures:
  - Lire les montants comme valeurs numeriques exactes ou decimals selon le besoin fiscal.
  - Convertir les dates Excel en dates explicites.
  - Ne pas exposer de lignes completes dans les logs.
  - Traiter `Sheet1 (2)` comme doublon potentiel tant qu'une difference fonctionnelle n'est pas demontree.

## Ambiguites a confirmer

- `GL BF00.xlsx` contient plusieurs feuilles de comptes; `Compte du Grand Livre.xlsx` semble etre la liste distincte la plus complete pour l'etape actuelle.
- Le compte `44910002` est present dans la liste des comptes GL mais absent du plan comptable fourni.
- Le plan comptable a une premiere colonne sans nom; le code doit la traiter comme `account_number`.

## Referentiels Complementaires

- `docs/reference/ras-classification-rules.csv` contient les mots-cles, categories, justifications et actions requises de pre-classification RAS.
- Ce referentiel est versionne pour le POC et pourra migrer plus tard vers PostgreSQL.
