-- Studyflash Support Platform - Initial Schema

-- ============================================================
-- Enum types
-- ============================================================

CREATE TYPE ticket_status AS ENUM ('open', 'in_progress', 'waiting', 'resolved', 'closed');
CREATE TYPE ticket_priority AS ENUM ('low', 'medium', 'high', 'urgent');
CREATE TYPE ticket_category AS ENUM (
    'refund_request', 'subscription_cancellation', 'subscription_info', 'billing_invoice',
    'flashcard_issues', 'quiz_issues', 'podcast_issues', 'summary_issues',
    'mindmap_issues', 'mock_exam_issues', 'content_upload', 'technical_errors',
    'account_issues', 'language_issues', 'general_how_to', 'data_loss',
    'misunderstanding', 'garbage', 'other'
);
CREATE TYPE user_role AS ENUM ('admin', 'support', 'billing', 'engineering');

-- ============================================================
-- Tables
-- ============================================================

-- User profiles (extends Supabase Auth users with app-specific data)
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name VARCHAR(100) NOT NULL DEFAULT '',
    role user_role NOT NULL DEFAULT 'support',
    department VARCHAR(100),
    phone VARCHAR(50),
    avatar_url VARCHAR(500),
    bio TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    max_open_tickets INTEGER NOT NULL DEFAULT 20,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tickets
CREATE TABLE tickets (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(100) UNIQUE,
    outlook_conversation_id VARCHAR(500),
    outlook_message_id VARCHAR(500),

    subject VARCHAR(500) NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    sender_email VARCHAR(200) NOT NULL DEFAULT '',
    sender_name VARCHAR(200) NOT NULL DEFAULT '',
    source VARCHAR(20) NOT NULL DEFAULT 'email',

    status ticket_status NOT NULL DEFAULT 'open',
    priority ticket_priority NOT NULL DEFAULT 'medium',
    category ticket_category,
    tags VARCHAR(500) NOT NULL DEFAULT '',

    language VARCHAR(10) NOT NULL DEFAULT 'en',
    translated_body TEXT,

    assignee_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,

    ai_category VARCHAR(50),
    ai_summary TEXT,
    ai_draft_response TEXT,
    ai_confidence FLOAT,
    ai_suggested_assignee VARCHAR(100),

    sentry_issues TEXT,
    posthog_recording_url VARCHAR(500),
    user_metadata TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Messages (conversation thread)
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,

    sender_type VARCHAR(20) NOT NULL,
    sender_name VARCHAR(200) NOT NULL DEFAULT '',
    sender_email VARCHAR(200) NOT NULL DEFAULT '',
    body TEXT NOT NULL,
    outlook_message_id VARCHAR(500),

    is_ai_draft BOOLEAN NOT NULL DEFAULT FALSE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- Indexes
-- ============================================================

CREATE INDEX idx_user_profiles_role ON user_profiles(role);
CREATE INDEX idx_user_profiles_active ON user_profiles(is_active);

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_category ON tickets(category);
CREATE INDEX idx_tickets_assignee ON tickets(assignee_id);
CREATE INDEX idx_tickets_created ON tickets(created_at DESC);
CREATE INDEX idx_tickets_external_id ON tickets(external_id);

CREATE INDEX idx_messages_ticket ON messages(ticket_id);
CREATE INDEX idx_messages_created ON messages(created_at);

-- ============================================================
-- Triggers
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tickets_updated_at
    BEFORE UPDATE ON tickets
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER user_profiles_updated_at
    BEFORE UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- Row Level Security
-- ============================================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

-- User profiles
CREATE POLICY "Authenticated users can read profiles"
    ON user_profiles FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Users can update own profile"
    ON user_profiles FOR UPDATE
    TO authenticated
    USING (auth.uid() = id);

CREATE POLICY "Service role full access"
    ON user_profiles FOR ALL
    TO service_role
    USING (TRUE);

-- Tickets
CREATE POLICY "Authenticated users can read tickets"
    ON tickets FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Authenticated users can update tickets"
    ON tickets FOR UPDATE
    TO authenticated
    USING (TRUE);

CREATE POLICY "Authenticated users can insert tickets"
    ON tickets FOR INSERT
    TO authenticated
    WITH CHECK (TRUE);

CREATE POLICY "Service role full access"
    ON tickets FOR ALL
    TO service_role
    USING (TRUE);

-- Messages
CREATE POLICY "Authenticated users can read messages"
    ON messages FOR SELECT
    TO authenticated
    USING (TRUE);

CREATE POLICY "Authenticated users can insert messages"
    ON messages FOR INSERT
    TO authenticated
    WITH CHECK (TRUE);

CREATE POLICY "Service role full access"
    ON messages FOR ALL
    TO service_role
    USING (TRUE);
