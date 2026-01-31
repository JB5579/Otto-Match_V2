-- Otto.AI Conversation History Database Schema
-- Supabase PostgreSQL schema for conversation history, session summaries, and GDPR compliance
-- Integrates with Zep Cloud for temporal memory and supports guest user sessions

-- Extensions (should already exist, but ensure they're available)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =================================================================
-- CONVERSATION HISTORY TABLE
-- =================================================================
-- Stores conversation summaries and metadata for historical tracking
-- Full conversation dialogue stored in Zep Cloud, this stores indexes and summaries
CREATE TABLE IF NOT EXISTS conversation_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification (guest or authenticated)
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,  -- NULL for guest users
    session_id VARCHAR(255) NOT NULL,  -- Zep session ID (for both guest and auth users)

    -- Conversation identification
    zep_conversation_id VARCHAR(255) NOT NULL,  -- Maps to Zep Cloud conversation/session

    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_message_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    conversation_date DATE NOT NULL DEFAULT CURRENT_DATE,

    -- Summary and analytics
    title VARCHAR(500),  -- Auto-generated title from conversation topic
    summary TEXT,  -- AI-generated conversation summary
    message_count INTEGER DEFAULT 0,  -- Total messages in conversation

    -- User preferences (extracted from conversation)
    preferences_json JSONB DEFAULT '{}',  -- Structured preference data
    -- Example: {"budget": "under $30000", "vehicle_types": ["SUV", "crossover"], "brands": ["Toyota", "Honda"]}

    -- Vehicles discussed
    vehicles_discussed JSONB DEFAULT '[]',  -- Array of vehicles mentioned
    -- Example: [{"make": "Toyota", "model": "RAV4", "year": 2023, "relevance_score": 0.95}]

    -- Journey tracking
    journey_stage VARCHAR(50) DEFAULT 'discovery',  -- discovery, consideration, decision, purchased
    evolution_detected BOOLEAN DEFAULT FALSE,  -- True if preferences changed during conversation

    -- Data retention and GDPR
    retention_days INTEGER DEFAULT 90,  -- User-configurable retention period
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '90 days'),
    is_marked_for_deletion BOOLEAN DEFAULT FALSE,

    -- Export and access tracking
    last_exported_at TIMESTAMP WITH TIME ZONE,
    export_count INTEGER DEFAULT 0,

    -- Privacy controls
    is_sensitive BOOLEAN DEFAULT FALSE,  -- Mark sensitive conversations
    user_can_delete BOOLEAN DEFAULT TRUE,  -- GDPR right to deletion

    -- Status and metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =================================================================
-- CONVERSATION MESSAGES TABLE (Optional - for caching/faster access)
-- =================================================================
-- Caches messages from Zep for faster access and full-text search
-- Full source of truth remains Zep Cloud
CREATE TABLE IF NOT EXISTS conversation_messages_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Reference to conversation history
    conversation_history_id UUID NOT NULL REFERENCES conversation_history(id) ON DELETE CASCADE,

    -- Message details (mirrored from Zep)
    zep_message_id VARCHAR(255),  -- Zep message UUID for synchronization
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),

    -- Message content
    content TEXT NOT NULL,

    -- Metadata
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Search optimization
    content_tsv TSVECTOR GENERATED ALWAYS AS (to_tsvector('english', coalesce(content, ''))) STORED
);

-- =================================================================
-- CONVERSATION EXPORTS TABLE
-- =================================================================
-- Tracks conversation exports for GDPR compliance and audit trail
CREATE TABLE IF NOT EXISTS conversation_exports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    session_id VARCHAR(255),  -- For guest users

    -- Export details
    export_type VARCHAR(20) NOT NULL CHECK (export_type IN ('pdf', 'json', 'full_gdpr')),
    conversation_ids UUID[] DEFAULT '{}',  -- Specific conversations exported (empty = all)

    -- Export metadata
    file_path TEXT,  -- Storage path for exported file
    file_size_bytes INTEGER,
    download_count INTEGER DEFAULT 0,
    last_downloaded_at TIMESTAMP WITH TIME ZONE,

    -- GDPR tracking
    request_type VARCHAR(50) DEFAULT 'user_request',  -- user_request, automated, gdpr_request
    gdpr_request_id VARCHAR(255),  -- Reference to formal GDPR data request

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days')  -- Auto-delete exports after 30 days
);

