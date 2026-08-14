"""
Notes d'architecture et choix de design.

Chaque patch peut ajouter une entrée ici. Le contenu est affiché
dans la popup d'information accessible depuis l'icône (i) en haut
à droite de la fenêtre.

PATCH 80 : chaque entrée existe en français et en anglais ; `tr()`
n'est pas utilisé ici (texte trop long pour `ui.i18n`), on sélectionne
directement la liste voulue via `get_design_notes()`.
"""

from ui.i18n import get_language, LANGUAGE_EN

DESIGN_NOTES_FR: list[tuple[str, str]] = [
    (
        "Architecture générale",
        "Le Document est l'unique source de vérité. Chaque bloc "
        "possède un identifiant UUID, un type et des données "
        "(<i>data</i>). Les vues n'affichent que ce que contient "
        "le document.",
    ),
    (
        "PATCH 3 — Bloc Texte",
        "Basé sur QTextEdit : édition libre, retour à la ligne, "
        "sélection et copier/coller sont natifs à Qt, pas de code "
        "supplémentaire nécessaire.",
    ),
    (
        "PATCH 4 — Titres",
        "H1/H2/H3 sont des blocs distincts (QLineEdit), avec une "
        "taille de police qui dépend du niveau.",
    ),
    (
        "PATCH 5 — Barre d'outils",
        "Un bug a été corrigé : le bouton « Nouveau bloc » passait "
        "involontairement un booléen comme contenu (le signal Qt "
        "<i>triggered(bool)</i>). Corrigé via une lambda sans "
        "argument.",
    ),
    (
        "PATCH 6 — Mise en forme",
        "Le contenu est sauvegardé en HTML (en plus du texte brut) "
        "pour préserver la mise en forme. Citation et code restent "
        "simplifiés (pas de bordure visuelle) pour l'instant.",
    ),
    (
        "PATCH 7 — Gestion du curseur",
        "Maj+Entrée sépare le bloc en deux ; Entrée seule fait un "
        "retour à la ligne dans le même bloc (inversé par rapport au "
        "comportement Notion d'origine, sur demande explicite). "
        "Retour arrière en début de bloc vide supprime le bloc, "
        "sinon il fusionne avec le bloc texte précédent (la fusion "
        "avec un titre n'est pas encore supportée).",
    ),
    (
        "PATCH 8 — Sauvegarde",
        "Format JSON versionné (<i>version</i> + <i>blocks</i>). Un "
        "registre (<i>blocks/registry.py</i>) reconstruit la bonne "
        "classe de bloc à partir du type stocké, pour que Nouveau, "
        "Ouvrir, Sauvegarder et Sauvegarder sous partagent le même "
        "rendu générique du document.",
    ),
    (
        "PATCH 9 — Chargement",
        "La reconstruction (id, type, données complètes) était déjà "
        "assurée par <i>Document.from_dict</i> (PATCH 8) ; ce patch "
        "ajoute la validation stricte (clé <i>blocks</i> manquante, "
        "version de fichier trop récente, type de bloc inconnu) et "
        "un test de non-régression qui prouve que chaque champ "
        "survit à l'aller-retour sauvegarde/chargement.",
    ),
    (
        "PATCH 10 — Bloc Checklist",
        "Chaque élément est {texte, coché} dans <i>data['items']</i>. "
        "Enregistré dans <i>blocks/registry.py</i> comme prévu, donc "
        "compatible sauvegarde/chargement sans modification du "
        "PATCH 8/9.",
    ),
    (
        "PATCH 11 — Checklist « À faire / Déjà fait »",
        "<i>ChecklistBlock.sort_by_status</i> trie (tri stable) les "
        "tâches non cochées avant les cochées. Le widget appelle ce "
        "tri à la construction (donc aussi après un chargement) et "
        "après chaque coche, puis reconstruit ses lignes dans le "
        "nouvel ordre : l'utilisateur ne déplace jamais rien "
        "manuellement.",
    ),
    (
        "PATCH 12 — Bloc Image",
        "Image encodée en base64 directement dans <i>data</i> : "
        "aucun fichier annexe, donc compatible tel quel avec la "
        "sauvegarde JSON (PATCH 8/9) et les tests de round-trip. "
        "Redimensionnement via une largeur (hauteur recalculée au "
        "ratio d'origine par Qt). Déplacement/suppression réutilisent "
        "<i>Document.move_block</i> et <i>remove_block</i> (PATCH 2), "
        "exposés ici par deux boutons ↑/↓ ; le drag & drop générique "
        "arrive au PATCH 13.",
    ),
    (
        "PATCH 13 — Drag & Drop",
        "<i>BlockContainer</i> ajoute une poignée « ⠿ » à chaque bloc "
        "et démarre un <i>QDrag</i> (mime-type privé transportant "
        "l'ID du bloc). <i>BlocksArea</i>, désormais le widget "
        "central, accepte le dépôt et calcule l'index d'insertion "
        "depuis la position Y. Le tout passe par "
        "<i>Document.move_block</i> (PATCH 2) : générique, donc "
        "valable pour tous les types de blocs (texte, titres, "
        "checklists, images, et tableaux au PATCH 14). Les boutons "
        "↑/↓ de l'image (PATCH 12) restent en complément accessible.",
    ),
    (
        "Correctif — API ChecklistBlock",
        "Les tests du PATCH 10 attendaient une API par id d'élément "
        "(<i>add_item</i> retourne l'item, <i>remove_item</i>/"
        "<i>set_item_text</i>/<i>set_item_checked</i> prennent un id) "
        "alors que l'implémentation était basée sur l'index. Corrigé "
        "en généralisant les id, avec rétrocompatibilité : un id est "
        "généré à la volée pour les checklists sauvegardées avant ce "
        "correctif. Le widget (PATCH 10/11) suit désormais le même id "
        "par ligne plutôt que sa position.",
    ),
    (
        "PATCH 26 — Menu contextuel",
        "Clic droit complet, en deux temps. Sur un bloc : "
        "<i>BlockContainer.contextMenuEvent</i> délègue à "
        "<i>MainWindow._show_block_context_menu</i>, qui propose "
        "Dupliquer (via <i>blocks.registry.block_from_dict</i> avec "
        "un nouvel id), Supprimer, Déplacer ↑/↓, et Convertir en "
        "(uniquement entre blocs à <i>content</i> texte simple : "
        "texte, titres, citation, code — la conversion préserve le "
        "contenu). Sur une zone vide : <i>BlocksArea</i> propose "
        "d'ajouter n'importe quel type de bloc en fin de document, "
        "via la même fabrique que le menu « / » (PATCH 25), désormais "
        "partagée (<i>_block_factory</i>) pour éviter toute "
        "divergence entre les deux menus.",
    ),
    (
        "PATCH 27 — Undo / Redo",
        "Une seule pile d'historique (<i>core/history.UndoHistory</i>), "
        "agnostique du type de bloc : chaque point d'annulation est un "
        "snapshot JSON complet du document (même sérialisation que la "
        "sauvegarde du PATCH 8/9), comparé à l'état courant par un "
        "<i>QTimer</i> qui sonde toutes les 600 ms — ce qui regroupe "
        "les frappes rapides en un seul « undo » par pause, sans "
        "instrumenter chaque widget de bloc individuellement. Ctrl+Z "
        "force de toute façon un flush immédiat, donc annuler "
        "fonctionne même juste après une frappe. Un filtre d'événements "
        "au niveau de l'application intercepte Ctrl+Z/Ctrl+Y avant "
        "l'undo natif de QTextEdit/QLineEdit (désactivé sur le bloc "
        "texte) pour garantir un historique unique et cohérent.",
    ),
    (
        "PATCH 28 — Recherche",
        "<i>core/search.py</i> : fonction pure "
        "(<i>search_document</i>), testable sans Qt, qui parcourt "
        "texte/titres/citation/code, checklists, listes et les deux "
        "moteurs de tableau (PATCH 14 typé et PATCH 24 simple). "
        "<i>SearchDialog</i> (Ctrl+F) relance la recherche à chaque "
        "frappe et fait défiler jusqu'au résultat choisi. Cela a "
        "révélé l'absence de <i>QScrollArea</i> autour des blocs : "
        "ajoutée ici (prérequis pour qu'« aller au résultat » ait un "
        "sens), sans changer la logique de drag & drop (coordonnées "
        "toujours relatives à <i>BlocksArea</i>).",
    ),
    (
        "PATCH 29 — Remplacement",
        "<i>core/replace.py</i> (<i>replace_all</i>) suit les mêmes "
        "catégories de blocs que la recherche, avec une exception "
        "volontaire : dans le tableau typé (PATCH 15), seules les "
        "colonnes textuelles (texte, nombre, liste déroulante, liste "
        "multiple, éléments d'une checklist imbriquée) sont "
        "concernées — les colonnes Personne sont exclues (un "
        "renommage doit passer par le PATCH 16 pour rester "
        "synchronisé avec le registre), et Date/Durée/Booléen ne "
        "sont pas du texte. Remplacer un texte riche (PATCH 6) efface "
        "son HTML devenu incohérent avec le nouveau contenu. "
        "« Tout remplacer », dans <i>SearchDialog</i>, est une "
        "mutation du document comme une autre : elle est donc "
        "annulable via l'historique générique du PATCH 27, sans code "
        "supplémentaire.",
    ),
    (
        "PATCH 30 — Liens internes",
        "Un lien interne est une ancre HTML "
        "<code>&lt;a href=\"block://ID\"&gt;</code> insérée dans le "
        "texte riche (PATCH 6) : il profite donc gratuitement de la "
        "sauvegarde JSON (le HTML du bloc le contient déjà) sans "
        "nouveau format. Le sélecteur de bloc (<i>BlockPickerDialog</i>, "
        "ouvert via le bouton « Lien interne » de la toolbar) réutilise "
        "<i>core/block_preview.py</i> (aperçu textuel générique, testé "
        "seul) pour afficher chaque bloc candidat. Ctrl+Clic sur le "
        "lien émet <i>link_activated</i>, branché sur "
        "<i>_scroll_to_block</i> (PATCH 28) : navigation et recherche "
        "partagent le même mécanisme de défilement.",
    ),
    (
        "PATCH 41 — Documentation",
        "<code>README.md</code> à la racine : installation, "
        "commande de tests correcte (<code>pytest</code>, pas "
        "<code>unittest discover</code> — voir le correctif du "
        "PATCH 13), architecture en trois couches "
        "(<code>core</code>/<code>blocks</code>/<code>ui</code>), API "
        "interne des points d'entrée les plus réutilisés "
        "(<i>Document</i>, <i>block_from_dict</i>, <i>UndoHistory</i>, "
        "recherche/remplacement, export/import), format de sauvegarde "
        "JSON complet avec un exemple généré depuis le code (pas "
        "inventé à la main), et un guide en cinq étapes pour ajouter "
        "un nouveau type de bloc. <code>requirements.txt</code> / "
        "<code>requirements-dev.txt</code> ajoutés : absents jusqu'ici, "
        "alors que le README doit pouvoir s'appuyer dessus.",
    ),
    (
        "PATCH 42 — Version 1.0",
        "Stabilisation : nettoyage des imports inutilisés repérés par "
        "analyse statique (<code>pyflakes</code>, 0 avertissement "
        "restant sur <code>core/</code>, <code>blocks/</code>, "
        "<code>ui/</code>), et un test d'intégration bout-en-bout "
        "(<code>tests/test_full_document_integration.py</code>) : un "
        "document avec un bloc de chaque type, cycle complet "
        "sauvegarde/rechargement disque, recherche et remplacement "
        "transverses, puis un smoke-test <i>MainWindow</i> réel "
        "(ajout de neuf types de blocs, annulé puis rétabli en un "
        "seul geste). Gel des fonctionnalités et publication : "
        "<code>core/version.py</code> (source unique de la version, "
        "affichée dans le titre de fenêtre et « À propos ») et "
        "<code>CHANGELOG.md</code> résumant les 42 patches.",
    ),
]

