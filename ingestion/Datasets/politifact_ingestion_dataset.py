import json
import hashlib
from datetime import datetime
from .claim_ingestion_dataset import ClaimIngestionDataset
from pathlib import Path

class PolitifactIngestionDataset(ClaimIngestionDataset):

    def _row_iterator(self):
        path = Path(self.path)

        if path.is_file():
            files = [path]
        else:
            files = sorted(path.glob("*.json*"))  # json or jsonl

        for file_path in files:
            with open(file_path) as f:
                for line in f:
                    yield json.loads(line)

    def _transform_row(self, row):
        claim = row["statement"].strip()

        uid = hashlib.sha256(
            (claim + row["factcheck_analysis_link"]).encode()
        ).hexdigest()

        record = {
            "uid": uid,
            "statement": claim,
            "verdict": row["verdict"],
            "statement_originator": row["statement_originator"],
            "statement_date": row["statement_date"],
            "statement_source": row["statement_source"],
            "factchecker": row["factchecker"],
            "factcheck_analysis_link": row["factcheck_analysis_link"],
            "source": "politifact"
        }

        return record