-- =================================================================
-- CONVERSATION PREFERENCES TABLE (For analytics and personalization)
-- =================================================================
-- Tracks preference evolution over time across all conversations
CREATE TABLE IF NOT EXISTS conversation_preferences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    session_id VARCHAR(255),  -- For guest users (denormalized for faster queries)

    -- Preference category and key
    category VARCHAR(50) NOT NULL,  -- budget, vehicle_type, brand, features, lifestyle
    preference_key VARCHAR(100) NOT NULL,  -- max_price, SUV, Toyota, leather_seats, family_of_4

    -- Preference value and confidence
    preference_value JSONB NOT NULL,  -- Flexible storage for different value types
    confidence_score DECIMAL(3,2) DEFAULT 0.50 CHECK (confidence_score >= 0 AND confidence_score <= 1),

    -- Source and tracking
    source_conversation_id UUID REFERENCES conversation_history(id) ON DELETE SET NULL,
    first_detected_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_confirmed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    confirmation_count INTEGER DEFAULT 1,  -- How many times this preference was mentioned

    -- Evolution tracking
    is_active BOOLEAN DEFAULT TRUE,  -- False if preference changed/revoked
    replaced_by_preference_id UUID REFERENCES conversation_preferences(id),  -- Preference evolution chain

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Unique constraint per user/session + category + key
    CONSTRAINT unique_active_preference UNIQUE (user_id, session_id, category, preference_key)
        WHERE is_active = TRUE
);

-- =================================================================
-- DATA RETENTION POLICIES TABLE
-- =================================================================
-- User-configurable data retention settings
CREATE TABLE IF NOT EXISTS data_retention_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- User identification
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,

    -- Retention settings
    default_retention_days INTEGER DEFAULT 90 CHECK (default_retention_days IN (30, 90, 180, 730, 0)),  -- 0 = indefinite
    auto_delete_enabled BOOLEAN DEFAULT TRUE,
    delete_on_account_closure BOOLEAN DEFAULT TRUE,

    -- Privacy settings
    allow_anonymous_usage BOOLEAN DEFAULT FALSE,  -- Allow using conversations for improving AI
    share_conversations_with_sellers BOOLEAN DEFAULT FALSE,

    -- Audit trail
    last_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_by VARCHAR(100) DEFAULT 'user',  -- user, admin, system

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =================================================================
-- INDEXES FOR PERFORMANCE
-- =================================================================

-- Conversation history indexes
CREATE INDEX idx_conversation_history_user ON conversation_history(user_id, last_message_at DESC);
CREATE INDEX idx_conversation_history_session ON conversation_history(session_id, last_message_at DESC);
CREATE INDEX idx_conversation_history_date ON conversation_history(conversation_date DESC);
CREATE INDEX idx_conversation_history_status ON conversation_history(status);
CREATE INDEX idx_conversation_history_expires ON conversation_history(expires_at);
CREATE INDEX idx_conversation_history_journey_stage ON conversation_history(journey_stage);

-- Full-text search on conversation summaries
CREATE INDEX idx_conversation_summary_search ON conversation_history USING GIN(
    to_tsvector('english', COALESCE(summary, '') || ' ' || COALESCE(title, ''))
);

-- JSONB indexes for filtering
CREATE INDEX idx_conversation_preferences_json ON conversation_history USING GIN(preferences_json);
CREATE INDEX idx_conversation_vehicles_json ON conversation_history USING GIN(vehicles_discussed);

