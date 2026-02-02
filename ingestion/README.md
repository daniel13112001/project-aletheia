# Ingestion Service

A batch pipeline that processes fact-check datasets, generates embeddings, and populates the vector store and metadata database. Designed to be run as a one-time job or periodically to update the knowledge base.

## Tech Stack

- **Language:** Python 3.11
- **Embeddings:** OpenAI (`text-embedding-3-small`)
- **Vector Store:** Pinecone (production) / FAISS (development)
- **Metadata Store:** PostgreSQL (production) / In-memory (development)
- **Data Source:** Kaggle (Politifact dataset)

## Prerequisites

- Python 3.11+
- OpenAI API key
- PostgreSQL database (production)
- Pinecone account and index (production)
- Kaggle API credentials (for downloading datasets)

## Installation

### Local Development

```bash
cd ingestion

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Docker

```bash
# From project root
docker build -t aletheia-ingestion -f ingestion/Dockerfile .
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | OpenAI API key for generating embeddings |
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `PINECONE_API_KEY` | Yes | Pinecone API key |
| `PINECONE_INDEX` | Yes | Name of the Pinecone index |

Create a `.env.local` file:
```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@host:5432/database
PINECONE_API_KEY=pcsk_...
PINECONE_INDEX=claims
```

### Kaggle Credentials

For automatic dataset download, configure Kaggle credentials:

```bash
# Option 1: Environment variable
export KAGGLE_API_TOKEN={"username":"...","key":"..."}

# Option 2: Kaggle config file
# Place kaggle.json in ~/.kaggle/
```

## Running

### Local Development

```bash
cd ingestion
python -m ingestion.ingest
```

### With Custom Parameters

```bash
python -m ingestion.ingest \
  --batch-size 100 \
  --max-batches 50 \
  --embedding-model text-embedding-3-small \
  --vector-dim 1536 \
  --no-sanity-check
```

### Docker

```bash
docker run \
  -e OPENAI_API_KEY=$OPENAI_API_KEY \
  -e DATABASE_URL=$DATABASE_URL \
  -e PINECONE_API_KEY=$PINECONE_API_KEY \
  -e PINECONE_INDEX=$PINECONE_INDEX \
  aletheia-ingestion \
  --batch-size 100 --max-batches 50
```

## Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--batch-size` | int | 3 | Number of records to process per batch |
| `--max-batches` | int | 1 | Maximum number of batches to process |
| `--embedding-model` | str | `text-embedding-3-small` | OpenAI embedding model |
| `--vector-dim` | int | 1536 | Embedding vector dimensions |
| `--no-sanity-check` | flag | false | Skip the sanity check after ingestion |

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Ingestion Pipeline                          │
│                                                                  │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐   │
│  │    Kaggle    │───►│   Dataset    │───►│  Batch Iterator  │   │
│  │   Download   │    │   Loader     │    │                  │   │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘   │
│                                                   │              │
│                     ┌─────────────────────────────┘              │
│                     │                                            │
│                     ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    For each batch:                        │   │
│  │                                                           │   │
│  │  1. Upsert metadata ──────────────► PostgreSQL            │   │
│  │                                                           │   │
│  │  2. Generate embeddings ──────────► OpenAI API            │   │
│  │                                                           │   │
│  │  3. Upsert vectors ───────────────► Pinecone              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                    Sanity Check:                          │   │
│  │  - Count vectors in store                                 │   │
│  │  - Count metadata entries                                 │   │
│  │  - Query with test embedding                              │   │
│  │  - Verify metadata retrieval                              │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ingestion/
├── ingest.py              # Main ingestion script
├── config.py              # Configuration constants
├── typing_defs.py         # Type definitions
├── requirements.txt       # Python dependencies
├── Dockerfile             # Container definition
├── Datasets/
│   ├── claim_ingestion_dataset.py    # Abstract base class
│   └── politifact_ingestion_dataset.py  # Politifact loader
├── VectorStores/
│   ├── vector_store.py    # Abstract base class
│   ├── faiss_vector_store.py    # FAISS implementation
│   └── pinecone_vector_store.py # Pinecone implementation
└── MetadataStores/
    ├── base_metadata_store.py       # Abstract base class
    ├── in_memory_metadata_store.py  # In-memory implementation
    └── postgres_metadata_store.py   # PostgreSQL implementation
