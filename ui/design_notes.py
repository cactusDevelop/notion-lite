"""
Notes d'architecture et choix de design.

Chaque patch peut ajouter une entrée ici. Le contenu est affiché
dans la popup d'information accessible depuis l'icône (i) en haut
à droite de la fenêtre.
"""

DESIGN_NOTES: list[tuple[str, str]] = [
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
        "Entrée seule sépare le bloc en deux (comportement Notion). "
        "Maj+Entrée fait un retour à la ligne dans le même bloc. "
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
]
