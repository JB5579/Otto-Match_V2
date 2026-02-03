-- Market Data Schema for Otto.AI
-- Extends existing vehicle schema with market intelligence

-- Add market data columns to existing vehicle_listings table
ALTER TABLE vehicle_listings
ADD COLUMN IF NOT EXISTS market_price_min DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS market_price_max DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS market_price_average DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS days_on_market_average INTEGER,
ADD COLUMN IF NOT EXISTS regional_multiplier DECIMAL(5,3) DEFAULT 1.000,
ADD COLUMN IF NOT EXISTS demand_indicator VARCHAR(20) CHECK (demand_indicator IN ('High', 'Medium', 'Low')),
ADD COLUMN IF NOT EXISTS price_competitiveness VARCHAR(20) CHECK (price_competitiveness IN ('Above', 'At', 'Below')),
ADD COLUMN IF NOT EXISTS market_confidence_score DECIMAL(3,2) CHECK (market_confidence_score >= 0.0 AND market_confidence_score <= 1.0),
ADD COLUMN IF NOT EXISTS market_data_source VARCHAR(50) DEFAULT 'synthetic',
ADD COLUMN IF NOT EXISTS market_data_updated_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS price_savings_amount DECIMAL(12,2),
ADD COLUMN IF NOT EXISTS price_savings_percentage DECIMAL(5,2);

-- Create market_data_updates table for tracking price changes over time
CREATE TABLE IF NOT EXISTS market_data_updates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    update_type VARCHAR(20) CHECK (update_type IN ('initial', 'price_change', 'market_shift', 'correction')),
    old_price_min DECIMAL(12,2),
    old_price_max DECIMAL(12,2),
    new_price_min DECIMAL(12,2),
    new_price_max DECIMAL(12,2),
    price_change_percent DECIMAL(5,2),
    demand_change VARCHAR(20) CHECK (demand_change IN ('increased', 'decreased', 'stable')),
    confidence_score_change DECIMAL(3,2),
    data_source VARCHAR(50),
    external_api_response JSONB,  -- Store raw API response for debugging
    processing_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    notes TEXT
);

-- Create market_data_api_calls table for tracking API usage and limits
CREATE TABLE IF NOT EXISTS market_data_api_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_source VARCHAR(50) NOT NULL,
    endpoint VARCHAR(200) NOT NULL,
    request_params JSONB,
    response_status INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN DEFAULT FALSE,
    error_message TEXT,
    rate_limit_remaining INTEGER,
    rate_limit_reset TIMESTAMP WITH TIME ZONE,
    vehicle_count INTEGER,  -- Number of vehicles processed in this call
    cost_estimate DECIMAL(10,4) DEFAULT 0.00,  -- Estimated cost in USD
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create market_data_cache table for expensive API calls
CREATE TABLE IF NOT EXISTS market_data_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cache_key VARCHAR(200) UNIQUE NOT NULL,  -- Composite key: make_model_year_region
    make VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    region VARCHAR(50),
    market_data JSONB NOT NULL,
    confidence_score DECIMAL(3,2),
    data_source VARCHAR(50),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_accessed TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    access_count INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_vehicle_listings_market_data
ON vehicle_listings(market_data_updated_at DESC)
WHERE market_data_updated_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_vehicle_listings_price_competitiveness
ON vehicle_listings(price_competitiveness);

CREATE INDEX IF NOT EXISTS idx_vehicle_listings_demand_indicator
ON vehicle_listings(demand_indicator);

