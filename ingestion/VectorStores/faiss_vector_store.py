import faiss
import json
import numpy as np
from pathlib import Path
from typing import List, Optional

from VectorStores.vector_store import VectorStore
from typing_defs import Vector, Metadata


class FaissVectorStore(VectorStore):
    def __init__(self, dim: int):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.id_map: List[str] = []  # position → UID

    # ---------- Core operations ----------

    def upsert(
        self,
        ids: List[str],
        vectors: List[Vector],
        metadatas: Optional[List[Metadata]] = None,  # intentionally ignored
    ) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have same length")

        vecs = np.asarray(vectors, dtype="float32")
        faiss.normalize_L2(vecs)

        self.index.add(vecs)
        self.id_map.extend(ids)

    def query(
        self,
        vector: Vector,
        k: int,
        filters: Optional[Metadata] = None,  # intentionally ignored
    ) -> List[str]:
        vec = np.asarray([vector], dtype="float32")
        faiss.normalize_L2(vec)

        scores, indices = self.index.search(vec, k)

        results: List[str] = []
        for i in indices[0]:
            if i == -1:
                continue
            results.append(self.id_map[i])

        return results

    def delete(self, ids: List[str]) -> None:
        raise NotImplementedError(
            "FAISS IndexFlat does not support deletes without rebuilding"
        )

    def count(self) -> int:
        return self.index.ntotal

    # ---------- Persistence ----------

    def save(self, path: str | Path) -> None:
        """
        Persist FAISS index + ID map to disk.

        Layout:
            path/
              ├─ index.faiss
              └─ ids.json
        """
        path = Path(path)
        path.mkdir(parents=True, exist_ok=True)

        faiss.write_index(self.index, str(path / "index.faiss"))

        with open(path / "ids.json", "w") as f:
            json.dump(self.id_map, f)

    @classmethod
    def load(cls, path: str | Path) -> "FaissVectorStore":
        """
        Load FAISS index + ID map from disk.
        """
        path = Path(path)

        index = faiss.read_index(str(path / "index.faiss"))

        with open(path / "ids.json") as f:
            id_map = json.load(f)

        store = cls(index.d)
        store.index = index
        store.id_map = id_map
        return store
