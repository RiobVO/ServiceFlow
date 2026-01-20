from fastapi import APIRouter

from app.core.health import check_database

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    db_ok = check_database()

    if db_ok:
        return {"status": "ok", "database": "ok", "details": None}

    return {"status": "degraded", "database": "unavailable", "details": None}
