"""Seed the database with sample tickets and team members via Supabase client."""

import asyncio
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
import random

import services.db_service as db
from services.ai_service import categorize_heuristic, detect_language, extract_source


TICKETS_DIR = Path(__file__).parent.parent / "tickets"

TAG_TO_CATEGORY = {
    "refund-request": "refund_request",
    "subscription-cancellation": "subscription_cancellation",
    "subscription-info": "subscription_info",
    "billing-invoice": "billing_invoice",
    "flashcard-issues": "flashcard_issues",
    "quiz-issues": "quiz_issues",
    "podcast-issues": "podcast_issues",
    "summary-issues": "summary_issues",
    "mindmap-issues": "mindmap_issues",
    "mock-exam-issues": "mock_exam_issues",
    "content-upload": "content_upload",
    "technical-errors": "technical_errors",
    "account-issues": "account_issues",
    "language-issues": "language_issues",
    "general-how-to": "general_how_to",
    "data-loss": "data_loss",
    "misunderstanding": "misunderstanding",
    "garbage": "garbage",
}

# Team members — these will also be created as Supabase Auth users
TEAM_MEMBERS = [
    {"name": "Admin User", "email": "admin@studyflash.ch", "role": "admin", "department": "Management"},
    {"name": "Anna Müller", "email": "anna@studyflash.ch", "role": "support", "department": "Customer Support"},
    {"name": "Marco Rossi", "email": "marco@studyflash.ch", "role": "support", "department": "Customer Support"},
    {"name": "Sophie Dubois", "email": "sophie@studyflash.ch", "role": "billing", "department": "Finance"},
    {"name": "Luca Weber", "email": "luca@studyflash.ch", "role": "engineering", "department": "Engineering"},
    {"name": "Elena Schmidt", "email": "elena@studyflash.ch", "role": "engineering", "department": "Engineering"},
]

DEFAULT_PASSWORD = "studyflash2026!"  # Default password for seeded users


def parse_ticket_file(filepath: Path) -> dict:
    content = filepath.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    tags_line = lines[0] if lines[0].startswith("Tags:") else ""
    tags = [t.strip() for t in tags_line.replace("Tags:", "").split(",") if t.strip()] if tags_line else []

    body = ""
    found_separator = False
    for line in lines:
        if line.strip() == "---":
            found_separator = True
            continue
        if found_separator:
            body += line + "\n"
    body = body.strip()

    category = None
    for tag in tags:
        if tag in TAG_TO_CATEGORY:
            category = TAG_TO_CATEGORY[tag]
            break

    source = extract_source(body)
    clean_body = re.sub(r"^(MOBILE|WEB):\s*", "", body)

    subject_match = re.match(r"^(.{1,80}?)[\.\!\?\n]", clean_body)
    subject = subject_match.group(1) if subject_match else clean_body[:80]

    language = detect_language(clean_body)

    ai_category, ai_confidence = categorize_heuristic(clean_body)
    if category:
        ai_category = category
        ai_confidence = max(ai_confidence, 0.7)

    return {
        "external_id": filepath.stem,
        "subject": subject.strip(),
        "body": clean_body,
        "source": source,
        "tags": ", ".join(tags),
        "language": language,
        "category": category,
        "ai_category": ai_category,
        "ai_confidence": ai_confidence,
        "ai_summary": clean_body[:200] + "..." if len(clean_body) > 200 else clean_body,
    }


def seed():
    # Check if already seeded
    existing = db.count_tickets_total()
    if existing.count and existing.count > 0:
        print(f"Database already has {existing.count} tickets, skipping seed.")
        return

    # Create team members with Supabase Auth accounts
    for tm in TEAM_MEMBERS:
        # Create auth user (service_role key can create users directly)
        try:
            auth_user = db.create_admin_user(
                email=tm["email"],
                password=DEFAULT_PASSWORD,
                display_name=tm["name"],
                role=tm["role"]
            )
            auth_user_id = auth_user.user.id
        except Exception as e:
            # User might already exist — try to find them
            print(f"Auth user creation for {tm['email']} failed ({e}), looking up existing...")
            users = db.list_admin_users()
            auth_user_id = None
            for u in users:
                if u.email == tm["email"]:
                    auth_user_id = u.id
                    break
            if not auth_user_id:
                print(f"  Could not find or create auth user for {tm['email']}, skipping auth link")

        if not auth_user_id:
            print(f"  Warning: Auth user ID not found for {tm['email']}")
            continue

        # Create user_profile row
        try:
            db.upsert_user_profile({
                "id": auth_user_id,
                "display_name": tm["name"],
                "role": tm["role"],
                "department": tm.get("department"),
            })
        except Exception as e:
            print(f"  Warning: user_profiles upsert failed for {tm['email']}: {e}")

    print(f"Created/verified {len(TEAM_MEMBERS)} team members with Supabase Auth accounts and profiles")
    print(f"  Default login: <email> / {DEFAULT_PASSWORD}")

    # Load and create tickets
    ticket_files = sorted(TICKETS_DIR.glob("ticket_*.txt"))
    print(f"Found {len(ticket_files)} ticket files")

    from services.ai_service import ASSIGNMENT_RULES

    for filepath in ticket_files:
        data = parse_ticket_file(filepath)

        created = datetime.now(timezone.utc) - timedelta(
            days=random.randint(0, 30),
            hours=random.randint(0, 23),
            minutes=random.randint(0, 59),
        )
        suggested_role = ASSIGNMENT_RULES.get(data["ai_category"], "support")

        ticket_data = {
            "external_id": data["external_id"],
            "subject": data["subject"],
            "body": data["body"],
            "sender_email": f"user{abs(hash(data['external_id'])) % 10000:04d}@example.com",
            "sender_name": f"User {abs(hash(data['external_id'])) % 10000:04d}",
            "source": data["source"],
            "status": "open",
            "priority": random.choice(["low", "medium", "medium", "high"]),
            "category": data["category"],
            "tags": data["tags"],
            "language": data["language"],
            "ai_category": data["ai_category"],
            "ai_confidence": data["ai_confidence"],
            "ai_summary": data["ai_summary"],
            "ai_suggested_assignee": suggested_role,
            "created_at": created.isoformat(),
            "updated_at": created.isoformat(),
        }
        ticket_result = db.insert_ticket(ticket_data)
        ticket_id = ticket_result.data[0]["id"]

        # Add the initial customer message
        db.insert_message({
            "ticket_id": ticket_id,
            "sender_type": "customer",
            "sender_name": ticket_data["sender_name"],
            "sender_email": ticket_data["sender_email"],
            "body": data["body"],
            "created_at": created.isoformat(),
        })

    print(f"Seeded {len(ticket_files)} tickets.")


if __name__ == "__main__":
    seed()
