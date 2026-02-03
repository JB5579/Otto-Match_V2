-- Migration: Add missing columns to vehicle_listings table
-- Run this in Supabase SQL Editor to update your existing schema

-- Add condition_grade if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'condition_grade') THEN
        ALTER TABLE vehicle_listings
        ADD COLUMN condition_grade VARCHAR(20) DEFAULT 'Average';

        -- Add check constraint
        ALTER TABLE vehicle_listings
        ADD CONSTRAINT condition_grade_check
        CHECK (condition_grade IN ('Clean', 'Average', 'Rough'));

        RAISE NOTICE 'Added condition_grade column';
    ELSE
        RAISE NOTICE 'condition_grade column already exists';
    END IF;
END $$;

-- Add condition_score if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'condition_score') THEN
        ALTER TABLE vehicle_listings
        ADD COLUMN condition_score DECIMAL(3,1) DEFAULT 4.0;

        -- Add check constraint
        ALTER TABLE vehicle_listings
        ADD CONSTRAINT condition_score_check
        CHECK (condition_score >= 1 AND condition_score <= 5);

        RAISE NOTICE 'Added condition_score column';
    ELSE
        RAISE NOTICE 'condition_score column already exists';
    END IF;
END $$;

-- Add body_style if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'body_style') THEN
        ALTER TABLE vehicle_listings ADD COLUMN body_style VARCHAR(50);
        RAISE NOTICE 'Added body_style column';
    END IF;
END $$;

-- Add fuel_type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'fuel_type') THEN
        ALTER TABLE vehicle_listings ADD COLUMN fuel_type VARCHAR(20);
        RAISE NOTICE 'Added fuel_type column';
    END IF;
END $$;

-- Add vehicle_type if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'vehicle_type') THEN
        ALTER TABLE vehicle_listings ADD COLUMN vehicle_type VARCHAR(30);
        RAISE NOTICE 'Added vehicle_type column';
    END IF;
END $$;

-- Add description_text if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'description_text') THEN
        ALTER TABLE vehicle_listings ADD COLUMN description_text TEXT;
        RAISE NOTICE 'Added description_text column';
    END IF;
END $$;

-- Add text_embedding if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'text_embedding') THEN
        ALTER TABLE vehicle_listings ADD COLUMN text_embedding vector(3072);
        RAISE NOTICE 'Added text_embedding column';
    END IF;
END $$;

-- Add listing_source if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'listing_source') THEN
        ALTER TABLE vehicle_listings ADD COLUMN listing_source VARCHAR(20) DEFAULT 'pdf_upload';
        RAISE NOTICE 'Added listing_source column';
    END IF;
END $$;

-- Add processing_metadata if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_listings' AND column_name = 'processing_metadata') THEN
        ALTER TABLE vehicle_listings ADD COLUMN processing_metadata JSONB DEFAULT '{}';
        RAISE NOTICE 'Added processing_metadata column';
    END IF;
END $$;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'vehicle_listings'
ORDER BY ordinal_position;
