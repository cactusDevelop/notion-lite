"""
PATCH 28 — Tests du moteur de recherche globale (sans Qt).
"""
from __future__ import annotations

import unittest

from blocks.checklist_block import ChecklistBlock
from blocks.heading_block import HeadingBlock
from blocks.list_block import ListBlock
from blocks.quote_block import QuoteBlock
from blocks.simple_table_block import SimpleTableBlock
from blocks.table_block import TableBlock
from blocks.text_block import TextBlock
from core.document import Document
from core.search import search_document


class SearchDocumentTests(unittest.TestCase):
    def test_empty_query_returns_nothing(self) -> None:
        document = Document()
        document.add_block(TextBlock(content="Bonjour le monde"))
        self.assertEqual(search_document(document, ""), [])
        self.assertEqual(search_document(document, "   "), [])

    def test_finds_match_in_text_block(self) -> None:
        document = Document()
        block = TextBlock(content="Le chat noir dort")
        document.add_block(block)

        results = search_document(document, "chat")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].block_id, block.id)
        self.assertEqual(results[0].location, "Texte")
        self.assertIn("chat", results[0].snippet)

    def test_search_is_case_insensitive(self) -> None:
        document = Document()
        document.add_block(TextBlock(content="Bonjour le Monde"))
        self.assertEqual(len(search_document(document, "MONDE")), 1)
        self.assertEqual(len(search_document(document, "monde")), 1)

    def test_finds_match_in_heading_quote_and_code(self) -> None:
        document = Document()
        document.add_block(HeadingBlock(level=1, content="Rapport annuel"))
        document.add_block(QuoteBlock(content="La vie est un rapport"))
        document.add_block(TextBlock(content="Rien à voir"))

        results = search_document(document, "rapport")

        self.assertEqual(len(results), 2)
        locations = {r.block_type for r in results}
        self.assertIn("heading1", locations)
        self.assertIn("quote", locations)

    def test_finds_match_in_checklist_item(self) -> None:
        document = Document()
        block = ChecklistBlock()
        block.add_item("Acheter du pain")
        block.add_item("Sortir le chien")
        document.add_block(block)

        results = search_document(document, "chien")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location, "Checklist — élément")

    def test_finds_match_in_list_item(self) -> None:
        document = Document()
        block = ListBlock()
        block.add_item("Première étape")
        block.add_item("Deuxième étape avec un mot-clé")
        document.add_block(block)

        results = search_document(document, "mot-clé")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].location, "Liste — élément")

    def test_finds_match_in_table_cell(self) -> None:
        document = Document()
        block = TableBlock()
        column = block.add_column(name="Nom")
        row = block.add_row()
        block.set_cell(row["id"], column["id"], "Alice Dupont")
        document.add_block(block)

        results = search_document(document, "dupont")

        self.assertEqual(len(results), 1)
        self.assertIn("Nom", results[0].location)

    def test_finds_match_in_simple_table_cell(self) -> None:
        document = Document()
        block = SimpleTableBlock(rows=[["A", "B"], ["C", "Trouve-moi"]])
        document.add_block(block)

        results = search_document(document, "trouve")

        self.assertEqual(len(results), 1)
        self.assertIn("ligne 2", results[0].location)

    def test_no_match_returns_empty_list(self) -> None:
        document = Document()
        document.add_block(TextBlock(content="Rien d'intéressant ici"))
        self.assertEqual(search_document(document, "introuvable"), [])

    def test_snippet_includes_ellipsis_for_long_text(self) -> None:
        document = Document()
        long_text = "x" * 100 + "AIGUILLE" + "y" * 100
        document.add_block(TextBlock(content=long_text))

        results = search_document(document, "AIGUILLE")

        self.assertTrue(results[0].snippet.startswith("…"))
        self.assertTrue(results[0].snippet.endswith("…"))
        self.assertIn("AIGUILLE", results[0].snippet)


if __name__ == "__main__":
    unittest.main()
