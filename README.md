# Studyflash Support Platform

An internal MVP support platform that ingests incoming support emails, structures them into actionable tickets, enriches them with internal context, and assists the team with AI-powered triage and responses.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack & Rationale](#tech-stack--rationale)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [AI Pipeline](#ai-pipeline)
- [Outlook Integration](#outlook-integration)
- [Enrichment Pipeline](#enrichment-pipeline)
- [Database Schema](#database-schema)
- [Design Decisions & Trade-offs](#design-decisions--trade-offs)
- [What I Decided Against](#what-i-decided-against)
- [Future Improvements](#future-improvements)

---

## Overview

Studyflash receives thousands of multilingual support requests per month. This MVP acts as an intelligent layer on top of Outlook: it ingests incoming emails, classifies them into 19 categories, drafts responses in the customer's language, suggests the right team member, and enriches tickets with data from Sentry, PostHog, and the user database.

---

## Features

| Feature | Description |
|---------|-------------|
| **Dashboard** | Stats overview with ticket counts by status, average AI confidence, and category breakdown chart |
| **Ticket List** | Filterable (status, category, assignee, search), sortable, paginated ticket table with 30s auto-refresh |
| **Ticket Detail** | Full conversation thread, sidebar actions, AI tools, enrichment panel, reply box |
| **AI Categorization** | Automatic classification into 19 categories with confidence scores (Claude or heuristic fallback) |
| **AI Draft Responses** | Multilingual response generation based on ticket category and language |
| **AI Translation** | One-click English translation for non-English tickets (team members aren't proficient in all languages) |
| **AI Auto-Assignment** | Suggests and assigns the right team (billing, engineering, support) based on category, with load balancing |
| **Batch Operations** | One-click batch categorization of all uncategorized tickets |
| **Enrichment** | Pulls Sentry exceptions, PostHog session recordings, and user metadata per ticket |
| **Outlook Sync** | Bidirectional: inbound emails become tickets, replies from the platform appear in Outlook threads |
| **Team Management** | View team members, roles, ticket loads; admins can create/edit users |
| **Authentication** | JWT-based auth via Supabase with role-based access (admin, support, billing, engineering) |
| **Auto-Seed** | 100 sample tickets + 5 team members created automatically on first startup |

---

## Tech Stack & Rationale

| Layer | Technology | Why |
|-------|-----------|-----|
| **Backend** | Python 3.12, FastAPI | Async-first, excellent for I/O-bound work (API calls, DB queries). FastAPI gives auto-generated OpenAPI docs, Pydantic validation, and dependency injection out of the box. |
| **Frontend** | Vue 3, TypeScript, Vite | Vue's composition API keeps components readable. Vite provides instant HMR. TypeScript catches type mismatches between frontend types and API responses at compile time. |
| **Database** | Supabase (PostgreSQL) | Managed Postgres with built-in auth, RLS policies, and a REST API (PostgREST). Eliminates connection pooling config, ORM setup, and auth infrastructure. One service handles DB + Auth. |
| **AI** | Anthropic Claude Sonnet | Excels at multilingual understanding and structured JSON output. Falls back to keyword heuristics when no API key is set. |
| **Email** | Microsoft Graph API | Direct integration with Outlook/Exchange. OAuth2 client credentials flow for server-to-server access to the shared mailbox. No IMAP polling needed. |
| **Infra** | Docker, docker-compose | Two-container setup (backend + nginx-served frontend). Single `docker-compose up` to run everything. |

---

## Architecture

### High-Level Flow

```
┌─────────────┐     ┌──────────────────────────────┐     ┌────────────────┐
│   Outlook    │────▶│  Email Sync Service (15s)     │────▶│   Supabase DB  │
│   Mailbox    │◀────│  (Background polling loop)    │     │  (PostgreSQL)  │
└─────────────┘     └──────────────────────────────┘     └───────┬────────┘
                                                                 │
                    ┌──────────────────────────────┐             │
                    │       FastAPI Backend         │◀────────────┘
                    │  • Auth (JWT via Supabase)    │
                    │  • Ticket CRUD + filters      │
                    │  • AI pipeline (Claude)       │
                    │  • Enrichment (Sentry/PH/DB)  │
                    │  • Outlook send (Graph API)   │
                    └──────────────┬───────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │     Vue 3 Frontend (SPA)      │
                    │  • Dashboard + Stats          │
                    │  • Ticket list + detail        │
                    │  • Team management             │
                    │  • AI actions (categorize,     │
                    │    draft, translate, enrich)   │
                    └──────────────────────────────┘
```

### Project Structure

```
studyflash/
├── backend/
│   ├── main.py                    # FastAPI app, CORS, lifespan (background tasks + auto-seed)
│   ├── config.py                  # Pydantic settings from .env
│   ├── database.py                # Supabase client singleton
│   ├── models.py                  # Enums (status, priority, category, role)
│   ├── schemas.py                 # Pydantic request/response models
│   ├── seed.py                    # Auto-seeds 5 users + 100 tickets from /tickets/
│   ├── Dockerfile
│   ├── routers/
│   │   ├── auth.py                # POST /login, GET /me
│   │   ├── tickets.py             # CRUD, pagination, filtering, stats
│   │   ├── ai.py                  # Categorize, draft, translate, enrich, batch
│   │   ├── users.py               # User CRUD, auto-assign, profile sync
│   │   ├── team.py                # Team member listing
│   │   └── outlook.py             # Manual sync trigger
│   ├── services/
│   │   ├── ai_service.py          # Claude + heuristic fallback for categorization/drafting
│   │   ├── outlook_service.py     # Microsoft Graph API client + mock mode
│   │   ├── email_sync_service.py  # Background inbox polling + ticket creation
│   │   ├── enrichment_service.py  # Sentry, PostHog, user DB lookups (mocked in MVP)
│   │   └── db_service.py          # 60+ database helper functions (Supabase queries)
│   └── prompts/
│       ├── categorize.yaml        # Claude prompt: classify into 19 categories
│       ├── draft.yaml             # Claude prompt: generate multilingual response
│       └── translate.yaml         # Claude prompt: translate to English
├── frontend/
│   ├── src/
│   │   ├── App.vue                # Sidebar layout, nav, user session
│   │   ├── api.ts                 # API client with JWT auth + auto-logout on 401
│   │   ├── router.ts              # Routes with auth guard
│   │   ├── types/index.ts         # TypeScript interfaces matching backend schemas
│   │   ├── style.css              # Design system (purple theme, badges, cards)
│   │   └── views/
│   │       ├── LoginView.vue      # Email/password login
│   │       ├── DashboardView.vue  # Stats cards + category breakdown chart
│   │       ├── TicketListView.vue # Paginated table with filters
│   │       ├── TicketDetailView.vue # Conversation thread + AI + enrichment
│   │       ├── TeamView.vue       # Team members with role cards + admin CRUD
│   │       └── ProfileView.vue    # User profile editor
│   ├── Dockerfile                 # Multi-stage: Node build → Nginx serve
│   └── nginx.conf                 # SPA routing + /api/ proxy to backend
├── supabase/
│   └── migrations/
│       └── 001_initial_schema.sql # Tables, enums, indexes, RLS policies, triggers
├── docker-compose.yml             # backend (port 8000) + frontend (port 5173)
└── README.md
```

---

## Setup Instructions

### Prerequisites

- **Supabase account** (free tier works) — [supabase.com](https://supabase.com)
- **Python 3.12+** and **Node.js 18+** (for local dev), or **Docker** (for containerized run)
- **Anthropic API key**

### Step 1: Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Go to **SQL Editor** and run the full migration from [`supabase/migrations/001_initial_schema.sql`](supabase/migrations/001_initial_schema.sql)
3. Copy your credentials from **Settings → API**:
   - **Project URL** (e.g. `https://xxxxx.supabase.co`)
   - **service_role key** (the secret one, NOT the anon key — needed for admin operations like creating auth users)

### Step 2: Configure Environment

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | Yes | Your Supabase project URL |
| `SUPABASE_SERVICE_KEY` | Yes | The **service_role** key (creates auth users, bypasses RLS) |
| `ANTHROPIC_API_KEY` | Yes | Enables Claude-powered categorization and drafting. Without it, the platform uses keyword heuristics and template responses. |
| `MS_TENANT_ID` | No | Azure AD tenant ID (for real Outlook sync) |
| `MS_CLIENT_ID` | No | Azure AD app client ID |
| `MS_CLIENT_SECRET` | No | Azure AD app client secret |
| `MS_SHARED_MAILBOX` | No | Shared mailbox email address |

> **Note**: Without Microsoft credentials, the platform runs a **mock Outlook service** that simulates incoming emails in batches — useful for demonstrating the sync flow.

### Step 3a: Run Locally (Development)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** and sign in.

### Step 3b: Run with Docker

```bash
# Ensure .env is configured (step 2) and migration is run (step 1)
docker-compose up --build
```

Open **http://localhost:5173**.

### Auto-Seeding

On first startup, the backend automatically:
1. Creates 5 team members as Supabase Auth users
2. Loads 100 sample support tickets from the `/tickets/` directory
3. Runs heuristic categorization and language detection on all tickets
4. Creates the initial message for each ticket

**Default Login Credentials** (all password: `studyflash2026!`):

| Name | Email | Role |
|------|-------|------|
| Anna Müller | anna@studyflash.ch | Support |
| Marco Rossi | marco@studyflash.ch | Support |
| Sophie Dubois | sophie@studyflash.ch | Billing |
| Luca Weber | luca@studyflash.ch | Engineering |
| Elena Schmidt | elena@studyflash.ch | Engineering |

---

## Usage Guide

### Typical Workflow

1. **Log in** as any team member
2. **Dashboard** shows an overview: open/in-progress/resolved counts, unassigned tickets, AI confidence, and category breakdown
3. **Tickets** page lists all tickets — filter by status, category, assignee, or search by subject/email
4. Click a ticket to open the **detail view**:
   - Read the conversation thread (customer messages + agent replies)
   - **Categorize** — click to run AI classification (sets category, confidence, summary, and suggested team)
   - **Draft Response** — AI generates a reply in the customer's language; review and edit before sending
   - **Translate** — translates non-English tickets to English for internal comprehension
   - **Enrich** — pulls Sentry errors, PostHog recordings, and user metadata
   - **Assign** — manually pick a team member, or use auto-assign (routes to least-loaded member of the suggested role)
   - **Reply** — type a response; it's saved as a message and (if Outlook-linked) sent as an email reply maintaining the thread
5. **Team** page shows all members with role cards, ticket load indicators, and admin controls for creating/editing users

### Key UI Elements

- **Status badges**: Color-coded (blue=open, amber=in progress, purple=waiting, green=resolved, gray=closed)
- **Priority badges**: Green=low, amber=medium, red=high, dark red=urgent
- **AI confidence**: Shown as a percentage bar — higher confidence means the AI is more certain about its categorization
- **Language flags**: Displayed next to ticket subjects in the list view
- **Auto-refresh**: Ticket list refreshes every 30s, ticket detail every 15s (picks up new Outlook replies)

---

## API Reference

All endpoints are prefixed with `/api`. Authentication is via `Authorization: Bearer <jwt_token>` header.

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/auth/login` | Sign in with email/password → returns JWT + user info |
| `GET` | `/auth/me` | Get current authenticated user from token |

### Tickets
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tickets` | List tickets with pagination, filtering (status, category, assignee, search), sorting |
| `GET` | `/tickets/stats` | Dashboard statistics (counts, avg confidence, category breakdown) |
| `GET` | `/tickets/{id}` | Single ticket with all messages and assignee info |
| `PATCH` | `/tickets/{id}` | Update status, priority, category, assignee, tags |
| `POST` | `/tickets/{id}/messages` | Add reply message; auto-sends to Outlook if ticket is email-linked |

### AI
| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/ai/categorize/{id}` | Classify ticket → category, confidence, summary, suggested assignee role |
| `POST` | `/ai/draft/{id}` | Generate response draft in customer's language |
| `POST` | `/ai/translate/{id}` | Translate ticket body to English |
| `POST` | `/ai/translate-text` | Translate arbitrary text to English |
| `POST` | `/ai/enrich/{id}` | Fetch Sentry issues, PostHog recording, user metadata |
| `POST` | `/ai/batch-categorize` | Categorize all uncategorized tickets in one call |

### Users
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/users` | List all user profiles (filterable by role) |
| `GET` | `/users/me` | Current user's profile |
| `GET` | `/users/{id}` | Specific user profile |
| `POST` | `/users` | Create new user — admin only (creates Supabase Auth account + profile) |
| `PATCH` | `/users/{id}` | Update user profile |
| `POST` | `/users/auto-assign` | Auto-assign ticket to least-loaded user of the suggested role |

### Team & Outlook
| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/team` | List active team members |
| `POST` | `/outlook/sync` | Manually trigger email sync |
| `GET` | `/health` | Health check |

Interactive docs available at **http://localhost:8000/docs** (Swagger UI).

---

## AI Pipeline

The AI system has two operating modes, ensuring the platform works with or without an Anthropic API key.

### Mode 1: Claude-Powered (with `ANTHROPIC_API_KEY`)

Uses **Claude Sonnet** (claude-sonnet-4-20250514) via the Anthropic API with YAML-configured prompts.

**Categorization** (`prompts/categorize.yaml`):
- Input: ticket subject + body
- Output: JSON with `category` (one of 19), `confidence` (0–1), `summary` (English), `suggested_assignee_role`, `translated_body` (English)
- Temperature: 0.3 (low variance for consistent classification)

**Draft Response** (`prompts/draft.yaml`):
- Input: ticket body, detected category, customer language, and **enrichment context** (if available)
- Output: JSON with `draft_response` (in customer's language), `confidence`
- The prompt instructs Claude to respond professionally, acknowledge the issue, and provide actionable next steps
- Temperature: 0.3

**Enrichment-Aware Drafting**: When a ticket has been enriched (via the Enrich button), the draft endpoint reads the stored `sentry_issues`, `posthog_recording_url`, and `user_metadata` from the ticket record and assembles them into a human-readable context block. This block is appended to the user message sent to Claude, alongside the ticket body and category. The prompt instructs Claude to use this context to personalize the response — for example:
- If the user is on a free plan, suggest upgrade options; if they're a long-term subscriber, acknowledge their loyalty
- If Sentry errors exist for this user, reference the issue naturally (e.g., "We can see this error has occurred on your account and our engineering team is investigating")
- If a PostHog session recording is available, mention that the team has access to it for faster debugging
- Claude is instructed to **never expose raw internal data** (Sentry URLs, PostHog links, internal IDs) to the customer — the context informs the tone and content, not the wording

This means the recommended workflow is: **Enrich → Categorize → Draft** — enriching first gives Claude the most context to produce an accurate, personalized response.

**Translation** (`prompts/translate.yaml`):
- Input: text in any language
- Output: plain English text (no JSON wrapping)
- Temperature: 0.1 (minimal creativity for translation accuracy)
- Skips if text is already in English

### Mode 2: Heuristic Fallback (no API key)

**Categorization**: Multilingual keyword matching across 17 category keyword maps (e.g., "Rückerstattung" → refund_request, "Karteikarten" → flashcard_issues). Confidence: `min(0.3 + keyword_count × 0.15, 0.8)`.

**Draft Response**: Language-aware templates for common categories (refund, cancellation) in DE/FR/EN. Generic professional template for others. Confidence: 0.5.

**Translation**: Not available without API key (returns null gracefully).

### Assignment Rules

Category-to-role mapping for auto-assignment:

| Categories | Assigned Role |
|-----------|--------------|
| refund_request, subscription_*, billing_invoice | Billing |
| technical_errors, data_loss | Engineering |
| flashcard_issues, quiz_issues, content_upload, account_issues, and others | Support |

Auto-assign picks the **least-loaded** member of the target role (respecting `max_open_tickets` capacity).

---

## Outlook Integration

### How It Works

The platform maintains **bidirectional parity** with Outlook email threads:

**Inbound (Outlook → Platform):**
1. A background async loop polls the shared mailbox every 15 seconds via Microsoft Graph API
2. New unread emails are fetched and deduplicated by `outlook_message_id`
3. If an email's `conversation_id` matches an existing ticket → it's appended as a new message (and the ticket is reopened if it was resolved/closed)
4. If no match → a new ticket is created with the email as the first message
5. The email is marked as read to prevent re-processing

**Outbound (Platform → Outlook):**
1. When an agent sends a reply on a ticket that has an `outlook_message_id`, the platform calls `POST /messages/{id}/reply` on the Graph API
2. This creates the reply **within the original Outlook thread**, so the customer sees a normal email reply
3. The reply is also stored as a message in the platform

### Mock Mode

Without Microsoft credentials, a `MockOutlookService` simulates realistic email arrival:
- 7 sample emails delivered across 4 batches (simulating drip-feed arrival)
- Multilingual samples (DE, FR, EN) including follow-ups to existing conversations
- Emails are marked as "read" after processing, just like the real service

### Enabling Real Outlook Sync

1. Register an app in **Azure AD** (portal.azure.com → App registrations)
2. Grant **Application permissions**: `Mail.ReadWrite`, `Mail.Send`
3. Admin consent for the permissions
4. Set the four `MS_*` variables in `.env`

---

## Enrichment Pipeline

The enrichment system pulls context from three internal data sources to give agents full visibility:

| Source | What It Provides | MVP Behavior |
|--------|-----------------|-------------|
| **Sentry** | Recent exceptions associated with the user's email — error title, level, count, first/last seen | Returns 0–2 realistic mock errors |
| **PostHog** | Session recording URL for the user's most recent session | Generates a plausible recording URL from email hash |
| **User Database** | Subscription plan, account status, activity dates, deck count, locale | Returns mock user profile with realistic data |

In production, replace the mock implementations in `enrichment_service.py` with real API calls — the query patterns and expected response formats are documented inline.

Enrichment data is stored on the ticket record (`sentry_issues`, `posthog_recording_url`, `user_metadata`) and displayed in the ticket detail sidebar.

---

## Database Schema

Three tables in Supabase (PostgreSQL), with Row Level Security enabled:

### `user_profiles`
Extends Supabase Auth users with app-specific data. PK is `auth.users.id`.

| Column | Type | Description |
|--------|------|-------------|
| id | UUID (PK, FK → auth.users) | Supabase Auth user ID |
| display_name | VARCHAR(100) | Displayed in UI |
| role | user_role enum | admin, support, billing, engineering |
| department | VARCHAR(100) | Optional department label |
| is_active | BOOLEAN | Whether user can receive assignments |
| max_open_tickets | INTEGER | Capacity limit for auto-assign (default: 20) |

### `tickets`
Core ticket record with AI and enrichment fields.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Auto-incrementing ticket ID |
| subject, body | TEXT | Customer's message |
| sender_email, sender_name | VARCHAR | Customer identity |
| status | ticket_status enum | open, in_progress, waiting, resolved, closed |
| priority | ticket_priority enum | low, medium, high, urgent |
| category | ticket_category enum | 19 categories (see below) |
| language | VARCHAR(10) | Detected language code |
| translated_body | TEXT | English translation (if translated) |
| assignee_id | UUID (FK → auth.users) | Assigned team member |
| ai_category, ai_confidence, ai_summary | — | AI classification results |
| ai_draft_response | TEXT | AI-generated draft reply |
| ai_suggested_assignee | VARCHAR | Suggested role (billing/engineering/support) |
| sentry_issues, posthog_recording_url, user_metadata | TEXT/JSON | Enrichment data |
| outlook_conversation_id, outlook_message_id | VARCHAR | Outlook thread linking |

**19 Ticket Categories**: refund_request, subscription_cancellation, subscription_info, billing_invoice, flashcard_issues, quiz_issues, podcast_issues, summary_issues, mindmap_issues, mock_exam_issues, content_upload, technical_errors, account_issues, language_issues, general_how_to, data_loss, misunderstanding, garbage, other

### `messages`
Conversation thread entries linked to tickets.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL (PK) | Message ID |
| ticket_id | INTEGER (FK → tickets) | Parent ticket |
| sender_type | VARCHAR | "customer" or "agent" |
| body | TEXT | Message content |
| is_ai_draft | BOOLEAN | Whether this was AI-generated |
| outlook_message_id | VARCHAR | For deduplication with Outlook sync |

### Security

- **Row Level Security** is enabled on all tables
- Authenticated users can read all records (team members need visibility across tickets)
- Users can only update their own profile
- Service role (backend) has full access for admin operations

---

## Design Decisions & Trade-offs

### 1. Supabase Over Self-Hosted PostgreSQL
**Decision**: Use Supabase as a managed backend-as-a-service instead of raw PostgreSQL + custom auth.

**Why**: Supabase gives us PostgreSQL + Auth + RLS + REST API in one managed service. This eliminated the need to build JWT infrastructure, connection pooling (PgBouncer), user management endpoints, and password hashing. The `service_role` key lets the backend bypass RLS for admin operations while the RLS policies protect data at the database level.

**Trade-off**: Vendor lock-in to Supabase's API conventions. Mitigated by using standard SQL for the schema — migration to raw Postgres would only require replacing `supabase-py` calls with an ORM.

### 2. No ORM — Direct Supabase Client
**Decision**: Use `supabase-py` (PostgREST) directly instead of SQLAlchemy/Prisma.

**Why**: The PostgREST client handles filtering, pagination, and joins declaratively. Adding an ORM would mean maintaining two data layers (ORM models + Supabase client) for no benefit. The `db_service.py` module provides a clean function-based abstraction over all queries.

**Trade-off**: No type-safe query building, no automatic migrations. Acceptable for an MVP with a stable schema.

### 3. Claude Sonnet with Heuristic Fallback
**Decision**: Default to working without an API key; Claude enhances but isn't required.

**Why**: An MVP that requires an API key to function is fragile. The heuristic fallback (keyword matching + templates) ensures the platform is usable immediately. When Claude is available, it provides significantly better multilingual categorization and natural-sounding responses.

**Trade-off**: Heuristic accuracy is lower (~60–70% vs Claude's ~90%+), and template responses are generic. But the platform is always functional.

### 4. Background Polling Over Webhooks for Outlook
**Decision**: Poll the mailbox every 15 seconds instead of using Microsoft Graph webhooks (subscription notifications).

**Why**: Webhooks require a publicly accessible HTTPS endpoint with a valid SSL certificate, plus webhook lifecycle management (creation, renewal every 3 days, validation). For an MVP running on localhost, polling is simpler and equally effective.

**Trade-off**: 15-second delay on incoming emails (vs near-instant with webhooks), and wasted API calls when no new email exists. Both are acceptable for an internal tool.

### 5. Mock Enrichment Services
**Decision**: Mock Sentry, PostHog, and user DB lookups instead of requiring real credentials.

**Why**: The enrichment UI and data flow are fully functional — the only difference is where the data comes from. Requiring three additional API keys would make setup prohibitive for evaluation. The mock implementations return realistic data structures that match what the real APIs would provide.

**Trade-off**: Can't demonstrate real enrichment data. The mock code documents the exact API calls and query patterns needed for production.

### 6. Vue 3 Over React/Next.js
**Decision**: Vue 3 with composition API and plain CSS.

**Why**: Vue's single-file components (template + script + style) are self-contained and readable. The composition API provides React-like reactivity without JSX. For an internal tool with 6 views, Vue's lower boilerplate (no `useState`/`useEffect` ceremony) speeds up development.

**Trade-off**: Smaller ecosystem than React. Not a concern for an internal tool with no complex state management needs.

### 7. Monolithic Backend Over Microservices
**Decision**: Single FastAPI process handles API routes, AI calls, email sync, and enrichment.

**Why**: Microservices add deployment complexity (service discovery, inter-service auth, distributed tracing) without benefit at this scale. The background email sync runs as an asyncio task within the same process. FastAPI's async architecture handles concurrent requests efficiently.

**Trade-off**: A slow AI call could theoretically block other requests. Mitigated by Python's async/await — AI calls are non-blocking I/O.

---

