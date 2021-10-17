from fastapi import APIRouter


router = APIRouter(
    prefix="/public",
    tags=["public"],
)

@router.get("/", tags=["public"])
async def public_root():
    return {
        "message": "Welcome to a Skeleton-FastAPI-Application. Composed by oryon-dominik with 💖",
    }
