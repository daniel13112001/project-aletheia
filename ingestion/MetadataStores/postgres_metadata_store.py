from typing import Dict, Any, Iterable
from .base_metadata_store import BaseMetadataStore
import psycopg
from psycopg.rows import dict_row
from datetime import date
from dotenv import load_dotenv
import os


class PostgresMetadataStore(BaseMetadataStore):
    def __init__(self, url: str):
        self.conn = psycopg.connect(url, row_factory=dict_row)

    # ---------- Helpers ----------

    def _row_to_record(self, row: Dict[str, Any]) -> Dict[str, Any]:

        if not row:
            return None

        return {
            "uid": row["uid"],
            "statement": row["statement"],
            "verdict": row["verdict"],
            "statement_originator": row["statement_originator"],
            "statement_date": row["statement_date"].isoformat()
            if row["statement_date"] else None,
            "statement_source": row["statement_source"],
            "factchecker": row["factchecker"],
            "factcheck_date": row["factcheck_date"].isoformat()
            if row["factcheck_date"] else None,
            "factcheck_analysis_link": row["factcheck_analysis_link"],
        }


    def upsert(self, uid: str, metadata: Dict[str, Any]) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO claim_metadata (
                    uid,
                    statement,
                    verdict,
                    statement_originator,
                    statement_date,
                    statement_source,
                    factchecker,
                    factcheck_date,
                    factcheck_analysis_link
                )
                VALUES (
                    %(uid)s,
                    %(statement)s,
                    %(verdict)s,
                    %(statement_originator)s,
                    %(statement_date)s,
                    %(statement_source)s,
                    %(factchecker)s,
                    %(factcheck_date)s,
                    %(factcheck_analysis_link)s
                )
                ON CONFLICT (uid) DO UPDATE SET
                    statement = EXCLUDED.statement,
                    verdict = EXCLUDED.verdict,
                    statement_originator = EXCLUDED.statement_originator,
                    statement_date = EXCLUDED.statement_date,
                    statement_source = EXCLUDED.statement_source,
                    factchecker = EXCLUDED.factchecker,
                    factcheck_date = EXCLUDED.factcheck_date,
                    factcheck_analysis_link = EXCLUDED.factcheck_analysis_link;
                """,
                {
                    "uid": uid,
                    "statement": metadata.get("statement"),
                    "verdict": metadata.get("verdict"),
                    "statement_originator": metadata.get("statement_originator"),
                    "statement_date": metadata.get("statement_date"),
                    "statement_source": metadata.get("statement_source"),
                    "factchecker": metadata.get("factchecker"),
                    "factcheck_date": metadata.get("factcheck_date"),
                    "factcheck_analysis_link": metadata.get("factcheck_analysis_link"),
                },
            )
            self.conn.commit()

    def get(self, uid: str) -> Dict[str, Any] | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM claim_metadata
                WHERE uid = %s;
                """,
                (uid,),
            )
            row = cur.fetchone()
            return self._row_to_record(row)

    def bulk_get(self, uids: Iterable[str]) -> Dict[str, Dict[str, Any]]:
        uids = list(uids)
        if not uids:
            return {}

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT *
                FROM claim_metadata
                WHERE uid = ANY(%s);
                """,
                (uids,),
            )
            rows = cur.fetchall()

        return {
            row["uid"]: self._row_to_record(row)
            for row in rows
        }

    def exists(self, uid: str) -> bool:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT 1
                FROM claim_metadata
                WHERE uid = %s
                LIMIT 1;
                """,
                (uid,),
            )
            return cur.fetchone() is not None


def main():
    # Test run supabase DB Connection
    
    load_dotenv(".env.local")

    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    # 2️⃣ Init store
    store = PostgresMetadataStore(database_url)

    # 3️⃣ Test data
    uid = "test-claim-001"
    record = {
        "uid": uid,
        "statement": "The Earth revolves around the Sun.",
        "verdict": "True",
        "statement_originator": "Copernicus",
        "statement_date": "1543-01-01",
        "statement_source": "De revolutionibus orbium coelestium",
        "factchecker": "Science",
        "factcheck_date": "2024-01-01",
        "factcheck_analysis_link": "https://example.com/factcheck",
    }

    # 4️⃣ Upsert
    print("Upserting record...")
    store.upsert(uid, record)

    # 5️⃣ Get
    print("Fetching record...")
    fetched = store.get(uid)
    print(fetched)

    # 6️⃣ Exists
    print("Exists?", store.exists(uid))

    # 7️⃣ Bulk get
    print("Bulk get...")
    bulk = store.bulk_get([uid, "non-existent"])
    print(bulk)


if __name__ == "__main__":
    main()