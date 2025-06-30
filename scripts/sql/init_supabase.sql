-- =====================================================
-- Twitter Bot Automated - Supabase Database Setup
-- =====================================================

-- Create tweets table
CREATE TABLE IF NOT EXISTS tweets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tweet_id VARCHAR UNIQUE NOT NULL,
    content TEXT NOT NULL,
    image_url VARCHAR,
    posted_at TIMESTAMPTZ DEFAULT NOW(),
    engagement JSONB DEFAULT '{}'::jsonb,
    topics TEXT[],
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create replies table
CREATE TABLE IF NOT EXISTS replies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    reply_id VARCHAR UNIQUE NOT NULL,
    original_tweet_id VARCHAR NOT NULL,
    author_id VARCHAR NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    liked BOOLEAN DEFAULT FALSE,
    liked_at TIMESTAMPTZ,
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create stats table
CREATE TABLE IF NOT EXISTS stats (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tweet_id VARCHAR NOT NULL,
    likes INTEGER DEFAULT 0,
    retweets INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    impressions INTEGER DEFAULT 0,
    engagement_rate DECIMAL(5,4) DEFAULT 0,
    collected_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create configs table
CREATE TABLE IF NOT EXISTS configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key VARCHAR UNIQUE NOT NULL,
    value JSONB NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create quota_tracking table
CREATE TABLE IF NOT EXISTS quota_tracking (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    date DATE DEFAULT CURRENT_DATE,
    posts_used INTEGER DEFAULT 0,
    reads_used INTEGER DEFAULT 0,
    likes_used INTEGER DEFAULT 0,
    plan VARCHAR DEFAULT 'basic',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(date)
);

-- Create performance_metrics table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR NOT NULL,
    metric_value DECIMAL,
    metric_data JSONB,
    recorded_at TIMESTAMPTZ DEFAULT NOW()
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Tweets indexes
CREATE INDEX IF NOT EXISTS idx_tweets_posted_at ON tweets(posted_at DESC);
CREATE INDEX IF NOT EXISTS idx_tweets_tweet_id ON tweets(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweets_topics ON tweets USING GIN(topics);

-- Replies indexes
CREATE INDEX IF NOT EXISTS idx_replies_original_tweet_id ON replies(original_tweet_id);
CREATE INDEX IF NOT EXISTS idx_replies_created_at ON replies(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_replies_liked ON replies(liked);
CREATE INDEX IF NOT EXISTS idx_replies_reply_id ON replies(reply_id);

-- Stats indexes
CREATE INDEX IF NOT EXISTS idx_stats_tweet_id ON stats(tweet_id);
CREATE INDEX IF NOT EXISTS idx_stats_collected_at ON stats(collected_at DESC);

-- Configs indexes
CREATE INDEX IF NOT EXISTS idx_configs_key ON configs(key);

-- Quota tracking indexes
CREATE INDEX IF NOT EXISTS idx_quota_tracking_date ON quota_tracking(date DESC);

-- Performance metrics indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_name_time ON performance_metrics(metric_name, recorded_at DESC);

-- =====================================================
-- Triggers for Updated At
-- =====================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers
CREATE TRIGGER update_tweets_updated_at BEFORE UPDATE ON tweets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_configs_updated_at BEFORE UPDATE ON configs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_quota_tracking_updated_at BEFORE UPDATE ON quota_tracking
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Row Level Security (RLS)
-- =====================================================

-- Enable RLS on all tables
ALTER TABLE tweets ENABLE ROW LEVEL SECURITY;
ALTER TABLE replies ENABLE ROW LEVEL SECURITY;
ALTER TABLE stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE quota_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;

-- Create policies (adjust based on your auth requirements)
-- These policies allow all operations for authenticated users
-- Modify according to your security requirements

CREATE POLICY "Allow all operations for authenticated users" ON tweets
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON replies
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON stats
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON configs
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON quota_tracking
    FOR ALL USING (auth.role() = 'authenticated');

CREATE POLICY "Allow all operations for authenticated users" ON performance_metrics
    FOR ALL USING (auth.role() = 'authenticated');

-- =====================================================
-- Storage Setup
-- =====================================================

-- Create storage bucket for generated images
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES ('generated-images', 'generated-images', true, 52428800, ARRAY['image/jpeg', 'image/png', 'image/webp'])
ON CONFLICT (id) DO NOTHING;

-- Create storage policies
CREATE POLICY "Allow public read access" ON storage.objects
    FOR SELECT USING (bucket_id = 'generated-images');

CREATE POLICY "Allow authenticated upload" ON storage.objects
    FOR INSERT WITH CHECK (bucket_id = 'generated-images' AND auth.role() = 'authenticated');

-- =====================================================
-- Realtime Setup
-- =====================================================

-- Enable realtime for replies table (for auto-liking)
ALTER PUBLICATION supabase_realtime ADD TABLE replies;

-- Enable realtime for performance monitoring
ALTER PUBLICATION supabase_realtime ADD TABLE performance_metrics;

-- =====================================================
-- Initial Data
-- =====================================================

-- Insert default configuration
INSERT INTO configs (key, value, description) VALUES 
('bot_status', '{"active": true, "last_startup": null}', 'Bot operational status'),
('posting_schedule', '{"enabled": true, "last_post": null}', 'Posting schedule status'),
('engagement_settings', '{"auto_like": true, "last_engagement": null}', 'Engagement automation settings')
ON CONFLICT (key) DO NOTHING;

-- Initialize quota tracking for current date
INSERT INTO quota_tracking (date, posts_used, reads_used, likes_used, plan)
VALUES (CURRENT_DATE, 0, 0, 0, 'basic')
ON CONFLICT (date) DO NOTHING;

-- =====================================================
-- Views for Analytics
-- =====================================================

-- Daily stats view
CREATE OR REPLACE VIEW daily_stats AS
SELECT 
    DATE(posted_at) as date,
    COUNT(*) as tweets_posted,
    AVG(COALESCE((engagement->>'likes')::int, 0)) as avg_likes,
    AVG(COALESCE((engagement->>'retweets')::int, 0)) as avg_retweets,
    AVG(COALESCE((engagement->>'replies')::int, 0)) as avg_replies
FROM tweets
WHERE posted_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(posted_at)
ORDER BY date DESC;

-- Top performing tweets view
CREATE OR REPLACE VIEW top_tweets AS
SELECT 
    tweet_id,
    content,
    posted_at,
    (engagement->>'likes')::int as likes,
    (engagement->>'retweets')::int as retweets,
    (engagement->>'replies')::int as replies,
    topics
FROM tweets
WHERE posted_at >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY (engagement->>'likes')::int DESC
LIMIT 10;

-- Engagement rate view
CREATE OR REPLACE VIEW engagement_overview AS
SELECT 
    COUNT(*) as total_tweets,
    AVG(COALESCE((engagement->>'likes')::int, 0)) as avg_likes,
    AVG(COALESCE((engagement->>'retweets')::int, 0)) as avg_retweets,
    AVG(COALESCE((engagement->>'replies')::int, 0)) as avg_replies,
    SUM(COALESCE((engagement->>'likes')::int, 0)) as total_likes,
    SUM(COALESCE((engagement->>'retweets')::int, 0)) as total_retweets,
    COUNT(DISTINCT DATE(posted_at)) as active_days
FROM tweets
WHERE posted_at >= CURRENT_DATE - INTERVAL '30 days';

-- =====================================================
-- Functions for Bot Operations
-- =====================================================

-- Function to update quota usage
CREATE OR REPLACE FUNCTION update_quota_usage(
    operation_type TEXT,
    count_increment INTEGER DEFAULT 1
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO quota_tracking (date, posts_used, reads_used, likes_used)
    VALUES (
        CURRENT_DATE,
        CASE WHEN operation_type = 'post' THEN count_increment ELSE 0 END,
        CASE WHEN operation_type = 'read' THEN count_increment ELSE 0 END,
        CASE WHEN operation_type = 'like' THEN count_increment ELSE 0 END
    )
    ON CONFLICT (date) 
    DO UPDATE SET
        posts_used = quota_tracking.posts_used + CASE WHEN operation_type = 'post' THEN count_increment ELSE 0 END,
        reads_used = quota_tracking.reads_used + CASE WHEN operation_type = 'read' THEN count_increment ELSE 0 END,
        likes_used = quota_tracking.likes_used + CASE WHEN operation_type = 'like' THEN count_increment ELSE 0 END,
        updated_at = NOW();
END;
$$ LANGUAGE plpgsql;

-- Function to get current quota status
CREATE OR REPLACE FUNCTION get_quota_status()
RETURNS TABLE(
    posts_used INTEGER,
    reads_used INTEGER,
    likes_used INTEGER,
    plan VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COALESCE(qt.posts_used, 0) as posts_used,
        COALESCE(qt.reads_used, 0) as reads_used,
        COALESCE(qt.likes_used, 0) as likes_used,
        COALESCE(qt.plan, 'basic') as plan
    FROM quota_tracking qt
    WHERE qt.date = CURRENT_DATE
    UNION ALL
    SELECT 0, 0, 0, 'basic'
    WHERE NOT EXISTS (SELECT 1 FROM quota_tracking WHERE date = CURRENT_DATE)
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Completion Message
-- =====================================================

DO $$
BEGIN
    RAISE NOTICE 'Twitter Bot Automated database setup completed successfully!';
    RAISE NOTICE 'Tables created: tweets, replies, stats, configs, quota_tracking, performance_metrics';
    RAISE NOTICE 'Storage bucket created: generated-images';
    RAISE NOTICE 'Realtime enabled for: replies, performance_metrics';
    RAISE NOTICE 'Views created: daily_stats, top_tweets, engagement_overview';
    RAISE NOTICE 'Functions created: update_quota_usage, get_quota_status';
END $$; 