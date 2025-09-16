# Distributed Key-Value Store API

A distributed FastAPI-based REST API for a versioned key-value store with API Gateway architecture.

## Features

- **Distributed Architecture**: API Gateway + Backend Server separation
- **Versioned Storage**: Each key can have multiple versions with automatic versioning
- **LRU Cache**: In-memory cache with configurable size limit
- **Data Persistence**: SQLite database for durability
- **Interactive Documentation**: Built-in Swagger UI at `/docs`
- **Container Ready**: Full Docker support with docker-compose orchestration

## Project Structure

```
Key - value store/
├── gateway/                    # API Gateway service
│   ├── __init__.py
│   ├── main.py                # API Gateway entry point
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
│   └── kv_store.db           # SQLite database
├── docker-compose.yml         # Multi-service orchestration
├── requirements.txt           # Python dependencies
├── DEPLOYMENT.md             # Deployment guide
├── LICENSE                   # MIT License
└── README.md                 # This file
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

Data is stored in SQLite database at `./data/kv_store.db` and persists across container restarts when using docker-compose.

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