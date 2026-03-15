from datetime import datetime
from pydantic import BaseModel
from models import TicketStatus, TicketPriority, TicketCategory, UserRole


# --- User Profiles ---

class UserProfileOut(BaseModel):
    id: str
    email: str
    display_name: str
    role: str
    department: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool = True
    max_open_tickets: int = 20
    open_ticket_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserProfileCreate(BaseModel):
    email: str
    password: str
    display_name: str
    role: UserRole = UserRole.support
    department: str | None = None
    phone: str | None = None
    bio: str | None = None
    max_open_tickets: int = 20


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    role: UserRole | None = None
    department: str | None = None
    phone: str | None = None
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool | None = None
    max_open_tickets: int | None = None


# --- Team Members (backwards compat) ---

class TeamMemberOut(BaseModel):
    id: str
    name: str
    email: str
    role: str
    is_active: bool


# --- Messages ---

class MessageOut(BaseModel):
    id: int
    ticket_id: int
    sender_type: str
    sender_name: str
    sender_email: str
    body: str
    is_ai_draft: bool = False
    outlook_message_id: str | None = None
    created_at: datetime


class MessageCreate(BaseModel):
    body: str
    sender_type: str = "agent"
    sender_name: str = ""
    sender_email: str = ""


# --- Tickets ---

class TicketOut(BaseModel):
    id: int
    external_id: str | None = None
    outlook_conversation_id: str | None = None
    outlook_message_id: str | None = None
    subject: str
    body: str
    sender_email: str
    sender_name: str
    source: str
    status: str
    priority: str
    category: str | None = None
    tags: str
    language: str
    translated_body: str | None = None
    assignee_id: str | None = None
    assignee: TeamMemberOut | None = None
    ai_category: str | None = None
    ai_summary: str | None = None
    ai_draft_response: str | None = None
    ai_confidence: float | None = None
    ai_suggested_assignee: str | None = None
    sentry_issues: str | None = None
    posthog_recording_url: str | None = None
    user_metadata: str | None = None
    created_at: datetime
    updated_at: datetime
    messages: list[MessageOut] = []


class TicketListOut(BaseModel):
    id: int
    external_id: str | None = None
    subject: str
    sender_email: str
    sender_name: str
    source: str
    status: str
    priority: str
    category: str | None = None
    tags: str
    language: str
    assignee_id: str | None = None
    assignee: TeamMemberOut | None = None
    ai_category: str | None = None
    ai_confidence: float | None = None
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class TicketUpdate(BaseModel):
    status: TicketStatus | None = None
    priority: TicketPriority | None = None
    category: TicketCategory | None = None
    assignee_id: str | None = None
    tags: str | None = None


class TicketListResponse(BaseModel):
    tickets: list[TicketListOut]
    total: int
    page: int
    page_size: int


# --- AI ---

class AICategorizationResult(BaseModel):
    category: str
    confidence: float
    summary: str
    suggested_assignee: str | None
    language: str
    translated_body: str | None


class AIDraftResult(BaseModel):
    draft_response: str
    confidence: float


# --- Enrichment ---

class EnrichmentResult(BaseModel):
    sentry_issues: list[dict] | None
    posthog_recording_url: str | None
    user_metadata: dict | None


# --- Stats ---

class DashboardStats(BaseModel):
    total_tickets: int
    open_tickets: int
    in_progress_tickets: int
    resolved_tickets: int
    unassigned_tickets: int
    avg_ai_confidence: float | None
    category_breakdown: dict[str, int]
