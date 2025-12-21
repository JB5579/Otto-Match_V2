-- Otto.AI Database Schema
-- Supabase PostgreSQL schema for vehicle listings and image management
-- Integrates with existing pgvector setup for semantic search

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgvector";

-- =================================================================
-- VEHICLE LISTINGS TABLE
-- =================================================================
CREATE TABLE IF NOT EXISTS vehicle_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vin VARCHAR(17) UNIQUE NOT NULL,

    -- Vehicle basic information
    year INTEGER NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    trim VARCHAR(100),

    -- Vehicle specifications
    odometer INTEGER NOT NULL,
    drivetrain VARCHAR(20) NOT NULL,
    transmission VARCHAR(50) NOT NULL,
    engine TEXT NOT NULL,
    exterior_color VARCHAR(50) NOT NULL,
    interior_color VARCHAR(50) NOT NULL,

    -- Body and additional details
    body_style VARCHAR(50),
    fuel_type VARCHAR(20),
    vehicle_type VARCHAR(30),

    -- Condition information
    condition_score DECIMAL(3,1) NOT NULL CHECK (condition_score >= 1 AND condition_score <= 5),
    condition_grade VARCHAR(20) NOT NULL CHECK (condition_grade IN ('Clean', 'Average', 'Rough')),

    -- Search and discovery
    description_text TEXT,
    text_embedding vector(3072), -- OpenAI text-embedding-3-large dimension

    -- Status and metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'reserved', 'inactive')),
    listing_source VARCHAR(20) DEFAULT 'pdf_upload' CHECK (listing_source IN ('pdf_upload', 'manual', 'api', 'import')),
    processing_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign keys
    seller_id UUID REFERENCES users(id) ON DELETE SET NULL,

    -- Constraints
    CONSTRAINT vehicle_listings_vin_format CHECK (vin ~ '^[A-HJ-NPR-Z0-9]{17}$')
);

-- Indexes for vehicle_listings
CREATE INDEX idx_vehicle_listings_vin ON vehicle_listings(vin);
CREATE INDEX idx_vehicle_listings_make_model ON vehicle_listings(make, model);
CREATE INDEX idx_vehicle_listings_year ON vehicle_listings(year);
CREATE INDEX idx_vehicle_listings_price_range ON vehicle_listings(odometer);
CREATE INDEX idx_vehicle_listings_status ON vehicle_listings(status);
CREATE INDEX idx_vehicle_listings_created_at ON vehicle_listings(created_at DESC);

-- pgvector index for semantic search
CREATE INDEX idx_vehicle_listings_text_embedding ON vehicle_listings USING ivfflat (text_embedding vector_cosine_ops) WITH (lists = 100);

-- =================================================================
-- VEHICLE IMAGES TABLE
-- =================================================================
CREATE TABLE IF NOT EXISTS vehicle_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    vin VARCHAR(17) NOT NULL REFERENCES vehicle_listings(vin) ON DELETE CASCADE,

    -- Image information
    category VARCHAR(20) NOT NULL CHECK (category IN ('hero', 'carousel', 'detail', 'documentation')),
    vehicle_angle VARCHAR(30) NOT NULL,
    description TEXT NOT NULL,
    suggested_alt TEXT NOT NULL,

    -- Image quality and metadata
    quality_score INTEGER NOT NULL CHECK (quality_score >= 1 AND quality_score <= 10),
    visible_damage TEXT[] DEFAULT '{}',

    -- File information
    original_filename VARCHAR(255),
    file_format VARCHAR(10) NOT NULL,
    file_size_bytes INTEGER,
    width INTEGER,
    height INTEGER,

    -- Storage URLs (optimized versions)
    original_url TEXT,
    web_url TEXT,
    thumbnail_url TEXT,
    detail_url TEXT,

    -- Embedding for visual search
    image_embedding vector(3072), -- Same dimension as text embeddings for CLIP

    -- Processing metadata
    page_number INTEGER,
    processing_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Ordering
    display_order INTEGER DEFAULT 0
);

