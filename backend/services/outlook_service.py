"""
Microsoft Graph API integration for Outlook email sync.

Handles:
- Fetching new emails from the shared support mailbox
- Sending replies that appear in the Outlook thread
- Syncing replies sent directly in Outlook back to the platform

When MS_CLIENT_ID is not configured, falls back to a mock service that
serves realistic sample emails for development/demo purposes.

Requires Azure AD app registration with Mail.ReadWrite, Mail.Send permissions.
"""

import time
import uuid
from datetime import datetime, timezone

import httpx
from config import get_settings


class OutlookService:
    BASE_URL = "https://graph.microsoft.com/v1.0"

    def __init__(self):
        self._token: str | None = None
        self._token_expires_at: float = 0

    async def _get_token(self) -> str:
        """Obtain an OAuth2 token using client credentials flow."""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        settings = get_settings()
        if not settings.ms_client_id:
            raise RuntimeError("Microsoft Graph API credentials not configured")

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"https://login.microsoftonline.com/{settings.ms_tenant_id}/oauth2/v2.0/token",
                data={
                    "grant_type": "client_credentials",
                    "client_id": settings.ms_client_id,
                    "client_secret": settings.ms_client_secret,
                    "scope": "https://graph.microsoft.com/.default",
                },
            )
            resp.raise_for_status()
            data = resp.json()
            self._token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            return self._token

    async def fetch_new_emails(self, since: str | None = None) -> list[dict]:
        """Fetch unread emails from the shared mailbox."""
        token = await self._get_token()
        settings = get_settings()

        params = {
            "$top": 50,
            "$orderby": "receivedDateTime desc",
            "$select": "id,conversationId,subject,body,from,receivedDateTime,isRead",
            "$filter": "isRead eq false",
        }
        if since:
            params["$filter"] += f" and receivedDateTime ge {since}"

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/{settings.ms_shared_mailbox}/messages",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            resp.raise_for_status()
            return resp.json().get("value", [])

    async def send_reply(self, message_id: str, body: str) -> dict:
        """Send a reply to an existing email thread (maintains Outlook conversation)."""
        token = await self._get_token()
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.BASE_URL}/users/{settings.ms_shared_mailbox}/messages/{message_id}/reply",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={
                    "message": {
                        "body": {
                            "contentType": "Text",
                            "content": body,
                        }
                    }
                },
            )
            resp.raise_for_status()
            return {"status": "sent"}

    async def mark_as_read(self, message_id: str):
        """Mark an email as read after importing."""
        token = await self._get_token()
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            await client.patch(
                f"{self.BASE_URL}/users/{settings.ms_shared_mailbox}/messages/{message_id}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"isRead": True},
            )

    async def fetch_thread_messages(self, conversation_id: str) -> list[dict]:
        """Fetch all messages in a conversation thread to sync Outlook replies."""
        token = await self._get_token()
        settings = get_settings()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.BASE_URL}/users/{settings.ms_shared_mailbox}/messages",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "$filter": f"conversationId eq '{conversation_id}'",
                    "$orderby": "receivedDateTime asc",
                    "$select": "id,subject,body,from,receivedDateTime",
                },
            )
            resp.raise_for_status()
            return resp.json().get("value", [])


# ---------------------------------------------------------------------------
# Mock service for development / demo without Azure credentials
# ---------------------------------------------------------------------------

