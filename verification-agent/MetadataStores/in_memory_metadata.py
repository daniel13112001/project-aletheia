from .metadata import MetadataStore
from typing import Dict, Any, Iterable


class InMemoryMetadataStore(MetadataStore):

    def __init__(self):
        self.data: Dict[str, Dict[str, Any]] = {}

    def upsert(self, uid: str, metadata: Dict[str, Any]) -> None:
        self.data[uid] = metadata

    def get(self, uid: str) -> Dict[str, Any] | None:
        return self.data.get(uid)

    def bulk_get(self, uids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        return {uid: self.data[uid] for uid in uids if uid in self.data}

    def exists(self, uid: str) -> bool:
        return uid in self.data