-- Indexes for vehicle_images
CREATE INDEX idx_vehicle_images_listing_id ON vehicle_images(listing_id);
CREATE INDEX idx_vehicle_images_vin ON vehicle_images(vin);
CREATE INDEX idx_vehicle_images_category ON vehicle_images(category);
CREATE INDEX idx_vehicle_images_angle ON vehicle_images(vehicle_angle);
CREATE INDEX idx_vehicle_images_quality ON vehicle_images(quality_score DESC);
CREATE INDEX idx_vehicle_images_display_order ON vehicle_images(listing_id, display_order);

-- pgvector index for visual search
CREATE INDEX idx_vehicle_images_embedding ON vehicle_images USING ivfflat (image_embedding vector_cosine_ops) WITH (lists = 100);

-- =================================================================
-- VEHICLE CONDITION ISSUES TABLE
-- =================================================================
CREATE TABLE IF NOT EXISTS vehicle_condition_issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    vin VARCHAR(17) NOT NULL REFERENCES vehicle_listings(vin) ON DELETE CASCADE,

    -- Issue classification
    issue_category VARCHAR(20) NOT NULL CHECK (issue_category IN ('exterior', 'interior', 'mechanical', 'tiresWheels')),
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL CHECK (severity IN ('minor', 'moderate', 'major', 'critical')),

    -- Issue details
    description TEXT NOT NULL,
    location VARCHAR(100),
    estimated_repair_cost DECIMAL(10,2),

    -- Visual evidence
    affected_image_ids UUID[] DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for condition issues
CREATE INDEX idx_condition_issues_listing_id ON vehicle_condition_issues(listing_id);
CREATE INDEX idx_condition_issues_vin ON vehicle_condition_issues(vin);
CREATE INDEX idx_condition_issues_category ON vehicle_condition_issues(issue_category);
CREATE INDEX idx_condition_issues_severity ON vehicle_condition_issues(severity);

-- =================================================================
-- SELLER INFORMATION TABLE
-- =================================================================
CREATE TABLE IF NOT EXISTS sellers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Seller identification
    seller_name VARCHAR(200) NOT NULL,
    seller_type VARCHAR(20) NOT NULL CHECK (seller_type IN ('dealer', 'private', 'enterprise')),

    -- Contact information
    email VARCHAR(255),
    phone VARCHAR(50),
    website VARCHAR(500),

    -- Location
    address TEXT,
    city VARCHAR(100),
    state VARCHAR(50),
    zip_code VARCHAR(20),
    country VARCHAR(50),

    -- Business details (for dealers)
    dealer_license VARCHAR(100),
    business_hours JSONB DEFAULT '{}',

    -- Status and verification
    is_verified BOOLEAN DEFAULT FALSE,
    verification_status VARCHAR(20) DEFAULT 'pending',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for sellers
CREATE INDEX idx_sellers_type ON sellers(seller_type);
CREATE INDEX idx_sellers_verified ON sellers(is_verified);
CREATE INDEX idx_sellers_city ON sellers(city);

-- =================================================================
-- PROCESSING TASKS TABLE (for async PDF processing)
-- =================================================================
CREATE TABLE IF NOT EXISTS processing_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(100) UNIQUE NOT NULL,

    -- Task information
    task_type VARCHAR(50) DEFAULT 'pdf_processing',
    status VARCHAR(20) NOT NULL CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress DECIMAL(5,2) DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),

    -- File information
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes INTEGER,

    -- Processing details
    processing_metadata JSONB DEFAULT '{}',
    error_message TEXT,

    -- Results (when completed)
    listing_id UUID,
    vin VARCHAR(17),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,

    -- TTL for cleanup (30 days)
    expires_at TIMESTAMP WITH TIME ZONE DEFAULT (NOW() + INTERVAL '30 days')
);

-- Indexes for processing tasks
CREATE INDEX idx_processing_tasks_task_id ON processing_tasks(task_id);
CREATE INDEX idx_processing_tasks_status ON processing_tasks(status);
CREATE INDEX idx_processing_tasks_created_at ON processing_tasks(created_at DESC);
CREATE INDEX idx_processing_tasks_expires_at ON processing_tasks(expires_at);

