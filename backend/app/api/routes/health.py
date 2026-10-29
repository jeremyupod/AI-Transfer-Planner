from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/")
def root() -> dict[str, str]:
    """Return a simple message confirming that the API is running."""
    return {"message": "AI Transfer Planner API is running"}


@router.get("/health")
def health_check() -> dict[str, str]:
    """Return the current basic health status of the API."""
    return {"status": "healthy"}
