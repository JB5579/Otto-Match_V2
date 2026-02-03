-- ============================================================
-- OTTO.AI COMPLETE SCHEMA RESET
-- WARNING: This will DELETE all existing data!
-- Run this in Supabase SQL Editor
-- ============================================================

-- Step 1: Drop existing tables (in correct order for foreign keys)
DROP TABLE IF EXISTS vehicle_condition_issues CASCADE;
DROP TABLE IF EXISTS vehicle_images CASCADE;
DROP TABLE IF EXISTS vehicle_listings CASCADE;
DROP TABLE IF EXISTS processing_tasks CASCADE;
DROP TABLE IF EXISTS sellers CASCADE;

-- Drop views
DROP VIEW IF EXISTS vehicle_listing_summaries CASCADE;

-- Drop functions
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Step 2: Ensure extensions are enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- ============================================================
-- VEHICLE LISTINGS TABLE
-- ============================================================
CREATE TABLE vehicle_listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vin VARCHAR(17) UNIQUE NOT NULL,

    -- Vehicle basic information
    year INTEGER NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    trim VARCHAR(100),

    -- Vehicle specifications
    odometer INTEGER NOT NULL DEFAULT 0,
    drivetrain VARCHAR(50) DEFAULT 'Unknown',
    transmission VARCHAR(50) DEFAULT 'Unknown',
    engine TEXT DEFAULT 'Unknown',
    exterior_color VARCHAR(50) DEFAULT 'Unknown',
    interior_color VARCHAR(50) DEFAULT 'Unknown',

    -- Body and additional details
    body_style VARCHAR(50),
    fuel_type VARCHAR(30),
    vehicle_type VARCHAR(30),

    -- Condition information
    condition_score DECIMAL(3,1) DEFAULT 4.0 CHECK (condition_score >= 1 AND condition_score <= 5),
    condition_grade VARCHAR(20) DEFAULT 'Average' CHECK (condition_grade IN ('Clean', 'Average', 'Rough')),

    -- Search and discovery
    description_text TEXT,
    text_embedding vector(1536), -- OpenAI text-embedding-3-large with dimensions=1536

    -- Status and metadata
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'sold', 'reserved', 'inactive')),
    listing_source VARCHAR(30) DEFAULT 'pdf_upload' CHECK (listing_source IN ('pdf_upload', 'manual', 'api', 'import', 'bulk_upload')),
    processing_metadata JSONB DEFAULT '{}',

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Foreign keys (seller_id optional for now)
    seller_id UUID
);

-- Indexes for vehicle_listings
CREATE INDEX idx_vehicle_listings_vin ON vehicle_listings(vin);
CREATE INDEX idx_vehicle_listings_make_model ON vehicle_listings(make, model);
CREATE INDEX idx_vehicle_listings_year ON vehicle_listings(year);
CREATE INDEX idx_vehicle_listings_status ON vehicle_listings(status);
CREATE INDEX idx_vehicle_listings_created_at ON vehicle_listings(created_at DESC);

