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
]
