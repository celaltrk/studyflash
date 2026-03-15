"""
User profile management endpoints.

Provides CRUD for user profiles with role-based auto-assignment support.
Admin users can create/update/deactivate other users.
Any authenticated user can view profiles and update their own.
"""

from fastapi import APIRouter, HTTPException, Header
import services.db_service as db
from schemas import UserProfileOut, UserProfileCreate, UserProfileUpdate

router = APIRouter(prefix="/api/users", tags=["users"])


async def _get_caller(authorization: str) -> dict:
    """Extract the calling user from the JWT token."""
    token = authorization.replace("Bearer ", "")
    try:
        user_response = db.get_auth_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = user_response.user
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


def _build_profile_response(profile: dict, email: str, open_count: int = 0) -> dict:
    """Build a UserProfileOut-compatible dict from a profile row."""
    return {
        "id": profile["id"],
        "email": email,
        "display_name": profile.get("display_name", ""),
        "role": profile.get("role", "support"),
        "department": profile.get("department"),
        "phone": profile.get("phone"),
        "avatar_url": profile.get("avatar_url"),
        "bio": profile.get("bio"),
        "is_active": profile.get("is_active", True),
        "max_open_tickets": profile.get("max_open_tickets", 20),
        "open_ticket_count": open_count,
        "created_at": profile.get("created_at"),
        "updated_at": profile.get("updated_at"),
    }


@router.get("", response_model=list[UserProfileOut])
async def list_users(role: str | None = None, active_only: bool = True):
    """List all user profiles, optionally filtered by role."""
    try:
        result = db.list_user_profiles(role=role, active_only=active_only)
        profiles = result.data or []
    except Exception:
        profiles = []

    # Get emails from auth (optional — may fail if service key is anon key)
    email_map: dict[str, str] = {}
    try:
        users_resp = db.list_admin_users()
        email_map = {u.id: u.email for u in users_resp}
    except Exception as e:
        print(f"Warning: could not fetch auth users for emails: {e}")

    # Get open ticket counts per assignee
    ticket_counts: dict[str, int] = {}
    if profiles:
        for p in profiles:
            uid = p["id"]
            count_r = db.count_tickets(status=["open", "in_progress"], assignee_id=uid)
            ticket_counts[uid] = count_r.count or 0

    return [
        _build_profile_response(p, email_map.get(p["id"], ""), ticket_counts.get(p["id"], 0))
        for p in profiles
    ]


@router.get("/me", response_model=UserProfileOut)
async def get_my_profile(authorization: str = Header()):
    """Get the current user's profile."""
    caller = await _get_caller(authorization)
    try:
        result = db.get_user_profile(caller.id)
    except Exception:
        raise HTTPException(status_code=404, detail="Profile not found. The user_profiles table may not exist — run migration 003.")

    if not result or not result.data:
        raise HTTPException(status_code=404, detail="Profile not found. It may not have been created yet.")

    count_r = db.count_tickets(status=["open", "in_progress"], assignee_id=caller.id)

    return _build_profile_response(result.data, caller.email, count_r.count or 0)


@router.get("/{user_id}", response_model=UserProfileOut)
async def get_user(user_id: str):
    """Get a specific user's profile."""
    try:
        result = db.get_user_profile(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="User not found. The user_profiles table may not exist.")

    if not result or not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Get email from auth
    try:
        u_resp = db.get_user_by_id(user_id)
        email = u_resp.user.email
    except Exception:
        email = ""

    count_r = db.count_tickets(status=["open", "in_progress"], assignee_id=user_id)

    return _build_profile_response(result.data, email, count_r.count or 0)


@router.post("", response_model=UserProfileOut, status_code=201)
async def create_user(data: UserProfileCreate, authorization: str = Header()):
    """Create a new user (admin only). Creates both auth account and profile."""
    caller = await _get_caller(authorization)
    # Check caller is admin
    try:
        caller_profile = db.get_user_profile(caller.id, select="role")
    except Exception:
        caller_profile = None
    if not caller_profile or not caller_profile.data or caller_profile.data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Only admins can create users")

    # Create Supabase Auth user
    try:
        auth_user = db.create_admin_user(
            email=data.email,
            password=data.password,
            display_name=data.display_name,
            role=data.role.value if hasattr(data.role, "value") else data.role
        )
        user_id = auth_user.user.id
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create auth user: {e}")

    # Create profile
    profile_data = {
        "id": user_id,
        "display_name": data.display_name,
        "role": data.role.value if hasattr(data.role, "value") else data.role,
        "department": data.department,
        "phone": data.phone,
        "bio": data.bio,
        "max_open_tickets": data.max_open_tickets,
    }
    db.insert_user_profile(profile_data)

    return _build_profile_response(
        {**profile_data, "is_active": True, "avatar_url": None},
        data.email,
        0,
    )


