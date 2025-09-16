# Distributed Key-Value Store API

A distributed FastAPI-based REST API for a versioned key-value store with API Gateway architecture.

## Features

- **Distributed Architecture**: API Gateway + Multiple Backend Servers with load balancing
- **Consistent Hashing**: Key-based routing with SHA-256 hashing and virtual nodes
- **Load Balancing**: Intelligent request distribution across backend servers
- **Versioned Storage**: Each key can have multiple versions with automatic versioning
- **LRU Cache**: In-memory cache with configurable size limit per server
- **Data Persistence**: SQLite database for durability with per-server isolation
- **Database Management**: Comprehensive cleanup scripts with safety features
- **Interactive Documentation**: Built-in Swagger UI at `/docs`
- **Container Ready**: Full Docker support with docker-compose orchestration
- **Fault Tolerance**: Automatic failover and key redistribution on server failures

## Project Structure

```
Key - value store/
├── gateway/                    # API Gateway service
│   ├── __init__.py
│   ├── main.py                # API Gateway entry point
│   ├── load_balancer.py       # Load balancing logic
│   ├── consistent_hash.py     # Consistent hashing implementation
│   └── Dockerfile             # Gateway container config
├── server/                    # Backend server service
│   ├── __init__.py
│   ├── main.py                # Server entry point
│   ├── routes.py              # FastAPI route handlers
│   ├── models.py              # Pydantic models
│   ├── store.py               # Cache layer with LRU eviction
│   ├── database.py            # SQLite database layer
│   └── Dockerfile             # Server container config
├── legacy/                    # Legacy monolithic version
│   ├── __init__.py
│   └── main.py                # Original monolithic service
├── shared/                    # Shared utilities
│   └── __init__.py
├── deploy/                    # Deployment configuration
│   ├── ansible/
│   │   ├── inventory.yaml     # Server inventory
│   │   └── playbook.yaml      # Deployment playbook
│   ├── ansible.cfg            # Ansible configuration
│   └── deploy.sh              # Deployment script
├── data/                      # Data directory
│   ├── kv_store.db           # Main SQLite database
│   ├── server-1/             # Server 1 data directory
│   │   └── kv_store.db       # Server 1 database
│   └── server-2/             # Server 2 data directory
│       └── kv_store.db       # Server 2 database
├── scripts/                   # Utility scripts
│   ├── clean_databases.py    # Database cleanup script
│   └── clean.sh              # Database cleanup wrapper
├── docker-compose.yml         # Multi-service orchestration
├── requirements.txt           # Python dependencies
├── LICENSE                   # MIT License
└── README.md                 # This file
```

## Architecture

```
Client Request
     ↓
API Gateway (Port 8000) ← Only External Access Point
     ↓
Load Balancer with Consistent Hashing
     ↓
┌─────────────────┬─────────────────┐
│   Backend       │   Backend       │
│   Server 1      │   Server 2      │
│   (Port 8080)   │   (Port 8080)   │
└─────────────────┴─────────────────┘
     ↓                     ↓
Cache Layer (LRU)    Cache Layer (LRU)
     ↓                     ↓
Database (SQLite)    Database (SQLite)
   server-1/            server-2/
   kv_store.db          kv_store.db
```

### Load Balancing & Consistent Hashing

The system uses **consistent hashing** to distribute keys across multiple backend servers:

- **Key-based routing**: Each key is consistently mapped to the same server using SHA-256 hashing
- **Virtual nodes**: 150 virtual nodes per server for better load distribution
- **Automatic failover**: If a server becomes unavailable, its keys are redistributed
- **Minimal data movement**: Adding/removing servers only affects a small portion of keys

**Security Note**: Backend servers are only accessible within the Docker network. External clients can only connect through the API Gateway.

## Load Balancing & Consistent Hashing Details

### How It Works

1. **Request Routing**: When a client makes a request to the API Gateway, the load balancer extracts the key from the URL path
2. **Hash Calculation**: The key is hashed using SHA-256 to produce a consistent hash value
3. **Server Selection**: The hash value is used to find the appropriate server on the consistent hash ring
4. **Request Forwarding**: The request is forwarded to the selected backend server

### Key Benefits

- **Consistent Mapping**: The same key always maps to the same server, ensuring data consistency
- **Load Distribution**: Virtual nodes (150 per server) provide even distribution of keys
- **Scalability**: Adding new servers requires minimal data redistribution
- **Fault Tolerance**: Server failures automatically redistribute affected keys to remaining servers

### Implementation Details

```python
# Consistent hashing with virtual nodes
class ConsistentHash:
    def __init__(self, servers: List[str], virtual_nodes: int = 150):
        # Creates 150 virtual nodes per server for better distribution
        
    def get_server(self, key: str) -> Optional[str]:
        # Uses SHA-256 hashing and binary search for O(log n) lookup
```

### Server Configuration

The system currently supports:
- **server-1:8080** - Backend server 1
- **server-2:8080** - Backend server 2

Each server maintains its own:
- In-memory LRU cache
- SQLite database (`server-1/kv_store.db`, `server-2/kv_store.db`)

## Running Locally

