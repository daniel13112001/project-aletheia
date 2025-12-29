from abc import ABC, abstractmethod

class ClaimIngestionDataset(ABC):
    """
    Base class for claim-based ingestion datasets.
    Responsible for streaming rows, transforming them
    into (id, text, metadata), and yielding batches.
    """

    def __init__(self, path: str):
        self.path = path

    @abstractmethod
    def _row_iterator(self):
        """
        Yield raw rows (dicts) from the dataset.
        Must be streaming.
        """
        pass

    @abstractmethod
    def _transform_row(self, row):
        """
        Transform a raw row into:
            (id: str, text: str, metadata: dict)
        """
        pass

    def batches(self, batch_size: int):
        """
        Yield batches of (ids, texts, metadatas).
        """
        ids, texts, metadatas = [], [], []

        for row in self._row_iterator():
            _id, text, metadata = self._transform_row(row)

            ids.append(_id)
            texts.append(text)
            metadatas.append(metadata)

            if len(ids) == batch_size:
                yield ids, texts, metadatas
                ids, texts, metadatas = [], [], []

        if ids:
            yield ids, texts, metadatas
