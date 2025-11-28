"""
API Gateway - Central routing and authentication
Routes requests to microservices and validates authentication via Security Service
"""
from fastapi import FastAPI, Request, HTTPException, status, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
import httpx
from typing import Optional
from datetime import datetime
import uvicorn
import os
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Rate limiting setup
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Request duration')

app = FastAPI(
    title="Clinical Trials Platform API Gateway",
    description="Central gateway for all microservices with authentication",
    version="1.0.0"
)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS configuration - use environment variable for allowed origins
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "*"  # Default to wildcard for development
).split(",") if os.getenv("ALLOWED_ORIGINS") else ["*"]

# Warn if using wildcard in production
if "*" in ALLOWED_ORIGINS and os.getenv("ENVIRONMENT") == "production":
    import warnings
    warnings.warn(
        "WARNING: CORS wildcard (*) enabled in API Gateway in production. "
        "Set ALLOWED_ORIGINS environment variable.",
        UserWarning
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Service Registry - Environment variables with defaults
SERVICES = {
    "security": os.getenv("SECURITY_SERVICE_URL", "http://localhost:8005"),
    "edc": os.getenv("EDC_SERVICE_URL", "http://localhost:8001"),
    "generation": os.getenv("GENERATION_SERVICE_URL", "http://localhost:8002"),
    "analytics": os.getenv("ANALYTICS_SERVICE_URL", "http://localhost:8003"),
    "quality": os.getenv("QUALITY_SERVICE_URL", "http://localhost:8004"),
    "daft": os.getenv("DAFT_SERVICE_URL", "http://localhost:8007"),
    "linkup": os.getenv("LINKUP_SERVICE_URL", "http://localhost:8008"),
    "gain": os.getenv("GAIN_SERVICE_URL", "http://localhost:8009"),
    "gan": os.getenv("GAN_SERVICE_URL", "http://localhost:8010"),
    "ai_monitor": os.getenv("AI_MONITOR_SERVICE_URL", "http://localhost:8011"),
}

# Public endpoints that don't require authentication
PUBLIC_ENDPOINTS = {
    "/",
    "/health",
    "/metrics",
    "/docs",
    "/openapi.json",
    "/security/auth/login",
}


async def verify_token(authorization: Optional[str] = Header(None)) -> dict:
    """
    Verify JWT token with Security Service

    Args:
        authorization: Bearer token from header

    Returns:
        User payload if valid

    Raises:
        HTTPException if token is invalid
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authorization header"
        )

    token = authorization.replace("Bearer ", "")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{SERVICES['security']}/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
                timeout=5.0
            )

            if response.status_code == 200:
                data = response.json()
                if data.get("valid"):
                    return data

            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Security service unavailable"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@app.get("/")
async def root():
    """Gateway information and service map"""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "security": "/security/*",
            "edc": "/edc/*",
            "generation": "/generation/*",
            "analytics": "/analytics/*",
            "quality": "/quality/*",
            "daft": "/daft/* (Distributed Analytics - Port 8007)",
            "linkup": "/linkup/* (Regulatory Intelligence - Port 8008)",
            "gain": "/gain/* (Missing Data Imputation - Port 8009)",
            "gan": "/gan/* (GAN Synthetic Data - Port 8010)",
        },
        "authentication": "Bearer token required (except /security/auth/login)",
        "docs": "/docs",
        "new_services": {
            "daft": "High-performance distributed analytics using Daft library",
            "linkup": "AI-powered regulatory intelligence and evidence generation",
            "gain": "GAN-based missing data imputation using CTGAN",
            "gan": "Conditional synthetic data generation using CTGAN"
        }
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health_check():
    """Health check for gateway and all services"""
    health_status = {
        "gateway": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }

    async with httpx.AsyncClient(timeout=3.0) as client:
        for service_name, service_url in SERVICES.items():
            try:
                response = await client.get(f"{service_url}/health")
                health_status["services"][service_name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "url": service_url
                }
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unreachable",
                    "error": str(e),
                    "url": service_url
                }

    # Overall health is healthy only if all services are healthy
    all_healthy = all(
        s.get("status") == "healthy"
        for s in health_status["services"].values()
    )
    health_status["gateway"] = "healthy" if all_healthy else "degraded"

    return health_status


@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_route(service: str, path: str, request: Request):
    """
    Route requests to appropriate microservice

    Authentication is checked for all non-public endpoints
    """
    # Check if service exists
    if service not in SERVICES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Service '{service}' not found"
        )

    # Build full path
    full_path = f"/{service}/{path}"

    # Check if authentication is required
    requires_auth = full_path not in PUBLIC_ENDPOINTS and not full_path.startswith("/security/auth/login")

    if requires_auth:
        # Verify token with Security Service
        auth_header = request.headers.get("authorization")
        try:
            await verify_token(auth_header)
        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={"detail": e.detail}
            )

    # Forward request to microservice
    service_url = SERVICES[service]
    target_url = f"{service_url}/{path}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Forward the request
            response = await client.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers.items() if k.lower() != "host"},
                content=await request.body(),
                params=request.query_params
            )

            # Return the response
            return JSONResponse(
                status_code=response.status_code,
                content=response.json() if response.headers.get("content-type", "").startswith("application/json") else {"data": response.text},
                headers=dict(response.headers)
            )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Service '{service}' timeout"
        )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Service '{service}' unavailable"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gateway error: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
