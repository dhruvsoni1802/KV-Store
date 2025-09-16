#!/usr/bin/env python3

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import uvicorn
import os
from load_balancer import LoadBalancer

app = FastAPI(
    title="API Gateway",
    description="API Gateway that forwards requests to backend services",
    version="1.0.0"
)

# Configuration - get backend servers from environment variable
BACKEND_SERVERS = os.getenv("BACKEND_SERVERS", "localhost:8080").split(",")
print(f"Backend servers configured: {BACKEND_SERVERS}")

# Create load balancer with consistent hashing
load_balancer = LoadBalancer(BACKEND_SERVERS)

@app.get("/servers")
async def get_servers():
    """Get list of available backend servers"""
    return {
        "servers": BACKEND_SERVERS,
        "count": len(BACKEND_SERVERS)
    }

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(request: Request, path: str):    
    try:
        # Check for server parameter in query params
        server_param = request.query_params.get("server")
        
        # Build the full URL for the backend using consistent hashing
        backend_url = load_balancer.get_backend_url(path, server_param)
        target_url = f"{backend_url}/{path}"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"No servers available: {str(e)}")
    
    # Extract server name for response headers
    server_name = backend_url.replace("http://", "")

    # Get all the request details
    method = request.method
    headers = dict(request.headers)
    headers.pop("host", None)
    params = dict(request.query_params)
    
    # Get request body for POST/PUT requests
    body = None
    if method in ["POST", "PUT"]:
        body = await request.body()
    
    try:
        # Make the request to the backend server
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=method,
                url=target_url,
                headers=headers,
                params=params,
                content=body
            )
            
            # Forward the response back to the client with server info
            response_headers = dict(response.headers)
            response_headers["X-Server-Used"] = server_name
            
            # Remove Content-Length header to let FastAPI calculate it
            response_headers.pop("content-length", None)
            
            if response.headers.get("content-type", "").startswith("application/json"):
                json_content = response.json()
                # Add server info to JSON response
                if isinstance(json_content, dict):
                    json_content["server_used"] = server_name
                
                return JSONResponse(
                    content=json_content,
                    status_code=response.status_code,
                    headers=response_headers
                )
            else:
                return JSONResponse(
                    content=response.text,
                    status_code=response.status_code,
                    headers=response_headers
                )
            
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503, 
            detail="Backend service is unavailable"
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504, 
            detail="Backend service timed out"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Gateway error: {str(e)}"
        )

def main():
    print("🚀 Starting API Gateway...")
    print(f"📍 Gateway URL: http://localhost:8000")
    print(f"🔗 Backend Servers: {BACKEND_SERVERS}")
    print("⏹️  Press Ctrl+C to stop")
    
    #Host is 0.0.0.0 to allow external access
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()
