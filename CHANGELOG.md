# Changelog

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
