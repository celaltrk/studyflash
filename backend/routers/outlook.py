from fastapi import APIRouter

from services.email_sync_service import sync_inbound_emails

router = APIRouter(prefix="/api/outlook", tags=["outlook"])


@router.post("/sync")
async def trigger_sync():
    """Manually trigger an inbound email sync (useful for testing/debugging)."""
    try:
        await sync_inbound_emails()
        return {"status": "ok", "message": "Sync completed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
