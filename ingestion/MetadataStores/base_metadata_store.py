from abc import ABC, abstractmethod
from typing import Dict, Any, Iterable

class BaseMetadataStore(ABC):

    @abstractmethod
    def upsert(self, uid: str, metadata: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def get(self, uid: str) -> Dict[str, Any] | None:
        ...

    @abstractmethod
    def bulk_get(self, uids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        ...

    @abstractmethod
    def exists(self, uid: str) -> bool:
        ...
