"""
PATCH 29 — Tests du remplacement de texte global (sans Qt).
"""
from __future__ import annotations

import unittest

from blocks.checklist_block import ChecklistBlock
from blocks.list_block import ListBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.document import Document
from core.replace import replace_all


class ReplaceAllTests(unittest.TestCase):
    def test_empty_query_replaces_nothing(self) -> None:
        document = Document()
        document.add_block(TextBlock(content="Bonjour"))
        self.assertEqual(replace_all(document, "", "x"), 0)
        self.assertEqual(document.blocks[0].content, "Bonjour")

    def test_replaces_in_text_block(self) -> None:
        document = Document()
        block = TextBlock(content="Le chat noir dort")
        document.add_block(block)

        count = replace_all(document, "chat", "chien")

        self.assertEqual(count, 1)
        self.assertEqual(block.content, "Le chien noir dort")

    def test_replace_is_case_insensitive(self) -> None:
        document = Document()
        block = TextBlock(content="Chat CHAT chat")
        document.add_block(block)

        count = replace_all(document, "chat", "chien")

        self.assertEqual(count, 3)
        self.assertEqual(block.content, "chien chien chien")

    def test_replace_clears_stale_rich_html(self) -> None:
        document = Document()
        block = TextBlock(content="Bonjour", html="<p><b>Bonjour</b></p>")
        document.add_block(block)

        replace_all(document, "Bonjour", "Salut")

        self.assertEqual(block.content, "Salut")
        self.assertEqual(block.html, "")

    def test_replaces_in_checklist_item(self) -> None:
        document = Document()
        block = ChecklistBlock()
        block.add_item("Acheter du pain")
        document.add_block(block)

        count = replace_all(document, "pain", "lait")

        self.assertEqual(count, 1)
        self.assertEqual(block.items[0]["text"], "Acheter du lait")

    def test_replaces_in_list_item(self) -> None:
        document = Document()
        block = ListBlock()
        block.add_item("Première étape")
        document.add_block(block)

        count = replace_all(document, "étape", "phase")

        self.assertEqual(count, 1)
        self.assertEqual(block.items[0]["text"], "Première phase")

    def test_replaces_in_text_table_column(self) -> None:
        document = Document()
        block = TableBlock()
        column = block.add_column(name="Nom", col_type="text")
        row = block.add_row()
        block.set_cell(row["id"], column["id"], "Alice Dupont")
        document.add_block(block)

        count = replace_all(document, "Dupont", "Martin")

        self.assertEqual(count, 1)
        self.assertEqual(block.get_cell(row["id"], column["id"]), "Alice Martin")

    def test_does_not_touch_person_column(self) -> None:
        document = Document()
        block = TableBlock()
        column = block.add_column(name="Responsable", col_type="person")
        row = block.add_row()
        block.set_cell(row["id"], column["id"], ["Dupont"])
        document.add_block(block)

        count = replace_all(document, "Dupont", "Martin")

        self.assertEqual(count, 0)
        self.assertEqual(block.get_cell(row["id"], column["id"]), ["Dupont"])

    def test_does_not_touch_date_column(self) -> None:
        document = Document()
        block = TableBlock()
        column = block.add_column(name="Échéance", col_type="date")
        row = block.add_row()
        block.set_cell(row["id"], column["id"], "2026-01-01")
        document.add_block(block)

        count = replace_all(document, "2026", "2027")

        self.assertEqual(count, 0)
        self.assertEqual(block.get_cell(row["id"], column["id"]), "2026-01-01")

    def test_replaces_in_multi_select_column(self) -> None:
        document = Document()
        block = TableBlock()
        column = block.add_column(name="Tags", col_type="multi_select")
        row = block.add_row()
        block.set_cell(row["id"], column["id"], ["urgent", "backend"])
        document.add_block(block)

        count = replace_all(document, "backend", "frontend")

        self.assertEqual(count, 1)
        self.assertEqual(block.get_cell(row["id"], column["id"]), ["urgent", "frontend"])

    def test_replaces_in_simple_table_cell(self) -> None:
        document = Document()
        block = SimpleTableBlock(rows=[["A", "B"], ["C", "trouve-moi"]])
        document.add_block(block)

        count = replace_all(document, "trouve-moi", "trouvé")

        self.assertEqual(count, 1)
        self.assertEqual(block.rows[1][1], "trouvé")

    def test_no_match_returns_zero_and_does_not_mutate(self) -> None:
        document = Document()
        block = TextBlock(content="Rien à voir")
        document.add_block(block)

        count = replace_all(document, "introuvable", "x")

        self.assertEqual(count, 0)
        self.assertEqual(block.content, "Rien à voir")


if __name__ == "__main__":
    unittest.main()
