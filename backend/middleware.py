"""
Middleware for F1 Undercut Simulation backend.

This module provides middleware for request ID generation, request logging,
and other cross-cutting concerns.
"""

import time
import uuid
import hashlib
import json
from typing import Callable, Dict, Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog
from starlette.middleware.base import BaseHTTPMiddleware


class RequestMiddleware(BaseHTTPMiddleware):
    """Middleware for request ID generation and logging."""
    
    def __init__(self, app, logger=None):
        super().__init__(app)
        self.logger = logger or structlog.get_logger(__name__)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with ID generation and logging."""
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add request ID to structlog context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        
        # Add request ID to request state for access in endpoints
        request.state.request_id = request_id
        
        # Record start time
        start_time = time.time()
        
        # Log incoming request
        await self._log_request_start(request, request_id)
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate duration
            duration = time.time() - start_time
            
            # Log successful response
            await self._log_request_end(request, response, request_id, duration)
            
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as exc:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Log exception
            self.logger.error(
                "Request failed",
                path=request.url.path,
                method=request.method,
                duration_ms=round(duration * 1000, 2),
                error=str(exc),
                error_type=type(exc).__name__
            )
            
            # Return error response with request ID
            return JSONResponse(
                status_code=500,
                content={
                    "detail": "Internal server error",
                    "request_id": request_id
                },
                headers={"X-Request-ID": request_id}
            )
    
    async def _log_request_start(self, request: Request, request_id: str) -> None:
        """Log request start."""
        self.logger.info(
            "Request started",
            method=request.method,
            path=request.url.path,
            query_params=dict(request.query_params),
            user_agent=request.headers.get("user-agent"),
            client_ip=self._get_client_ip(request)
        )
    
    async def _log_request_end(self, request: Request, response: Response, 
                              request_id: str, duration: float) -> None:
        """Log request completion."""
        # For /simulate endpoint, log additional details
        log_data = {
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": round(duration * 1000, 2),
        }
        
        # Add simulation-specific logging for /simulate endpoint
        if request.url.path == "/simulate" and request.method == "POST":
            try:
                # Get request body for hashing (don't log PII)
                body = await self._get_request_body_hash(request)
                log_data["request_body_hash"] = body
                
                # Get response size
                if hasattr(response, "body"):
                    log_data["response_size_bytes"] = len(response.body)
                    
            except Exception as e:
                self.logger.warning("Failed to extract simulation details", error=str(e))
        
        self.logger.info("Request completed", **log_data)
    
    async def _get_request_body_hash(self, request: Request) -> str:
        """Get SHA256 hash of request body for privacy-safe logging."""
        try:
            # This is tricky because the body may have been consumed
            # We'll use the request state if available
            if hasattr(request.state, 'body_hash'):
                return request.state.body_hash
            
            # For logging purposes, create a simple hash of the URL params
            query_str = str(request.query_params)
            return hashlib.sha256(query_str.encode()).hexdigest()[:16]
        except Exception:
            return "unknown"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check for forwarded headers first (for reverse proxies)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded = request.headers.get("x-forwarded")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client
        if request.client:
            return request.client.host
        
        return "unknown"


def hash_simulation_inputs(data: Dict[str, Any]) -> str:
    """Create privacy-safe hash of simulation inputs."""
    # Extract only non-PII fields for hashing
    safe_fields = {
        "gp": data.get("gp"),
        "year": data.get("year"), 
        "compound_a": data.get("compound_a"),
        "lap_now": data.get("lap_now"),
        "samples": data.get("samples")
    }
    
    # Create deterministic hash
    content = json.dumps(safe_fields, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def round_simulation_outputs(data: Dict[str, Any]) -> Dict[str, Any]:
    """Round simulation outputs for consistent logging."""
    rounded = data.copy()
    
    # Round numerical outputs to reasonable precision
    if "p_undercut" in rounded:
        rounded["p_undercut"] = round(rounded["p_undercut"], 4)
    if "pitLoss_s" in rounded:
        rounded["pitLoss_s"] = round(rounded["pitLoss_s"], 2)
    if "outLapDelta_s" in rounded:
        rounded["outLapDelta_s"] = round(rounded["outLapDelta_s"], 2)
    
    # Round assumption values
    if "assumptions" in rounded and isinstance(rounded["assumptions"], dict):
        assumptions = rounded["assumptions"]
        for key, value in assumptions.items():
            if isinstance(value, float):
                assumptions[key] = round(value, 3)
            elif isinstance(value, list) and len(value) > 0 and isinstance(value[0], float):
                assumptions[key] = [round(v, 3) for v in value]
    
    return rounded