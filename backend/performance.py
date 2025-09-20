"""
Performance monitoring and caching for F1 Undercut Simulation backend.

This module provides LRU caching for simulation results, latency tracking,
and performance metrics collection.
"""

import time
import hashlib
import json
from typing import Dict, Any, Optional, List
from cachetools import LRUCache
import structlog
from dataclasses import dataclass
from collections import deque
import threading

logger = structlog.get_logger(__name__)


@dataclass
class LatencyMetrics:
    """Container for latency tracking metrics."""
    request_times: deque
    lock: threading.Lock
    
    def __init__(self, max_samples: int = 1000):
        self.request_times = deque(maxlen=max_samples)
        self.lock = threading.Lock()
    
    def add_request_time(self, duration_ms: float) -> None:
        """Add a request duration to the metrics."""
        with self.lock:
            self.request_times.append(duration_ms)
    
    def get_percentile(self, percentile: float) -> Optional[float]:
        """Get the specified percentile of request times."""
        with self.lock:
            if not self.request_times:
                return None
            
            sorted_times = sorted(self.request_times)
            index = int(len(sorted_times) * percentile / 100)
            return sorted_times[min(index, len(sorted_times) - 1)]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive latency statistics."""
        with self.lock:
            if not self.request_times:
                return {"count": 0}
            
            sorted_times = sorted(self.request_times)
            count = len(sorted_times)
            
            return {
                "count": count,
                "min_ms": sorted_times[0],
                "max_ms": sorted_times[-1],
                "avg_ms": sum(sorted_times) / count,
                "p50_ms": sorted_times[int(count * 0.5)],
                "p90_ms": sorted_times[int(count * 0.9)],
                "p95_ms": sorted_times[int(count * 0.95)],
                "p99_ms": sorted_times[int(count * 0.99)],
            }


class SimulationCache:
    """LRU cache for simulation results with performance tracking."""
    
    def __init__(self, max_size: int = 1000):
        self.cache = LRUCache(maxsize=max_size)
        self.metrics = LatencyMetrics()
        self.hit_count = 0
        self.miss_count = 0
        self.lock = threading.Lock()
    
    def _create_cache_key(
        self, 
        gp: str, 
        year: int, 
        driver_a: str, 
        driver_b: str, 
        compound_a: str, 
        lap_now: int, 
        samples: int, 
        gap_rounded: float
    ) -> str:
        """Create a cache key from simulation parameters."""
        # Round gap to 0.1s precision for cache efficiency
        gap_key = round(gap_rounded, 1)
        
        cache_data = {
            "gp": gp.lower(),
            "year": year,
            "driver_a": driver_a,
            "driver_b": driver_b,
            "compound_a": compound_a.upper(),
            "lap_now": lap_now,
            "samples": samples,
            "gap": gap_key
        }
        
        # Create deterministic hash
        cache_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_str.encode()).hexdigest()[:16]
    
    def get(
        self, 
        gp: str, 
        year: int, 
        driver_a: str, 
        driver_b: str, 
        compound_a: str, 
        lap_now: int, 
        samples: int, 
        gap_rounded: float
    ) -> Optional[Dict[str, Any]]:
        """Get cached simulation result if available."""
        cache_key = self._create_cache_key(
            gp, year, driver_a, driver_b, compound_a, lap_now, samples, gap_rounded
        )
        
        with self.lock:
            result = self.cache.get(cache_key)
            if result is not None:
                self.hit_count += 1
                logger.debug("Cache hit", cache_key=cache_key[:8])
                return result
            else:
                self.miss_count += 1
                logger.debug("Cache miss", cache_key=cache_key[:8])
                return None
    
    def set(
        self, 
        gp: str, 
        year: int, 
        driver_a: str, 
        driver_b: str, 
        compound_a: str, 
        lap_now: int, 
        samples: int, 
        gap_rounded: float,
        result: Dict[str, Any]
    ) -> None:
        """Store simulation result in cache."""
        cache_key = self._create_cache_key(
            gp, year, driver_a, driver_b, compound_a, lap_now, samples, gap_rounded
        )
        
        with self.lock:
            self.cache[cache_key] = result
            logger.debug("Cache set", cache_key=cache_key[:8])
    
    def add_request_time(self, duration_ms: float) -> None:
        """Add request timing to performance metrics."""
        self.metrics.add_request_time(duration_ms)
        
        # Log p95 latency periodically
        if self.get_total_requests() % 10 == 0:
            p95 = self.metrics.get_percentile(95)
            if p95:
                logger.info("Performance metrics", **self.get_performance_stats())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = (self.hit_count / total_requests * 100) if total_requests > 0 else 0
            
            return {
                "cache_size": len(self.cache),
                "max_cache_size": self.cache.maxsize,
                "cache_hits": self.hit_count,
                "cache_misses": self.miss_count,
                "hit_rate_percent": round(hit_rate, 2),
                "total_requests": total_requests
            }
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = self.get_cache_stats()
        latency_stats = self.metrics.get_stats()
        
        return {
            **cache_stats,
            **latency_stats
        }
    
    def get_total_requests(self) -> int:
        """Get total number of requests processed."""
        with self.lock:
            return self.hit_count + self.miss_count
    
    def clear(self) -> None:
        """Clear the cache and reset metrics."""
        with self.lock:
            self.cache.clear()
            self.hit_count = 0
            self.miss_count = 0
    
    def __contains__(self, key: str) -> bool:
        """Check if a key exists in the cache (enables 'in' operator)."""
        with self.lock:
            return key in self.cache
    
    def __getitem__(self, key: str) -> Dict[str, Any]:
        """Get item from cache (enables cache[key] syntax)."""
        with self.lock:
            result = self.cache.get(key)
            if result is None:
                raise KeyError(f"Cache key not found: {key}")
            return result
    
    def __setitem__(self, key: str, value: Dict[str, Any]) -> None:
        """Set item in cache (enables cache[key] = value syntax)."""
        with self.lock:
            self.cache[key] = value


# Global cache instance
simulation_cache = SimulationCache(max_size=1000)


def get_simulation_cache() -> SimulationCache:
    """Get the global simulation cache instance."""
    return simulation_cache