-- Conversation messages cache indexes
CREATE INDEX idx_conversation_messages_history ON conversation_messages_cache(conversation_history_id, created_at);
CREATE INDEX idx_conversation_messages_content ON conversation_messages_cache USING GIN(content_tsv);

-- Conversation exports indexes
CREATE INDEX idx_conversation_exports_user ON conversation_exports(user_id, created_at DESC);
CREATE INDEX idx_conversation_exports_session ON conversation_exports(session_id, created_at DESC);

-- Conversation preferences indexes
CREATE INDEX idx_conversation_prefs_user ON conversation_preferences(user_id, is_active, last_confirmed_at DESC);
CREATE INDEX idx_conversation_prefs_session ON conversation_preferences(session_id, is_active, last_confirmed_at DESC);
CREATE INDEX idx_conversation_prefs_category ON conversation_preferences(category, is_active);

-- Data retention policies index
CREATE INDEX idx_data_retention_user ON data_retention_policies(user_id);

-- =================================================================
-- FUNCTIONS AND TRIGGERS
-- =================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_conversation_history_updated_at
    BEFORE UPDATE ON conversation_history
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_conversation_preferences_updated_at
    BEFORE UPDATE ON conversation_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to increment message count when new message cached
CREATE OR REPLACE FUNCTION increment_conversation_message_count()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE conversation_history
    SET message_count = message_count + 1,
        last_message_at = NEW.created_at
    WHERE id = NEW.conversation_history_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER increment_message_count_on_new_message
    AFTER INSERT ON conversation_messages_cache
    FOR EACH ROW EXECUTE FUNCTION increment_conversation_message_count();

-- Function to set expiration based on retention policy
CREATE OR REPLACE FUNCTION set_conversation_expiration()
RETURNS TRIGGER AS $$
BEGIN
    -- Set expires_at based on retention_days (0 means indefinite/NULL)
    IF NEW.retention_days = 0 THEN
        NEW.expires_at = NULL;
    ELSE
        NEW.expires_at = NEW.started_at + (NEW.retention_days || ' days')::INTERVAL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_conversation_expiration_on_insert
    BEFORE INSERT ON conversation_history
    FOR EACH ROW EXECUTE FUNCTION set_conversation_expiration();

CREATE TRIGGER set_conversation_expiration_on_update
    BEFORE UPDATE ON conversation_history
    FOR EACH ROW
    WHEN (OLD.retention_days IS DISTINCT FROM NEW.retention_days)
    FOR EACH ROW EXECUTE FUNCTION set_conversation_expiration();

-- Function to handle guest->user session merge
CREATE OR REPLACE FUNCTION merge_guest_conversation_history(target_user_id UUID, guest_session_id VARCHAR(255))
RETURNS INTEGER AS $$
DECLARE
    merged_count INTEGER;
BEGIN
    -- Update all guest conversations to belong to the authenticated user
    UPDATE conversation_history
    SET
        user_id = target_user_id,
        session_id = session_id,  -- Keep same Zep session ID
        metadata = jsonb_set(
            COALESCE(metadata, '{}'),
            '{merged_from_guest}',
            'true'
        )
    WHERE
        user_id IS NULL  -- Was guest
        AND session_id = guest_session_id
        AND status != 'deleted';

    GET DIAGNOSTICS merged_count = ROW_COUNT;

    -- Update conversation preferences
    UPDATE conversation_preferences
    SET
        user_id = target_user_id,
        session_id = session_id
    WHERE
        user_id IS NULL
        AND session_id = guest_session_id;

    -- Update export records
    UPDATE conversation_exports
    SET user_id = target_user_id
    WHERE
        user_id IS NULL
        AND session_id = guest_session_id;

    RETURN merged_count;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- =================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =================================================================

-- Enable RLS on all conversation tables
ALTER TABLE conversation_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_messages_cache ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_exports ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE data_retention_policies ENABLE ROW LEVEL SECURITY;

