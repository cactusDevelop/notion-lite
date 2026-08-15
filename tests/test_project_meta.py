from __future__ import annotations

from core.project_meta import ProjectMeta, meta_path_for


def test_meta_path_is_hidden_system_file_next_to_document(tmp_path):
    document_path = tmp_path / "Plan Q3.json"
    assert meta_path_for(document_path) == tmp_path / ".methodo-project.json"


def test_create_and_reload_meta(tmp_path):
    document_path = tmp_path / "projet.json"
    document_path.write_text("{}", encoding="utf-8")

    meta = ProjectMeta.create("Lancement produit")
    meta.save(document_path)

    reloaded = ProjectMeta.load(document_path)
    assert reloaded is not None
    assert reloaded.name == "Lancement produit"
    assert reloaded.id == meta.id


def test_load_returns_none_when_missing(tmp_path):
    document_path = tmp_path / "projet.json"
    assert ProjectMeta.load(document_path) is None


def test_load_or_create_falls_back_to_filename(tmp_path):
    document_path = tmp_path / "ancien_projet.json"
    document_path.write_text("{}", encoding="utf-8")

    meta = ProjectMeta.load_or_create(document_path)
    assert meta.name == "ancien_projet"
    # Persisté : un second appel retrouve exactement le même projet.
    again = ProjectMeta.load_or_create(document_path)
    assert again.id == meta.id
    assert again.name == "ancien_projet"


def test_project_name_independent_from_json_filename(tmp_path):
    """Le coeur du correctif : renommer le fichier .json ne doit pas
    changer le nom du projet, puisqu'il est stocké séparément."""
    document_path = tmp_path / "data.json"
    document_path.write_text("{}", encoding="utf-8")
    meta = ProjectMeta.create("Mon super projet")
    meta.save(document_path)

    renamed_path = tmp_path / "export_final_v3.json"
    document_path.rename(renamed_path)

    reloaded = ProjectMeta.load(renamed_path)
    assert reloaded is not None
    assert reloaded.name == "Mon super projet"


def test_rename_updates_name_only(tmp_path):
    document_path = tmp_path / "projet.json"
    document_path.write_text("{}", encoding="utf-8")
    meta = ProjectMeta.create("Ancien nom")
    meta.save(document_path)

    meta.rename(document_path, "Nouveau nom")

    reloaded = ProjectMeta.load(document_path)
    assert reloaded.name == "Nouveau nom"
    assert reloaded.id == meta.id


def test_find_project_root_climbs_to_ancestor_with_meta(tmp_path):
    """PATCH 88 — Un document rangé dans un sous-dossier du projet
    (ex. "client 1" du template "Modèle OG") doit voir sa racine
    retrouvée en remontant jusqu'au dossier qui porte la métadonnée."""
    from core.project_meta import find_project_root

    client1 = tmp_path / "client 1"
    client1.mkdir()
    document_path = client1 / "client 1.json"
    document_path.write_text("{}", encoding="utf-8")

    ProjectMeta.create("Mon projet").save_to_folder(tmp_path)

    assert find_project_root(document_path) == tmp_path


def test_find_project_root_falls_back_to_parent_without_meta(tmp_path):
    """Sans métadonnée nulle part (document isolé), repli sur le
    dossier parent immédiat du document — comportement historique."""
    from core.project_meta import find_project_root

    document_path = tmp_path / "isole.json"
    document_path.write_text("{}", encoding="utf-8")

    assert find_project_root(document_path) == tmp_path


def test_load_for_document_finds_meta_in_ancestor(tmp_path):
    """PATCH 88 — `load_for_document` doit retrouver la métadonnée même
    quand elle n'est pas dans le dossier parent immédiat du document."""
    client1 = tmp_path / "client 1"
    client1.mkdir()
    document_path = client1 / "client 1.json"
    document_path.write_text("{}", encoding="utf-8")

    ProjectMeta.create("Mon projet").save_to_folder(tmp_path)

    reloaded = ProjectMeta.load_for_document(document_path)
    assert reloaded is not None
    assert reloaded.name == "Mon projet"
    # `load` (sans remontée) ne le trouve pas dans "client 1" lui-même.
    assert ProjectMeta.load(document_path) is None
