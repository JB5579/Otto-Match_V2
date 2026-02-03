-- Migration: Add missing columns to vehicle_images table
-- Run this in Supabase SQL Editor after the listings migration

-- Add page_number if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_images' AND column_name = 'page_number') THEN
        ALTER TABLE vehicle_images ADD COLUMN page_number INTEGER;
        RAISE NOTICE 'Added page_number column';
    END IF;
END $$;

-- Add processing_metadata if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_images' AND column_name = 'processing_metadata') THEN
        ALTER TABLE vehicle_images ADD COLUMN processing_metadata JSONB DEFAULT '{}';
        RAISE NOTICE 'Added processing_metadata column';
    END IF;
END $$;

-- Add display_order if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_images' AND column_name = 'display_order') THEN
        ALTER TABLE vehicle_images ADD COLUMN display_order INTEGER DEFAULT 0;
        RAISE NOTICE 'Added display_order column';
    END IF;
END $$;

-- Add image_embedding if it doesn't exist (for visual search)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                   WHERE table_name = 'vehicle_images' AND column_name = 'image_embedding') THEN
        ALTER TABLE vehicle_images ADD COLUMN image_embedding vector(3072);
        RAISE NOTICE 'Added image_embedding column';
    END IF;
END $$;

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'vehicle_images'
ORDER BY ordinal_position;
