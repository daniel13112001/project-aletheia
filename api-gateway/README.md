# API Gateway

REST API server that serves as the main entry point for the Aletheia fact-checking system. Handles HTTP requests from clients, communicates with the Retrieval Service via gRPC, and fetches metadata from PostgreSQL.

## Tech Stack

- **Language:** Go 1.21+
- **Database:** PostgreSQL (via pgx)
- **Cache:** Redis (rate limiting)
- **Communication:** gRPC (to Retrieval Service)

## Prerequisites

- Go 1.21 or higher
- PostgreSQL database with `claim_metadata` table
- Redis server running
- Retrieval Service running on port 50051

## Configuration

### Environment Variables

Create a `.env.local` file in the `api-gateway` directory:

```bash
DATABASE_URL=postgresql://user:password@host:5432/database
```

### Service Connections

| Service | Default Address | Description |
|---------|-----------------|-------------|
| Redis | `localhost:6379` | Rate limiting store |
| gRPC (Retrieval) | `localhost:50051` | Vector search service |

## Running

### Local Development

```bash
cd api-gateway
go run main.go
```

The server starts on port **8080**.

### Building

```bash
cd api-gateway
go build -o api-gateway main.go
./api-gateway
```

## API Endpoints

### GET /health

Health check endpoint.

**Response:**
```
200 OK
ok
```

### GET /search

Search for similar fact-checked claims.

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| q | string | Yes | The text to fact-check |

**Example:**
```bash
curl "http://localhost:8080/search?q=The%20earth%20is%20flat"
```

**Success Response (200):**
```json
[
  {
    "uid": "a1b2c3d4...",
    "statement": "The earth is flat",
    "verdict": "False",
    "statement_originator": "Various social media users",
    "statement_date": "2023-05-10",
    "statement_source": "Social media",
    "factchecker": "PolitiFact",
    "factcheck_date": "2023-05-15",
    "factcheck_analysis_link": "https://www.politifact.com/..."
  }
]
```

**Error Responses:**

| Status | Condition | Body |
|--------|-----------|------|
| 400 | Missing query parameter | `missing query parameter: q` |
| 429 | Rate limit exceeded | `Too many requests. Max is 5 requests per minute` |
| 500 | Metadata lookup failed | `metadata lookup failed` |
| 502 | Vector search failed | `vector search failed` |

### POST /login

*Not implemented.* Returns 501.

### POST /claims

*Not implemented.* Returns 501.

## Rate Limiting

- **Limit:** 5 requests per minute per IP address
- **Implementation:** Redis-backed sliding window
- **Key format:** `rl:search:<ip_address>`

When the rate limit is exceeded, the API returns:
```
HTTP 429 Too Many Requests
Too many requests. Max is 5 requests per minute
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                        API Gateway                            │
│                                                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐   │
│  │   Handler   │───►│ RateLimiter │───►│   Redis Store   │   │
│  └──────┬──────┘    └─────────────┘    └─────────────────┘   │
│         │                                                     │
│         ├───────────────────────────────────────────────┐    │
│         │                                               │    │
│         ▼                                               ▼    │
│  ┌─────────────┐                              ┌─────────────┐│
│  │ gRPC Client │                              │  Metadata   ││
│  │ (Vector)    │                              │   Store     ││
│  └──────┬──────┘                              └──────┬──────┘│
└─────────┼───────────────────────────────────────────┼───────┘
          │                                           │
          ▼                                           ▼
   ┌─────────────┐                           ┌─────────────┐
   │  Retrieval  │                           │ PostgreSQL  │
   │  Service    │                           │             │
   └─────────────┘                           └─────────────┘
```

## Project Structure

```
api-gateway/
├── main.go              # Application entry point
├── go.mod               # Go module definition
├── go.sum               # Dependency checksums
├── handlers/
│   └── handlers.go      # HTTP handlers (search, health, etc.)
├── stores/
│   ├── metadata-store.go           # MetadataStore interface
│   ├── postgres_metadata_store.go  # PostgreSQL implementation
│   ├── rate-limit-store.go         # RateLimitStore interface
│   └── redis_rate_limit_store.go   # Redis implementation
├── db/
│   └── postgres.go      # PostgreSQL connection
├── gen/
│   └── vectorsearch/    # Generated gRPC client code
└── config/
    └── config.go        # Configuration (placeholder)
```

## Dependencies

Key dependencies from `go.mod`:

| Package | Version | Purpose |
|---------|---------|---------|
| google.golang.org/grpc | v1.78.0 | gRPC client |
| github.com/jackc/pgx/v5 | v5.8.0 | PostgreSQL driver |
| github.com/redis/go-redis/v9 | v9.17.2 | Redis client |
| github.com/joho/godotenv | v1.5.1 | Environment loading |

## gRPC Communication

The API Gateway communicates with the Retrieval Service using gRPC.

**Proto definition:** `../proto/vector_search.proto`

```protobuf
service VectorSearchService {
  rpc Search (SearchRequest) returns (SearchResponse);
}

message SearchRequest {
  string query = 1;
  uint32 k = 2;
}

message SearchResponse {
  repeated SearchResult results = 1;
}
```

**Regenerating gRPC code:**
```bash
protoc --go_out=. --go-grpc_out=. ../proto/vector_search.proto
```

## Database Schema

The API Gateway reads from the `claim_metadata` table:

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
