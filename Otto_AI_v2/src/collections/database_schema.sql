-- Collections Database Schema
-- Story 1.7: Add Curated Vehicle Collections and Categories

-- Main vehicle collections table
CREATE TABLE IF NOT EXISTS vehicle_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    type collection_type NOT NULL DEFAULT 'curated', -- 'curated', 'trending', 'dynamic', 'template'
    criteria JSONB, -- Collection rules and filtering criteria
    sort_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_by VARCHAR(255), -- Admin user ID
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_refreshed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collection-vehicle mapping table (many-to-many)
CREATE TABLE IF NOT EXISTS collection_vehicle_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES vehicle_collections(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    score FLOAT DEFAULT 1.0, -- Relevance score within collection
    rank_position INTEGER, -- Position in ranked results
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(collection_id, vehicle_id)
);

-- Collection analytics table for engagement tracking
CREATE TABLE IF NOT EXISTS collection_analytics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    collection_id UUID REFERENCES vehicle_collections(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL, -- 'view', 'click', 'share', 'filter'
    user_id VARCHAR(255), -- User identifier
    session_id VARCHAR(255),
    metadata JSONB, -- Additional event data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collection templates for predefined collection types
CREATE TABLE IF NOT EXISTS collection_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    template_type VARCHAR(50) NOT NULL, -- 'use_case', 'price_range', 'feature_based', 'seasonal'
    criteria_template JSONB NOT NULL, -- Template criteria with placeholders
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- A/B testing variations for collections
CREATE TABLE IF NOT EXISTS collection_ab_tests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_name VARCHAR(255) NOT NULL,
    collection_id UUID REFERENCES vehicle_collections(id) ON DELETE CASCADE,
    variation_name VARCHAR(255) NOT NULL,
    variation_config JSONB, -- Configuration for this variation
    traffic_split FLOAT DEFAULT 0.5, -- Percentage of traffic (0.0-1.0)
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(test_name, variation_name)
);

-- A/B test results tracking
CREATE TABLE IF NOT EXISTS collection_ab_test_results (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    test_id UUID REFERENCES collection_ab_tests(id) ON DELETE CASCADE,
    user_id VARCHAR(255),
    session_id VARCHAR(255),
    variation_name VARCHAR(255),
    event_type VARCHAR(50), -- 'view', 'click', 'conversion'
    conversion_value FLOAT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for optimal query performance
CREATE INDEX IF NOT EXISTS idx_vehicle_collections_type ON vehicle_collections(type);
CREATE INDEX IF NOT EXISTS idx_vehicle_collections_featured ON vehicle_collections(is_featured, is_active);
CREATE INDEX IF NOT EXISTS idx_vehicle_collections_sort ON vehicle_collections(sort_order, is_active);
CREATE INDEX IF NOT EXISTS idx_vehicle_collections_updated ON vehicle_collections(updated_at);

CREATE INDEX IF NOT EXISTS idx_collection_mappings_collection ON collection_vehicle_mappings(collection_id);
CREATE INDEX IF NOT EXISTS idx_collection_mappings_score ON collection_vehicle_mappings(collection_id, score DESC);
CREATE INDEX IF NOT EXISTS idx_collection_mappings_rank ON collection_vehicle_mappings(collection_id, rank_position);

CREATE INDEX IF NOT EXISTS idx_collection_analytics_collection ON collection_analytics(collection_id, created_at);
CREATE INDEX IF NOT EXISTS idx_collection_analytics_event ON collection_analytics(event_type, created_at);
CREATE INDEX IF NOT EXISTS idx_collection_analytics_user ON collection_analytics(user_id, created_at);

CREATE INDEX IF NOT EXISTS idx_collection_ab_tests_active ON collection_ab_tests(is_active);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_test ON collection_ab_test_results(test_id, variation_name);

-- Create updated_at trigger function (reuse existing if available)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers
CREATE TRIGGER update_vehicle_collections_updated_at
    BEFORE UPDATE ON vehicle_collections
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE vehicle_collections IS 'Main table for curated and dynamic vehicle collections';
COMMENT ON TABLE collection_vehicle_mappings IS 'Many-to-many mapping between collections and vehicles with scoring';
COMMENT ON TABLE collection_analytics IS 'Analytics tracking for collection engagement and user interactions';
COMMENT ON TABLE collection_templates IS 'Predefined templates for generating dynamic collections';
COMMENT ON TABLE collection_ab_tests IS 'A/B testing configuration for collection variations';
COMMENT ON TABLE collection_ab_test_results IS 'Results tracking for A/B testing experiments';

-- Collection types enum
DO $$ BEGIN
    CREATE TYPE collection_type AS ENUM ('curated', 'trending', 'dynamic', 'template');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Collection event types enum
DO $$ BEGIN
    CREATE TYPE collection_event_type AS ENUM ('view', 'click', 'share', 'filter', 'conversion');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Insert default collection templates
INSERT INTO collection_templates (name, description, template_type, criteria_template) VALUES
('Electric Vehicles', 'All electric and plug-in hybrid vehicles', 'feature_based', '{"fuel_type": ["electric", "plug-in_hybrid"]}'),
('Family SUVs', 'Spacious SUVs perfect for families', 'use_case', '{"vehicle_type": "SUV", "seats_min": 7, "safety_rating_min": 4}'),
('Budget Friendly Under $30k', 'Affordable vehicles for budget-conscious buyers', 'price_range', '{"price_max": 30000, "sort_by": "price"}'),
('Luxury Vehicles', 'Premium vehicles with high-end features', 'use_case', '{"price_min": 50000, "features": ["leather", "premium_audio", "navigation"]}'),
('Performance Cars', 'Sports cars and high-performance vehicles', 'feature_based', '{"vehicle_type": ["sports", "coupe", "convertible"], "horsepower_min": 300}'),
('Off-Road Capable', 'Vehicles suitable for off-road adventures', 'use_case', '{"features": ["4wd", "offroad_package"], "ground_clearance_min": 8}'),
('Commuter Friendly', 'Efficient vehicles perfect for daily commuting', 'use_case', '{"fuel_efficiency_min": 30, "vehicle_type": ["sedan", "compact", "hatchback"]}'),
('Winter Ready', 'Vehicles with all-wheel drive for winter conditions', 'seasonal', '{"drive_type": "awd", "features": ["heated_seats", "remote_start"]}')
ON CONFLICT (name) DO NOTHING;