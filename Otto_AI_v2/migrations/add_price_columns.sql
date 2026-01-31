-- Migration: Add Price Columns for Vehicle Listings
-- Created: 2025-12-31
-- Purpose: Add pricing fields to support dealer asking prices, auction forecasts,
--          and AI-estimated market prices with confidence scoring

-- ============================================================================
-- STEP 1: Add price columns to vehicle_listings
-- ============================================================================

-- Dealer's asking price (if available)
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS asking_price DECIMAL(12,2);

-- AI-estimated market price (from Groq Compound or other sources)
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS estimated_price DECIMAL(12,2);

-- Auction forecast price (for vehicles going to auction)
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS auction_forecast DECIMAL(12,2);

-- Source of the price: 'dealer', 'auction', 'ai_estimate', 'market_data'
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS price_source VARCHAR(30);

-- Confidence score for estimated prices (0.0 to 1.0)
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS price_confidence DECIMAL(3,2);

-- When the price was last updated/verified
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS price_updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- ============================================================================
-- STEP 2: Create computed effective_price column
-- ============================================================================

-- The effective price prioritizes: asking_price > auction_forecast > estimated_price
-- This provides a single "best available" price for filtering/sorting
ALTER TABLE vehicle_listings ADD COLUMN IF NOT EXISTS effective_price DECIMAL(12,2)
  GENERATED ALWAYS AS (
    COALESCE(asking_price, auction_forecast, estimated_price)
  ) STORED;

-- ============================================================================
-- STEP 3: Create indexes for price queries
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_vehicle_effective_price ON vehicle_listings(effective_price);
CREATE INDEX IF NOT EXISTS idx_vehicle_asking_price ON vehicle_listings(asking_price);
CREATE INDEX IF NOT EXISTS idx_vehicle_price_source ON vehicle_listings(price_source);

-- ============================================================================
-- STEP 4: Add comments for documentation
-- ============================================================================

COMMENT ON COLUMN vehicle_listings.asking_price IS 'Dealer asking price, if available';
COMMENT ON COLUMN vehicle_listings.estimated_price IS 'AI-estimated market price from Groq Compound';
COMMENT ON COLUMN vehicle_listings.auction_forecast IS 'Predicted auction price for wholesale vehicles';
COMMENT ON COLUMN vehicle_listings.price_source IS 'Origin of price: dealer, auction, ai_estimate, market_data';
COMMENT ON COLUMN vehicle_listings.price_confidence IS 'Confidence score 0.0-1.0 for AI estimates';
COMMENT ON COLUMN vehicle_listings.effective_price IS 'Best available price (asking > auction > estimated)';
COMMENT ON COLUMN vehicle_listings.price_updated_at IS 'Timestamp of last price update';

-- ============================================================================
-- Verification queries
-- ============================================================================

-- Check columns were added:
-- SELECT column_name, data_type, column_default
-- FROM information_schema.columns
-- WHERE table_name = 'vehicle_listings'
-- AND column_name IN ('asking_price', 'estimated_price', 'auction_forecast',
--                     'price_source', 'price_confidence', 'effective_price', 'price_updated_at');