-- Policy: Users can view their own conversation history (authenticated)
CREATE POLICY "Users can view own conversation history"
    ON conversation_history
    FOR SELECT
    USING (
        user_id = auth.uid()
        OR (user_id IS NULL AND session_id IN (
            -- Allow access to guest sessions tied to current user's browser
            SELECT session_id FROM conversation_history
            WHERE user_id = auth.uid()
            LIMIT 1  -- Simplified - in production, use session cookie mapping
        ))
    );

-- Policy: Users can view conversations from their current session (guest users via session_id)
CREATE POLICY "Users can view session conversations"
    ON conversation_history
    FOR SELECT
    USING (user_id IS NULL);  -- Guest users can see guest conversations

-- Policy: Users can insert their own conversations
CREATE POLICY "Users can insert own conversations"
    ON conversation_history
    FOR INSERT
    WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

-- Policy: Users can update their own conversations
CREATE POLICY "Users can update own conversations"
    ON conversation_history
    FOR UPDATE
    USING (user_id = auth.uid() OR (user_id IS NULL AND session_id = session_id));

-- Policy: Users can delete their own conversations (GDPR right to deletion)
CREATE POLICY "Users can delete own conversations"
    ON conversation_history
    FOR DELETE
    USING (user_id = auth.uid() AND user_can_delete = TRUE);