# Sample emails that simulate a realistic Outlook inbox.
# Each batch is served once then "marked as read" so the sync loop
# doesn't re-import them on the next poll cycle.
_MOCK_EMAILS = [
    # --- Batch 1: three new conversations ---
    {
        "id": "mock-msg-001",
        "conversationId": "mock-conv-001",
        "subject": "Cannot access my flashcards after update",
        "body": {
            "contentType": "Text",
            "content": (
                "Hi support,\n\n"
                "Since the latest app update I can no longer open my flashcard decks. "
                "The app just shows a blank screen when I tap on any deck. "
                "I've tried reinstalling but the issue persists.\n\n"
                "My account email is lena.mueller@gmail.com and I'm on iOS 17.4.\n\n"
                "Thanks,\nLena"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Lena Müller",
                "address": "lena.mueller@gmail.com",
            }
        },
        "receivedDateTime": "2026-03-15T08:12:00Z",
        "isRead": False,
    },
    {
        "id": "mock-msg-002",
        "conversationId": "mock-conv-002",
        "subject": "Refund request – annual subscription",
        "body": {
            "contentType": "HTML",
            "content": (
                "<html><body>"
                "<p>Hello,</p>"
                "<p>I subscribed to the annual plan last week but I realised "
                "the app doesn't support the subjects I need (law studies). "
                "Could I please get a full refund?</p>"
                "<p>Order confirmation number: SF-29481</p>"
                "<p>Best regards,<br/>Marco Bianchi</p>"
                "</body></html>"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Marco Bianchi",
                "address": "marco.bianchi@outlook.com",
            }
        },
        "receivedDateTime": "2026-03-15T09:05:00Z",
        "isRead": False,
    },
    {
        "id": "mock-msg-003",
        "conversationId": "mock-conv-003",
        "subject": "Quiz results not saving",
        "body": {
            "contentType": "Text",
            "content": (
                "Hey there,\n\n"
                "I completed a 40-question quiz on Biology Chapter 5 but when I went "
                "back to check my results they were gone. This has happened twice now.\n\n"
                "Can you look into this? My username is sophie_r.\n\n"
                "Cheers,\nSophie"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Sophie Renault",
                "address": "sophie.renault@edu.ch",
            }
        },
        "receivedDateTime": "2026-03-15T10:30:00Z",
        "isRead": False,
    },
    # --- Batch 2: a reply to conversation mock-conv-001 (Lena follows up) ---
    {
        "id": "mock-msg-004",
        "conversationId": "mock-conv-001",
        "subject": "Re: Cannot access my flashcards after update",
        "body": {
            "contentType": "Text",
            "content": (
                "Hi again,\n\n"
                "I forgot to mention — I also get error code E-4012 in the "
                "bottom-left corner of the blank screen. Hope that helps.\n\n"
                "Lena"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Lena Müller",
                "address": "lena.mueller@gmail.com",
            }
        },
        "receivedDateTime": "2026-03-15T11:45:00Z",
        "isRead": False,
    },
    # --- Batch 3: another new conversation + reply to mock-conv-002 ---
    {
        "id": "mock-msg-005",
        "conversationId": "mock-conv-004",
        "subject": "How to change subscription language?",
        "body": {
            "contentType": "Text",
            "content": (
                "Bonjour,\n\n"
                "I signed up with the French version but I'd like to switch "
                "my entire account to German. Is this possible without losing "
                "my study progress?\n\n"
                "Merci,\nAmélie Dupont"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Amélie Dupont",
                "address": "amelie.dupont@gmail.com",
            }
        },
        "receivedDateTime": "2026-03-15T13:00:00Z",
        "isRead": False,
    },
    {
        "id": "mock-msg-006",
        "conversationId": "mock-conv-002",
        "subject": "Re: Refund request – annual subscription",
        "body": {
            "contentType": "Text",
            "content": (
                "Hi, just following up on my refund request. "
                "It's been a few hours and I haven't heard back. "
                "Could you let me know the status?\n\n"
                "Thanks,\nMarco"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Marco Bianchi",
                "address": "marco.bianchi@outlook.com",
            }
        },
        "receivedDateTime": "2026-03-15T14:20:00Z",
        "isRead": False,
    },
    # --- Batch 4: customer replies to an agent response (full round-trip demo) ---
    # This simulates: agent replied from the platform (which was sent to Outlook),
    # then the customer replied to that email in Outlook, and it syncs back here.
    {
        "id": "mock-msg-007",
        "conversationId": "mock-conv-003",
        "subject": "Re: Quiz results not saving",
        "body": {
            "contentType": "Text",
            "content": (
                "Thanks for looking into this!\n\n"
                "Yes, I'm using the latest version (3.2.1) on Android. "
                "The quiz was in Biology > Chapter 5 > Practice Quiz. "
                "I noticed it happens specifically when I switch apps "
                "during the quiz and come back.\n\n"
                "Hope that helps narrow it down.\n\n"
                "Sophie"
            ),
        },
        "from": {
            "emailAddress": {
                "name": "Sophie Renault",
                "address": "sophie.renault@edu.ch",
            }
        },
        "receivedDateTime": "2026-03-15T15:30:00Z",
        "isRead": False,
    },
]


class MockOutlookService:
    """
    Drop-in replacement for OutlookService that serves canned sample emails.
    Emails are delivered in batches across successive poll cycles to simulate
    realistic drip-feed arrival. Once "read", they are not returned again.
    """

    def __init__(self):
        # Track which mock emails are still "unread"
        self._unread_ids: set[str] = {e["id"] for e in _MOCK_EMAILS}
        # Deliver emails in waves: batch index tracks how far we've gone
        self._batch_index: int = 0
        self._batches: list[list[str]] = [
            ["mock-msg-001", "mock-msg-002", "mock-msg-003"],  # initial emails
            ["mock-msg-004"],                                    # Lena's follow-up
            ["mock-msg-005", "mock-msg-006"],                   # new + Marco follow-up
            ["mock-msg-007"],                                    # Sophie replies after agent response
        ]
        self._emails_by_id: dict[str, dict] = {e["id"]: e for e in _MOCK_EMAILS}

    async def fetch_new_emails(self, since: str | None = None) -> list[dict]:
        if self._batch_index >= len(self._batches):
            return []

        batch_ids = self._batches[self._batch_index]
        self._batch_index += 1

        emails = []
        for msg_id in batch_ids:
            if msg_id in self._unread_ids:
                # Return a copy with a fresh timestamp so it looks current
                email = dict(self._emails_by_id[msg_id])
                email["receivedDateTime"] = datetime.now(timezone.utc).isoformat()
                emails.append(email)
        return emails

    async def send_reply(self, message_id: str, body: str) -> dict:
        print(f"[Mock Outlook] send_reply to {message_id}: {body[:80]}...")
        return {"status": "sent"}

    async def mark_as_read(self, message_id: str):
        self._unread_ids.discard(message_id)

    async def fetch_thread_messages(self, conversation_id: str) -> list[dict]:
        return [
            e for e in _MOCK_EMAILS
            if e.get("conversationId") == conversation_id
        ]


# ---------------------------------------------------------------------------
# Singleton — picks mock or real based on configuration
# ---------------------------------------------------------------------------

def _is_real_credential(value: str) -> bool:
    """Check if a credential is a real value, not a placeholder."""
    placeholders = {"", "your-client-id", "your-tenant-id", "your-client-secret"}
    return value not in placeholders


def _create_service():
    settings = get_settings()
    if _is_real_credential(settings.ms_client_id):
        print("Outlook service: using Microsoft Graph API (production)")
        return OutlookService()
    else:
        print("Outlook service: using MOCK data (no MS credentials configured)")
        return MockOutlookService()

outlook_service = _create_service()
