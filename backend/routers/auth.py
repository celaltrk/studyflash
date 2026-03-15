"""
Authentication endpoints using Supabase Auth.

Team members sign in with email/password. The frontend stores the JWT
and sends it as a Bearer token. The backend verifies it via Supabase.
"""

from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
import services.db_service as db

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    name: str
    role: str
    department: str | None = None
    is_admin: bool = False


class CurrentUser(BaseModel):
    id: str
    email: str
    name: str
    role: str
    team_member_id: str
    department: str | None = None
    is_admin: bool = False


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """Sign in with email/password via Supabase Auth."""
    try:
        auth_response = db.sign_in_with_password(req.email, req.password)
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid credentials: {e}")

    user = auth_response.user
    session = auth_response.session

    if not user or not session:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    meta = user.user_metadata or {}

    # Try to get profile data
    profile_role = meta.get("role") or "support"
    department = None
    try:
        profile_r = db.get_user_profile(user.id, select="role, department")
        if profile_r and profile_r.data:
            profile_role = profile_r.data.get("role", profile_role)
            department = profile_r.data.get("department")
    except Exception:
        pass

    return AuthResponse(
        access_token=session.access_token,
        user_id=user.id,
        email=user.email,
        name=meta.get("name") or "",
        role=profile_role,
        department=department,
        is_admin=profile_role == "admin",
    )


@router.get("/me", response_model=CurrentUser)
async def get_current_user(authorization: str = Header()):
    """Get current user from JWT token."""
    token = authorization.replace("Bearer ", "")

    try:
        user_response = db.get_auth_user(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user = user_response.user
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")

    meta = user.user_metadata or {}

    profile_role = meta.get("role") or "support"
    department = None
    try:
        profile_r = db.get_user_profile(user.id, select="role, department")
        if profile_r and profile_r.data:
            profile_role = profile_r.data.get("role", profile_role)
            department = profile_r.data.get("department")
    except Exception:
        pass

    return CurrentUser(
        id=user.id,
        email=user.email,
        name=meta.get("name") or "",
        role=profile_role,
        team_member_id=user.id,
        department=department,
        is_admin=profile_role == "admin",
    )
