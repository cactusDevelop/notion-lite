"""
Internationalisation de l'interface (PATCH 79).

Réglage de langue de session, même principe que `ui.settings`
(stockage en mémoire, pas de persistance entre lancements pour
l'instant). Seuls le français (langue par défaut, historique de
l'app) et l'anglais sont proposés pour le moment — d'autres langues
pourront être ajoutées à `LANGUAGES`/`_STRINGS` sans toucher au reste
du code, qui ne connaît que des clés (`tr("menu.file")`, ...).

Périmètre actuel des chaînes traduites : la barre de menu principale
(Fichier/Édition/Affichage) et son sous-menu "Langue". Le reste de
l'interface (barre d'outils, blocs, boîtes de dialogue) reste en
français pour l'instant et sera traduit progressivement.
"""
from __future__ import annotations

LANGUAGE_FR = "fr"
LANGUAGE_EN = "en"

# Ordre d'affichage dans le sous-menu "Langue".
LANGUAGES: dict[str, str] = {
    LANGUAGE_FR: "Français",
    LANGUAGE_EN: "English",
}

_language = LANGUAGE_FR

_STRINGS: dict[str, dict[str, str]] = {
    "menu.file": {"fr": "&Fichier", "en": "&File"},
    "menu.file.templates": {"fr": "Templates", "en": "Templates"},
    "menu.file.template_og": {"fr": "Modèle OG", "en": "OG template"},
    "menu.file.new_blank": {"fr": "Nouveau document vide", "en": "New blank document"},
    "menu.file.open": {"fr": "Ouvrir...", "en": "Open..."},
    "menu.file.save": {"fr": "Sauvegarder", "en": "Save"},
    "menu.file.save_as": {"fr": "Sauvegarder sous...", "en": "Save as..."},
    "menu.file.export_pdf": {"fr": "Exporter en PDF...", "en": "Export as PDF..."},
    "menu.file.rename_project": {"fr": "Renommer le projet...", "en": "Rename project..."},
    "menu.edit": {"fr": "&Édition", "en": "&Edit"},
    "menu.edit.undo": {"fr": "Annuler", "en": "Undo"},
    "menu.edit.redo": {"fr": "Rétablir", "en": "Redo"},
    "menu.edit.search": {"fr": "Rechercher...", "en": "Find..."},
    "menu.edit.replace": {"fr": "Remplacer...", "en": "Replace..."},
    "menu.edit.people_manager": {"fr": "Gestionnaire de personnes...", "en": "People manager..."},
    "menu.view": {"fr": "&Affichage", "en": "&View"},
    "menu.view.dark_mode": {"fr": "Mode sombre", "en": "Dark mode"},
    "menu.view.theme": {"fr": "Thème", "en": "Theme"},
    "menu.view.block_spacing": {
        "fr": "Espacer les titres, tableaux et graphiques",
        "en": "Add spacing above headings, tables and charts",
    },
    "menu.view.autosave": {"fr": "Sauvegarde automatique", "en": "Autosave"},
    "menu.view.explorer": {"fr": "Explorateur de fichiers", "en": "File explorer"},
    "menu.view.language": {"fr": "Langue", "en": "Language"},

    # -- Toolbar (PATCH 80) ------------------------------------------------
    "toolbar.title": {"fr": "Barre d'outils", "en": "Toolbar"},
    "toolbar.new_block": {"fr": "Nouveau bloc", "en": "New block"},
    "toolbar.new_checklist": {"fr": "Nouvelle checklist", "en": "New checklist"},
    "toolbar.new_image": {"fr": "Insérer une image", "en": "Insert an image"},
    "toolbar.new_table": {"fr": "Nouveau tableau", "en": "New table"},
    "toolbar.new_simple_table": {"fr": "Nouveau tableau simple", "en": "New simple table"},
    "toolbar.new_gantt": {"fr": "Nouveau Gantt", "en": "New Gantt"},
    "toolbar.new_separator": {"fr": "Insérer un séparateur", "en": "Insert a separator"},
    "toolbar.new_quote": {"fr": "Insérer une citation", "en": "Insert a quote"},
    "toolbar.new_code": {"fr": "Insérer un bloc de code", "en": "Insert a code block"},
    "toolbar.new_list": {"fr": "Insérer une liste", "en": "Insert a list"},
    "toolbar.bold": {"fr": "Gras", "en": "Bold"},
    "toolbar.italic": {"fr": "Italique", "en": "Italic"},
    "toolbar.underline": {"fr": "Souligné", "en": "Underline"},
    "toolbar.strikethrough": {"fr": "Barré", "en": "Strikethrough"},
    "toolbar.align_left": {"fr": "Aligner à gauche", "en": "Align left"},
    "toolbar.align_center": {"fr": "Centrer", "en": "Center"},
    "toolbar.align_right": {"fr": "Aligner à droite", "en": "Align right"},
    "toolbar.align_justify": {"fr": "Justifier", "en": "Justify"},
    "toolbar.bullet_list": {"fr": "Liste à puces", "en": "Bulleted list"},
    "toolbar.numbered_list": {"fr": "Liste numérotée", "en": "Numbered list"},
    "toolbar.quote": {"fr": "Citation", "en": "Quote"},
    "toolbar.code": {"fr": "Code", "en": "Code"},
    "toolbar.color": {"fr": "Couleur", "en": "Color"},
    "toolbar.insert_link": {"fr": "Lien interne...", "en": "Internal link..."},
    "toolbar.insert_emoji": {"fr": "Emoji...", "en": "Emoji..."},
    "toolbar.info_tooltip": {"fr": "Informations et choix de design", "en": "Information and design notes"},

    # -- Menu "/" (PATCH 80) ------------------------------------------------
    "command.text": {"fr": "Texte", "en": "Text"},
    "command.heading1": {"fr": "Titre 1", "en": "Heading 1"},
    "command.heading2": {"fr": "Titre 2", "en": "Heading 2"},
    "command.heading3": {"fr": "Titre 3", "en": "Heading 3"},
    "command.checklist": {"fr": "Checklist", "en": "Checklist"},
    "command.linked_checklist": {"fr": "Checklists liées", "en": "Linked checklists"},
    "command.table": {"fr": "Tableau", "en": "Table"},
    "command.simple_table": {"fr": "Tableau simple", "en": "Simple table"},
    "command.gantt": {"fr": "Gantt", "en": "Gantt"},
    "command.dependency_gantt": {"fr": "Planning par dépendances", "en": "Dependency schedule"},
    "command.line_chart": {"fr": "Courbes", "en": "Line chart"},
    "command.bar_chart": {"fr": "Bâtonnets", "en": "Bar chart"},
    "command.formula": {"fr": "Résultat calculé", "en": "Computed result"},
    "command.image": {"fr": "Image", "en": "Image"},
    "command.separator": {"fr": "Séparateur", "en": "Separator"},
    "command.quote": {"fr": "Citation", "en": "Quote"},
    "command.code": {"fr": "Code", "en": "Code"},
    "command.list": {"fr": "Liste", "en": "List"},

    # -- Sélecteur de bloc / lien interne (PATCH 80) -------------------------
    "block_picker.title": {"fr": "Lier vers un bloc", "en": "Link to a block"},

    # -- Popup d'information (PATCH 80) --------------------------------------
    "info.title": {"fr": "À propos de ce projet", "en": "About this project"},
    "info.heading": {"fr": "Méthodo OG", "en": "Méthodo OG"},
    "info.subheading": {"fr": "Explications et choix de design", "en": "Explanations and design choices"},

    # -- Sélecteur d'emoji (PATCH 80) ----------------------------------------
    "emoji.search_placeholder": {"fr": "Rechercher un emoji (ex. smile)...", "en": "Search for an emoji (e.g. smile)..."},

    # -- Recherche / remplacement (PATCH 80) ---------------------------------
    "search.title": {"fr": "Rechercher et remplacer", "en": "Find and replace"},
    "search.placeholder": {"fr": "Rechercher dans le document...", "en": "Search the document..."},
    "search.replace_placeholder": {"fr": "Remplacer par...", "en": "Replace with..."},
    "search.replace_all": {"fr": "Tout remplacer", "en": "Replace all"},
    "search.no_results": {"fr": "Aucun résultat.", "en": "No results."},
    "search.result": {"fr": "résultat", "en": "result"},
    "search.results": {"fr": "résultats", "en": "results"},
    "search.no_replacement": {"fr": "Aucun remplacement effectué.", "en": "No replacement made."},
    "search.replacement_done_one": {"fr": "{count} remplacement effectué.", "en": "{count} replacement made."},
    "search.replacement_done_many": {"fr": "{count} remplacements effectués.", "en": "{count} replacements made."},

    # -- Gestionnaire de personnes (PATCH 80) --------------------------------
    "people.title": {"fr": "Gestionnaire de personnes", "en": "People manager"},
    "people.add": {"fr": "Ajouter...", "en": "Add..."},
    "people.rename": {"fr": "Renommer...", "en": "Rename..."},
    "people.color": {"fr": "Couleur...", "en": "Color..."},
    "people.remove": {"fr": "Retirer du projet", "en": "Remove from project"},
    "people.close": {"fr": "Fermer", "en": "Close"},
    "people.new_person": {"fr": "Nouvelle personne", "en": "New person"},
    "people.rename_person": {"fr": "Renommer la personne", "en": "Rename person"},
    "people.name_label": {"fr": "Nom :", "en": "Name:"},
    "people.pick_color": {"fr": "Choisir une couleur", "en": "Choose a color"},
    "people.remove_title": {"fr": "Retirer du projet", "en": "Remove from project"},
    "people.remove_confirm": {
        "fr": "Retirer « {name} » de ce projet et la retirer de toutes les cellules qui la référencent ? "
        "Elle restera disponible dans vos autres projets.",
        "en": "Remove \"{name}\" from this project and clear it from every cell that references them? "
        "They will remain available in your other projects.",
    },
    "people.link_existing": {"fr": "Lier une personne existante...", "en": "Link existing person..."},
    "people.link_existing_title": {"fr": "Lier une personne existante", "en": "Link existing person"},
    "people.link_existing_empty": {
        "fr": "Toutes les personnes du registre partagé sont déjà dans ce projet.",
        "en": "Every person in the shared registry is already in this project.",
    },
    "people.shared_hint": {
        "fr": "Ces personnes sont partagées entre tous vos projets (fichier système).",
        "en": "These people are shared across all your projects (system file).",
    },

    # -- Métadonnées système du projet (PATCH 82) ------------------------------
    "project.rename_title": {"fr": "Renommer le projet", "en": "Rename project"},
    "project.rename_label": {"fr": "Nom du projet :", "en": "Project name:"},
    "project.rename_no_project": {
        "fr": "Aucun projet ouvert : sauvegardez d'abord ce document.",
        "en": "No project open: save this document first.",
    },

    # -- Écran d'accueil (PATCH 80) -------------------------------------------
    "welcome.title": {"fr": "Bienvenue dans Méthodo OG", "en": "Welcome to Méthodo OG"},
    "welcome.version": {"fr": "version", "en": "version"},
    "welcome.new_project_template": {"fr": "＋  Nouveau projet (Modèle OG)", "en": "＋  New project (OG template)"},
    "welcome.new_blank": {"fr": "＋  Nouveau document vide", "en": "＋  New blank document"},
    "welcome.open_project": {"fr": "📂  Ouvrir un projet...", "en": "📂  Open a project..."},
    "welcome.recent_projects": {"fr": "Projets récents", "en": "Recent projects"},
    "welcome.no_recent_projects": {"fr": "(aucun projet récent)", "en": "(no recent projects)"},
    "welcome.remove_recent_tooltip": {
        "fr": "Retirer de la liste des projets récents",
        "en": "Remove from the recent projects list",
    },
    "welcome.error": {"fr": "Erreur", "en": "Error"},
    "welcome.folder_creation_error": {"fr": "Impossible de créer le dossier du projet :", "en": "Could not create the project folder:"},
    "welcome.open_project_dialog": {"fr": "Ouvrir un projet", "en": "Open a project"},
    "welcome.new_project.title": {"fr": "Nouveau projet", "en": "New project"},
    "welcome.new_project.name_placeholder": {"fr": "Mon projet", "en": "My project"},
    "welcome.new_project.name_label": {"fr": "Nom du projet", "en": "Project name"},
    "welcome.new_project.browse": {"fr": "Parcourir...", "en": "Browse..."},
    "welcome.new_project.location_label": {"fr": "Emplacement", "en": "Location"},
    "welcome.new_project.location_dialog": {"fr": "Emplacement du projet", "en": "Project location"},
    "welcome.new_project.name_fallback": {"fr": "<nom du projet>", "en": "<project name>"},
    "welcome.new_project.preview": {"fr": "Sera créé dans :", "en": "Will be created in:"},
    "welcome.new_project.missing_name_title": {"fr": "Nom manquant", "en": "Missing name"},
    "welcome.new_project.missing_name_text": {
        "fr": "Merci de donner un nom au projet.",
        "en": "Please give the project a name.",
    },
    "welcome.new_project.folder_exists_title": {"fr": "Dossier existant", "en": "Folder already exists"},
    "welcome.new_project.folder_exists_text": {
        "fr": "Un dossier « {name} » existe déjà à cet emplacement.\nChoisis un autre nom ou un autre emplacement.",
        "en": "A folder named \"{name}\" already exists at this location.\nChoose another name or location.",
    },

    # -- Explorateur de fichiers (PATCH 80) ------------------------------------
    "explorer.title": {"fr": "Fichiers", "en": "Files"},
    "explorer.no_folder": {"fr": "Aucun dossier sélectionné", "en": "No folder selected"},
    "explorer.choose_folder": {"fr": "Choisir un dossier...", "en": "Choose a folder..."},
    "explorer.choose_folder_dialog": {"fr": "Choisir un dossier", "en": "Choose a folder"},

    # -- Explorateur : créer / renommer / supprimer (PATCH 81) ----------------
    "explorer.new_file": {"fr": "Nouveau fichier", "en": "New file"},
    "explorer.new_folder": {"fr": "Nouveau dossier", "en": "New folder"},
    "explorer.rename": {"fr": "Renommer", "en": "Rename"},
    "explorer.delete": {"fr": "Supprimer", "en": "Delete"},
    "explorer.new_file_name": {"fr": "Nouveau document", "en": "New document"},
    "explorer.new_folder_name": {"fr": "Nouveau dossier", "en": "New folder"},
    "explorer.create_error_title": {"fr": "Erreur de création", "en": "Creation error"},
    "explorer.create_error_text": {
        "fr": "Impossible de créer l'élément :",
        "en": "Could not create the item:",
    },
    "explorer.delete_title": {"fr": "Supprimer", "en": "Delete"},
    "explorer.delete_confirm": {
        "fr": "Supprimer définitivement « {name} » ?",
        "en": "Permanently delete \"{name}\"?",
    },
    "explorer.delete_error_title": {"fr": "Erreur de suppression", "en": "Deletion error"},
    "explorer.delete_error_text": {
        "fr": "Impossible de supprimer l'élément :",
        "en": "Could not delete the item:",
    },

    # -- Menu contextuel des blocs (PATCH 80) ----------------------------------
    "context.duplicate": {"fr": "Dupliquer", "en": "Duplicate"},
    "context.delete": {"fr": "Supprimer", "en": "Delete"},
    "context.add_favorite": {"fr": "Ajouter aux favoris", "en": "Add to favorites"},
    "context.remove_favorite": {"fr": "Retirer des favoris", "en": "Remove from favorites"},
    "context.move_up": {"fr": "Déplacer vers le haut", "en": "Move up"},
    "context.move_down": {"fr": "Déplacer vers le bas", "en": "Move down"},
    "context.convert_to": {"fr": "Convertir en", "en": "Convert to"},
    "context.convert.text": {"fr": "Texte", "en": "Text"},
    "context.convert.heading1": {"fr": "Titre 1", "en": "Heading 1"},
    "context.convert.heading2": {"fr": "Titre 2", "en": "Heading 2"},
    "context.convert.heading3": {"fr": "Titre 3", "en": "Heading 3"},
    "context.convert.quote": {"fr": "Citation", "en": "Quote"},
    "context.convert.code": {"fr": "Code", "en": "Code"},

    # -- Dialogues fichier (PATCH 80) -------------------------------------------
    "dialog.open_document": {"fr": "Ouvrir un document", "en": "Open a document"},
    "dialog.save_as": {"fr": "Sauvegarder sous", "en": "Save as"},
    "dialog.export_pdf": {"fr": "Exporter en PDF", "en": "Export as PDF"},
    "dialog.insert_image": {"fr": "Insérer une image", "en": "Insert an image"},
    "dialog.images_filter": {"fr": "Images", "en": "Images"},

    # -- Messages d'erreur (PATCH 80) ---------------------------------------
    "error.generic_title": {"fr": "Erreur", "en": "Error"},
    "error.create_project_file": {
        "fr": "Impossible de créer le fichier du projet :",
        "en": "Could not create the project file:",
    },
    "error.open_title": {"fr": "Erreur d'ouverture", "en": "Opening error"},
    "error.open_text": {"fr": "Impossible d'ouvrir le fichier :", "en": "Could not open the file:"},
    "error.save_title": {"fr": "Erreur de sauvegarde", "en": "Saving error"},
    "error.save_text": {"fr": "Impossible d'enregistrer le fichier :", "en": "Could not save the file:"},
    "error.insert_title": {"fr": "Erreur d'insertion", "en": "Insertion error"},
    "error.insert_text": {"fr": "Impossible de lire l'image :", "en": "Could not read the image:"},

    # -- Fermeture avec modifications non sauvegardées (PATCH 80) -----------
    "unsaved.title": {"fr": "Modifications non sauvegardées", "en": "Unsaved changes"},
    "unsaved.text": {
        "fr": "Voulez-vous sauvegarder les modifications avant de quitter ?",
        "en": "Do you want to save your changes before quitting?",
    },

    # -- Bloc Checklist (PATCH 80) -------------------------------------------
    "checklist.item_placeholder": {"fr": "Élément de la liste...", "en": "List item..."},
    "checklist.item_placeholder_short": {"fr": "Élément...", "en": "Item..."},
    "checklist.remove_item": {"fr": "Supprimer cet élément", "en": "Remove this item"},

    # -- Bloc Checklists liées (PATCH 80) ------------------------------------
    "linked_checklist.todo": {"fr": "À faire", "en": "To do"},
    "linked_checklist.done": {"fr": "Faites", "en": "Done"},

    # -- Bloc Liste (PATCH 80) -----------------------------------------------
    "list.style": {"fr": "Style :", "en": "Style:"},
    "list.bullet": {"fr": "À puces", "en": "Bulleted"},
    "list.numbered": {"fr": "Numérotée", "en": "Numbered"},
    "list.add_item": {"fr": "+ Élément", "en": "+ Item"},

    # -- Bloc Effectif / personnes (PATCH 80) --------------------------------
    "people_list.remove_tooltip": {"fr": "Retirer cette personne de l'effectif", "en": "Remove this person from the team"},
    "people_list.add_placeholder": {"fr": "Ajouter une personne… (Entrée pour valider)", "en": "Add a person… (press Enter)"},

    # -- Bloc Image (PATCH 80) -----------------------------------------------
    "image.width": {"fr": "Largeur :", "en": "Width:"},

    # -- Bloc Résultat calculé (PATCH 80) ------------------------------------
    "formula.label": {"fr": "Libellé :", "en": "Label:"},
    "formula.table": {"fr": "Tableau :", "en": "Table:"},
    "formula.table_prefix": {"fr": "Tableau", "en": "Table"},
    "formula.points": {"fr": "Points :", "en": "Points:"},
    "formula.state": {"fr": "État :", "en": "State:"},
    "formula.none": {"fr": "(aucun)", "en": "(none)"},
    "formula.unnamed": {"fr": "(sans nom)", "en": "(unnamed)"},

    # -- Bloc Gantt (PATCH 80) ------------------------------------------------
    "gantt.no_data": {"fr": "Aucune donnée à afficher.", "en": "No data to display."},
    "gantt.untitled": {"fr": "(sans titre)", "en": "(untitled)"},
    "gantt.dates": {"fr": "Dates :", "en": "Dates:"},
    "gantt.scale": {"fr": "Échelle :", "en": "Scale:"},
    "gantt.auto": {"fr": "Auto", "en": "Auto"},
    "gantt.auto_tooltip": {"fr": "Ajuster l'échelle pour tout voir", "en": "Adjust the scale to fit everything"},

    # -- Bloc Gantt (dépendances) (PATCH 80) -----------------------------------
    "dep_gantt.days": {"fr": "Jours", "en": "Days"},
    "dep_gantt.months": {"fr": "Mois", "en": "Months"},
    "dep_gantt.unassigned": {"fr": "(non assigné)", "en": "(unassigned)"},
    "dep_gantt.delta": {"fr": "Écart", "en": "Deviation"},
    "dep_gantt.delta_hint": {"fr": "Retard (positif) ou avance (négatif), en", "en": "Delay (positive) or lead (negative), in"},
    "dep_gantt.subtasks": {"fr": "Sous-tâches", "en": "Subtasks"},
    "dep_gantt.people": {"fr": "Personnes", "en": "People"},
    "dep_gantt.duration": {"fr": "Durée", "en": "Duration"},
    "dep_gantt.risks": {"fr": "Risques", "en": "Risks"},
    "dep_gantt.dependencies": {"fr": "Dépendances", "en": "Dependencies"},
    "dep_gantt.deltas": {"fr": "Ecarts", "en": "Deviations"},
    "dep_gantt.phases": {"fr": "Phases", "en": "Phases"},
    "dep_gantt.format": {"fr": "Format :", "en": "Format:"},
    "dep_gantt.micro": {"fr": "Micro", "en": "Micro"},
    "dep_gantt.macro": {"fr": "Macro", "en": "Macro"},
    "dep_gantt.week": {"fr": "Semaine", "en": "Week"},
    "dep_gantt.start_date": {"fr": "Jour 0 :", "en": "Day 0:"},
    "dep_gantt.weekday.mon": {"fr": "Lun", "en": "Mon"},
    "dep_gantt.weekday.tue": {"fr": "Mar", "en": "Tue"},
    "dep_gantt.weekday.wed": {"fr": "Mer", "en": "Wed"},
    "dep_gantt.weekday.thu": {"fr": "Jeu", "en": "Thu"},
    "dep_gantt.weekday.fri": {"fr": "Ven", "en": "Fri"},
    "dep_gantt.weekday.sat": {"fr": "Sam", "en": "Sat"},
    "dep_gantt.weekday.sun": {"fr": "Dim", "en": "Sun"},
    "dep_gantt.month.1": {"fr": "Janvier", "en": "January"},
    "dep_gantt.month.2": {"fr": "Février", "en": "February"},
    "dep_gantt.month.3": {"fr": "Mars", "en": "March"},
    "dep_gantt.month.4": {"fr": "Avril", "en": "April"},
    "dep_gantt.month.5": {"fr": "Mai", "en": "May"},
    "dep_gantt.month.6": {"fr": "Juin", "en": "June"},
    "dep_gantt.month.7": {"fr": "Juillet", "en": "July"},
    "dep_gantt.month.8": {"fr": "Août", "en": "August"},
    "dep_gantt.month.9": {"fr": "Septembre", "en": "September"},
    "dep_gantt.month.10": {"fr": "Octobre", "en": "October"},
    "dep_gantt.month.11": {"fr": "Novembre", "en": "November"},
    "dep_gantt.month.12": {"fr": "Décembre", "en": "December"},
    "dep_gantt.none_fem": {"fr": "(aucune)", "en": "(none)"},

    # -- Bloc Graphique en bâtonnets (PATCH 80) --------------------------------
    "bar_chart.no_data": {"fr": "Aucune barre à afficher.", "en": "No bars to display."},
    "bar_chart.title_placeholder": {"fr": "Titre", "en": "Title"},
    "bar_chart.y_axis_placeholder": {"fr": "Axe Y", "en": "Y axis"},
    "bar_chart.source": {"fr": "Source :", "en": "Source:"},
    "bar_chart.group_by": {"fr": "Regrouper par :", "en": "Group by:"},
    "bar_chart.planned": {"fr": "Prévu :", "en": "Planned:"},
    "bar_chart.actual": {"fr": "Réel :", "en": "Actual:"},
    "bar_chart.schedule": {"fr": "Planning", "en": "Schedule"},
    "bar_chart.by_subtask": {"fr": "Par sous-tâche", "en": "By subtask"},
    "bar_chart.duration_plus_delta": {"fr": "Durée + écart (Gantt)", "en": "Duration + deviation (Gantt)"},

    # -- Bloc Courbes (PATCH 80) ------------------------------------------------
    "line_chart.title": {"fr": "Titre", "en": "Title"},
    "line_chart.y_axis": {"fr": "Axe Y", "en": "Y axis"},
    "line_chart.x_axis": {"fr": "Axe X", "en": "X axis"},
    "line_chart.add_series": {"fr": "+ Ajouter une droite", "en": "+ Add a line"},
    "line_chart.constant": {"fr": "Constante", "en": "Constant"},
    "line_chart.real_velocity": {"fr": "Vélocité réelle (planning)", "en": "Actual velocity (schedule)"},
    "line_chart.no_schedule": {"fr": "(aucun planning)", "en": "(no schedule)"},
    "line_chart.line": {"fr": "Droite", "en": "Line"},

    # -- Bloc Tableau simple (PATCH 80) ------------------------------------
    "simple_table.add_row": {"fr": "+ Ligne", "en": "+ Row"},
    "simple_table.add_column": {"fr": "+ Colonne", "en": "+ Column"},
    "simple_table.delete_row": {"fr": "- Ligne", "en": "- Row"},
    "simple_table.delete_column": {"fr": "- Colonne", "en": "- Column"},

    # -- Types de colonne du bloc Tableau (PATCH 80) -------------------------
    "column_type.text": {"fr": "Texte", "en": "Text"},
    "column_type.number": {"fr": "Nombre", "en": "Number"},
    "column_type.date": {"fr": "Date", "en": "Date"},
    "column_type.duration": {"fr": "Durée", "en": "Duration"},
    "column_type.boolean": {"fr": "Booléen", "en": "Boolean"},
    "column_type.person": {"fr": "Personne", "en": "Person"},
    "column_type.select": {"fr": "Liste", "en": "List"},
    "column_type.multi_select": {"fr": "Liste multiple", "en": "Multi-select"},
    "column_type.checklist": {"fr": "Checklist", "en": "Checklist"},

    # -- Dialogues du bloc Tableau (PATCH 80) --------------------------------
    "table.column_dialog.title": {"fr": "Colonne", "en": "Column"},
    "table.column_dialog.name": {"fr": "Nom :", "en": "Name:"},
    "table.column_dialog.type": {"fr": "Type :", "en": "Type:"},
    "table.column_dialog.options": {
        "fr": "Choix possibles (séparés par des virgules) :",
        "en": "Possible choices (comma-separated):",
    },
    "table.column_dialog.date_range": {"fr": "Plage de dates (début / fin)", "en": "Date range (start / end)"},
    "table.column_dialog.unit": {
        "fr": "Unité affichée dans l'en-tête (ex : j, €, %) :",
        "en": "Unit shown in the header (e.g. d, €, %):",
    },
    "table.people_dialog.title": {"fr": "Personnes assignées", "en": "Assigned people"},
    "table.people_dialog.new_person": {"fr": "Nouvelle personne...", "en": "New person..."},
    "people.add_short": {"fr": "Ajouter", "en": "Add"},
    "table.multi_select_dialog.title": {"fr": "Choix multiples", "en": "Multiple choices"},
    "table.multi_select_dialog.no_options": {
        "fr": "Aucun choix défini pour cette colonne.",
        "en": "No choices defined for this column.",
    },
    "table.checklist_dialog.title": {"fr": "Checklist", "en": "Checklist"},
    "table.checklist_dialog.add_item": {"fr": "+ Ajouter un élément", "en": "+ Add an item"},

    # -- Grille du bloc Tableau (PATCH 80) -----------------------------------
    "table.column_prefix": {"fr": "Colonne", "en": "Column"},
    "table.merge_up": {"fr": "Fusionner avec la ligne au-dessus", "en": "Merge with the row above"},
    "table.merge_down": {"fr": "Fusionner avec la ligne en dessous", "en": "Merge with the row below"},
    "table.unmerge": {"fr": "Annuler la fusion", "en": "Undo merge"},
    "table.date_from": {"fr": "Du", "en": "From"},
    "table.date_to": {"fr": "au", "en": "to"},
}


def get_language() -> str:
    return _language


def set_language(language: str) -> None:
    global _language
    if language in LANGUAGES:
        _language = language


def tr(key: str) -> str:
    """Traduit `key` dans la langue courante. Repli sur le français
    (ou sur la clé elle-même) si `key` n'est pas encore traduite."""
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_language) or entry.get(LANGUAGE_FR, key)
