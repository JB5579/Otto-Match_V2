-- Otto.AI Semantic Search Database Schema
-- PostgreSQL with pgvector extension for semantic vehicle search

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enum types for vehicle attributes
CREATE TYPE vehicle_type AS ENUM (
    'sedan', 'suv', 'truck', 'coupe', 'convertible', 'hatchback',
    'minivan', 'pickup', 'van', 'wagon', 'luxury', 'sports', 'electric', 'hybrid'
);

CREATE TYPE fuel_type AS ENUM (
    'gasoline', 'diesel', 'electric', 'hybrid', 'plugin_hybrid', 'flex_fuel'
);

CREATE TYPE transmission_type AS ENUM (
    'manual', 'automatic', 'cvt', 'dual_clutch', 'electric', 'hybrid'
);

CREATE TYPE drivetrain_type AS ENUM (
    'fwd', 'rwd', 'awd', '4wd'
);

CREATE TYPE condition_level AS ENUM (
    'excellent', 'great', 'good', 'fair', 'poor'
);

-- Main vehicles table with vector embeddings
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vin VARCHAR(17) UNIQUE NOT NULL,
    make VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    year INTEGER NOT NULL,
    trim VARCHAR(100),

    -- Vehicle specifications
    vehicle_type vehicle_type NOT NULL,
    fuel_type fuel_type NOT NULL,
    transmission transmission_type,
    drivetrain drivetrain_type,

    -- Engine and performance
    engine_displacement DECIMAL(4,1), -- in liters
    horsepower INTEGER,
    torque INTEGER,

    -- Physical specifications
    exterior_color VARCHAR(50),
    interior_color VARCHAR(50),
    num_doors INTEGER,

    -- Pricing
    price DECIMAL(10,2), -- List price
    msrp DECIMAL(10,2),    -- Manufacturer suggested retail price

    -- Mileage and condition
    mileage INTEGER,
    condition condition_level,

    -- Location
    city VARCHAR(100),
    state VARCHAR(2),
    country VARCHAR(100) DEFAULT 'USA',

    -- Text descriptions for semantic search
    description TEXT,
    features TEXT[], -- Array of vehicle features

    -- Images (stored as URLs or references)
    images TEXT[],

    -- Vector embeddings (3072 dimensions for OpenRouter text-embedding-3-large)
    title_embedding vector(3072),
    description_embedding vector(3072),
    features_embedding vector(3072),

    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    is_available BOOLEAN DEFAULT TRUE
);

-- Create HNSW index for title similarity search (cosine distance)
CREATE INDEX idx_vehicles_title_embedding_cosine ON vehicles
USING hnsw (title_embedding vector_cosine_ops);

-- Create HNSW index for description similarity search (cosine distance)
CREATE INDEX idx_vehicles_description_embedding_cosine ON vehicles
USING hnsw (description_embedding vector_cosine_ops);

-- Create HNSW index for features similarity search (cosine distance)
CREATE INDEX idx_vehicles_features_embedding_cosine ON vehicles
USING hnsw (features_embedding vector_cosine_ops);

-- Create traditional indexes for filtering
CREATE INDEX idx_vehicles_make_model_year ON vehicles (make, model, year);
CREATE INDEX idx_vehicles_price_range ON vehicles (price);
CREATE INDEX idx_vehicles_mileage ON vehicles (mileage);
CREATE INDEX idx_vehicles_location ON vehicles (city, state);
CREATE INDEX idx_vehicles_vehicle_type ON vehicles (vehicle_type);
CREATE INDEX idx_vehicles_fuel_type ON vehicles (fuel_type);
CREATE INDEX idx_vehicles_created_at ON vehicles (created_at);

-- Vehicle categories for browsing
CREATE TABLE vehicle_categories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    icon_url TEXT,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Vehicle-category junction table (many-to-many)
CREATE TABLE vehicle_categories_map (
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    category_id UUID REFERENCES vehicle_categories(id) ON DELETE CASCADE,
    PRIMARY KEY (vehicle_id, category_id)
);

-- Search history and user interactions
CREATE TABLE search_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255), -- Will be updated when user auth is implemented
    search_query TEXT NOT NULL,
    search_embedding vector(3072), -- Embedding of the search query
    filters JSONB, -- Search filters used
    result_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create index for search query similarity
CREATE INDEX idx_search_history_query_embedding_cosine ON search_history
USING hnsw (search_embedding vector_cosine_ops);

-- User favorites (for future implementation)
CREATE TABLE user_favorites (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255), -- Will be updated when user auth is implemented
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(user_id, vehicle_id)
);

-- Vehicle views tracking
CREATE TABLE vehicle_views (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    user_id VARCHAR(255), -- Will be updated when user auth is implemented
    view_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(vehicle_id, user_id, view_date)
);

-- Create indexes for views
CREATE INDEX idx_vehicle_views_vehicle_date ON vehicle_views (vehicle_id, view_date);
CREATE INDEX idx_vehicle_views_user_date ON vehicle_views (user_id, view_date);

-- Insert sample categories
INSERT INTO vehicle_categories (name, description, sort_order) VALUES
('SUVs', 'Sport Utility Vehicles with ample space and versatility', 1),
('Electric', 'Zero-emission electric vehicles', 2),
('Luxury', 'Premium vehicles with high-end features', 3),
('Trucks', 'Pickup trucks and commercial vehicles', 4),
('Compact', 'Efficient smaller vehicles for city driving', 5),
('Performance', 'Sports cars and high-performance vehicles', 6),
('Hybrid', 'Eco-friendly hybrid and plug-in hybrid vehicles', 7);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_vehicles_updated_at
    BEFORE UPDATE ON vehicles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments to tables for documentation
COMMENT ON TABLE vehicles IS 'Main vehicle inventory table with semantic search embeddings';
COMMENT ON TABLE vehicle_categories IS 'Vehicle categories for browsing and classification';
COMMENT ON TABLE search_history IS 'User search history with query embeddings';
COMMENT ON TABLE user_favorites IS 'User favorite vehicles for future implementation';
COMMENT ON TABLE vehicle_views IS 'Vehicle view tracking for analytics';