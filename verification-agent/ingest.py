import os
import argparse
import kagglehub
from dotenv import load_dotenv
from openai import OpenAI

from Datasets.politifact_ingestion_dataset import PolitifactIngestionDataset
from MetadataStores.in_memory_metadata import InMemoryMetadataStore
from VectorStores.faiss_vector_store import FaissVectorStore


def ingest(
    *,
    dataset_path: str,
    embedding_model: str,
    vector_dim: int,
    batch_size: int,
    max_batches: int | None,
    run_sanity_check: bool,
):
    
    # Env vars and Open AI client
    load_dotenv(".env.local")
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    # Data Stores
    metadata_store = InMemoryMetadataStore()
    vector_store = FaissVectorStore(vector_dim)

    dataset = PolitifactIngestionDataset(dataset_path)

    test_uid = None
    test_text = None
    test_embedding = None

    for i, (ids, texts, metadatas) in enumerate(dataset.batches(batch_size=batch_size)):

        if max_batches is not None and i >= max_batches:
            break

        for uid, metadata in zip(ids, metadatas):
            metadata_store.upsert(uid, metadata)

        response = client.embeddings.create(
            model=embedding_model,
            input=texts,
            encoding_format="float",
        )

        embeddings = [item.embedding for item in response.data]

        vector_store.upsert(ids=ids, vectors=embeddings)

        if test_uid is None:
            test_uid = ids[0]
            test_text = texts[0]
            test_embedding = embeddings[0]

    # Sanity Check.
    if run_sanity_check and test_embedding is not None:
        print("\n--- SANITY CHECK ---")
        print("Total vectors stored:", vector_store.count())
        print("Total metadata entries:", len(metadata_store.data))

        nearest_ids = vector_store.query(vector=test_embedding, k=3)

        print("\nQuery text:")
        print(test_text)

        print("\nNearest IDs returned:", nearest_ids)

        for uid in nearest_ids:
            print("\nUID:", uid)
            print("Metadata:", metadata_store.get(uid))


def main(
    *,
    batch_size: int,
    max_batches: int | None,
    embedding_model: str,
    vector_dim: int,
    run_sanity_check: bool,
):
    
    dataset_path = kagglehub.dataset_download(
        "rmisra/politifact-fact-check-dataset"
    )

    ingest(
        dataset_path=dataset_path,
        embedding_model=embedding_model,
        vector_dim=vector_dim,
        batch_size=batch_size,
        max_batches=max_batches,
        run_sanity_check=run_sanity_check,
    )


if __name__ == "__main__":
    # ---- defaults live here ----
    DEFAULT_BATCH_SIZE = 3
    DEFAULT_MAX_BATCHES = 1   
    DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
    DEFAULT_VECTOR_DIM = 1536
    DEFAULT_RUN_SANITY_CHECK = True

    parser = argparse.ArgumentParser(description="Politifact ingestion pipeline")

    parser.add_argument("--batch-size", type=int)
    parser.add_argument("--max-batches", type=int)
    parser.add_argument("--embedding-model", type=str)
    parser.add_argument("--vector-dim", type=int)
    parser.add_argument("--no-sanity-check", action="store_true")

    args = parser.parse_args()

    main(
        batch_size=args.batch_size or DEFAULT_BATCH_SIZE,
        max_batches=args.max_batches if args.max_batches is not None else DEFAULT_MAX_BATCHES,
        embedding_model=args.embedding_model or DEFAULT_EMBEDDING_MODEL,
        vector_dim=args.vector_dim or DEFAULT_VECTOR_DIM,
        run_sanity_check=not args.no_sanity_check
        if args.no_sanity_check is not None
        else DEFAULT_RUN_SANITY_CHECK,
    )
