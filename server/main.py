#!/usr/bin/env python3

from fastapi import FastAPI
import uvicorn
from routes import router

# Create FastAPI app for the server service
app = FastAPI(
    title="Key-Value Store Server",
    description="Individual server instance for distributed key-value store",
    version="1.0.0"
)

# Include routes
app.include_router(router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check for the server instance"""
    return {"status": "healthy", "service": "kv-store-server"}


def main():
    print("Starting key-value store server...")
    print("Server will run at http://localhost:8080")
    print("Press Ctrl+C to stop the server")
    
    uvicorn.run(app, host="0.0.0.0", port=8080)


if __name__ == '__main__':
    main()
