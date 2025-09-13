# Distributed Key-Value Store API

A distributed FastAPI-based REST API for a versioned key-value store with API Gateway architecture that maintains multiple versions of values for each key.

## Features

- **Distributed Architecture**: API Gateway + Backend Server separation for independent scaling
- **Versioned Storage**: Each key can have multiple versions with automatic versioning
- **Three-Layer Architecture**: API Gateway, Server, Cache, and Database layers
- **Write-Through Cache**: Every PUT operation writes to both cache and database
- **Cache Fallback**: GET operations fall back to database on cache miss
- **LRU Cache**: In-memory cache with configurable size limit and Least Recently Used eviction
- **Data Persistence**: All data is stored in SQLite database for durability
- **Type Safety**: Full Pydantic model validation and type hints
- **Interactive Documentation**: Built-in Swagger UI at `/docs`
- **Thread Safe**: Thread-safe operations using RLock
- **Container Ready**: Full Docker support with docker-compose orchestration

## Project Structure

```
Key - value store/
├── gateway/             # API Gateway service
│   ├── __init__.py
│   ├── main.py         # API Gateway entry point
│   └── Dockerfile      # Gateway container config
├── server/             # Backend server service
│   ├── __init__.py
│   ├── main.py         # Server entry point
│   ├── routes.py       # FastAPI route handlers
│   ├── models.py       # Pydantic models
│   ├── store.py        # Cache layer with LRU eviction
│   ├── database.py     # SQLite database layer
│   └── Dockerfile      # Server container config
├── legacy/             # Legacy monolithic version
│   ├── __init__.py
│   └── main.py         # Original monolithic service
├── shared/             # Shared utilities (for future use)
│   └── __init__.py
├── data/               # Data directory
│   └── kv_store.db
├── docker-compose.yml  # Multi-service orchestration
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Architecture

```
Client Request
     ↓
API Gateway (Port 8000) ← Only External Access Point
     ↓
Backend Server (Internal - Port 8080)
     ↓
Cache Layer (In-Memory LRU)
     ↓
Database Layer (SQLite)
```

**Security Note**: The backend server is only accessible within the Docker network. External clients can only connect through the API Gateway.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Distributed System

### Option 1: Docker Compose (Recommended)
```bash
# Start the distributed system (API Gateway + Backend Server)
docker-compose up --build

# Stop the services
docker-compose down
```

### Option 2: Run Individual Services
```bash
# Start API Gateway only
python gateway/main.py

# Start Backend Server only (in another terminal)
python server/main.py
```

### Option 3: Legacy Single Service
```bash
# Run the original monolithic version
python legacy/main.py
```

## Service URLs

- **API Gateway**: http://localhost:8000 (Entry point - use this for all client requests)
- **Backend Server**: Only accessible through API Gateway (no direct access)
- **Legacy Service**: http://localhost:8080 (When running main.py directly)

## Data Persistence

The application now supports **persistent data storage** across container restarts:

### Database Location
- **Container Path**: `/app/data/kv_store.db`
- **Host Path**: `./data/kv_store.db` (when using docker-compose)

### Persistence Methods

#### Method 1: Docker Compose (Recommended)
The `docker-compose.yml` file automatically mounts a local `./data` directory to `/app/data` in the container:

```bash
# Start with persistent storage
docker-compose up -d

# Your data will be stored in ./data/kv_store.db
# Data persists across container restarts
```

#### Method 2: Manual Volume Mount
```bash
# Create data directory
mkdir -p ./data

# Run with volume mount
docker run -p 8080:8080 -v $(pwd)/data:/app/data kv-store
```

#### Method 3: Docker Named Volume
```bash
# Create named volume
docker volume create kv-store-data

# Run with named volume
docker run -p 8080:8080 -v kv-store-data:/app/data kv-store
```

### Data Backup
To backup your data:
```bash
# Copy database file
cp ./data/kv_store.db ./backup/kv_store_$(date +%Y%m%d).db
```

### Data Migration
To migrate data between environments:
```bash
# Copy database file to new environment
scp ./data/kv_store.db user@new-server:/path/to/data/
```

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

**All requests should go through the API Gateway at port 8000:**

```bash
# Store a value through API Gateway
curl -X PUT "http://localhost:8000/put/mykey" \
     -H "Content-Type: application/json" \
     -d '{"value": "hello world"}'

# Get latest value through API Gateway
curl "http://localhost:8000/get/mykey"

# Get specific version through API Gateway
curl "http://localhost:8000/get/mykey?version=1"

# Check cache statistics through API Gateway
curl "http://localhost:8000/cache/stats"

# Check database statistics through API Gateway
curl "http://localhost:8000/db/stats"
```

**Note: Backend server is not directly accessible. All requests must go through the API Gateway.**

## Distributed Architecture

The system implements a distributed architecture with separated layers for independent scaling:

### 1. API Gateway Layer
- **Entry Point**: All client requests come through the API Gateway (port 8000)
- **Request Forwarding**: Transparently forwards requests to backend servers
- **Error Handling**: Handles connection failures and timeouts gracefully
- **Load Distribution**: Ready for multiple backend servers (future enhancement)

### 2. Backend Server Layer
- **Business Logic**: Handles all key-value operations
- **FastAPI Application**: Provides REST API endpoints
- **Input Validation**: Uses Pydantic models for request/response validation
- **Interactive Documentation**: Swagger UI available at `/docs`

### 3. Cache Layer (In-Memory)
- **LRU Cache**: Least Recently Used eviction strategy
- **Default Size**: 100 keys maximum (configurable)
- **Fast Access**: In-memory storage for frequently accessed data
- **Access Tracking**: Both GET and PUT operations update access time

### 4. Database Layer (SQLite)
- **Persistent Storage**: All data is stored in SQLite database
- **Versioned Data**: Each version is stored separately
- **Durability**: Data survives application and container restarts
- **File Storage**: Database stored as `/app/data/kv_store.db` (persistent volume)

## Data Flow

### PUT Operations (Write-Through)
```
Client → API Gateway → Backend Server → Database Write → Cache Update → Response
```
- Client sends request to API Gateway (port 8000)
- Gateway forwards to Backend Server (port 8080)
- Server writes to database first (durability)
- Then updates cache (performance)
- Database controls version numbering

### GET Operations (Cache-First with Fallback)
```
Client → API Gateway → Backend Server → Cache Check → Database Fallback (if miss) → Cache Update → Response
```
- Client sends request to API Gateway (port 8000)
- Gateway forwards to Backend Server (port 8080)
- Server tries cache first for speed
- Falls back to database on cache miss
- Adds database results to cache (cache-aside pattern)

## Cache Configuration

You can modify the cache size by changing the `max_cache_size` parameter in `routes.py`:

```python
store = VersionedKeyValueStore(database=db, max_cache_size=2)
```

## Response Models

All responses use Pydantic models for consistent structure and validation:

- **VersionedValueResponse**: Contains value, version, and timestamp
- **PutResponse**: Contains operation details (create/update)
