"""Actual model + Chroma integration, with separate processes proving persistence.

Run build_vectors.py once first so the shared model cache is available offline.
No synthetic embeddings or keyword fallback are used in these integration checks.
"""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SETUP = '''
import sys
from pathlib import Path
from semantic import SemanticIndex
index = SemanticIndex(Path(sys.argv[1]), model_cache=Path('data/model-cache'))
records = [
 {'id': 1, 'title': 'Robotic timber construction', 'source_abstract': 'Industrial manipulators assemble wooden beams into load bearing structures. Digital fabrication allows machines to create complex architectural components.'},
 {'id': 2, 'title': 'Spatial sound', 'source_abstract': 'An immersive audio installation explores listening through a distributed array of speakers in a public gallery.'},
 {'id': 3, 'title': 'Garden cultivation', 'source_abstract': 'Community gardens grow vegetables through irrigation and composting to improve access to fresh produce.'},
]
'''


class VectorIntegrationTests(unittest.TestCase):
    # Launch a fresh Python process to verify real disk persistence, not shared memory.
    def run_child(self, directory, script):
        result = subprocess.run([sys.executable, '-c', SETUP + script, str(directory)],
                                cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_multilingual_retrieval_persistence_and_changes(self):
        with tempfile.TemporaryDirectory(dir=ROOT / 'tmp') as directory:
            self.run_child(directory, '''
index.synchronize(records)
assert index.search('un brazo automatizado que construye con madera', ids=[1,2,3], k=1)[0]['id'] == 1
assert index.map()['theses'] == 3
neighbors = index.neighbors(1, k=2, minimum=0)
assert all(item['id'] != 1 for item in neighbors)
assert neighbors == sorted(neighbors, key=lambda item: -item['similarity'])
''')
            self.run_child(directory, '''
assert index.profiles.count() == 3  # persisted without synchronize or re-embedding
original_embed = index.embed
def fail_if_reembedded(texts):
    raise AssertionError('Unchanged corpus was embedded again')
index.embed = fail_if_reembedded
index.synchronize(records)
index.embed = original_embed
filtered = index.search('wooden fabrication', ids=[2,3])
assert all(item['id'] in (2,3) for item in filtered)
index.upsert({'id':4, 'title':'Adaptive domestic lighting', 'source_abstract':'Rooms automatically change their light when people walk through them. Motion sensors control the brightness of lamps in a house.'})
assert index.search('habitaciones que cambian la luz cuando camino', ids=[1,2,3,4], k=1)[0]['id'] == 4
index.remove(4)
assert index.profiles.count() == 3
assert all(item['id'] != 4 for item in index.search('domestic lighting', ids=[1,2,3,4]))
assert len(index.map()['points']) == 3
''')


if __name__ == '__main__':
    unittest.main()
