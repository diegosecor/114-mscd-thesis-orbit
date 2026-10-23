"""Check the archive does not silently stop at the first collection page."""
import unittest
import io
import json
from unittest.mock import patch

from scripts import import_collection
from scripts.enrich_advisors import advisor_fields
from advisors import advisor_names


# Build a minimal public thesis search item without contacting KiltHub.
def entry(index):
    return {"id": index, "defined_type": 8, "url_public_html": f"https://kilthub.cmu.edu/articles/thesis/{index}"}


# Provide an in-memory JSON stream matching the public API response format.
def response(batch):
    return io.BytesIO(json.dumps(batch).encode())


class CollectionPaginationTests(unittest.TestCase):
    def test_loads_next_page_and_deduplicates_source_ids(self):
        first = [entry(index) for index in range(1000)]
        second = [entry(999), entry(1000)]
        with patch.object(import_collection, "urlopen", side_effect=[response(first), response(second)]) as fetch:
            entries = import_collection.collection_entries()
        self.assertEqual(len(entries), 1001)
        self.assertEqual(entries[-1]["id"], 1000)
        self.assertEqual(json.loads(fetch.call_args_list[1].args[0].data)["offset"], 1000)

    def test_explicit_limit_still_supported(self):
        with patch.object(import_collection, "urlopen", return_value=response([entry(n) for n in range(84)])):
            self.assertEqual(len(import_collection.collection_entries(30)), 30)

    def test_repeated_page_reports_incomplete_import(self):
        batch = [entry(n) for n in range(1000)]
        with patch.object(import_collection, "urlopen", side_effect=[response(batch), response(batch)]):
            with self.assertRaisesRegex(ValueError, "repeated a page"):
                import_collection.collection_entries()

    def test_advisors_preserve_newlines_as_separate_people(self):
        detail = {"custom_fields": [{"name": "Advisor(s)", "value": "Ada Example\nAlan Example<br>Grace Example"}]}
        self.assertEqual(advisor_fields(detail), "Ada Example, Alan Example, Grace Example")
        self.assertEqual(advisor_fields({"authors": [{"full_name": "Not an advisor"}]}), "")

    def test_advisor_aliases_do_not_create_duplicate_groups(self):
        self.assertEqual(advisor_names("Daragh Byrne, Darragh Byrne, Daragh Byrme"), ["Daragh Byrne"])
        self.assertEqual(advisor_names("Vernelle Noel, New Person"), ["Vernelle A. A. Noel", "New Person"])
        self.assertEqual(advisor_names(""), [])


if __name__ == "__main__":
    unittest.main()
