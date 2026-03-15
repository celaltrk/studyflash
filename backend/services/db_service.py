from database import get_supabase

# --- Auth ---

def sign_in_with_password(email, password):
    sb = get_supabase()
    return sb.auth.sign_in_with_password({"email": email, "password": password})

def get_auth_user(token):
    sb = get_supabase()
    return sb.auth.get_user(token)

def get_user_by_id(user_id):
    sb = get_supabase()
    return sb.auth.admin.get_user_by_id(user_id)

def list_admin_users():
    sb = get_supabase()
    return sb.auth.admin.list_users()

def create_admin_user(email, password, display_name, role):
    sb = get_supabase()
    return sb.auth.admin.create_user({
        "email": email,
        "password": password,
        "email_confirm": True,
        "user_metadata": {
            "name": display_name,
            "role": role,
        },
    })

def update_admin_user_metadata(user_id, metadata):
    sb = get_supabase()
    return sb.auth.admin.update_user_by_id(user_id, {"user_metadata": metadata})

# --- Tickets ---

def list_tickets(limit=None, offset=None, status=None, category=None, assignee_id=None,
                 search=None, sort_by="created_at", sort_order="desc"):
    sb = get_supabase()
    query = sb.table("tickets").select("*", count="exact")
    
    if status:
        query = query.eq("status", status)
    if category:
        query = query.eq("category", category)
    if assignee_id is not None:
        if assignee_id == "0":
            query = query.is_("assignee_id", "null")
        else:
            query = query.eq("assignee_id", assignee_id)
    if search:
        query = query.or_(f"body.ilike.%{search}%,subject.ilike.%{search}%")

    query = query.order(sort_by, desc=(sort_order == "desc"))
    if limit is not None and offset is not None:
        query = query.range(offset, offset + limit - 1)
        
    return query.execute()

def count_tickets(status=None, assignee_id=None, is_unassigned=False):
    sb = get_supabase()
    query = sb.table("tickets").select("id", count="exact")
    if status:
        if isinstance(status, list):
            query = query.in_("status", status)
        else:
            query = query.eq("status", status)
    if assignee_id:
        query = query.eq("assignee_id", assignee_id)
    if is_unassigned:
        query = query.is_("assignee_id", "null")
    return query.execute()

def count_uncategorized_tickets():
    sb = get_supabase()
    return sb.table("tickets").select("ai_confidence, ai_category").not_.is_("ai_category", "null").execute()

def count_tickets_total():
    sb = get_supabase()
    return sb.table("tickets").select("id", count="exact").execute()

def get_ticket(ticket_id, select="*"):
    sb = get_supabase()
    return sb.table("tickets").select(select).eq("id", ticket_id).maybe_single().execute()

def update_ticket(ticket_id, update_data):
    sb = get_supabase()
    return sb.table("tickets").update(update_data).eq("id", ticket_id).execute()

def insert_ticket(ticket_data):
    sb = get_supabase()
    return sb.table("tickets").insert(ticket_data).execute()

def get_uncategorized_tickets(select="id, body, language"):
    sb = get_supabase()
    return sb.table("tickets").select(select).is_("ai_category", "null").execute()

# --- Outlook lookup helpers ---

def get_ticket_by_outlook_conversation(conversation_id):
    """Find a ticket by its Outlook conversation ID."""
    sb = get_supabase()
    return sb.table("tickets").select("*").eq(
        "outlook_conversation_id", conversation_id
    ).maybe_single().execute()

def message_exists_by_outlook_id(outlook_message_id):
    """Check if a message with this Outlook message ID already exists."""
    sb = get_supabase()
    result = sb.table("messages").select("id", count="exact").eq(
        "outlook_message_id", outlook_message_id
    ).execute()
    return (result.count or 0) > 0

def ticket_exists_by_outlook_message_id(outlook_message_id):
    """Check if a ticket with this Outlook message ID already exists."""
    sb = get_supabase()
    result = sb.table("tickets").select("id", count="exact").eq(
        "outlook_message_id", outlook_message_id
    ).execute()
    return (result.count or 0) > 0

# --- Messages ---

def count_messages(ticket_id):
    sb = get_supabase()
    return sb.table("messages").select("id", count="exact").eq("ticket_id", ticket_id).execute()

def get_ticket_messages(ticket_id):
    sb = get_supabase()
    return sb.table("messages").select("*").eq("ticket_id", ticket_id).order("created_at").execute()

def insert_message(message_data):
    sb = get_supabase()
    return sb.table("messages").insert(message_data).execute()

# --- User Profiles ---

def get_user_profile(user_id, select="*"):
    sb = get_supabase()
    return sb.table("user_profiles").select(select).eq("id", user_id).maybe_single().execute()

def update_user_profile(user_id, update_data):
    sb = get_supabase()
    return sb.table("user_profiles").update(update_data).eq("id", user_id).execute()

def insert_user_profile(profile_data):
    sb = get_supabase()
    return sb.table("user_profiles").insert(profile_data).execute()

def upsert_user_profile(profile_data):
    sb = get_supabase()
    return sb.table("user_profiles").upsert(profile_data).execute()

def list_user_profiles(role=None, active_only=False, select="*"):
    sb = get_supabase()
    query = sb.table("user_profiles").select(select)
    if role:
        query = query.eq("role", role)
    if active_only:
        query = query.eq("is_active", True)
    return query.order("display_name").execute()