-- =================================================================
-- TRIGGERS AND FUNCTIONS
-- =================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply updated_at triggers to relevant tables
CREATE TRIGGER update_vehicle_listings_updated_at
    BEFORE UPDATE ON vehicle_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicle_images_updated_at
    BEFORE UPDATE ON vehicle_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_condition_issues_updated_at
    BEFORE UPDATE ON vehicle_condition_issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sellers_updated_at
    BEFORE UPDATE ON sellers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- =================================================================

-- Enable RLS on sensitive tables
ALTER TABLE vehicle_listings ENABLE ROW LEVEL SECURITY;
ALTER TABLE vehicle_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE sellers ENABLE ROW LEVEL SECURITY;

-- Policy for vehicle_listings (read access to authenticated users)
CREATE POLICY "Users can view vehicle listings" ON vehicle_listings
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy for vehicle_images (read access to authenticated users)
CREATE POLICY "Users can view vehicle images" ON vehicle_images
    FOR SELECT USING (auth.role() = 'authenticated');

-- Policy for sellers (read access to authenticated users)
CREATE POLICY "Users can view seller info" ON sellers
    FOR SELECT USING (auth.role() = 'authenticated');

-- =================================================================
-- VIEWS FOR COMMON QUERIES
-- =================================================================

-- Vehicle listing summary view (for search results)
CREATE OR REPLACE VIEW vehicle_listing_summaries AS
SELECT
    vl.id AS listing_id,
    vl.vin,
    vl.year,
    vl.make,
    vl.model,
    vl.trim,
    vl.odometer,
    vl.exterior_color,
    vl.interior_color,
    vl.condition_score,
    vl.condition_grade,
    vl.status,
    vl.created_at,
    s.seller_name,
    s.seller_type,
    COALESCE(vi.web_url, vi.thumbnail_url) AS primary_image_url,
    COUNT(vi.id) AS image_count
FROM vehicle_listings vl
LEFT JOIN sellers s ON vl.seller_id = s.id
LEFT JOIN LATERAL (
    SELECT id, web_url, thumbnail_url
    FROM vehicle_images
    WHERE listing_id = vl.id AND category = 'hero'
    LIMIT 1
) vi ON true
WHERE vl.status = 'active'
GROUP BY vl.id, vl.vin, vl.year, vl.make, vl.model, vl.trim, vl.odometer,
         vl.exterior_color, vl.interior_color, vl.condition_score, vl.condition_grade,
         vl.status, vl.created_at, s.seller_name, s.seller_type, vi.web_url, vi.thumbnail_url;

-- =================================================================
-- SAMPLE DATA (for development)
-- =================================================================

-- Insert a sample seller (development only)
INSERT INTO sellers (seller_name, seller_type, email, city, state, is_verified) VALUES
('Otto Motors Demo', 'dealer', 'demo@otto.ai', 'San Francisco', 'CA', TRUE)
ON CONFLICT DO NOTHING;

-- =================================================================
-- COMMENTS AND DOCUMENTATION
-- =================================================================

COMMENT ON TABLE vehicle_listings IS 'Core vehicle listings with full specifications and search embeddings';
COMMENT ON TABLE vehicle_images IS 'Vehicle photos with categorization and visual search embeddings';
COMMENT ON TABLE vehicle_condition_issues IS 'Detailed condition issues extracted from PDF reports';
COMMENT ON TABLE sellers IS 'Seller/dealer information and verification status';
COMMENT ON TABLE processing_tasks IS 'Async processing task tracking for PDF uploads';

COMMENT ON COLUMN vehicle_listings.text_embedding IS 'Text embedding for semantic search using OpenAI text-embedding-3-large';
COMMENT ON COLUMN vehicle_images.image_embedding IS 'Visual embedding for image similarity search using CLIP';

COMMENT ON VIEW vehicle_listing_summaries IS 'Optimized view for search results and listing grids';