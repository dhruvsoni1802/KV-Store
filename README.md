# Versioned Key-Value Store API

A simple FastAPI-based REST API for a versioned key-value store that maintains multiple versions of values for each key.

## Features

- **Versioned Storage**: Each key can have multiple versions with automatic versioning
- **Three-Layer Architecture**: API layer, LRU cache layer, and SQLite database layer
- **Write-Through Cache**: Every PUT operation writes to both cache and database
- **Cache Fallback**: GET operations fall back to database on cache miss
- **LRU Cache**: In-memory cache with configurable size limit and Least Recently Used eviction
- **Data Persistence**: All data is stored in SQLite database for durability
- **Type Safety**: Full Pydantic model validation and type hints
- **Interactive Documentation**: Built-in Swagger UI at `/docs`
- **Thread Safe**: Thread-safe operations using RLock

## Project Structure

```
Key - value store/
├── main.py              # FastAPI application entry point
├── models.py            # Pydantic models for request/response
├── store.py             # Cache layer with LRU eviction
├── database.py          # SQLite database layer
├── routes.py            # FastAPI route handlers
├── requirements.txt     # Python dependencies
├── Dockerfile          # Docker container configuration
├── .dockerignore       # Docker ignore file
└── README.md           # This file
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Server

### Option 1: Direct Python
```bash
python main.py
```

### Option 2: Docker
```bash
# Build the Docker image
docker build -t kv-store .

# Run the container
docker run -p 8080:8080 kv-store
```

The server will start on `http://localhost:8080`

## API Endpoints

### PUT Operations
- `POST /put/{key}` - Store a value for a key
  - Body: `{"value": "your_value"}`
  - Returns: Operation details with version info

### GET Operations
- `GET /get/{key}` - Get the latest value for a key
- `GET /get/{key}?version=N` - Get a specific version of a key

### Cache Operations
- `GET /cache/stats` - Get cache statistics (size, max size, is full)

### Database Operations
- `GET /db/stats` - Get database statistics (total keys, versions, file size)

### Interactive Documentation
- `GET /docs` - Swagger UI for testing the API

## Example Usage

```bash
# Store a value
curl -X POST "http://localhost:8080/put/mykey" \
     -H "Content-Type: application/json" \
     -d '{"value": "hello world"}'

# Get latest value
curl "http://localhost:8080/get/mykey"

# Get specific version
curl "http://localhost:8080/get/mykey?version=1"

# Check cache statistics
curl "http://localhost:8080/cache/stats"

# Check database statistics
curl "http://localhost:8080/db/stats"
```

## Three-Layer Architecture

The system implements a three-layer architecture for optimal performance and data durability:

### 1. API Layer (FastAPI)
- Handles HTTP requests and responses
- Validates input using Pydantic models
- Provides interactive documentation at `/docs`

### 2. Cache Layer (In-Memory)
- **LRU Cache**: Least Recently Used eviction strategy
- **Default Size**: 100 keys maximum (configurable)
- **Fast Access**: In-memory storage for frequently accessed data
- **Access Tracking**: Both GET and PUT operations update access time

### 3. Database Layer (SQLite)
- **Persistent Storage**: All data is stored in SQLite database
- **Versioned Data**: Each version is stored separately
- **Durability**: Data survives application restarts
- **File Storage**: Database stored as `kv_store.db` file

## Data Flow

### PUT Operations (Write-Through)
```
PUT Request → Database Write → Cache Update → Response
```
- Every write goes to database first (durability)
- Then updates cache (performance)
- Database controls version numbering

### GET Operations (Cache-First with Fallback)
```
GET Request → Cache Check → Database Fallback (if miss) → Cache Update → Response
```
- Try cache first for speed
- Fall back to database on cache miss
- Add database results to cache (cache-aside pattern)

## Cache Configuration

You can modify the cache size by changing the `max_cache_size` parameter in `routes.py`:

```python
store = VersionedKeyValueStore(database=db, max_cache_size=2)
```

## Response Models

All responses use Pydantic models for consistent structure and validation:

- **VersionedValueResponse**: Contains value, version, and timestamp
- **PutResponse**: Contains operation details (create/update)