-- pgvector index for semantic search (HNSW for better performance)
CREATE INDEX idx_vehicle_listings_text_embedding ON vehicle_listings
USING hnsw (text_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================
-- VEHICLE IMAGES TABLE
-- ============================================================
CREATE TABLE vehicle_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    vin VARCHAR(17) NOT NULL,

    -- Image classification
    category VARCHAR(20) NOT NULL CHECK (category IN ('hero', 'carousel', 'detail', 'documentation')),
    vehicle_angle VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    suggested_alt TEXT NOT NULL,

    -- Image quality and analysis
    quality_score INTEGER NOT NULL DEFAULT 5 CHECK (quality_score >= 1 AND quality_score <= 10),
    visible_damage TEXT[] DEFAULT '{}',

    -- File information
    original_filename VARCHAR(255),
    file_format VARCHAR(10) NOT NULL DEFAULT 'jpeg',
    file_size_bytes INTEGER,
    width INTEGER,
    height INTEGER,

    -- Storage URLs (for future cloud storage)
    original_url TEXT,
    web_url TEXT,
    thumbnail_url TEXT,
    detail_url TEXT,

    -- Embedding for visual search
    image_embedding vector(1536),

    -- Processing metadata
    page_number INTEGER,
    processing_metadata JSONB DEFAULT '{}',
    display_order INTEGER DEFAULT 0,

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for vehicle_images
CREATE INDEX idx_vehicle_images_listing_id ON vehicle_images(listing_id);
CREATE INDEX idx_vehicle_images_vin ON vehicle_images(vin);
CREATE INDEX idx_vehicle_images_category ON vehicle_images(category);
CREATE INDEX idx_vehicle_images_display_order ON vehicle_images(listing_id, display_order);

-- pgvector index for visual search
CREATE INDEX idx_vehicle_images_embedding ON vehicle_images
USING hnsw (image_embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- ============================================================
-- VEHICLE CONDITION ISSUES TABLE
-- ============================================================
CREATE TABLE vehicle_condition_issues (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    listing_id UUID NOT NULL REFERENCES vehicle_listings(id) ON DELETE CASCADE,
    vin VARCHAR(17) NOT NULL,

    -- Issue classification
    issue_category VARCHAR(20) NOT NULL CHECK (issue_category IN ('exterior', 'interior', 'mechanical', 'tiresWheels')),
    issue_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'minor' CHECK (severity IN ('minor', 'moderate', 'major', 'critical')),

    -- Issue details
    description TEXT NOT NULL,
    location VARCHAR(100),
    estimated_repair_cost DECIMAL(10,2),

    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for condition issues
CREATE INDEX idx_condition_issues_listing_id ON vehicle_condition_issues(listing_id);
CREATE INDEX idx_condition_issues_vin ON vehicle_condition_issues(vin);
CREATE INDEX idx_condition_issues_category ON vehicle_condition_issues(issue_category);

-- ============================================================
-- PROCESSING TASKS TABLE (for async PDF processing)
-- ============================================================
CREATE TABLE processing_tasks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id VARCHAR(100) UNIQUE NOT NULL,

    -- Task information
    task_type VARCHAR(50) DEFAULT 'pdf_processing',
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'completed', 'failed')),
    progress DECIMAL(5,2) DEFAULT 0 CHECK (progress >= 0 AND progress <= 100),

    -- File information
    original_filename VARCHAR(255) NOT NULL,
    file_size_bytes INTEGER,

    -- Processing details
    processing_metadata JSONB DEFAULT '{}',
    error_message TEXT,

    -- Results (when completed)
    listing_id UUID REFERENCES vehicle_listings(id),
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

-- ============================================================
-- SELLERS TABLE (for future use)
-- ============================================================
CREATE TABLE sellers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seller_name VARCHAR(200) NOT NULL,
    seller_type VARCHAR(20) NOT NULL DEFAULT 'dealer' CHECK (seller_type IN ('dealer', 'private', 'enterprise')),
    email VARCHAR(255),
    phone VARCHAR(50),
    city VARCHAR(100),
    state VARCHAR(50),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================
-- TRIGGERS FOR updated_at
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vehicle_listings_updated_at
    BEFORE UPDATE ON vehicle_listings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_vehicle_images_updated_at
    BEFORE UPDATE ON vehicle_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_condition_issues_updated_at
    BEFORE UPDATE ON vehicle_condition_issues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- RPC FUNCTIONS FOR SEMANTIC SEARCH
-- ============================================================

-- Function to search vehicle listings by text embedding similarity
CREATE OR REPLACE FUNCTION match_vehicle_listings(
    query_embedding vector(1536),
    match_count int DEFAULT 10,
    min_similarity float DEFAULT 0.5
)
RETURNS TABLE (
    id uuid,
    vin varchar,
    year int,
    make varchar,
    model varchar,
    "trim" varchar,
    odometer int,
    exterior_color varchar,
    interior_color varchar,
    condition_score decimal,
    condition_grade varchar,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vl.id,
        vl.vin,
        vl.year,
        vl.make,
        vl.model,
        vl."trim",
        vl.odometer,
        vl.exterior_color,
        vl.interior_color,
        vl.condition_score,
        vl.condition_grade,
        1 - (vl.text_embedding <=> query_embedding) as similarity
    FROM vehicle_listings vl
    WHERE vl.status = 'active'
      AND vl.text_embedding IS NOT NULL
      AND 1 - (vl.text_embedding <=> query_embedding) >= min_similarity
    ORDER BY vl.text_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to search vehicle images by image embedding similarity
CREATE OR REPLACE FUNCTION match_vehicle_images(
    query_embedding vector(1536),
    match_count int DEFAULT 5,
    exclude_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    listing_id uuid,
    vin varchar,
    category varchar,
    vehicle_angle varchar,
    description text,
    thumbnail_url text,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        vi.id,
        vi.listing_id,
        vi.vin,
        vi.category,
        vi.vehicle_angle,
        vi.description,
        vi.thumbnail_url,
        1 - (vi.image_embedding <=> query_embedding) as similarity
    FROM vehicle_images vi
    WHERE vi.image_embedding IS NOT NULL
      AND (exclude_id IS NULL OR vi.id != exclude_id)
    ORDER BY vi.image_embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- ============================================================
-- ROW LEVEL SECURITY (Optional - enable when auth is ready)
-- ============================================================

-- Uncomment these when you're ready to enable RLS:
-- ALTER TABLE vehicle_listings ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE vehicle_images ENABLE ROW LEVEL SECURITY;

-- For now, allow all operations (development mode)
-- In production, you'll want proper RLS policies

-- ============================================================
-- VERIFY SCHEMA
-- ============================================================
SELECT 'Schema reset complete!' as status;

SELECT table_name,
       (SELECT count(*) FROM information_schema.columns WHERE table_name = t.table_name) as column_count
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
  AND table_name IN ('vehicle_listings', 'vehicle_images', 'vehicle_condition_issues', 'processing_tasks', 'sellers')
ORDER BY table_name;
