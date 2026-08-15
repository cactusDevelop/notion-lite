# Changelog

## Post-1.0

- **92** — Gantt (dépendances), calendrier réaliste du mode macro
  (PATCH 91) :
  - La teinte des week-ends (`_weekend_color`) est désormais calculée
    à partir de la couleur de fond courante (plus sombre en thème
    clair, plus claire en thème sombre) plutôt que fixée en dur
    (`#f0f0f0`), qui rendait les week-ends invisibles en mode sombre
    et à peine visibles en mode clair.
  - Nouvelle case à cocher "Travailler le weekend" (`work_weekends`
    sur le bloc, décochée par défaut) : décochée (comportement par
    défaut), samedi/dimanche restent grisés dans le calendrier ;
    cochée, ils sont affichés comme des jours normaux. Sans effet sur
    le calcul du planning (toujours en jours calendaires continus,
    voir compute_schedule) ni sur le mode micro.
- **91** — Gantt (dépendances) : nouvelle option "Jour 0" (case à
  cocher + sélecteur de date), qui ancre le planning (toujours calculé
  en jours relatifs, sans changement) à une vraie date calendaire.
  Sans effet en mode micro. En mode macro, dès que "Jour 0" est
  configuré, le calendrier devient réaliste : vrais jours de la
  semaine (Lundi à Dimanche) affichés une seule fois en en-tête, vraie
  date du mois dans chaque case, semaines qui commencent toujours un
  lundi (les cases avant le "Jour 0" dans sa semaine sont affichées
  sans bâtonnet), week-ends grisés, nom du mois affiché dès qu'il
  change, et la case du jour courant est mise en évidence. Sans "Jour
  0" configuré, le mode macro garde son ancien calendrier relatif
  ("Semaine N" / J1..J7, PATCH 90).
- **90** — Gantt (dépendances) : le menu "Unité" (Jours/Mois) devient
  "Format", avec deux options :
  - **micro** — comportement précédent, mais l'axe temporel bascule
    désormais automatiquement entre jours et mois selon le zoom
    (progression adaptative 1J, 2J, 4J, 8J, 16J, 1M, 2M... au lieu du
    choix manuel Jours/Mois, supprimé) ;
  - **macro** — nouveau : calendrier (une ligne = une semaine de 7
    cases/jours), avec les bâtonnets de chaque personne dessinés à
    l'intérieur de chaque semaine (retard/avance gérés comme en
    micro). Le clic-glissé d'ajustement direct reste réservé au mode
    micro ; en macro, cliquer un bâtonnet ouvre toujours la pop-up de
    saisie précise (échelle non uniforme d'une semaine à l'autre).
  `DependencyGanttBlock.time_unit` (jours/mois) est remplacé par
  `chart_format` (micro/macro) ; la saisie précise de l'écart se fait
  désormais toujours en jours.
- **89** — Corrige la colonne "Phases" du Gantt (dépendances) du
  template "Modèle OG" (et de tout Gantt utilisant cette option) :
  bien sélectionnée à la création, mais perdue dès la première
  réouverture du fichier. `blocks/registry.py::block_from_dict`
  oubliait de relire `phase_column_id` depuis le JSON pour
  `DependencyGanttBlock` (déjà bien écrit à la sauvegarde — un simple
  oubli à la reconstruction).
- **88** — Corrige "Ouvrir un projet" (et les projets récents) pour un
  projet "Modèle OG" : l'explorateur se rouvrait sur "client 1" (où
  vit réellement le `.json` ouvert) au lieu de la racine du projet,
  masquant "client 2" — l'arborescence ne montrait donc plus que des
  fichiers, jamais de dossier. `.methodo-project.json` déménage à la
  racine du projet (il décrit les deux dossiers clients, pas
  "client 1" seul) ; `ProjectMeta.find_project_root`/`load_for_document`
  remontent l'arborescence pour le retrouver quel que soit le
  sous-dossier du document ouvert. L'icône des entrées "cachées" par
  convention (nom préfixé d'un point) est désormais grisée en plus du
  texte de leur libellé.
- **87** — Fichier système `.methodo-project.json` du template "Modèle
  OG" : reste dans "client 1" (voir explication en session, il décrit
  ce document précis, pas "le projet" au sens du dossier parent avec
  ses deux clients — cohérent avec le reste de l'architecture où un
  dossier = un projet = un `.json`). Explorateur : les entrées
  préfixées d'un point (invisibles par défaut sous Unix, mais pas
  masquées par Windows faute d'attribut système "caché" posé à la
  création) sont désormais grisées quand elles apparaissent, à
  l'instar de l'explorateur de fichiers Windows
  (`_ExplorerHiddenFileDelegate`).
- **86** — "Nouveau projet (Modèle OG)" crée désormais deux dossiers
  clients ("client 1", "client 2") dans le dossier projet, le gabarit
  "Modèle OG" étant initialisé dans "client 1" (au lieu d'un unique
  fichier gabarit à la racine). Explorateur de fichiers : sélection
  multiple façon IDE (Shift = plage consécutive, Ctrl = ajout/retrait
  un par un).
