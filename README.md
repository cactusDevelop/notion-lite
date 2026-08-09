# Notion Lite

Éditeur de documents façon Notion, en blocs, construit avec Python et
PySide6 (Qt). Application de bureau locale : les documents sont des
fichiers `.json` sur disque, sans compte ni serveur.

Ce document sert de référence : architecture générale, API interne,
format de sauvegarde JSON, et guide pour ajouter un nouveau type de
bloc. Le détail des choix de conception patch par patch reste dans
**Aide → Informations** (`ui/design_notes.py`), qui reste la source la
plus précise sur le *pourquoi* de chaque décision ; ce README se
concentre sur le *comment* utiliser et étendre le code.

## Sommaire

- [Installation et lancement](#installation-et-lancement)
- [Tests](#tests)
- [Architecture](#architecture)
- [API interne](#api-interne)
- [Format de sauvegarde JSON](#format-de-sauvegarde-json)
- [Ajouter un nouveau type de bloc](#ajouter-un-nouveau-type-de-bloc)

## Installation et lancement

```bash
pip install -r requirements.txt
python3 main.py
```

Pour lancer les tests, installer aussi les dépendances de
développement (`requirements-dev.txt` ajoute `pytest`) :

```bash
pip install -r requirements-dev.txt
```

Testé avec Python 3.12 et PySide6 6.11. `requirements.txt` fixe une
borne minimale (`PySide6>=6.5`) plutôt qu'une version exacte : le
projet n'utilise que des API Qt stables depuis plusieurs versions.

## Tests

La suite compte environ 200 tests (`tests/`), un mélange de style
`unittest.TestCase` (les modules les plus anciens) et de fonctions
`pytest` nues (la majorité depuis le PATCH 15). **Utiliser `pytest`**,
qui exécute les deux styles :

```bash
python3 -m pytest tests/ -q
```

`python -m unittest discover` ne fait tourner que les classes
`TestCase` et ignore silencieusement les modules écrits en style
pytest (aucune erreur affichée) : sur cette base, cela représente
plus de la moitié des tests. Ce n'est pas un bug applicatif, juste la
mauvaise commande — mentionné ici pour ne pas le re-découvrir plus
tard.

Les tests d'UI (Qt) tournent sans affichage réel via la plateforme
offscreen, pas besoin d'environnement graphique :

```bash
QT_QPA_PLATFORM=offscreen python3 -m pytest tests/ -q
```

## Architecture

Trois couches, dépendances à sens unique (`ui` → `blocks` → `core`,
jamais l'inverse) :

```
core/     Logique indépendante de Qt : Document, Block, historique
          undo/redo, recherche, remplacement, export/import,
          registre d'icônes, données d'emoji, etc. Tout ce dossier
          est testable sans QApplication.
blocks/   Un module par type de bloc (TextBlock, HeadingBlock,
          ChecklistBlock, TableBlock, ImageBlock, ...). Chaque bloc
          hérite de core.block.Block et expose ses propres accesseurs
          typés (ex. TableBlock.add_column, ChecklistBlock.add_item).
          blocks/registry.py fait le pont JSON -> classe concrète.
ui/       Widgets Qt. ui/main_window.py est le chef d'orchestre ;
          ui/blocks/ contient un widget par type de bloc (le pendant
          visuel de blocks/) ; ui/themes/ gère la palette Qt.
```

Principe central : **`core.document.Document` est l'unique source de
vérité**. Toute mutation (ajout/suppression/déplacement de bloc,
édition de texte, case cochée, cellule de tableau modifiée...) passe
par un appel sur `Document` ou sur un `Block` qu'il contient — jamais
uniquement dans un widget. C'est ce qui rend gratuits, sans code
spécifique par type de bloc :

- la **sauvegarde JSON** (PATCH 8/9) : `Document.to_dict()` sérialise
  tout ce qui existe ;
- l'**undo/redo** (PATCH 27) : l'historique est une pile de snapshots
  JSON du document entier, comparés périodiquement à l'état courant ;
- la **recherche/remplacement** (PATCH 28/29) : parcourt les blocs du
  document, pas les widgets.

`ui/main_window.py` fait le lien entre les deux mondes : il maintient
`self._document` (un `Document`) et une colonne de widgets
(`BlocksArea`, dans un `QScrollArea`), un widget par bloc, enveloppé
dans un `BlockContainer` qui ajoute la poignée de glisser-déposer
(PATCH 13) et le clic droit (PATCH 26). `_render_document()`
reconstruit entièrement cette colonne de widgets à partir de
`self._document` — c'est la méthode appelée après toute opération qui
change la structure du document (ajout, suppression, déplacement,
conversion, undo/redo, ouverture de fichier...).

## API interne

Points d'entrée les plus utiles pour étendre le projet.

### `core.block.Block`

Classe de base (dataclass) de tous les blocs :

```python
@dataclass
class Block:
    type: str
    data: dict[str, Any]
    id: str  # UUID, généré automatiquement si omis

    def to_dict(self) -> dict: ...          # {"id", "type", "data"}

    @classmethod
    def from_dict(cls, raw: dict) -> Block: ...
```

Chaque sous-classe concrète (`TextBlock`, `HeadingBlock`, ...) stocke
ses champs dans `data` et expose des propriétés typées par-dessus
(ex. `TextBlock.content`, `TableBlock.columns`). Voir
[Ajouter un nouveau type de bloc](#ajouter-un-nouveau-type-de-bloc).

### `core.document.Document`

```python
doc = Document()

doc.add_block(block, index=None)      # ajoute (fin par défaut)
doc.remove_block(block_id) -> bool
doc.move_block(block_id, new_index) -> bool
doc.find_block(block_id) -> Block | None
doc.blocks -> list[Block]             # copie ordonnée

# Registre des personnes (PATCH 16), partagé par les colonnes
# "Personne" des tableaux :
doc.add_person(name, color=None) -> dict
doc.rename_person(person_id, name) -> bool
doc.remove_person(person_id) -> bool  # purge aussi les tableaux
doc.people -> list[dict]

# Favoris (PATCH 31) :
doc.toggle_favorite(block_id) -> bool | None
doc.favorite_blocks() -> list[Block]

# Sauvegarde JSON (PATCH 8/9) :
doc.to_dict() -> dict
Document.from_dict(raw) -> Document   # lève ValueError si invalide
```

### `blocks.registry.block_from_dict(raw: dict) -> Block`

Point d'entrée unique de reconstruction : lit `raw["type"]` et
instancie la classe concrète correspondante. Utilisé par
`Document.from_dict`, mais aussi partout où un bloc doit être
dupliqué (PATCH 26 : `MainWindow._duplicate_block` fait
`block_from_dict({**block.to_dict(), "id": nouveau_uuid})`).

### `core.history.UndoHistory`

Pile undo/redo générique, indépendante de Qt (testable seule) :

```python
history = UndoHistory(initial_snapshot)  # une chaîne (JSON du document)
history.check(current_snapshot) -> bool  # crée un point si ça a changé
history.undo(current_snapshot) -> str | None
history.redo() -> str | None
```

`MainWindow` l'alimente avec `json.dumps(document.to_dict(), sort_keys=True)`
et la sonde toutes les 600 ms (`QTimer`) pour regrouper les frappes
rapides en un seul point d'annulation ; `Ctrl+Z` force un flush
immédiat via `history.undo(...)`, donc annuler fonctionne même sans
attendre le sondage.

### `core.search` / `core.replace`

```python
search_document(document, query) -> list[SearchResult]   # PATCH 28
replace_all(document, query, replacement) -> int          # PATCH 29
```

Deux fonctions pures qui parcourent les mêmes catégories de blocs
(texte, checklists, listes, tableaux typés et simples). `replace_all`
exclut volontairement les colonnes "Personne" (un renommage doit
passer par le registre de personnes) et les colonnes non textuelles
(date, durée, booléen).

### Export / import

```python
from core.document_html_export import document_to_html          # PATCH 36/38
from core.document_markdown_export import document_to_markdown  # PATCH 37
from core.document_markdown_import import markdown_to_document
from core.document_html_import import html_to_document
from ui.export_pdf import export_document_to_pdf                 # PATCH 36

document_to_html(document) -> str
document_to_markdown(document) -> str
markdown_to_document(text: str) -> Document
html_to_document(text: str) -> Document
export_document_to_pdf(document, filepath: str) -> None
```

Les fonctions de rendu (`_export`) sont pures ; seul `export_pdf`
touche Qt (`QTextDocument` + `QPrinter`), en réutilisant le HTML
généré par `document_to_html`.

## Format de sauvegarde JSON

Un fichier `.json` sauvegardé (PATCH 8/9) a la forme :

```json
{
  "version": 1,
  "blocks": [
    {
      "id": "940b9ae5-ab1a-4c48-be07-b63277f9c025",
      "type": "heading1",
      "data": { "content": "Notes de réunion", "level": 1 }
    },
    {
      "id": "8bc9a813-7eaa-4041-b3ce-b91fcd15c38d",
      "type": "text",
      "data": { "content": "Compte-rendu ci-dessous.", "html": "" }
    },
    {
      "id": "c6545adf-078c-4ec2-aba4-f651040dca66",
      "type": "checklist",
      "data": {
        "items": [
          { "id": "7431bc88-...", "text": "Relire le document", "checked": false }
        ]
      }
    }
  ],
  "people": [],
  "favorite_ids": ["8bc9a813-7eaa-4041-b3ce-b91fcd15c38d"]
}
```

- **`version`** : entier. `Document.from_dict` refuse (`ValueError`)
  tout fichier dont la version est supérieure à celle supportée par
  le code courant (`core.document.DOCUMENT_FORMAT_VERSION`), pour
  éviter de charger silencieusement un format plus récent.
- **`blocks`** : liste ordonnée. Chaque bloc a `id` (UUID), `type`
  (voir table ci-dessous) et `data` (forme propre à chaque type).
- **`people`** : registre partagé `{"id", "name", "color"}`
  (PATCH 16), référencé par les colonnes de type `person`.
- **`favorite_ids`** : liste d'`id` de blocs (PATCH 31).

### Types de blocs (`data["type"]`)

| type | contenu de `data` |
|---|---|
| `text` | `content` (texte brut), `html` (mise en forme riche, PATCH 6) |
| `heading1` / `heading2` / `heading3` | `content`, `level` |
| `checklist` | `items`: `[{id, text, checked}]`, toujours triés non cochés d'abord (PATCH 11) |
| `list` | `items`: `[{id, text}]`, `list_type`: `"bullet"` ou `"numbered"` |
| `quote` | `content` |
| `code` | `content`, `language` |
| `separator` | *(aucune donnée)* |
| `image` | `image_base64`, `format`, `width` (px, `None` = taille native) |
| `table` | `columns`: `[{id, name, type, options?, range?}]`, `rows`: `[{id, cells: {column_id: valeur}}]`. Forme de `valeur` selon `type` de colonne : voir le docstring de `blocks/table_block.py` (texte/nombre = chaîne, date = ISO ou `{start,end}`, durée = `{amount, unit}`, personne/liste-multiple = liste de chaînes, checklist imbriquée = `[{id,text,checked}]`) |
| `simple_table` | `rows`: liste de listes de chaînes (grille simple, sans colonnes typées, PATCH 24) |
| `gantt` | `table_block_id`, `label_column_id`, `date_column_id` — vue dérivée d'un `table` existant, ne duplique aucune donnée |

Les images sont encodées en base64 **directement dans le JSON** :
pas de fichier annexe à gérer, au prix d'une sauvegarde plus lourde
pour des images volumineuses.

## Ajouter un nouveau type de bloc

Cinq étapes, illustrées par un type `note` fictif (texte simple avec
un champ `color`) :

1. **`blocks/note_block.py`** — sous-classe de `Block`, type constant,
   propriétés typées :

   ```python
   NOTE_BLOCK_TYPE = "note"

   class NoteBlock(Block):
       def __init__(self, content="", color="#ffeb3b", id=None):
           super().__init__(
               type=NOTE_BLOCK_TYPE,
               data={"content": content, "color": color},
               id=id or str(uuid.uuid4()),
           )

       @property
       def content(self) -> str:
           return self.data.get("content", "")

       @content.setter
       def content(self, value: str) -> None:
           self.data["content"] = value
   ```

2. **`blocks/registry.py`** — ajouter la reconstruction dans
   `block_from_dict` (import + branche `if block_type == NOTE_BLOCK_TYPE`).

3. **`ui/blocks/note_block_widget.py`** — widget Qt de rendu/édition.

4. **`ui/main_window.py`** — brancher le nouveau widget dans
   `_create_content_widget_for_block` (dispatch par `isinstance`), et
   ajouter une méthode `_add_note_block` + une entrée dans
   `_block_factory` (partagée par le menu "/" du PATCH 25 et le clic
   droit du PATCH 26) pour pouvoir insérer le bloc.

5. **Tests** — `tests/test_note_block.py` (sérialisation, round-trip
   via `Document.to_dict`/`from_dict`) au minimum ; ajouter aussi le
   type aux fonctions qui parcourent tous les blocs si pertinent
   (`core/search.py`, `core/replace.py`, `core/block_preview.py`,
   `core/document_to_html`/`_to_markdown`).

Aucune de ces étapes ne touche à la sauvegarde JSON, à l'undo/redo, à
la recherche générique ou au glisser-déposer : ces mécanismes
opèrent sur `Document`/`Block` en général, pas sur des types
particuliers.
