"""Metrics collection and tracking for API monitoring"""

import time
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from threading import Lock
import statistics


@dataclass
class RequestMetrics:
    """Metrics for a single request"""
    timestamp: float
    endpoint: str
    method: str
    status_code: int
    latency_ms: float
    error: Optional[str] = None


class MetricsCollector:
    """
    Collects and tracks API metrics including request counts, 
    error rates, and latency percentiles.
    """
    
    def __init__(self):
        """Initialize metrics collector"""
        self._lock = Lock()
        self._requests: List[RequestMetrics] = []
        self._request_counts: Dict[str, int] = {}
        self._error_counts: Dict[str, int] = {}
        self._latencies: Dict[str, List[float]] = {}
        
    def record_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        latency_ms: float,
        error: Optional[str] = None
    ) -> None:
        """
        Record a request with its metrics.
        
        Args:
            endpoint: The API endpoint path
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP response status code
            latency_ms: Request latency in milliseconds
            error: Optional error message if request failed
        """
        with self._lock:
            # Create metrics record
            metrics = RequestMetrics(
                timestamp=time.time(),
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                latency_ms=latency_ms,
                error=error
            )
            
            # Store the request
            self._requests.append(metrics)
            
            # Update request counts
            key = f"{method} {endpoint}"
            self._request_counts[key] = self._request_counts.get(key, 0) + 1
            
            # Update error counts if this was an error
            if status_code >= 400:
                self._error_counts[key] = self._error_counts.get(key, 0) + 1
            
            # Track latency
            if key not in self._latencies:
                self._latencies[key] = []
            self._latencies[key].append(latency_ms)
    
    def get_metrics(self) -> Dict:
        """
        Get current metrics summary.
        
        Returns:
            Dictionary containing request counts, error rates, and latency percentiles
        """
        with self._lock:
            total_requests = len(self._requests)
            total_errors = sum(1 for r in self._requests if r.status_code >= 400)
            
            # Calculate error rate
            error_rate = (total_errors / total_requests * 100) if total_requests > 0 else 0.0
            
            # Calculate latency percentiles across all requests
            all_latencies = [r.latency_ms for r in self._requests]
            latency_percentiles = {}
            
            if all_latencies:
                sorted_latencies = sorted(all_latencies)
                latency_percentiles = {
                    "p50": self._percentile(sorted_latencies, 50),
                    "p90": self._percentile(sorted_latencies, 90),
                    "p95": self._percentile(sorted_latencies, 95),
                    "p99": self._percentile(sorted_latencies, 99),
                    "mean": statistics.mean(all_latencies),
                    "min": min(all_latencies),
                    "max": max(all_latencies)
                }
            
            # Build per-endpoint metrics
            endpoint_metrics = {}
            for key in self._request_counts.keys():
                request_count = self._request_counts[key]
                error_count = self._error_counts.get(key, 0)
                endpoint_error_rate = (error_count / request_count * 100) if request_count > 0 else 0.0
                
                # Calculate endpoint-specific latency percentiles
                endpoint_latencies = self._latencies.get(key, [])
                endpoint_latency = {}
                
                if endpoint_latencies:
                    sorted_endpoint_latencies = sorted(endpoint_latencies)
                    endpoint_latency = {
                        "p50": self._percentile(sorted_endpoint_latencies, 50),
                        "p90": self._percentile(sorted_endpoint_latencies, 90),
                        "p95": self._percentile(sorted_endpoint_latencies, 95),
                        "p99": self._percentile(sorted_endpoint_latencies, 99),
                        "mean": statistics.mean(endpoint_latencies)
                    }
                
                endpoint_metrics[key] = {
                    "request_count": request_count,
                    "error_count": error_count,
                    "error_rate": round(endpoint_error_rate, 2),
                    "latency": endpoint_latency
                }
            
            return {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": round(error_rate, 2),
                "latency_percentiles": latency_percentiles,
                "endpoints": endpoint_metrics,
                "timestamp": datetime.utcnow().isoformat()
            }
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """
        Calculate percentile from sorted data.
        
        Args:
            sorted_data: List of values sorted in ascending order
            percentile: Percentile to calculate (0-100)
            
        Returns:
            The value at the given percentile
        """
        if not sorted_data:
            return 0.0
        
        if len(sorted_data) == 1:
            return sorted_data[0]
        
        # Calculate index
        index = (percentile / 100) * (len(sorted_data) - 1)
        
        # If index is an integer, return that value
        if index.is_integer():
            return sorted_data[int(index)]
        
        # Otherwise, interpolate between two values
        lower_index = int(index)
        upper_index = lower_index + 1
        weight = index - lower_index
        
        return sorted_data[lower_index] * (1 - weight) + sorted_data[upper_index] * weight
    
    def reset(self) -> None:
        """Reset all metrics (useful for testing)"""
        with self._lock:
            self._requests.clear()
            self._request_counts.clear()
            self._error_counts.clear()
            self._latencies.clear()


# Global metrics collector instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get the global metrics collector instance"""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def reset_metrics_collector() -> None:
    """Reset the global metrics collector (useful for testing)"""
    global _metrics_collector
    if _metrics_collector is not None:
        _metrics_collector.reset()
    _metrics_collector = None
