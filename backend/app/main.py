"""UMATANI API — main entrypoint."""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import get_settings
from app.core.limiter import limiter
from app.modules.admin.routes import router as admin_router
from app.modules.auth.routes import router as auth_router
from app.modules.businesses.routes import admin_router as businesses_admin_router
from app.modules.businesses.routes import router as businesses_router
from app.modules.categories.routes import admin_router as categories_admin_router
from app.modules.categories.routes import router as categories_router
from app.modules.media.routes import admin_router as media_admin_router
from app.modules.media.routes import router as media_router
from app.modules.reviews.routes import admin_router as reviews_admin_router
from app.modules.reviews.routes import router as reviews_router
from app.modules.schools.routes import admin_router as schools_admin_router
from app.modules.schools.routes import router as schools_router
from app.modules.support.routes import admin_router as support_admin_router
from app.modules.support.routes import router as support_router

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description="Student talent and business discovery platform",
    debug=settings.DEBUG,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url=None,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected error occurred. Please try again later."},
    )


@app.get("/health", tags=["meta"])
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.APP_NAME, "version": "1.0.0"}


prefix = settings.API_V1_PREFIX
app.include_router(auth_router, prefix=prefix)
app.include_router(schools_router, prefix=prefix)
app.include_router(schools_admin_router, prefix=prefix)
app.include_router(categories_router, prefix=prefix)
app.include_router(categories_admin_router, prefix=prefix)
app.include_router(businesses_router, prefix=prefix)
app.include_router(businesses_admin_router, prefix=prefix)
app.include_router(reviews_router, prefix=prefix)
app.include_router(reviews_admin_router, prefix=prefix)
app.include_router(media_router, prefix=prefix)
app.include_router(media_admin_router, prefix=prefix)
app.include_router(support_router, prefix=prefix)
app.include_router(support_admin_router, prefix=prefix)
app.include_router(admin_router, prefix=prefix)