### Prerequisites
1. Install Docker and Docker Compose
2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Start Services
```bash
# Start the distributed system (API Gateway + Backend Server)
docker-compose up --build

# Stop the services
docker-compose down
```

## Service URLs

- **API Gateway**: http://localhost:8000 (Entry point - use this for all client requests)
- **Backend Server**: Only accessible through API Gateway (no direct access)
- **Legacy Service**: http://localhost:8080 (When running main.py directly)

## Data Persistence

Data is stored in SQLite databases across multiple servers:
- **Main database**: `./data/kv_store.db` (legacy)
- **Server 1**: `./data/server-1/kv_store.db`
- **Server 2**: `./data/server-2/kv_store.db`

All databases persist across container restarts when using docker-compose.

## Database Management

### Database Cleanup Script

The system includes a comprehensive database cleanup script located in the `scripts/` directory:

**Files:**
- `scripts/clean_databases.py` - Main Python cleanup script
- `scripts/clean.sh` - Bash wrapper for easier execution

**Features:**
- Automatically discovers all database files in the data directory
- Shows detailed statistics before cleaning
- Supports dry-run mode for safe preview
- Cleans both `keys` and `values` tables
- Resets AUTOINCREMENT counters
- Runs VACUUM to reclaim disk space
- Includes confirmation prompts for safety

**Usage Examples:**

```bash
# Navigate to scripts directory
cd scripts/

# Preview what would be cleaned (safe to run)
python3 clean_databases.py --dry-run
# or
./clean.sh --dry-run

# Clean all databases with confirmation
python3 clean_databases.py
# or
./clean.sh

# Clean all databases without confirmation (for automation)
python3 clean_databases.py --confirm
# or
./clean.sh --confirm
```

**Safety Features:**
- **Dry-run mode**: Always test with `--dry-run` first
- **Confirmation prompt**: Requires explicit confirmation before cleaning
- **Detailed statistics**: Shows exactly what will be cleaned
- **Error handling**: Gracefully handles missing files or database errors

## API Endpoints

### PUT Operations
- `POST /put/{key}` - Store a value for a key
  - Body: `{"value": "your_value"}`
  - Returns: Operation details with version info

### GET Operations
- `GET /get/{key}` - Get the latest value for a key
- `GET /get/{key}?version=N` - Get a specific version of a key

### Cache Operations
- `GET /cache/stats?server={server_name}` - Get cache statistics from specific server (size, max size, is full)

### Database Operations
- `GET /db/stats?server={server_name}` - Get database statistics from specific server (total keys, versions, file size)

**Note**: The `server` parameter is mandatory for stats endpoints. Available servers: `server-1:8080`, `server-2:8080`

### Server Information
- `GET /servers` - Get list of available backend servers

### Interactive Documentation
- `GET /docs` - Swagger UI for testing the API

## Example Usage

**All requests should go through the API Gateway at port 8000. The load balancer will automatically route requests to the appropriate backend server based on the key:**

```bash
# Note: Keys are automatically distributed across servers using consistent hashing
# The same key will always go to the same server for consistency
```

```bash
# Store a value through API Gateway
curl -X PUT "http://localhost:8000/put/mykey" \
     -H "Content-Type: application/json" \
     -d '{"value": "hello world"}'

# Get latest value through API Gateway
curl "http://localhost:8000/get/mykey"

# Get specific version through API Gateway
curl "http://localhost:8000/get/mykey?version=1"

# Get list of available servers
curl "http://localhost:8000/servers"

# Check cache statistics from server-1 through API Gateway
curl "http://localhost:8000/cache/stats?server=server-1:8080"

# Check cache statistics from server-2 through API Gateway
curl "http://localhost:8000/cache/stats?server=server-2:8080"

# Check database statistics from server-1 through API Gateway
curl "http://localhost:8000/db/stats?server=server-1:8080"

# Check database statistics from server-2 through API Gateway
curl "http://localhost:8000/db/stats?server=server-2:8080"
```

**Note: Backend server is not directly accessible. All requests must go through the API Gateway.**

## Deployment

### Prerequisites
- Three Ubuntu servers (1 for API Gateway, 2 for backend servers)
- SSH access with sudo privileges
- Ansible installed on your local machine

### Step 1: Configure Inventory File
Edit `deploy/ansible/inventory.yaml` and replace the placeholder values:

```yaml
all:
  children:
    gateway:
      hosts:
        gateway-server:
          ansible_host: YOUR_GATEWAY_IP      # Replace with actual IP
          ansible_user: YOUR_USERNAME         # Replace with SSH username
    
    servers:
      hosts:
        server-1:
          ansible_host: YOUR_SERVER1_IP       # Replace with actual IP
          ansible_user: YOUR_USERNAME         # Replace with SSH username
        server-2:
          ansible_host: YOUR_SERVER2_IP       # Replace with actual IP
          ansible_user: YOUR_USERNAME         # Replace with SSH username
```

### Step 2: Run Deployment
```bash
# Navigate to deployment directory
cd deploy

# Run the deployment script
./deploy.sh

```

For detailed deployment information, or any issues please contact me at dhruvsoni1802@gmail.com