# CLAUDE.md — Notice de session pour l'assistant IA

Ce fichier n'est pas destiné à un développeur humain (voir `README.md`
et `CHANGELOG.md` pour ça) : il condense ce qu'une session repart en
découvrant sinon à chaque fois — règles de travail, pièges déjà
rencontrés, état d'avancement de l'architecture. Objectif : réduire le
nombre d'allers-retours et de fichiers explorés avant de pouvoir coder.

**Le garder court.** Renvoyer vers `README.md`/`CHANGELOG.md` plutôt
que dupliquer leur contenu ; n'ajouter ici que ce qui coûterait cher à
redécouvrir (pièges, décisions non évidentes, état courant du système).
Le mettre à jour à la fin de tout patch qui change l'architecture,
introduit un nouveau piège, ou rend une section ci-dessous obsolète.

## Règles de session (rappel)

- Le dépôt de référence est `https://github.com/cactusDevelop/notion-lite`
  (`git clone`). Ne re-vérifier le dernier commit que si l'utilisateur
  dit avoir push, ou en tout début de conversation — sinon travailler
  sur l'état déjà cloné/patché localement.
- Chaque livraison = **un seul fichier patch** (`git diff --cached`
  après `git add -A`) **jamais cumulatif** : basé sur le patch
  précédent (committer localement après chaque patch livré, voir
  ci-dessous) ou sur le dernier push connu, jamais sur "tout depuis le
  début".
- Réponses précises, peu de texte inutile. Pas d'analyse d'image
  (demander si besoin).
- Chaque patch se termine par le fichier `.diff` + la commande
  `git apply patchNN.diff` associée.

## Checklist avant de livrer un patch

1. Coder le changement.
2. `QT_QPA_PLATFORM=offscreen python -m pytest tests/ -q` → doit être
   100 % vert (307+ tests). Ajouter un test pour tout bug corrigé ou
   comportement nouveau.
3. `python build_standalone.py` — régénère `notion_lite_standalone.py`
   à partir des sources. **Toujours faire ça avant de générer le
   patch**, sinon le bundle diverge silencieusement du code source.
4. Ajouter une entrée `CHANGELOG.md` (section "Post-1.0", même style
   que les entrées existantes : numéro de patch, quoi, pas pourquoi en
   détail).
5. `git add -A && git diff --cached > patchNN.diff`.
6. Vérifier que le patch s'applique proprement sur une copie propre du
   commit précédent (`git apply --check`) puis relancer les tests
   dessus — pas seulement sur l'arbre de travail courant.
