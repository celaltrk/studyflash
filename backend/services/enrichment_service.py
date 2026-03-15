"""
Enrichment service: pulls user context from Sentry, PostHog, and the Studyflash database.

In production, these would connect to real APIs. For the MVP, they return
realistic mock data to demonstrate the enrichment pipeline.
"""

import json
import random
from datetime import datetime, timedelta


async def enrich_ticket(sender_email: str, body: str) -> dict:
    """
    Enrich a ticket with external context.

    In production:
    - Sentry: query by user email for recent exceptions
    - PostHog: find session recordings for the user
    - Database: pull subscription status, plan, activity data
    """
    return {
        "sentry_issues": await _fetch_sentry_issues(sender_email),
        "posthog_recording_url": await _get_posthog_recording(sender_email),
        "user_metadata": await _get_user_metadata(sender_email),
    }


async def _fetch_sentry_issues(email: str) -> list[dict] | None:
    """
    Query Sentry for recent exceptions associated with this user.

    Production implementation:
        GET https://sentry.io/api/0/projects/{org}/{project}/issues/
        ?query=user.email:{email}&sort=date&limit=5

    Requires SENTRY_AUTH_TOKEN and SENTRY_ORG/PROJECT in config.
    """
    if not email:
        return None

    # MVP: return realistic mock data
    sample_issues = [
        {
            "id": "STUDY-4A2",
            "title": "TypeError: Cannot read property 'flashcards' of undefined",
            "level": "error",
            "count": 3,
            "first_seen": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            "last_seen": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
            "url": "https://studyflash.sentry.io/issues/STUDY-4A2/",
        },
        {
            "id": "STUDY-3F1",
            "title": "NetworkError: Failed to fetch /api/v1/decks",
            "level": "warning",
            "count": 1,
            "first_seen": (datetime.utcnow() - timedelta(days=1)).isoformat(),
            "last_seen": (datetime.utcnow() - timedelta(hours=12)).isoformat(),
            "url": "https://studyflash.sentry.io/issues/STUDY-3F1/",
        },
    ]
    # Randomly include 0-2 issues to simulate real data
    return random.sample(sample_issues, k=random.randint(0, min(2, len(sample_issues))))


async def _get_posthog_recording(email: str) -> str | None:
    """
    Find the most recent PostHog session recording for this user.

    Production implementation:
        POST https://app.posthog.com/api/projects/{project_id}/query/
        HogQL: SELECT session_id FROM sessions WHERE person.properties.email = '{email}'
               ORDER BY start_time DESC LIMIT 1

    Requires POSTHOG_API_KEY and POSTHOG_PROJECT_ID in config.
    """
    if not email:
        return None

    # MVP: return a plausible PostHog URL
    mock_session_id = hex(hash(email) % (10**12))[2:]
    return f"https://app.posthog.com/recordings/{mock_session_id}"


async def _get_user_metadata(email: str) -> dict | None:
    """
    Pull user info from the Studyflash PostgreSQL database.

    Production implementation:
        SELECT id, plan, status, created_at, last_active_at, deck_count, locale
        FROM users WHERE email = $1

    Connects to the main Studyflash database (read-only replica recommended).
    """
    if not email:
        return None

    # MVP: return realistic mock data
    plans = ["free", "monthly", "yearly"]
    statuses = ["active", "churned", "trial"]

    return {
        "user_id": f"usr_{abs(hash(email)) % 100000:05d}",
        "email": email,
        "plan": random.choice(plans),
        "status": random.choice(statuses),
        "created_at": (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat(),
        "last_active_at": (datetime.utcnow() - timedelta(hours=random.randint(1, 72))).isoformat(),
        "deck_count": random.randint(0, 50),
        "locale": "de-CH",
    }
