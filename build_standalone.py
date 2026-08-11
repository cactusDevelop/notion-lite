"""
Génère un fichier unique et autonome (notion_lite_standalone.py) regroupant
tout le code local du projet (core/, blocks/, ui/, main.py).

Usage:
    python build_standalone.py

Le fichier produit ne dépend plus que de PySide6 (dépendance externe),
plus aucun fichier du dépôt n'est nécessaire pour l'exécuter.
"""
from __future__ import annotations

import base64
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
LOCAL_PACKAGES = ("core", "blocks", "ui")
OUTPUT = os.path.join(ROOT, "notion_lite_standalone.py")


def collect_modules() -> dict[str, tuple[str, bool]]:
    """Retourne {nom_module_dotted: (source, is_package)}."""
    modules: dict[str, tuple[str, bool]] = {}
    for pkg in LOCAL_PACKAGES:
        pkg_dir = os.path.join(ROOT, pkg)
        for dirpath, _dirnames, filenames in os.walk(pkg_dir):
            rel_dir = os.path.relpath(dirpath, ROOT)
            dotted_dir = rel_dir.replace(os.sep, ".")
            for fname in filenames:
                if not fname.endswith(".py"):
                    continue
                fpath = os.path.join(dirpath, fname)
                with open(fpath, "r", encoding="utf-8") as f:
                    src = f.read()
                if fname == "__init__.py":
                    modules[dotted_dir] = (src, True)
                else:
                    mod_name = f"{dotted_dir}.{fname[:-3]}"
                    modules[mod_name] = (src, False)
    return modules


def main() -> None:
    modules = collect_modules()

    # L'icône (i) de la toolbar est chargée depuis icon-info.svg via un
    # chemin disque relatif au dépôt : on l'embarque en base64 et on
    # l'écrit dans un fichier temporaire au démarrage pour rester 100%
    # autonome (plus besoin du fichier .svg à côté du script).
    with open(os.path.join(ROOT, "icon-info.svg"), "rb") as f:
        icon_b64 = base64.b64encode(f.read()).decode("ascii")
    src, is_pkg = modules["ui.main_window"]
    src = src.replace(
        '_PROJECT_ROOT = Path(__file__).resolve().parent.parent\n'
        '_INFO_ICON_PATH = str(_PROJECT_ROOT / "icon-info.svg")',
        "import atexit as _atexit\n"
        "import base64 as _base64\n"
        "import os as _os\n"
        "import tempfile as _tempfile\n"
        f"_ICON_INFO_SVG_B64 = {icon_b64!r}\n"
        "_icon_tmp = _tempfile.NamedTemporaryFile(suffix='.svg', delete=False)\n"
        "_icon_tmp.write(_base64.b64decode(_ICON_INFO_SVG_B64))\n"
        "_icon_tmp.close()\n"
        "_atexit.register(lambda: _os.unlink(_icon_tmp.name))\n"
        "_INFO_ICON_PATH = _icon_tmp.name",
    )
    modules["ui.main_window"] = (src, is_pkg)

    with open(os.path.join(ROOT, "main.py"), "r", encoding="utf-8") as f:
        main_src = f.read()
    main_src = main_src.replace(
        'if __name__ == "__main__":\n    main()\n', ""
    )
    main_src = main_src.replace("window.show()", "window.showMaximized()")

    with open(OUTPUT, "w", encoding="utf-8") as out:
        out.write(
            '"""\n'
            "Notion Lite - build autonome (fichier unique).\n"
            "Généré automatiquement par build_standalone.py, ne pas éditer à la main.\n"
            "Dépendance externe requise: PySide6.\n"
            '"""\n'
            "import sys\n"
            "import types\n"
            "import importlib.abc\n"
            "import importlib.util\n\n"
            "_SOURCES = {}\n"
            "_PACKAGES = set()\n\n"
        )
        for name, (src, is_pkg) in sorted(modules.items()):
            out.write(f"_SOURCES[{name!r}] = {src!r}\n")
            if is_pkg:
                out.write(f"_PACKAGES.add({name!r})\n")
        out.write("\n\n")
        out.write(
            "class _EmbeddedLoader(importlib.abc.Loader):\n"
            "    def __init__(self, name):\n"
            "        self._name = name\n\n"
            "    def create_module(self, spec):\n"
            "        module = types.ModuleType(spec.name)\n"
            "        module.__file__ = f'<embedded:{spec.name}>'\n"
            "        module.__loader__ = self\n"
            "        module.__spec__ = spec\n"
            "        if spec.submodule_search_locations is not None:\n"
            "            module.__path__ = []\n"
            "            module.__package__ = spec.name\n"
            "        else:\n"
            "            module.__package__ = spec.name.rpartition('.')[0]\n"
            "        return module\n\n"
            "    def exec_module(self, module):\n"
            "        exec(compile(_SOURCES[self._name], module.__file__, 'exec'), module.__dict__)\n\n\n"
            "class _EmbeddedFinder(importlib.abc.MetaPathFinder):\n"
            "    def find_spec(self, name, path, target=None):\n"
            "        if name not in _SOURCES:\n"
            "            return None\n"
            "        is_pkg = name in _PACKAGES\n"
            "        spec = importlib.util.spec_from_loader(name, _EmbeddedLoader(name), is_package=is_pkg)\n"
            "        return spec\n\n\n"
            "sys.meta_path.insert(0, _EmbeddedFinder())\n\n\n"
        )
        out.write(main_src)
        out.write("\n\nif __name__ == \"__main__\":\n    main()\n")

    print(f"Fichier généré: {OUTPUT}")


if __name__ == "__main__":
    main()
