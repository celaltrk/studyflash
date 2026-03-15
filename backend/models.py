"""Enums and type definitions for the support platform. No ORM — Supabase handles persistence."""

import enum


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    waiting = "waiting"
    resolved = "resolved"
    closed = "closed"


class TicketPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    urgent = "urgent"


class UserRole(str, enum.Enum):
    admin = "admin"
    support = "support"
    billing = "billing"
    engineering = "engineering"


class TicketCategory(str, enum.Enum):
    refund_request = "refund_request"
    subscription_cancellation = "subscription_cancellation"
    subscription_info = "subscription_info"
    billing_invoice = "billing_invoice"
    flashcard_issues = "flashcard_issues"
    quiz_issues = "quiz_issues"
    podcast_issues = "podcast_issues"
    summary_issues = "summary_issues"
    mindmap_issues = "mindmap_issues"
    mock_exam_issues = "mock_exam_issues"
    content_upload = "content_upload"
    technical_errors = "technical_errors"
    account_issues = "account_issues"
    language_issues = "language_issues"
    general_how_to = "general_how_to"
    data_loss = "data_loss"
    misunderstanding = "misunderstanding"
    garbage = "garbage"
    other = "other"
