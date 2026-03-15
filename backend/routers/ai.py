import json
from fastapi import APIRouter, HTTPException
import services.db_service as db
from services.ai_service import categorize_ticket, draft_response, translate_to_english
from services.enrichment_service import enrich_ticket

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/categorize/{ticket_id}")
async def categorize(ticket_id: int):
    """Run AI categorization on a ticket."""
    result = db.get_ticket(ticket_id, select="id, body, language")
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = result.data
    ai_result = await categorize_ticket(ticket["body"])
    language = ai_result.get("language", ticket.get("language", "en"))

    # Translate summary to English if ticket is not in English
    summary = ai_result.get("summary")
    if summary and language != "en":
        translation = await translate_to_english(summary, language)
        summary = translation.get("translated_body") or summary

    update_data = {
        "ai_category": ai_result["category"],
        "ai_confidence": ai_result["confidence"],
        "ai_summary": summary,
        "ai_suggested_assignee": ai_result.get("suggested_assignee_role"),
        "language": language,
    }
    if ai_result.get("translated_body"):
        update_data["translated_body"] = ai_result["translated_body"]

    # Set the category enum if it's a valid value
    try:
        from models import TicketCategory
        TicketCategory(ai_result["category"])
        update_data["category"] = ai_result["category"]
    except (ValueError, KeyError):
        pass

    db.update_ticket(ticket_id, update_data)
    return ai_result


@router.post("/draft/{ticket_id}")
async def draft(ticket_id: int):
    """Generate an AI draft response for a ticket."""
    result = db.get_ticket(
        ticket_id,
        select="id, body, ai_category, category, language, sentry_issues, posthog_recording_url, user_metadata",
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = result.data
    category = ticket.get("ai_category") or ticket.get("category") or "other"

    # Build enrichment context from stored data
    enrichment_context = _build_enrichment_context(ticket)

    ai_result = await draft_response(
        ticket["body"], category, ticket.get("language", "en"), enrichment_context
    )
    db.update_ticket(ticket_id, {"ai_draft_response": ai_result["draft_response"]})

    return ai_result


def _build_enrichment_context(ticket: dict) -> str | None:
    """Build a human-readable enrichment summary from stored ticket data."""
    parts = []

    # User metadata
    user_meta = ticket.get("user_metadata")
    if user_meta:
        try:
            meta = json.loads(user_meta) if isinstance(user_meta, str) else user_meta
            plan = meta.get("plan", "unknown")
            status = meta.get("status", "unknown")
            locale = meta.get("locale", "")
            deck_count = meta.get("deck_count")
            last_active = meta.get("last_active_at", "")
            parts.append(
                f"User profile: plan={plan}, status={status}, locale={locale}, "
                f"deck_count={deck_count}, last_active={last_active}"
            )
        except (json.JSONDecodeError, TypeError):
            pass

    # Sentry issues
    sentry = ticket.get("sentry_issues")
    if sentry:
        try:
            issues = json.loads(sentry) if isinstance(sentry, str) else sentry
            if issues:
                issue_lines = []
                for issue in issues:
                    title = issue.get("title", "Unknown error")
                    level = issue.get("level", "error")
                    count = issue.get("count", 0)
                    issue_lines.append(f"  - [{level}] {title} (occurred {count}x)")
                parts.append("Recent errors (Sentry):\n" + "\n".join(issue_lines))
        except (json.JSONDecodeError, TypeError):
            pass

    # PostHog
    recording_url = ticket.get("posthog_recording_url")
    if recording_url:
        parts.append(f"Session recording available: {recording_url}")

    return "\n".join(parts) if parts else None


@router.post("/enrich/{ticket_id}")
async def enrich(ticket_id: int):
    """Enrich a ticket with Sentry, PostHog, and user data."""
    result = db.get_ticket(ticket_id, select="id, sender_email, body")
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = result.data
    enrichment = await enrich_ticket(ticket.get("sender_email", ""), ticket["body"])

    update_data = {
        "sentry_issues": json.dumps(enrichment["sentry_issues"]) if enrichment["sentry_issues"] else None,
        "posthog_recording_url": enrichment["posthog_recording_url"],
        "user_metadata": json.dumps(enrichment["user_metadata"]) if enrichment["user_metadata"] else None,
    }
    db.update_ticket(ticket_id, update_data)

    return enrichment


@router.post("/translate/{ticket_id}")
async def translate(ticket_id: int):
    """Translate a ticket body to English."""
    result = db.get_ticket(ticket_id, select="id, body, language")
    if not result.data:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket = result.data
    ai_result = await translate_to_english(ticket["body"], ticket.get("language", "en"))

    if ai_result.get("translated_body"):
        db.update_ticket(ticket_id, {"translated_body": ai_result["translated_body"]})

    return ai_result


@router.post("/translate-text")
async def translate_text(payload: dict):
    """Translate arbitrary text to English."""
    text = payload.get("text", "")
    language = payload.get("language", "auto")
    if not text.strip():
        raise HTTPException(status_code=400, detail="No text provided")

    from services.ai_service import detect_language
    if language == "auto":
        language = detect_language(text)

    ai_result = await translate_to_english(text, language)
    return ai_result


@router.post("/batch-categorize")
async def batch_categorize():
    """Categorize all uncategorized tickets."""
    result = db.get_uncategorized_tickets(select="id, body, language")
    tickets = result.data or []

    results = []
    for ticket in tickets:
        ai_result = await categorize_ticket(ticket["body"])
        language = ai_result.get("language", ticket.get("language", "en"))

        # Translate summary to English if ticket is not in English
        summary = ai_result.get("summary")
        if summary and language != "en":
            translation = await translate_to_english(summary, language)
            summary = translation.get("translated_body") or summary

        update_data = {
            "ai_category": ai_result["category"],
            "ai_confidence": ai_result["confidence"],
            "ai_summary": summary,
            "ai_suggested_assignee": ai_result.get("suggested_assignee_role"),
            "language": language,
        }
        if ai_result.get("translated_body"):
            update_data["translated_body"] = ai_result["translated_body"]

        try:
            from models import TicketCategory
            TicketCategory(ai_result["category"])
            update_data["category"] = ai_result["category"]
        except (ValueError, KeyError):
            pass

        db.update_ticket(ticket["id"], update_data)
        results.append({"ticket_id": ticket["id"], **ai_result})

    return {"categorized": len(results), "results": results}
