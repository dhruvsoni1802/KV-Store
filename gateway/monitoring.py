#!/usr/bin/env python3

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class ServerMetrics:
    server_name: str
    request_count: int
    avg_latency_ms: float
    cpu_usage_percent: float
    memory_usage_percent: float


# Simple storage for metrics
server_metrics: List[ServerMetrics] = []


def update_metrics(metrics: List[ServerMetrics]):
    global server_metrics
    server_metrics = metrics


def get_insights() -> Dict[str, Any]:
    if not server_metrics:
        return {"error": "No metrics data available"}
    
    # Simple analysis
    total_requests = sum(m.request_count for m in server_metrics)
    avg_latency = sum(m.avg_latency_ms for m in server_metrics) / len(server_metrics)
    
    # Find problems
    hot_spots = []
    slow_servers = []
    
    for metric in server_metrics:
        # Hot spot: more than 50% of average requests
        if metric.request_count > (total_requests / len(server_metrics)) * 1.5:
            hot_spots.append(metric.server_name)
        
        # Slow server: more than 50% higher latency than average
        if metric.avg_latency_ms > avg_latency * 1.5:
            slow_servers.append(metric.server_name)
    
    return {
        "total_requests": total_requests,
        "avg_latency_ms": round(avg_latency, 2),
        "hot_spots": hot_spots,
        "slow_servers": slow_servers,
        "servers": {m.server_name: {
            "requests": m.request_count,
            "latency_ms": m.avg_latency_ms,
            "cpu_percent": m.cpu_usage_percent,
            "memory_percent": m.memory_usage_percent
        } for m in server_metrics}
    }