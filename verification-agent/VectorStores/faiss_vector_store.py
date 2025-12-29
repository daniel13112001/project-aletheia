import faiss
import numpy as np
from VectorStores.vector_store import VectorStore
from typing import List, Dict, Any, Tuple, Optional
from typing_defs import Vector, Metadata



class FaissVectorStore(VectorStore):
    def __init__(self, dim: int):
        self.index = faiss.IndexFlatIP(dim)
        self.id_map: List[str] = []  # position → string ID

    def upsert(
        self,
        ids: List[str],
        vectors: List[Vector],
        metadatas: Optional[List[Metadata]] = None,
    ) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have same length")

        vecs = np.array(vectors, dtype="float32")
        faiss.normalize_L2(vecs)
        self.index.add(vecs)
        self.id_map.extend(ids)

    def query(
        self,
        vector: Vector,
        k: int,
        filters: Optional[Metadata] = None,
    ) -> List[str]:
        vec = np.array([vector], dtype="float32")
        faiss.normalize_L2(vec)
        distances, indices = self.index.search(vec, k)

        results = []
        for i in indices[0]:
            if i == -1:
                continue
            results.append(self.id_map[i])

        return results

    def delete(self, ids: List[str]) -> None:
        raise NotImplementedError(
            "FAISS does not support deletes without rebuilding"
        )

    def count(self) -> int:
        return self.index.ntotal