-- Similar policies for conversation_messages_cache
CREATE POLICY "Users can view own conversation messages"
    ON conversation_messages_cache
    FOR SELECT
    USING (
        conversation_history_id IN (
            SELECT id FROM conversation_history
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );

CREATE POLICY "Users can insert own conversation messages"
    ON conversation_messages_cache
    FOR INSERT
    WITH CHECK (
        conversation_history_id IN (
            SELECT id FROM conversation_history
            WHERE user_id = auth.uid() OR user_id IS NULL
        )
    );

-- Policies for conversation_exports
CREATE POLICY "Users can view own exports"
    ON conversation_exports
    FOR SELECT
    USING (user_id = auth.uid() OR (user_id IS NULL AND session_id = session_id));

CREATE POLICY "Users can insert own exports"
    ON conversation_exports
    FOR INSERT
    WITH CHECK (user_id = auth.uid() OR user_id IS NULL);

-- Policies for conversation_preferences
CREATE POLICY "Users can view own preferences"
    ON conversation_preferences
    FOR SELECT
    USING (user_id = auth.uid() OR user_id IS NULL);

CREATE POLICY "Users can manage own preferences"
    ON conversation_preferences
    FOR ALL
    USING (user_id = auth.uid() OR user_id IS NULL);

-- Policies for data_retention_policies
CREATE POLICY "Users can view own retention policies"
    ON data_retention_policies
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Users can manage own retention policies"
    ON data_retention_policies
    FOR ALL
    USING (user_id = auth.uid());

-- =================================================================
-- VIEWS FOR COMMON QUERIES
-- =================================================================

-- Conversation history summary view (for list display)
CREATE OR REPLACE VIEW conversation_history_summaries AS
SELECT
    ch.id,
    ch.user_id,
    ch.session_id,
    ch.zep_conversation_id,
    ch.title,
    ch.summary,
    ch.started_at,
    ch.last_message_at,
    ch.message_count,
    ch.journey_stage,
    ch.evolution_detected,
    ch.status,

    -- Preference highlights (top 3 preferences)
    (
        SELECT jsonb_agg(DISTINCT jsonb_build_object(
            'category', cp.category,
            'key', cp.preference_key,
            'value', cp.preference_value
        ))
        FROM conversation_preferences cp
        WHERE cp.source_conversation_id = ch.id
        AND cp.is_active = TRUE
        LIMIT 3
    ) AS top_preferences,

    -- Vehicle mentions count
    jsonb_array_length(ch.vehicles_discussed) AS vehicles_mentioned_count,

    -- Expiration info
    ch.retention_days,
    ch.expires_at,

    -- Format for display
    CASE
        WHEN ch.message_count = 1 THEN '1 message'
        ELSE ch.message_count || ' messages'
    END AS message_count_display,

    CASE
        WHEN DATE(ch.started_at) = CURRENT_DATE THEN 'Today'
        WHEN DATE(ch.started_at) = CURRENT_DATE - INTERVAL '1 day' THEN 'Yesterday'
        ELSE TO_CHAR(ch.started_at, 'Mon DD, YYYY')
    END AS date_display

FROM conversation_history ch
WHERE ch.status != 'deleted'
ORDER BY ch.last_message_at DESC;

-- Journey timeline view (for user journey summary)
CREATE OR REPLACE VIEW conversation_journey_timeline AS
SELECT
    COALESCE(ch.user_id, ch.session_id) AS identifier,
    ch.user_id,
    ch.session_id,
    MIN(ch.started_at) AS first_conversation,
    MAX(ch.last_message_at) AS last_conversation,
    COUNT(*) AS total_conversations,
    SUM(ch.message_count) AS total_messages,

    -- Journey stages visited
    jsonb_agg(DISTINCT ch.journey_stage) AS stages_visited,

    -- All vehicles ever discussed
    (
        SELECT jsonb_agg(DISTINCT v)
        FROM conversation_history ch2,
        jsonb_array_elements(ch2.vehicles_discussed) v
        WHERE (ch2.user_id = ch.user_id OR ch2.session_id = ch.session_id)
        AND ch2.status != 'deleted'
    ) AS all_vehicles_discussed,

    -- Current active preferences
    (
        SELECT jsonb_agg(jsonb_build_object(
            'category', category,
            'key', preference_key,
            'value', preference_value,
            'confidence', confidence_score,
            'last_confirmed', last_confirmed_at
        ))
        FROM conversation_preferences
        WHERE (user_id = ch.user_id OR session_id = ch.session_id)
        AND is_active = TRUE
    ) AS active_preferences,

    -- Evolution detected flag
    BOOL_OR(ch.evolution_detected) AS preferences_evolved

FROM conversation_history ch
WHERE ch.status != 'deleted'
GROUP BY COALESCE(ch.user_id, ch.session_id), ch.user_id, ch.session_id
ORDER BY last_conversation DESC;

-- =================================================================
-- COMMENTS AND DOCUMENTATION
-- =================================================================

COMMENT ON TABLE conversation_history IS 'Stores conversation summaries and metadata; full dialogue in Zep Cloud';
COMMENT ON TABLE conversation_messages_cache IS 'Cache of Zep messages for faster access and full-text search';
COMMENT ON TABLE conversation_exports IS 'GDPR-compliant export tracking and audit trail';
COMMENT ON TABLE conversation_preferences IS 'User preference tracking across all conversations for personalization';
COMMENT ON TABLE data_retention_policies IS 'User-configurable data retention and privacy settings';

COMMENT ON COLUMN conversation_history.session_id IS 'Zep session ID; links guest/auth users to conversations';
COMMENT ON COLUMN conversation_history.retention_days IS 'Days before auto-deletion (0 = indefinite)';
COMMENT ON COLUMN conversation_history.preferences_json IS 'Flexible JSON storage for extracted preferences';
COMMENT ON COLUMN conversation_history.vehicles_discussed IS 'Array of vehicles mentioned with relevance scores';

COMMENT ON COLUMN conversation_preferences.preference_value IS 'Flexible JSON for different value types (string, number, object)';
COMMENT ON COLUMN conversation_preferences.replaced_by_preference_id IS 'Forms evolution chain when preferences change';

COMMENT ON VIEW conversation_history_summaries IS 'Optimized view for conversation list display with metadata';
COMMENT ON VIEW conversation_journey_timeline IS 'Aggregated user journey across all conversations';

COMMENT ON FUNCTION merge_guest_conversation_history IS 'Merges guest session data to authenticated user account';
