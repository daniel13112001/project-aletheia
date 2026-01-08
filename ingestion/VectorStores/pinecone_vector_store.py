from typing import List, Optional, Tuple
import numpy as np
import pinecone
import os
from .vector_store import VectorStore
from ..typing_defs import Vector, Metadata
from dotenv import load_dotenv
from pathlib import Path


from typing import List, Optional, Tuple
import numpy as np
from pinecone import Pinecone

from .vector_store import VectorStore
from ..typing_defs import Vector, Metadata


class PineconeVectorStore(VectorStore):
    def __init__(
        self,
        index_name: str,
        api_key: str,
    ):
        self.pc = Pinecone(api_key=api_key)

        # assumes index already exists
        self.index = self.pc.Index(index_name)

    # ---------- Core operations ----------

    def upsert(
        self,
        ids: List[str],
        vectors: List[Vector],
        metadatas: Optional[List[Metadata]] = None,
    ) -> None:
        if len(ids) != len(vectors):
            raise ValueError("ids and vectors must have same length")

        if metadatas is not None and len(metadatas) != len(ids):
            raise ValueError("metadatas must align with ids")

        vecs = np.asarray(vectors, dtype="float32")
        vecs = self._normalize(vecs)

        items = []
        for i, uid in enumerate(ids):
            item = {
                "id": uid,
                "values": vecs[i].tolist(),
            }
            if metadatas:
                item["metadata"] = metadatas[i]
            items.append(item)

        self.index.upsert(vectors=items)

    def query(
        self,
        vector: Vector,
        k: int,
        filters: Optional[Metadata] = None,
    ) -> Tuple[List[str], List[float]]:
        vec = np.asarray(vector, dtype="float32")
        vec = self._normalize(vec.reshape(1, -1))[0]

        response = self.index.query(
            vector=vec.tolist(),
            top_k=k,
            filter=filters,
            include_metadata=False,
            include_values=False,
        )

        ids, scores = [], []
        for match in response.matches:
            ids.append(match.id)
            scores.append(match.score)

        return ids, scores

    def delete(self, ids: List[str]) -> None:
        if ids:
            self.index.delete(ids=ids)

    def count(self) -> int:
        stats = self.index.describe_index_stats()
        return stats.total_vector_count

    # ---------- Helpers ----------

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1
        return vectors / norms


# Sanity Check
def main():

    # Env vars 
    BASE_DIR = Path(__file__).resolve().parent
    env_path = BASE_DIR.parent / ".env.local"

    print(env_path)

    load_dotenv(env_path)

    api_key = os.environ.get("PINECONE_API_KEY")
    index_name = os.environ.get("PINECONE_INDEX")

    if not all([api_key, index_name]):
        raise RuntimeError("Missing Pinecone env vars")

    # 2️⃣ Init store
    store = PineconeVectorStore(
        index_name=index_name,
        api_key=api_key
    )

    # 3️⃣ Create dummy vectors
    dim = 1536  # MUST match index dimension
    ids = ["test-1", "test-2", "test-3"]
    vectors = np.random.rand(len(ids), dim).tolist()

    # 4️⃣ Upsert
    print("Upserting vectors...")
    store.upsert(ids=ids, vectors=vectors)

    print("Vector count:", store.count())

    # 5️⃣ Query using first vector
    print("Querying...")
    q_ids, scores = store.query(
        vector=vectors[0],
        k=3,
    )

    print("Results:")
    for uid, score in zip(q_ids, scores):
        print(uid, score)

    # 6️⃣ Optional cleanup
    store.delete(ids)
    print("Deleted test vectors")


if __name__ == "__main__":
    main()