CREATE INDEX IF NOT EXISTS idx_market_data_updates_vehicle_created
ON market_data_updates(vehicle_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_api_calls_created
ON market_data_api_calls(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_api_calls_success
ON market_data_api_calls(success, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_market_data_cache_expires
ON market_data_cache(expires_at);

-- Create index on cache key for lookups
CREATE INDEX IF NOT EXISTS idx_market_data_cache_key
ON market_data_cache(cache_key);

-- Function to calculate price savings
CREATE OR REPLACE FUNCTION calculate_price_savings()
RETURNS TRIGGER AS $$
BEGIN
    -- Calculate savings amount and percentage
    IF NEW.market_price_average IS NOT NULL AND NEW.price IS NOT NULL THEN
        NEW.price_savings_amount = GREATEST(0, NEW.market_price_average - NEW.price);

        IF NEW.market_price_average > 0 THEN
            NEW.price_savings_percentage = (NEW.price_savings_amount / NEW.market_price_average) * 100;
        ELSE
            NEW.price_savings_percentage = 0;
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically calculate price savings
CREATE TRIGGER trigger_calculate_price_savings
    BEFORE INSERT OR UPDATE ON vehicle_listings
    FOR EACH ROW
    EXECUTE FUNCTION calculate_price_savings();

-- Function to log market data changes
CREATE OR REPLACE FUNCTION log_market_data_change()
RETURNS TRIGGER AS $$
BEGIN
    -- Only log if market prices actually changed
    IF OLD.market_price_min IS DISTINCT FROM NEW.market_price_min OR
       OLD.market_price_max IS DISTINCT FROM NEW.market_price_max THEN

        INSERT INTO market_data_updates (
            vehicle_id,
            update_type,
            old_price_min,
            old_price_max,
            new_price_min,
            new_price_max,
            price_change_percent,
            data_source,
            notes
        ) VALUES (
            NEW.id,
            CASE
                WHEN OLD.market_price_min IS NULL THEN 'initial'
                ELSE 'price_change'
            END,
            OLD.market_price_min,
            OLD.market_price_max,
            NEW.market_price_min,
            NEW.market_price_max,
            CASE
                WHEN OLD.market_price_min IS NOT NULL AND OLD.market_price_min > 0
                THEN ((NEW.market_price_min - OLD.market_price_min) / OLD.market_price_min) * 100
                ELSE 0
            END,
            NEW.market_data_source,
            'Automatic market data update'
        );
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to log market data changes
CREATE TRIGGER trigger_log_market_data_change
    AFTER UPDATE ON vehicle_listings
    FOR EACH ROW
    WHEN (OLD.market_price_min IS DISTINCT FROM NEW.market_price_min OR
          OLD.market_price_max IS DISTINCT FROM NEW.market_price_max)
    EXECUTE FUNCTION log_market_data_change();

-- View for market data analytics
CREATE OR REPLACE VIEW market_data_analytics AS
SELECT
    COUNT(*) as total_vehicles,
    AVG(price_savings_amount) as avg_savings,
    AVG(price_savings_percentage) as avg_savings_percent,
    COUNT(CASE WHEN demand_indicator = 'High' THEN 1 END) as high_demand_count,
    COUNT(CASE WHEN demand_indicator = 'Medium' THEN 1 END) as medium_demand_count,
    COUNT(CASE WHEN demand_indicator = 'Low' THEN 1 END) as low_demand_count,
    COUNT(CASE WHEN price_competitiveness = 'Below' THEN 1 END) as below_market_count,
    COUNT(CASE WHEN price_competitiveness = 'At' THEN 1 END) as at_market_count,
    COUNT(CASE WHEN price_competitiveness = 'Above' THEN 1 END) as above_market_count,
    AVG(market_confidence_score) as avg_confidence_score,
    MAX(market_data_updated_at) as last_update
FROM vehicle_listings
WHERE market_data_updated_at IS NOT NULL;

-- View for API usage monitoring
CREATE OR REPLACE VIEW api_usage_summary AS
SELECT
    api_source,
    DATE(created_at) as call_date,
    COUNT(*) as total_calls,
    COUNT(CASE WHEN success THEN 1 END) as successful_calls,
    AVG(response_time_ms) as avg_response_time,
    SUM(cost_estimate) as total_cost,
    MAX(rate_limit_remaining) as lowest_rate_limit
FROM market_data_api_calls
GROUP BY api_source, DATE(created_at)
ORDER BY call_date DESC, api_source;

-- Function to clean up expired cache entries
CREATE OR REPLACE FUNCTION cleanup_expired_cache()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM market_data_cache
    WHERE expires_at < NOW();

    GET DIAGNOSTICS deleted_count = ROW_COUNT;

    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Comment on tables for documentation
COMMENT ON TABLE vehicle_listings IS 'Extended with market data fields for pricing intelligence and market analysis';
COMMENT ON TABLE market_data_updates IS 'Tracks price changes and market data history for analytics';
COMMENT ON TABLE market_data_api_calls IS 'Logs all external API calls for monitoring and cost tracking';
COMMENT ON TABLE market_data_cache IS 'Caches expensive API calls to improve performance and reduce costs';