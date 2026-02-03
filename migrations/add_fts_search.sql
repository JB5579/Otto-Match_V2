-- Migration: Add Full-Text Search for Hybrid Search
-- Story: 1-9 Implement Hybrid Search with FTS
-- Created: 2025-12-31

-- ============================================================================
-- STEP 1: Add FTS column with auto-generation
-- ============================================================================

-- Add tsvector column that auto-generates from vehicle text fields
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS fts_document tsvector
  GENERATED ALWAYS AS (
    to_tsvector('english',
      coalesce(make, '') || ' ' ||
      coalesce(model, '') || ' ' ||
      coalesce("trim", '') || ' ' ||
      coalesce(vehicle_type, '') || ' ' ||
      coalesce(fuel_type, '') || ' ' ||
      coalesce(transmission, '') || ' ' ||
      coalesce(exterior_color, '') || ' ' ||
      coalesce(interior_color, '') || ' ' ||
      coalesce(description_text, '')
    )
  ) STORED;

-- ============================================================================
-- STEP 2: Create GIN index for fast full-text search
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_vehicle_fts ON vehicle_listings USING GIN(fts_document);

-- ============================================================================
-- STEP 3: Create keyword search function
-- ============================================================================

CREATE OR REPLACE FUNCTION keyword_search_vehicles(
  search_query text,
  match_count int DEFAULT 20
)
RETURNS TABLE(
  id uuid,
  vin varchar,
  year int,
  make varchar,
  model varchar,
  "trim" varchar,
  vehicle_type varchar,
  mileage int,
  rank float
)
LANGUAGE sql STABLE
AS $$
  SELECT
    vl.id,
    vl.vin,
    vl.year,
    vl.make,
    vl.model,
    vl."trim",
    vl.vehicle_type,
    vl.odometer as mileage,
    ts_rank(vl.fts_document, websearch_to_tsquery('english', search_query)) AS rank
  FROM vehicle_listings vl
  WHERE vl.fts_document @@ websearch_to_tsquery('english', search_query)
    AND vl.status = 'active'
  ORDER BY rank DESC
  LIMIT match_count;
$$;

-- ============================================================================
-- STEP 4: Create hybrid search function (combines vector + keyword + filters)
-- ============================================================================

