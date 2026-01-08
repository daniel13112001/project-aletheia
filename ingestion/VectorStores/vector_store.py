from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Dict, Any
from ..typing_defs import Vector, Metadata



class VectorStore(ABC):
    """
    Backend-agnostic vector store interface.

    """

    @abstractmethod
    def upsert(
        self,
        ids: List[str],
        vectors: List[Vector],
        metadatas: Optional[List[Metadata]] = None,
    ) -> None:
        """
        Insert or update vectors.

        - ids must be stable and globally unique
        - vectors must align 1:1 with ids
        - metadatas are optional but must align if provided
        """
        raise NotImplementedError

    @abstractmethod
    def query(
        self,
        vector: Vector,
        k: int,
        filters: Optional[Metadata] = None,
    ) -> List[str]:
        """
        Return top-k matching vector IDs.

        - filters may be ignored by some backends (e.g. FAISS)
        - ordering must be relevance-descending
        """
        raise NotImplementedError

    @abstractmethod
    def delete(self, ids: List[str]) -> None:
        """
        Delete vectors by ID.
        """
        raise NotImplementedError

    @abstractmethod
    def count(self) -> int:
        """
        Return number of stored vectors.
        """
        raise NotImplementedError

    def save(self, path: str) -> None:
        pass