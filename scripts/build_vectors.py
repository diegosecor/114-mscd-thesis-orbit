"""Build or incrementally refresh the persistent multilingual abstract index."""
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import init_db, semantic_store

if __name__ == "__main__":
    # Reconcile the source catalogue before deriving coordinates and topic groups.
    init_db()
    print(json.dumps(semantic_store().map(), ensure_ascii=False, indent=2))