CREATE OR REPLACE FUNCTION hybrid_search_vehicles(
  query_embedding vector(1536),
  search_query text DEFAULT NULL,
  filter_make varchar DEFAULT NULL,
  filter_model varchar DEFAULT NULL,
  filter_year_min int DEFAULT NULL,
  filter_year_max int DEFAULT NULL,
  filter_price_min decimal DEFAULT NULL,
  filter_price_max decimal DEFAULT NULL,
  filter_mileage_max int DEFAULT NULL,
  filter_vehicle_type varchar DEFAULT NULL,
  match_count int DEFAULT 20,
  vector_weight float DEFAULT 0.4,
  keyword_weight float DEFAULT 0.3,
  filter_weight float DEFAULT 0.3,
  rrf_k int DEFAULT 60
)
RETURNS TABLE(
  id uuid,
  vin varchar,
  year int,
  make varchar,
  model varchar,
  "trim" varchar,
  vehicle_type varchar,
  mileage int,
  price decimal,
  price_source varchar,
  description_text text,
  vector_similarity float,
  keyword_rank float,
  hybrid_score float
)
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  candidate_limit int := match_count * 3;  -- Get more candidates for fusion
BEGIN
  RETURN QUERY
  WITH
  -- Vector similarity search
  vector_results AS (
    SELECT
      vl.id,
      1 - (vl.text_embedding <=> query_embedding) AS similarity,
      ROW_NUMBER() OVER (ORDER BY vl.text_embedding <=> query_embedding) AS vrank
    FROM vehicle_listings vl
    WHERE vl.status = 'active'
      AND vl.text_embedding IS NOT NULL
      AND (filter_make IS NULL OR vl.make ILIKE filter_make)
      AND (filter_model IS NULL OR vl.model ILIKE filter_model)
      AND (filter_year_min IS NULL OR vl.year >= filter_year_min)
      AND (filter_year_max IS NULL OR vl.year <= filter_year_max)
      AND (filter_price_min IS NULL OR vl.effective_price >= filter_price_min)
      AND (filter_price_max IS NULL OR vl.effective_price <= filter_price_max)
      AND (filter_mileage_max IS NULL OR vl.odometer <= filter_mileage_max)
      AND (filter_vehicle_type IS NULL OR vl.vehicle_type ILIKE filter_vehicle_type)
    ORDER BY vl.text_embedding <=> query_embedding
    LIMIT candidate_limit
  ),

  -- Keyword search (only if search_query provided)
  keyword_results AS (
    SELECT
      vl.id,
      ts_rank(vl.fts_document, websearch_to_tsquery('english', search_query)) AS krank_score,
      ROW_NUMBER() OVER (ORDER BY ts_rank(vl.fts_document, websearch_to_tsquery('english', search_query)) DESC) AS krank
    FROM vehicle_listings vl
    WHERE search_query IS NOT NULL
      AND search_query != ''
      AND vl.fts_document @@ websearch_to_tsquery('english', search_query)
      AND vl.status = 'active'
      AND (filter_make IS NULL OR vl.make ILIKE filter_make)
      AND (filter_model IS NULL OR vl.model ILIKE filter_model)
      AND (filter_year_min IS NULL OR vl.year >= filter_year_min)
      AND (filter_year_max IS NULL OR vl.year <= filter_year_max)
      AND (filter_price_min IS NULL OR vl.effective_price >= filter_price_min)
      AND (filter_price_max IS NULL OR vl.effective_price <= filter_price_max)
      AND (filter_mileage_max IS NULL OR vl.odometer <= filter_mileage_max)
      AND (filter_vehicle_type IS NULL OR vl.vehicle_type ILIKE filter_vehicle_type)
    ORDER BY krank_score DESC
    LIMIT candidate_limit
  ),

  -- Combine with RRF
  rrf_scores AS (
    SELECT
      COALESCE(vr.id, kr.id) AS id,
      COALESCE(vr.similarity, 0) AS vector_sim,
      COALESCE(kr.krank_score, 0) AS keyword_rnk,
      -- RRF formula: weight * (1 / (k + rank))
      COALESCE(vector_weight * (1.0 / (rrf_k + vr.vrank)), 0) +
      COALESCE(keyword_weight * (1.0 / (rrf_k + kr.krank)), 0) +
      -- Filter bonus for exact matches (treated as filter_weight)
      CASE WHEN vr.id IS NOT NULL THEN filter_weight * 0.5 ELSE 0 END AS rrf_score
    FROM vector_results vr
    FULL OUTER JOIN keyword_results kr ON vr.id = kr.id
  )

  SELECT
    vl.id,
    vl.vin,
    vl.year,
    vl.make,
    vl.model,
    vl."trim",
    vl.vehicle_type,
    vl.odometer AS mileage,
    vl.effective_price AS price,
    vl.price_source,
    vl.description_text,
    rs.vector_sim::float AS vector_similarity,
    rs.keyword_rnk::float AS keyword_rank,
    rs.rrf_score::float AS hybrid_score
  FROM rrf_scores rs
  JOIN vehicle_listings vl ON vl.id = rs.id
  ORDER BY rs.rrf_score DESC
  LIMIT match_count;
END;
$$;

-- ============================================================================
-- STEP 5: Grant permissions
-- ============================================================================

GRANT EXECUTE ON FUNCTION keyword_search_vehicles TO anon, authenticated;
GRANT EXECUTE ON FUNCTION hybrid_search_vehicles TO anon, authenticated;

-- ============================================================================
-- Verification queries (run after migration)
-- ============================================================================

-- Check FTS column exists:
-- SELECT column_name, data_type FROM information_schema.columns
-- WHERE table_name = 'vehicle_listings' AND column_name = 'fts_document';

-- Check GIN index exists:
-- SELECT indexname FROM pg_indexes WHERE tablename = 'vehicle_listings' AND indexname = 'idx_vehicle_fts';

-- Test keyword search:
-- SELECT * FROM keyword_search_vehicles('F-250 truck', 5);

-- Test hybrid search:
-- SELECT * FROM hybrid_search_vehicles(
--   (SELECT text_embedding FROM vehicle_listings LIMIT 1),
--   'pickup truck',
--   NULL, NULL, NULL, NULL, NULL, NULL, NULL,
--   10, 0.4, 0.3, 0.3, 60
-- );
