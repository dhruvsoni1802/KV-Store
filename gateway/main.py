#!/usr/bin/env python3

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import httpx
import uvicorn

app = FastAPI(
    title="API Gateway",
    description="API Gateway that forwards requests to backend services",
    version="1.0.0"
)

# Configuration - where our backend server is running
BACKEND_URL = "http://server-1:8080"

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def forward_request(request: Request, path: str):    
    # Build the full URL for the backend
    target_url = f"{BACKEND_URL}/{path}"

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
            
            # Forward the response back to the client
            if response.headers.get("content-type", "").startswith("application/json"):
                return JSONResponse(
                    content=response.json(),
                    status_code=response.status_code
                )
            else:
                return JSONResponse(
                    content=response.text,
                    status_code=response.status_code
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
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print("⏹️  Press Ctrl+C to stop")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == '__main__':
    main()
