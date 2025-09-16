#!/usr/bin/env python3

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import uvicorn
import os
import time
from load_balancer import LoadBalancer
from monitoring import get_insights, update_metrics, ServerMetrics

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

@app.get("/insights")
async def get_load_balancer_insights():
    # Get metrics from load balancer
    lb_metrics = load_balancer.get_server_metrics()
    
    # Create simple metrics for each server
    server_metrics_list = []
    for server in BACKEND_SERVERS:
        lb_data = lb_metrics.get(server, {"request_count": 0, "avg_latency_ms": 0})
        
        # Simple mock CPU/memory data
        cpu_percent = 50.0
        memory_percent = 60.0
        
        server_metrics = ServerMetrics(
            server_name=server,
            request_count=lb_data["request_count"],
            avg_latency_ms=lb_data["avg_latency_ms"],
            cpu_usage_percent=cpu_percent,
            memory_usage_percent=memory_percent
        )
        server_metrics_list.append(server_metrics)
    
    # Update and return insights
    update_metrics(server_metrics_list)
    return get_insights()

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(request: Request, path: str):    
    start_time = time.time()
    
    try:
        # Get server from load balancer
        server_param = request.query_params.get("server")
        backend_url = load_balancer.get_backend_url(path, server_param)
        target_url = f"{backend_url}/{path}"
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"No servers available: {str(e)}")
    
    server_name = backend_url.replace("http://", "")

    # Make request to backend
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=dict(request.headers),
                params=dict(request.query_params),
                content=await request.body() if request.method in ["POST", "PUT"] else None
            )
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            load_balancer.record_request(server_name, latency_ms)
            
            # Return response with server info
            response_headers = dict(response.headers)
            response_headers["X-Server-Used"] = server_name
            
            # Remove Content-Length header to let FastAPI calculate it
            response_headers.pop("content-length", None)
            
            if response.headers.get("content-type", "").startswith("application/json"):
                json_content = response.json()
                if isinstance(json_content, dict):
                    json_content["server_used"] = server_name
                return JSONResponse(content=json_content, status_code=response.status_code, headers=response_headers)
            else:
                return JSONResponse(content=response.text, status_code=response.status_code, headers=response_headers)
            
    except Exception as e:
        # Record failed request
        latency_ms = (time.time() - start_time) * 1000
        load_balancer.record_request(server_name, latency_ms)
        raise HTTPException(status_code=500, detail=f"Gateway error: {str(e)}")

def main():
    print("🚀 Starting API Gateway...")
    print(f"📍 Gateway URL: http://localhost:8000")
    print(f"🔗 Backend Servers: {BACKEND_SERVERS}")
    print("⏹️  Press Ctrl+C to stop")
    
    #Host is 0.0.0.0 to allow external access
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()