```

## Data Model

### Input Record (from Politifact)

```python
{
    "statement": "The claim text",
    "verdict": "True|False|Pants on Fire|...",
    "statement_originator": "Who made the claim",
    "statement_date": "2024-01-15",
    "statement_source": "Where it appeared",
    "factchecker": "PolitiFact",
    "factcheck_analysis_link": "https://..."
}
```

### Processed Record

```python
{
    "uid": "sha256_hash",  # SHA256(statement + analysis_link)
    "statement": "The claim text",
    "verdict": "True",
    "statement_originator": "Who made the claim",
    "statement_date": "2024-01-15",
    "statement_source": "Where it appeared",
    "factchecker": "PolitiFact",
    "factcheck_analysis_link": "https://...",
    "source": "politifact"
}
```

## Store Interfaces

### VectorStore

```python
class VectorStore(ABC):
    def upsert(ids: List[str], vectors: List[Vector], metadatas: Optional[List[Metadata]])
    def query(vector: Vector, k: int, filters: Optional[Metadata]) -> Tuple[List[str], List[float]]
    def delete(ids: List[str])
    def count() -> int
    def save(path: str)  # Optional, for local stores
```

**Implementations:**
- `FaissVectorStore` - Local FAISS index (development)
- `PineconeVectorStore` - Cloud Pinecone (production)

### MetadataStore

```python
class BaseMetadataStore(ABC):
    def upsert(uid: str, metadata: Dict[str, Any])
    def get(uid: str) -> Optional[Dict[str, Any]]
    def bulk_get(uids: Iterable[str]) -> Dict[str, Dict[str, Any]]
    def exists(uid: str) -> bool
    def count() -> int
    def save(path: str)  # Optional, for local stores
```

**Implementations:**
- `InMemoryMetadataStore` - In-memory dict (development)
- `PostgresMetadataStore` - PostgreSQL table (production)

## Database Schema

The ingestion service populates the `claim_metadata` table:

```sql
CREATE TABLE claim_metadata (
    uid TEXT PRIMARY KEY,
    statement TEXT,
    verdict TEXT,
    statement_originator TEXT,
    statement_date DATE,
    statement_source TEXT,
    factchecker TEXT,
    factcheck_date DATE,
    factcheck_analysis_link TEXT
);
```

## Adding New Datasets

To add a new fact-check dataset:

1. Create a new class extending `ClaimIngestionDataset`:

```python
# Datasets/my_dataset.py
from .claim_ingestion_dataset import ClaimIngestionDataset

class MyDataset(ClaimIngestionDataset):
    def _row_iterator(self):
        # Yield raw rows from your data source
        for row in load_data():
            yield row

    def _transform_row(self, row):
        # Transform to standard format
        return {
            "uid": generate_uid(row),
            "statement": row["claim"],
            "verdict": row["rating"],
            # ... other fields
        }
```

2. Update `ingest.py` to use your dataset:

```python
dataset = MyDataset(dataset_path)
```

## Local Development Mode

For development without cloud services, use local stores:

```python
# In ingest.py, switch to local stores:
metadata_store = InMemoryMetadataStore()
vector_store = FaissVectorStore(vector_dim)

# After ingestion, save to disk:
vector_store.save("../artifacts/faiss")
metadata_store.save("../artifacts/metadata.jsonl")
```

## Dependencies

Key packages from `requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| openai | 2.15.0 | Embedding generation |
| pinecone | 8.0.0 | Vector database |
| faiss-cpu | 1.13.2 | Local vector search |
| psycopg | 3.3.2 | PostgreSQL driver |
| kagglehub | 0.4.0 | Dataset download |
| numpy | 2.4.1 | Array operations |

## Troubleshooting

**"OPENAI_API_KEY is not set":**
- Ensure environment variables are loaded before running
- Check `.env.local` file exists and is properly formatted

**Kaggle download fails:**
- Verify Kaggle credentials are configured
- Check internet connectivity
- Dataset may have been removed or renamed

**PostgreSQL connection error:**
- Verify `DATABASE_URL` format: `postgresql://user:pass@host:port/db`
- Check database is accessible from your network
- Ensure the `claim_metadata` table exists

**Pinecone errors:**
- Verify index name matches `PINECONE_INDEX`
- Check API key has write permissions
- Ensure index dimensions match embedding model (1536)
