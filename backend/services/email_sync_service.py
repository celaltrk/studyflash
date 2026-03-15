"""
Inbound email sync: polls Outlook shared mailbox for new/reply emails
and creates tickets or appends messages in the support platform.
"""

import asyncio
import re
from html.parser import HTMLParser

from config import get_settings
from services.outlook_service import outlook_service, _is_real_credential
import services.db_service as db


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML-to-text converter using stdlib."""

    def __init__(self):
        super().__init__()
        self._parts: list[str] = []

    def handle_data(self, data: str):
        self._parts.append(data)

    def get_text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self._parts)).strip()


def _html_to_text(html: str) -> str:
    extractor = _HTMLTextExtractor()
    extractor.feed(html)
    return extractor.get_text()


async def sync_inbound_emails():
    """
    Fetch unread emails from the shared Outlook mailbox and either
    create new tickets or append replies to existing conversations.
    """
    settings = get_settings()
    emails = await outlook_service.fetch_new_emails()

    for email in emails:
        try:
            await _process_email(email, settings)
        except Exception as e:
            print(f"Email sync: failed to process email {email.get('id', '?')}: {e}")


async def _process_email(email: dict, settings):
    outlook_msg_id = email["id"]
    conversation_id = email.get("conversationId", "")
    subject = email.get("subject", "(no subject)")
    from_info = email.get("from", {}).get("emailAddress", {})
    from_email = from_info.get("address", "")
    from_name = from_info.get("name", from_email)

    # Extract body as plain text
    body_obj = email.get("body", {})
    if body_obj.get("contentType") == "HTML":
        body = _html_to_text(body_obj.get("content", ""))
    else:
        body = body_obj.get("content", "")

    # Skip emails sent FROM our own shared mailbox (outbound replies we already track)
    if from_email.lower() == settings.ms_shared_mailbox.lower():
        await outlook_service.mark_as_read(outlook_msg_id)
        return

    # Dedup: skip if we already imported this exact message
    if db.ticket_exists_by_outlook_message_id(outlook_msg_id):
        await outlook_service.mark_as_read(outlook_msg_id)
        return
    if db.message_exists_by_outlook_id(outlook_msg_id):
        await outlook_service.mark_as_read(outlook_msg_id)
        return

    # Try to match to an existing ticket by conversation ID
    existing = db.get_ticket_by_outlook_conversation(conversation_id) if conversation_id else None
    ticket = existing.data if existing else None

    if ticket:
        # This is a reply to an existing conversation — add as message
        db.insert_message({
            "ticket_id": ticket["id"],
            "sender_type": "customer",
            "sender_name": from_name,
            "sender_email": from_email,
            "body": body,
            "outlook_message_id": outlook_msg_id,
        })
        # Reopen ticket if it was resolved/closed
        if ticket["status"] in ("resolved", "closed"):
            db.update_ticket(ticket["id"], {"status": "open"})
        print(f"Email sync: added reply to ticket #{ticket['id']} from {from_email}")
    else:
        # New conversation — create ticket + initial message
        ticket_data = {
            "subject": subject,
            "body": body,
            "sender_email": from_email,
            "sender_name": from_name,
            "source": "email",
            "status": "open",
            "priority": "medium",
            "outlook_conversation_id": conversation_id,
            "outlook_message_id": outlook_msg_id,
        }
        result = db.insert_ticket(ticket_data)
        new_ticket = result.data[0]

        db.insert_message({
            "ticket_id": new_ticket["id"],
            "sender_type": "customer",
            "sender_name": from_name,
            "sender_email": from_email,
            "body": body,
            "outlook_message_id": outlook_msg_id,
        })
        print(f"Email sync: created ticket #{new_ticket['id']} — \"{subject}\" from {from_email}")

    # Mark as read so we don't re-process
    await outlook_service.mark_as_read(outlook_msg_id)


async def email_poll_loop():
    """Background loop that periodically syncs inbound emails."""
    settings = get_settings()

    mode = "Microsoft Graph API" if _is_real_credential(settings.ms_client_id) else "MOCK data"
    interval = settings.email_poll_interval_seconds
    print(f"Email sync started in {mode} mode (polling every {interval}s)")

    while True:
        try:
            await sync_inbound_emails()
        except Exception as e:
            print(f"Email sync error: {e}")
        await asyncio.sleep(interval)
