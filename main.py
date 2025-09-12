#!/usr/bin/env python3

from fastapi import FastAPI
import uvicorn
from routes import router

# Create FastAPI app
app = FastAPI(
    title="Versioned Key-Value Store API",
    description="A REST API for a versioned key-value store",
    version="1.0.0"
)

# Include routes
app.include_router(router)


def main():
    print("Starting versioned key-value store server...\n")
    print("Server will run at http://localhost:8080\n")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