7. `git commit -q -m "patchNN"` **localement** (pas de push — c'est
   l'utilisateur qui applique le patch de son côté) : ça donne une
   base propre et diffable pour le patch suivant dans la même session.

## Architecture — pointeurs rapides

Ne pas dupliquer `README.md` (`## Architecture`, `## API interne`,
`## Format de sauvegarde JSON`, `## Ajouter un nouveau type de bloc` —
tout y est à jour et détaillé). Résumé ultra-condensé :

```
core/   Logique pure (testable sans QApplication) : Document (source
        de vérité unique), Block, historique undo/redo, recherche,
        export/import, registre de personnes, métadonnées de projet.
blocks/ Un module par type de bloc. blocks/registry.py = JSON -> classe.
  PATCH 89 — piège vécu : `block_from_dict` reconstruit chaque bloc à
  la main, champ par champ, en dupliquant la liste des paramètres du
  constructeur. Ajouter un champ à un bloc (nouveau paramètre du
  constructeur + entrée dans `self.data`, ex. `phase_column_id` de
  `DependencyGanttBlock`) SANS l'ajouter aussi dans le bloc
  `if block_type == ...` correspondant ici ne provoque aucune erreur :
  le champ se sauvegarde très bien (Block.to_dict sérialise tout
  `self.data`), mais se réinitialise silencieusement à sa valeur par
  défaut à chaque relecture du JSON. Toujours vérifier `registry.py`
  après avoir ajouté un paramètre à un bloc existant.
ui/     Qt. main_window.py = chef d'orchestre, _render_document()
        reconstruit toute la colonne de widgets depuis self._document.
        ui/blocks/ = un widget par type de bloc. ui/i18n.py = tr().
```

Dépendances à sens unique : `ui` → `blocks` → `core`, jamais l'inverse
(imports circulaires connus : voir Pièges ci-dessous).

## État courant du système (au-delà du README)

Ajouts récents pas encore digérés par le README au moment où ce
fichier a été écrit (patch 82-84) — vérifier `CHANGELOG.md` en premier
pour ce qui est plus récent que cette section :

- **`core/people_registry.py`** (`PeopleRegistry`) — LE registre des
  personnes est désormais système, partagé entre tous les projets
  (`~/.methodo-og/people.json`, surchargeable via
  `METHODO_OG_PEOPLE_FILE`). `Document` ne garde que des
  `person_ids` ; nom/couleur vivent dans le registre. Voir
  `Document.add_person/link_person/remove_person` (ce dernier détache
  du projet, ne supprime pas globalement — c'est le comportement
  voulu, pas un bug).
- **`core/project_meta.py`** (`ProjectMeta`) — nom "métier" du projet
  dans un fichier système caché `.methodo-project.json`, indépendant
  du nom de fichier. Titre de fenêtre et projets récents l'utilisent
  (`ui/main_window.py::_update_window_title`). PATCH 88 — Il n'est pas
  toujours à côté du document ouvert : le template "Modèle OG" range
  son document dans un sous-dossier ("client 1") alors que la
  métadonnée décrit tout le projet et vit à sa racine. Toujours
  utiliser `ProjectMeta.load_for_document`/`find_project_root` (qui
  remontent l'arborescence) plutôt que `ProjectMeta.load`/
  `meta_path_for` (dossier parent immédiat seulement) pour retrouver
  le projet d'un document déjà ouvert — sinon l'explorateur se
  rouvrira sur le mauvais dossier (régression du PATCH 86, corrigée
  en 88).
- **`Document.add_people_listener`/`remove_people_listener`** —
  observer pattern minimal pour garder les vues synchronisées
  (bloc "Effectif" ↔ popup "Personne" d'un tableau ↔ Gestionnaire de
  personnes) sans re-rendu complet. S'abonner dans `__init__` du
  widget, se désabonner via `self.destroyed.connect(...)`.
- **`tests/conftest.py`** — fixture `autouse` qui redirige
  `METHODO_OG_PEOPLE_FILE` vers un `tmp_path` à chaque test : ne
  jamais retirer ça, sinon les tests polluent le vrai fichier
  utilisateur qui lance la suite.

## Pièges déjà rencontrés (ne pas re-découvrir)

- **`QPushButton/QToolButton.clicked` passe un booléen `checked`.**
  `button.clicked.connect(lambda x=default: f(x))` reçoit ce booléen
  à la place de `default` (Qt/PySide compte les paramètres acceptés
  par le callable, pas les valeurs par défaut). Idiome correct partout
  dans ce code : `lambda _checked, x=default: f(x)` ou
  `lambda _checked=False: f()`. Bug réel corrigé en PATCH 83 (croix du
  bloc Effectif inopérante) — grep `clicked.connect(lambda` avant de
  soupçonner autre chose sur un bouton qui "ne répond pas".
- **`BlockContainer.eventFilter`** (`ui/blocks/block_container.py`)
  n'installe le filtre que sur les enfants existants **au moment de la
  construction** (`self.findChildren(QWidget)` une seule fois). Des
  widgets créés plus tard par un `_refresh()` interne (ex. les puces
  du bloc Effectif) n'en héritent pas — sans conséquence pour la
  détection de clic simple (ce n'est qu'une notification, pas un
  filtrage bloquant), mais à garder en tête si un futur besoin dépend
  de cet event filter précisément.
- **Imports circulaires `core` ↔ `blocks`** — résolus par des imports
  locaux dans les méthodes concernées (`Document.remove_person`,
  `Document.from_dict`), jamais en haut de fichier. Suivre ce même
  motif pour tout nouveau couplage `core` → `blocks`.
- **`deleteLater()` + un seul `processEvents()` ne suffit pas
  toujours** pour observer le signal `destroyed` dans un test :
  utiliser `QCoreApplication.sendPostedEvents()` puis
  `PySide6.QtTest.QTest.qWait(10)` (voir
  `tests/test_people_list_block_widget.py`).
- **`python -m unittest discover` ignore silencieusement les tests
  écrits en style pytest** (plus de la moitié de la suite). Toujours
  utiliser `pytest`, jamais `unittest discover`, pour juger si "les
  tests passent".
- **`QFileSystemModel.setFilter(... | QDir.Hidden)`** fait planter la
  suite de tests offscreen (segfault natif Qt, non déterministe dans
  le trace Python — n'apparaît pas forcément dans le test qui en est
  la cause). Cause probable : indexation/watch récursif de tous les
  dotfiles/dossiers cachés d'un dossier racine (dont `Path.home()`,
  repli par défaut de l'explorateur), multiplié par les nombreuses
  instances `MainWindow()` créées à travers la suite. Pour griser une
  entrée "cachée" par convention (nom préfixé d'un point) sans
  toucher au filtre du modèle, vérifier le nom via
  `model.fileName(index).startswith(".")` dans un délégué
  (`QStyledItemDelegate.initStyleOption`), pas `QFileInfo.isHidden()`
  (dépend de l'attribut système sous Windows, pas du nom — ne se
  déclenche pas pour un fichier juste préfixé d'un point sans cet
  attribut posé).

## Conventions de test

- `QT_QPA_PLATFORM=offscreen` pour tout test touchant Qt (pas besoin
  d'affichage). Fixture `qapp` module-scope réutilisée dans plusieurs
  fichiers (`QApplication.instance() or QApplication(sys.argv)`).
- Un test par bug corrigé, nommé explicitement comme régression quand
  c'en est une (`test_remove_chip_button_actually_removes_person`,
  pas juste `test_remove_chip`), avec un commentaire PATCH n pointant
  vers la cause.
- `tests/conftest.py` isole déjà le registre de personnes ; pas besoin
  de mocker/monkeypatcher `Document()` pour ça dans un nouveau test.

## Conventions de code

- Commentaires et docstrings en français, orientés *pourquoi* plutôt
  que *quoi* (le code dit déjà le "quoi"). En-tête de docstring de
  module avec le(s) numéro(s) de PATCH concerné(s) quand c'est un
  changement notable, pour tracer une décision jusqu'à
  `CHANGELOG.md`/`ui/design_notes.py`.
- `ui/i18n.py::tr(key)` pour tout texte affiché ; les clés suivent un
  schéma `domaine.sous_element` (`people.remove`, `menu.file.export_pdf`).
  Ajouter la clé en `fr` et `en`. Les widgets qui vivent au-delà de
  leur construction doivent avoir une méthode de retraduction appelée
  depuis `MainWindow.retranslate_ui` si le texte peut changer de
  langue en cours de session.