- **85** — Documentation : `CLAUDE.md` (nouveau), document de contexte
  dédié à l'assistant IA pour les sessions de développement futures
  (règles de session, checklist de patch, pièges Qt déjà rencontrés,
  état courant de l'architecture). Mise à jour de `README.md`
  (sections "Registre des personnes" et format JSON), restées
  obsolètes depuis les PATCH 82/83 (registre système partagé,
  `.methodo-project.json`).
- **84** — Le Gantt du template "Modèle OG" a désormais sa colonne
  "Phases" pré-sélectionnée (regroupement par phase visible dès
  l'ouverture, sans configuration manuelle).
- **83** — Corrige la croix de suppression des étiquettes du bloc
  "Effectif" : ne réagissait pas au clic (le signal Qt `clicked(bool)`
  écrasait silencieusement l'identifiant de la personne attendu par le
  callback). Synchronisation live des personnes : ajouter/retirer une
  personne depuis la popup "Personne" d'un tableau (ou depuis le
  Gestionnaire de personnes) met désormais à jour le bloc "Effectif"
  immédiatement, sans re-rendu complet du document
  (`Document.add_people_listener`).
- **82** — Nom du projet indépendant du fichier JSON : fichier système
  `.methodo-project.json` (nom, id, date de création) posé à côté du
  document, qui devient la source du titre de fenêtre et des projets
  récents (renommer/déplacer le `.json` ne change plus le nom du
  projet). Refonte du registre des personnes : nom et couleur vivent
  désormais dans un fichier système partagé par utilisateur
  (`~/.methodo-og/people.json`, `core.people_registry.PeopleRegistry`),
  réutilisable d'un projet à l'autre ; chaque document ne garde que les
  identifiants des personnes qu'il référence et peut les détacher sans
  les supprimer ailleurs (`Document.remove_person` / `link_person`).
  Gestionnaire de personnes enfin accessible depuis le menu Édition,
  avec un bouton "Lier une personne existante...".

## 1.0.0 — Première version stable

Fonctionnalités gelées ; les correctifs post-1.0 seront listés
au-dessus de cette section. Pour le détail de chaque décision de
conception, voir **Aide → Informations** dans l'application
(`ui/design_notes.py`) ; ce fichier ne liste que le *quoi*, patch par
patch, tel que défini dans le cahier des charges du projet.

- **1** — Création du projet (structure de base)
- **2** — Gestionnaire de documents (`Document` : ajout/suppression/déplacement de blocs)
- **3** — Bloc Texte
- **4** — Titres (H1/H2/H3)
- **5** — Barre d'outils
- **6** — Mise en forme du texte (gras, italique, souligné, couleurs, alignement...)
- **7** — Gestion du curseur (scission/fusion de blocs texte façon Notion)
- **8** — Sauvegarde (format JSON)
- **9** — Chargement (reconstruction complète depuis le JSON)
- **10** — Bloc Checklist
- **11** — Checklist « À faire / Déjà fait » (tri automatique)
- **12** — Bloc Image
- **13** — Drag & Drop (réordonner n'importe quel bloc)
- **14** — Bloc Tableau (moteur : colonnes, lignes)
- **15** — Colonnes typées (texte, nombre, date, durée, booléen, personne, liste, checklist)
- **16** — Colonne Personne (registre partagé, couleur, renommage propagé)
- **17** — Colonne Durée
- **18** — Colonne Date (dont plages de dates)
- **19** — Vue Gantt (dérivée d'un tableau existant)
- **20** — Bloc Séparateur
- **21** — Bloc Citation
- **22** — Bloc Code
- **23** — Bloc Liste (à puces / numérotée)
- **24** — Bloc Tableau simple (grille de texte, sans colonnes typées)
- **25** — Système de commandes (menu « / »)
- **26** — Menu contextuel (clic droit complet : dupliquer, supprimer, déplacer, convertir)
- **27** — Undo / Redo (Ctrl+Z / Ctrl+Y, historique générique par snapshots)
- **28** — Recherche (globale : texte, checklists, tableaux)
- **29** — Remplacement (texte, global)
- **30** — Liens internes (lien cliquable vers un autre bloc)
- **31** — Favoris
- **32** — Mode sombre
- **33** — Thèmes (plusieurs palettes)
- **34** — Icônes de bloc
- **35** — Emojis
- **36** — Export PDF
- **37** — Export Markdown
- **38** — Export HTML
- **39** — Performances (gros documents, mémoire, chargement)
- **40** — Tests (unitaires et d'intégration)
- **41** — Documentation (README : architecture, API interne, format JSON)
- **42** — Version 1.0 : stabilisation, nettoyage (imports inutilisés retirés),
  test d'intégration bout-en-bout couvrant tous les types de blocs,
  gel des fonctionnalités, publication.
