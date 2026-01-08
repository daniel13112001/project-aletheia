from .base_metadata_store import BaseMetadataStore
from typing import Dict, Any, Iterable
from pathlib import Path
import json

class InMemoryMetadataStore(BaseMetadataStore):

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}

    def upsert(self, uid: str, record: Dict[str, Any]) -> None:
        self.data[uid] = record

    def get(self, uid: str) -> Dict[str, Any] | None:
        return self.data.get(uid)

    def bulk_get(self, uids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        return {uid: self.data[uid] for uid in uids if uid in self.data}

    def exists(self, uid: str) -> bool:
        return uid in self.data
    
  # ---------- Persistence ----------

    def save(self, path: str) -> None:
        """
        Persist metadata to disk as JSONL.
        Each line is a single flattened record.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            for record in self.data.values():
                f.write(json.dumps(record, ensure_ascii=False))
                f.write("\n")


    @classmethod
    def load(cls, path: str) -> "InMemoryMetadataStore":
        """
        Load metadata from a JSONL file.
        """
        store = cls()
        path = Path(path)

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                record = json.loads(line)
                store.data[record["uid"]] = record["metadata"]

        return store