@router.patch("/{user_id}", response_model=UserProfileOut)
async def update_user(user_id: str, data: UserProfileUpdate, authorization: str = Header()):
    """Update a user profile. Users can update themselves; admins can update anyone."""
    caller = await _get_caller(authorization)
    # Check permissions: self-update or admin
    is_self = caller.id == user_id
    try:
        caller_profile = db.get_user_profile(caller.id, select="role")
    except Exception:
        caller_profile = None
    is_admin = caller_profile and caller_profile.data and caller_profile.data["role"] == "admin"

    if not is_self and not is_admin:
        raise HTTPException(status_code=403, detail="You can only update your own profile or be an admin")

    # Non-admins cannot change their own role or active status
    update_data = data.model_dump(exclude_unset=True)
    if not is_admin:
        update_data.pop("role", None)
        update_data.pop("is_active", None)
        update_data.pop("max_open_tickets", None)

    # Convert enums
    for key, value in update_data.items():
        if hasattr(value, "value"):
            update_data[key] = value.value

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = db.update_user_profile(user_id, update_data)
    if not result.data:
        raise HTTPException(status_code=404, detail="User not found")

    # Sync display_name and role to auth user_metadata if changed
    sync_meta = {}
    if "display_name" in update_data:
        sync_meta["name"] = update_data["display_name"]
    if "role" in update_data:
        sync_meta["role"] = update_data["role"]
    if sync_meta:
        try:
            db.update_admin_user_metadata(user_id, sync_meta)
        except Exception as e:
            print(f"Warning: failed to sync user_metadata: {e}")

    return await get_user(user_id)


@router.post("/sync", response_model=dict)
async def sync_profiles(authorization: str = Header()):
    """Sync user_profiles from existing Supabase Auth users. Creates missing profiles."""
    users_resp = db.list_admin_users()
    created = 0
    for u in users_resp:
        meta = u.user_metadata or {}
        role = meta.get("role", "support")
        if role not in ("admin", "support", "billing", "engineering"):
            role = "support"
        try:
            db.upsert_user_profile({
                "id": u.id,
                "display_name": meta.get("name", ""),
                "role": role,
            })
            created += 1
        except Exception as e:
            print(f"Sync failed for {u.email}: {e}")

    return {"synced": created, "total_auth_users": len(users_resp)}


@router.post("/auto-assign", response_model=dict)
async def auto_assign_ticket(ticket_id: int, authorization: str = Header()):
    """
    Auto-assign a ticket to the best-fit user based on category-to-role mapping.
    Uses least-loaded strategy: picks the active user with the fewest open tickets.
    """
    # Get the ticket
    ticket_r = db.get_ticket(ticket_id, select="id, ai_category, category, assignee_id")
    if not ticket_r.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_r.data
    category = ticket.get("category") or ticket.get("ai_category")

    if not category:
        raise HTTPException(status_code=400, detail="Ticket has no category — categorize it first")

    # Determine target role from category
    from services.ai_service import ASSIGNMENT_RULES
    target_role = ASSIGNMENT_RULES.get(category, "support")

    # Find active users with this role
    users_r = db.list_user_profiles(role=target_role, active_only=True, select="id, display_name, max_open_tickets")
    candidates = users_r.data or []

    if not candidates:
        return {"assigned": False, "message": f"No active {target_role} users available"}

    # Count open tickets per candidate and pick least loaded
    best_user = None
    best_count = float("inf")

    for c in candidates:
        count_r = db.count_tickets(status=["open", "in_progress"], assignee_id=c["id"])
        open_count = count_r.count or 0

        # Skip if at capacity
        if open_count >= c.get("max_open_tickets", 20):
            continue

        if open_count < best_count:
            best_count = open_count
            best_user = c

    if not best_user:
        return {"assigned": False, "message": f"All {target_role} users are at capacity"}

    # Assign the ticket
    db.update_ticket(ticket_id, {"assignee_id": best_user["id"]})

    return {
        "assigned": True,
        "assignee_id": best_user["id"],
        "assignee_name": best_user["display_name"],
        "role": target_role,
        "open_tickets": best_count + 1,
    }
