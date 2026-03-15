from fastapi import APIRouter
import services.db_service as db
from schemas import TeamMemberOut

router = APIRouter(prefix="/api/team", tags=["team"])


@router.get("", response_model=list[TeamMemberOut])
async def list_team_members():
    # Get users from user_profiles table (reliable, no admin API needed)
    profiles_r = db.list_user_profiles(active_only=True)
    profiles = profiles_r.data or []

    # Try to get emails from auth admin API (optional)
    email_map: dict[str, str] = {}
    try:
        users_resp = db.list_admin_users()
        email_map = {u.id: u.email for u in users_resp}
    except Exception as e:
        print(f"Warning: could not fetch auth users for emails: {e}")

    result = []
    for p in profiles:
        result.append({
            "id": p["id"],
            "name": p.get("display_name", ""),
            "email": email_map.get(p["id"], ""),
            "role": p.get("role", "support"),
            "is_active": p.get("is_active", True),
        })

    return sorted(result, key=lambda x: x["name"])

