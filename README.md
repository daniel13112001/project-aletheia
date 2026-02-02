# Project Aletheia

A real-time fact-checking system that allows users to verify claims against a database of fact-checked statements. Users can highlight text on any webpage through a Chrome extension and instantly receive relevant fact-check results.

## Architecture

```
┌─────────────────────┐
│  Chrome Extension   │
│     (JavaScript)    │
└──────────┬──────────┘
           │ HTTP
           ▼
┌─────────────────────┐      gRPC       ┌─────────────────────┐
│    API Gateway      │ ◄─────────────► │  Retrieval Service  │
│       (Go)          │                 │      (Python)       │
│     :8080           │                 │       :50051        │
└──────────┬──────────┘                 └──────────┬──────────┘
           │                                       │
           │ SQL                                   │ Vector Search
           ▼                                       ▼
┌─────────────────────┐                 ┌─────────────────────┐
│    PostgreSQL       │                 │   FAISS / Pinecone  │
│  (Claim Metadata)   │                 │   (Vector Store)    │
└─────────────────────┘                 └─────────────────────┘

┌─────────────────────┐
│  Ingestion Service  │  ──► Processes datasets, generates embeddings,
│     (Python)        │      populates vector store and metadata DB
└─────────────────────┘
```

## Components

| Component | Description | Tech Stack |
|-----------|-------------|------------|
| [API Gateway](./api-gateway) | REST API with rate limiting, routes requests to services | Go, gRPC, Redis |
| [Chrome Extension](./chrome-extension) | Browser extension for fact-checking highlighted text | JavaScript, Manifest V3 |
| [Retrieval Service](./retrieval_service) | Vector similarity search via gRPC | Python, FAISS, OpenAI |
| [Ingestion Service](./ingestion) | Batch pipeline for processing fact-check datasets | Python, Pinecone, PostgreSQL |

## Quick Start

### Prerequisites

- Go 1.21+
- Python 3.11+
- PostgreSQL
- Redis
- Docker (optional)

### Environment Variables

Create a `.env.local` file in the project root:

```bash
OPENAI_API_KEY=sk-...
DATABASE_URL=postgresql://user:password@host:5432/database
PINECONE_API_KEY=...
PINECONE_INDEX=claims
```

### Running Locally

1. **Start Redis:**
   ```bash
   redis-server
   ```

2. **Start the Retrieval Service:**
   ```bash
   cd retrieval_service
   python -m retrieval_service.server
   ```

3. **Start the API Gateway:**
   ```bash
   cd api-gateway
   go run main.go
   ```

4. **Load the Chrome Extension:**
   - Open Chrome → `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked" → Select `chrome-extension/` folder

### Running with Docker

```bash
# Build and run the retrieval service
docker build -t aletheia-retrieval -f retrieval_service/Dockerfile .
docker run -p 50051:50051 -e OPENAI_API_KEY=$OPENAI_API_KEY aletheia-retrieval

# Build and run the ingestion service
docker build -t aletheia-ingestion -f ingestion/Dockerfile .
docker run -e OPENAI_API_KEY=$OPENAI_API_KEY \
           -e DATABASE_URL=$DATABASE_URL \
           -e PINECONE_API_KEY=$PINECONE_API_KEY \
           -e PINECONE_INDEX=$PINECONE_INDEX \
           aletheia-ingestion
```

## Data Flow

### User Query Flow

1. User highlights text on a webpage and clicks the extension
2. Extension sends the text to the API Gateway (`GET /search?q=...`)
3. API Gateway checks rate limits (5 requests/minute per IP via Redis)
4. API Gateway calls the Retrieval Service via gRPC
5. Retrieval Service generates an embedding using OpenAI
6. Retrieval Service queries FAISS for similar vectors
7. API Gateway fetches metadata from PostgreSQL for matched UIDs
8. Results are returned to the extension and displayed to the user

### Data Ingestion Flow

1. Ingestion Service downloads fact-check datasets (e.g., Politifact from Kaggle)
2. Records are processed in batches
3. Metadata is stored in PostgreSQL
4. Embeddings are generated via OpenAI API
5. Vectors are stored in Pinecone (production) or FAISS (development)

## API Reference

### Search Endpoint

```
GET /search?q=<query>
```

**Response:**
```json
[
  {
    "uid": "abc123...",
    "statement": "The claim text",
    "verdict": "True",
    "statement_originator": "Person who made the claim",
    "statement_date": "2024-01-15",
    "statement_source": "News source",
    "factchecker": "PolitiFact",
    "factcheck_date": "2024-01-20",
    "factcheck_analysis_link": "https://..."
  }
]
```

**Rate Limit:** 5 requests per minute per IP

### Health Check

```
GET /health
```

Returns `ok` with status 200.

## Database Schema

### claim_metadata

| Column | Type | Description |
|--------|------|-------------|
| uid | TEXT (PK) | SHA256 hash of claim + analysis link |
| statement | TEXT | The claim text |
| verdict | TEXT | True, False, or Mixed |
| statement_originator | TEXT | Who made the claim |
| statement_date | DATE | When the claim was made |
| statement_source | TEXT | Source of the claim |
| factchecker | TEXT | Organization that checked it |
| factcheck_date | DATE | When it was checked |
| factcheck_analysis_link | TEXT | URL to full analysis |

## Project Structure

```
project-aletheia/
├── api-gateway/           # Go REST API server
│   ├── handlers/          # HTTP handlers
│   ├── stores/            # Data store interfaces
│   ├── db/                # Database connections
│   └── gen/               # Generated gRPC code
├── chrome-extension/      # Browser extension
│   ├── manifest.json
│   ├── popup.html/js/css
│   └── background.js
├── retrieval_service/     # Python gRPC server
│   ├── server.py
│   └── Dockerfile
├── ingestion/             # Data ingestion pipeline
│   ├── ingest.py
│   ├── Datasets/          # Dataset loaders
│   ├── VectorStores/      # Vector store implementations
│   ├── MetadataStores/    # Metadata store implementations
│   └── Dockerfile
├── proto/                 # Protocol buffer definitions
└── artifacts/             # Generated artifacts (FAISS index, etc.)
```

## External Services

| Service | Purpose |
|---------|---------|
| OpenAI | Text embeddings (`text-embedding-3-small`) |
| Pinecone | Production vector database |
| PostgreSQL | Claim metadata storage |
| Redis | Rate limiting |
| Kaggle | Fact-check dataset source |

## License

MIT
