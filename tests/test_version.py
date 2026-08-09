"""
PATCH 42 — Vérifie le marqueur de version unique de l'application.
"""
from __future__ import annotations

import unittest

from core.version import __version__


class VersionTests(unittest.TestCase):
    def test_version_is_semantic(self) -> None:
        self.assertRegex(__version__, r"^\d+\.\d+\.\d+$")

    def test_version_is_1_0_0_at_release(self) -> None:
        self.assertEqual(__version__, "1.0.0")


if __name__ == "__main__":
    unittest.main()