DESIGN_NOTES_EN: list[tuple[str, str]] = [
    (
        "Overall architecture",
        "The Document is the single source of truth. Every block "
        "has a UUID identifier, a type and data "
        "(<i>data</i>). Views only render what the document "
        "actually contains.",
    ),
    (
        "PATCH 3 — Text block",
        "Built on QTextEdit: free editing, line breaks, selection "
        "and copy/paste are native to Qt, no extra code "
        "needed.",
    ),
    (
        "PATCH 4 — Headings",
        "H1/H2/H3 are separate blocks (QLineEdit), with a font "
        "size that depends on the level.",
    ),
    (
        "PATCH 5 — Toolbar",
        "A bug was fixed: the \"New block\" button unintentionally "
        "passed a boolean as content (Qt's "
        "<i>triggered(bool)</i> signal). Fixed with an argument-less "
        "lambda.",
    ),
    (
        "PATCH 6 — Formatting",
        "Content is saved as HTML (in addition to plain text) "
        "to preserve formatting. Quote and code blocks stay "
        "simplified (no visual border) for now.",
    ),
    (
        "PATCH 7 — Cursor handling",
        "Shift+Enter splits the block in two; Enter alone adds a "
        "line break within the same block (reversed compared to "
        "Notion's original behaviour, per explicit request). "
        "Backspace at the start of an empty block removes it, "
        "otherwise it merges with the previous text block (merging "
        "with a heading isn't supported yet).",
    ),
    (
        "PATCH 8 — Saving",
        "Versioned JSON format (<i>version</i> + <i>blocks</i>). A "
        "registry (<i>blocks/registry.py</i>) rebuilds the right "
        "block class from the stored type, so New, Open, Save and "
        "Save As all share the same generic document "
        "rendering.",
    ),
    (
        "PATCH 9 — Loading",
        "Reconstruction (id, type, full data) was already handled "
        "by <i>Document.from_dict</i> (PATCH 8); this patch adds "
        "strict validation (missing <i>blocks</i> key, file version "
        "too recent, unknown block type) and a regression test "
        "proving every field survives a save/load round trip.",
    ),
    (
        "PATCH 10 — Checklist block",
        "Each item is {text, checked} in <i>data['items']</i>. "
        "Registered in <i>blocks/registry.py</i> as expected, so "
        "already compatible with saving/loading without touching "
        "PATCH 8/9.",
    ),
    (
        "PATCH 11 — \"To do / Done\" checklist",
        "<i>ChecklistBlock.sort_by_status</i> stably sorts unchecked "
        "tasks before checked ones. The widget runs this sort on "
        "construction (so also after loading) and after every "
        "checkbox toggle, then rebuilds its rows in the new order: "
        "the user never has to move anything by hand.",
    ),
    (
        "PATCH 12 — Image block",
        "Image encoded as base64 straight into <i>data</i>: no "
        "companion file, so it's compatible as-is with JSON saving "
        "(PATCH 8/9) and the round-trip tests. Resized via a width "
        "value (height recomputed from the original ratio by Qt). "
        "Moving/deleting reuse <i>Document.move_block</i> and "
        "<i>remove_block</i> (PATCH 2), exposed here as two ↑/↓ "
        "buttons; generic drag & drop arrives in PATCH 13.",
    ),
    (
        "PATCH 13 — Drag & Drop",
        "<i>BlockContainer</i> adds a \"⠿\" handle to every block "
        "and starts a <i>QDrag</i> (private mime-type carrying the "
        "block ID). <i>BlocksArea</i>, now the central widget, "
        "accepts the drop and computes the insertion index from the "
        "Y position. It all goes through "
        "<i>Document.move_block</i> (PATCH 2): generic, so it works "
        "for every block type (text, headings, checklists, images, "
        "and tables in PATCH 14). The image's ↑/↓ buttons "
        "(PATCH 12) remain as an accessible alternative.",
    ),
    (
        "Fix — ChecklistBlock API",
        "PATCH 10's tests expected an item-id-based API "
        "(<i>add_item</i> returns the item, <i>remove_item</i>/"
        "<i>set_item_text</i>/<i>set_item_checked</i> take an id) "
        "while the implementation was index-based. Fixed by "
        "generalising ids, with backward compatibility: an id is "
        "generated on the fly for checklists saved before this "
        "fix. The widget (PATCH 10/11) now tracks the same id per "
        "row instead of its position.",
    ),
    (
        "PATCH 26 — Context menu",
        "Full right-click support, in two flavours. On a block: "
        "<i>BlockContainer.contextMenuEvent</i> delegates to "
        "<i>MainWindow._show_block_context_menu</i>, which offers "
        "Duplicate (via <i>blocks.registry.block_from_dict</i> with "
        "a new id), Delete, Move ↑/↓, and Convert to "
        "(only between simple text-<i>content</i> blocks: text, "
        "headings, quote, code — the conversion preserves the "
        "content). On an empty area: <i>BlocksArea</i> offers to "
        "add any block type at the end of the document, "
        "via the same factory as the \"/\" menu (PATCH 25), now "
        "shared (<i>_block_factory</i>) to avoid any divergence "
        "between the two menus.",
    ),
    (
        "PATCH 27 — Undo / Redo",
        "A single history stack (<i>core/history.UndoHistory</i>), "
        "agnostic of block type: each undo point is a full JSON "
        "snapshot of the document (same serialisation as saving in "
        "PATCH 8/9), compared to the current state by a "
        "<i>QTimer</i> polling every 600 ms — which groups fast "
        "typing into a single \"undo\" per pause, without "
        "instrumenting every block widget individually. Ctrl+Z "
        "always forces an immediate flush, so undo works even right "
        "after a keystroke. An application-level event filter "
        "intercepts Ctrl+Z/Ctrl+Y before QTextEdit/QLineEdit's "
        "native undo (disabled on the text block) to guarantee a "
        "single, consistent history.",
    ),
    (
        "PATCH 28 — Search",
        "<i>core/search.py</i>: a pure function "
        "(<i>search_document</i>), testable without Qt, that scans "
        "text/headings/quote/code, checklists, lists and both table "
        "engines (typed PATCH 14 and simple PATCH 24). "
        "<i>SearchDialog</i> (Ctrl+F) reruns the search on every "
        "keystroke and scrolls to the chosen result. This exposed "
        "the lack of a <i>QScrollArea</i> around the blocks: added "
        "here (a prerequisite for \"go to result\" to make sense), "
        "without changing the drag & drop logic (coordinates still "
        "relative to <i>BlocksArea</i>).",
    ),
    (
        "PATCH 29 — Replace",
        "<i>core/replace.py</i> (<i>replace_all</i>) follows the "
        "same block categories as search, with one deliberate "
        "exception: in the typed table (PATCH 15), only text "
        "columns (text, number, dropdown, multi-select, items of a "
        "nested checklist) are affected — Person columns are "
        "excluded (a rename must go through PATCH 16 to stay in "
        "sync with the registry), and Date/Duration/Boolean aren't "
        "text. Replacing rich text (PATCH 6) clears its HTML, which "
        "would otherwise become inconsistent with the new content. "
        "\"Replace all\", in <i>SearchDialog</i>, is a document "
        "mutation like any other: it's therefore undoable via "
        "PATCH 27's generic history, with no extra code.",
    ),
    (
        "PATCH 30 — Internal links",
        "An internal link is an HTML anchor "
        "<code>&lt;a href=\"block://ID\"&gt;</code> inserted into "
        "rich text (PATCH 6): it therefore gets JSON saving for "
        "free (the block's HTML already contains it), no new "
        "format needed. The block picker (<i>BlockPickerDialog</i>, "
        "opened via the toolbar's \"Internal link\" button) reuses "
        "<i>core/block_preview.py</i> (generic text preview, tested "
        "on its own) to display each candidate block. Ctrl+Click on "
        "the link emits <i>link_activated</i>, wired to "
        "<i>_scroll_to_block</i> (PATCH 28): navigation and search "
        "share the same scrolling mechanism.",
    ),
    (
        "PATCH 41 — Documentation",
        "<code>README.md</code> at the root: install instructions, "
        "the correct test command (<code>pytest</code>, not "
        "<code>unittest discover</code> — see the PATCH 13 fix), "
        "the three-layer architecture "
        "(<code>core</code>/<code>blocks</code>/<code>ui</code>), the "
        "internal API of the most reused entry points "
        "(<i>Document</i>, <i>block_from_dict</i>, <i>UndoHistory</i>, "
        "search/replace, export/import), the full JSON save format "
        "with an example generated from the code (not hand-written), "
        "and a five-step guide for adding a new block type. "
        "<code>requirements.txt</code> / "
        "<code>requirements-dev.txt</code> added: missing until now, "
        "even though the README needs to reference them.",
    ),
    (
        "PATCH 42 — Version 1.0",
        "Stabilisation: cleaned up unused imports flagged by static "
        "analysis (<code>pyflakes</code>, 0 warnings left on "
        "<code>core/</code>, <code>blocks/</code>, "
        "<code>ui/</code>), and an end-to-end integration test "
        "(<code>tests/test_full_document_integration.py</code>): a "
        "document with one block of every type, a full disk "
        "save/reload cycle, cross-cutting search and replace, then "
        "a real <i>MainWindow</i> smoke test "
        "(adding nine block types, undone then redone in one "
        "step). Feature freeze and release: "
        "<code>core/version.py</code> (single source of the "
        "version, shown in the window title and \"About\") and "
        "<code>CHANGELOG.md</code> summarising the 42 patches.",
    ),
]


def get_design_notes() -> list[tuple[str, str]]:
    """Retourne les notes de design dans la langue courante."""
    if get_language() == LANGUAGE_EN:
        return DESIGN_NOTES_EN
    return DESIGN_NOTES_FR


# Conservé pour compatibilité ascendante (ancien nom importé ailleurs).
DESIGN_NOTES = DESIGN_NOTES_FR
