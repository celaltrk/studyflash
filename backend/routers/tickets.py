from fastapi import APIRouter, HTTPException, Query
import services.db_service as db
from schemas import (
    TicketOut, TicketListOut, TicketListResponse, TicketUpdate,
    MessageOut, MessageCreate, DashboardStats,
)

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=TicketListResponse)
async def list_tickets(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    category: str | None = None,
    assignee_id: str | None = None,
    search: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    offset = (page - 1) * page_size
    result = db.list_tickets(
        limit=page_size, offset=offset, status=status,
        category=category, assignee_id=assignee_id, search=search,
        sort_by=sort_by, sort_order=sort_order
    )

    total = result.count if result.count is not None else 0
    tickets = result.data or []

    # Get message counts for these tickets
    ticket_ids = [t["id"] for t in tickets]
    msg_counts: dict[int, int] = {}
    if ticket_ids:
        for tid in ticket_ids:
            mc = db.count_messages(tid)
            msg_counts[tid] = mc.count if mc.count is not None else 0

    # Fetch all users to resolve assignees
    users_dict = {}
    try:
        users_resp = db.list_admin_users()
        for u in users_resp:
            meta = u.user_metadata or {}
            users_dict[u.id] = {
                "id": u.id,
                "name": meta.get("name", ""),
                "email": u.email,
                "role": meta.get("role", "support"),
                "is_active": True
            }
    except Exception as e:
        print(f"Error fetching users: {e}")

    items = []
    for t in tickets:
        t["message_count"] = msg_counts.get(t["id"], 0)
        t["assignee"] = users_dict.get(t["assignee_id"]) if t.get("assignee_id") else None
        items.append(t)

    return TicketListResponse(tickets=items, total=total, page=page, page_size=page_size)


@router.get("/stats", response_model=DashboardStats)
async def get_stats():
    total_r = db.count_tickets_total()
    total = total_r.count or 0

    open_r = db.count_tickets(status="open")
    open_count = open_r.count or 0

    ip_r = db.count_tickets(status="in_progress")
    in_progress = ip_r.count or 0

    res_r = db.count_tickets(status="resolved")
    resolved = res_r.count or 0

    una_r = db.count_tickets(is_unassigned=True)
    unassigned = una_r.count or 0

    # Avg confidence + category breakdown
    ai_r = db.count_uncategorized_tickets()
    ai_data = ai_r.data or []

    confidences = [r["ai_confidence"] for r in ai_data if r.get("ai_confidence") is not None]
    avg_conf = round(sum(confidences) / len(confidences), 2) if confidences else None

    cat_breakdown: dict[str, int] = {}
    for r in ai_data:
        cat = r.get("ai_category")
        if cat:
            cat_breakdown[cat] = cat_breakdown.get(cat, 0) + 1

    return DashboardStats(
        total_tickets=total,
        open_tickets=open_count,
        in_progress_tickets=in_progress,
        resolved_tickets=resolved,
        unassigned_tickets=unassigned,
        avg_ai_confidence=avg_conf,
        category_breakdown=cat_breakdown,
    )


@router.get("/{ticket_id}", response_model=TicketOut)
async def get_ticket(ticket_id: int):
    result = db.get_ticket(ticket_id)
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = result.data

    # Fetch assignee detail
    if ticket.get("assignee_id"):
        try:
            u_resp = db.get_user_by_id(ticket["assignee_id"])
            u = u_resp.user
            meta = u.user_metadata or {}
            ticket["assignee"] = {
                "id": u.id,
                "name": meta.get("name", ""),
                "email": u.email,
                "role": meta.get("role", "support"),
                "is_active": True
            }
        except Exception:
            ticket["assignee"] = None
    else:
        ticket["assignee"] = None

    # Fetch messages
    msg_result = db.get_ticket_messages(ticket_id)
    ticket["messages"] = msg_result.data or []

    return ticket


@router.patch("/{ticket_id}", response_model=TicketOut)
async def update_ticket(ticket_id: int, update: TicketUpdate):


    update_data = update.model_dump(exclude_unset=True)
    # Convert enums to string values for Supabase
    for key, value in update_data.items():
        if hasattr(value, "value"):
            update_data[key] = value.value

    result = db.update_ticket(ticket_id, update_data)
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return await get_ticket(ticket_id)


@router.post("/{ticket_id}/messages", response_model=MessageOut)
async def add_message(ticket_id: int, msg: MessageCreate):
    # Verify ticket exists
    ticket_r = db.get_ticket(ticket_id, select="id, status, outlook_message_id")
    if not ticket_r.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = ticket_r.data

    # Insert message
    message_data = {
        "ticket_id": ticket_id,
        "sender_type": msg.sender_type,
        "sender_name": msg.sender_name or "Support Agent",
        "sender_email": msg.sender_email,
        "body": msg.body,
    }
    msg_result = db.insert_message(message_data)

    # If agent is replying to an open ticket, update status
    if msg.sender_type == "agent" and ticket["status"] == "open":
        db.update_ticket(ticket_id, {"status": "in_progress"})

    # Try to send via Outlook if conversation is linked
    if ticket.get("outlook_message_id") and msg.sender_type == "agent":
        try:
            from services.outlook_service import outlook_service
            await outlook_service.send_reply(ticket["outlook_message_id"], msg.body)
        except Exception as e:
            print(f"Outlook send failed (expected in dev): {e}")

    return msg_result.data[0]
