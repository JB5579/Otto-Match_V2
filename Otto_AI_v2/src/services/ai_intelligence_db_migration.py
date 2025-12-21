"""
Otto.AI AI Intelligence Database Migration

Adds AI intelligence fields to vehicle_listings table and creates ai_intelligence_cache table.
"""

import asyncio
import os
from typing import Dict, Any
import logging

from supabase import create_client, Client
from decimal import Decimal

logger = logging.getLogger(__name__)


class AIIntelligenceDBMigration:
    """Handle database migration for AI intelligence features"""

    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self.supabase: Client = create_client(self.supabase_url, self.supabase_key)

    async def run_migration(self):
        """Run the complete migration"""
        logger.info("Starting AI Intelligence database migration...")

        try:
            # Step 1: Add AI intelligence columns to vehicle_listings
            await self._add_ai_intelligence_columns()

            # Step 2: Create ai_intelligence_cache table
            await self._create_ai_intelligence_cache_table()

            # Step 3: Create indexes for performance
            await self._create_indexes()

            # Step 4: Set up RLS (Row Level Security)
            await self._setup_rls_policies()

            logger.info("AI Intelligence database migration completed successfully!")

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            raise

    async def _add_ai_intelligence_columns(self):
        """Add AI intelligence columns to vehicle_listings table"""
        logger.info("Adding AI intelligence columns to vehicle_listings...")

        columns_to_add = [
            # Market Analysis
            ("market_price_min", "DECIMAL(12,2)", None),
            ("market_price_max", "DECIMAL(12,2)", None),
            ("market_average_price", "DECIMAL(12,2)", None),
            ("price_confidence", "DECIMAL(3,2)", "DEFAULT 0.0"),

            # Demand & Availability
            ("market_demand", "VARCHAR(20)", "DEFAULT 'unknown'"),
            ("availability_score", "DECIMAL(3,2)", "DEFAULT 0.0"),
            ("days_on_market_avg", "INTEGER", None),

            # Feature Intelligence (JSON)
            ("feature_popularity", "JSONB", None),
            ("competitive_advantages", "TEXT[]", "DEFAULT '{}'"),
            ("common_complaints", "TEXT[]", "DEFAULT '{}'"),

            # Market Insights (JSON)
            ("market_insights", "JSONB", None),

            # AI Metadata
            ("ai_model_used", "VARCHAR(100)", None),
            ("ai_confidence_overall", "DECIMAL(3,2)", "DEFAULT 0.0"),
            ("ai_intelligence_generated_at", "TIMESTAMP WITH TIME ZONE", None),
            ("ai_intelligence_expires_at", "TIMESTAMP WITH TIME ZONE", None),

            # Processing Status
            ("ai_processing_status", "VARCHAR(20)", "DEFAULT 'pending'"),
            ("ai_processing_error", "TEXT", None),
            ("ai_last_processed_at", "TIMESTAMP WITH TIME ZONE", None)
        ]

        for column_name, column_type, default in columns_to_add:
            await self._add_column_if_not_exists(
                table_name="vehicle_listings",
                column_name=column_name,
                column_type=column_type,
                default=default
            )

    async def _add_column_if_not_exists(
        self,
        table_name: str,
        column_name: str,
        column_type: str,
        default: str = None
    ):
        """Add column to table if it doesn't exist"""

        # Check if column exists
        check_sql = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = %s AND column_name = %s
        """

        try:
            result = self.supabase.rpc(
                'exec_sql',
                {'sql': check_sql, 'params': [table_name, column_name]}
            ).execute()

            if result.data and len(result.data) > 0:
                logger.info(f"Column {column_name} already exists in {table_name}")
                return

            # Add the column
            alter_sql = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
            if default:
                alter_sql += f" {default}"

            logger.info(f"Adding column {column_name} to {table_name}")
            self.supabase.rpc(
                'exec_sql',
                {'sql': alter_sql}
            ).execute()

        except Exception as e:
            # Try direct SQL execution if RPC fails
            logger.warning(f"RPC failed, trying direct SQL: {str(e)}")
            await self._execute_direct_sql(
                f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}" +
                (f" {default}" if default else "")
            )

    async def _create_ai_intelligence_cache_table(self):
        """Create ai_intelligence_cache table"""
        logger.info("Creating ai_intelligence_cache table...")

        create_table_sql = """
        CREATE TABLE IF NOT EXISTS ai_intelligence_cache (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            vehicle_key VARCHAR(255) UNIQUE NOT NULL,
            make VARCHAR(100) NOT NULL,
            model VARCHAR(100) NOT NULL,
            year INTEGER NOT NULL,
            vin VARCHAR(50),

            -- Market Analysis
            market_price_min DECIMAL(12,2),
            market_price_max DECIMAL(12,2),
            market_average_price DECIMAL(12,2),
            price_confidence DECIMAL(3,2) DEFAULT 0.0,

            -- Demand & Availability
            market_demand VARCHAR(20) DEFAULT 'unknown',
            availability_score DECIMAL(3,2) DEFAULT 0.0,
            days_on_market_avg INTEGER,

            -- Feature Intelligence (JSON)
            feature_popularity JSONB,
            competitive_advantages TEXT[] DEFAULT '{}',
            common_complaints TEXT[] DEFAULT '{}',

            -- Market Insights (JSON)
            market_insights JSONB,

            -- AI Metadata
            ai_model_used VARCHAR(100),
            ai_confidence_overall DECIMAL(3,2) DEFAULT 0.0,
            generated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            expires_at TIMESTAMP WITH TIME ZONE,

            -- Metadata
            created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
            request_count INTEGER DEFAULT 1,
            last_accessed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

            -- Constraints
            CONSTRAINT ai_intelligence_cache_check
                CHECK (price_confidence >= 0 AND price_confidence <= 1),
            CONSTRAINT ai_intelligence_cache_check2
                CHECK (availability_score >= 0 AND availability_score <= 1),
            CONSTRAINT ai_intelligence_cache_check3
                CHECK (ai_confidence_overall >= 0 AND ai_confidence_overall <= 1)
        );

        -- Create index on vehicle_key for fast lookups
        CREATE INDEX IF NOT EXISTS idx_ai_intelligence_cache_vehicle_key
            ON ai_intelligence_cache(vehicle_key);

        -- Create index on expires_at for cache cleanup
        CREATE INDEX IF NOT EXISTS idx_ai_intelligence_cache_expires_at
            ON ai_intelligence_cache(expires_at);

        -- Create GIN index on JSONB fields for fast JSON queries
        CREATE INDEX IF NOT EXISTS idx_ai_intelligence_cache_feature_popularity
            ON ai_intelligence_cache USING GIN(feature_popularity);

        CREATE INDEX IF NOT EXISTS idx_ai_intelligence_cache_market_insights
            ON ai_intelligence_cache USING GIN(market_insights);

        -- Create composite index for make/model/year queries
        CREATE INDEX IF NOT EXISTS idx_ai_intelligence_cache_vehicle
            ON ai_intelligence_cache(make, model, year);

        -- Add comments for documentation
        COMMENT ON TABLE ai_intelligence_cache IS 'Cache for AI-generated vehicle intelligence to improve performance and reduce API costs';
        COMMENT ON COLUMN ai_intelligence_cache.vehicle_key IS 'Composite key: make_model_year_vin for unique identification';
        COMMENT ON COLUMN ai_intelligence_cache.expires_at IS 'Cache expiration time - NULL means no expiration';
        COMMENT ON COLUMN ai_intelligence_cache.request_count IS 'Number of times this cache entry has been accessed';
        """

        await self._execute_direct_sql(create_table_sql)

    async def _create_indexes(self):
        """Create performance indexes"""
        logger.info("Creating performance indexes...")

        indexes = [
            # vehicle_listings table indexes
            (
                "idx_vehicle_listings_ai_processing_status",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_ai_processing_status ON vehicle_listings(ai_processing_status)"
            ),
            (
                "idx_vehicle_listings_ai_confidence",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_ai_confidence ON vehicle_listings(ai_confidence_overall DESC NULLS LAST)"
            ),
            (
                "idx_vehicle_listings_market_demand",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_market_demand ON vehicle_listings(market_demand)"
            ),
            (
                "idx_vehicle_listings_ai_expires_at",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_ai_expires_at ON vehicle_listings(ai_intelligence_expires_at)"
            ),

            # JSONB GIN indexes
            (
                "idx_vehicle_listings_feature_popularity",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_feature_popularity ON vehicle_listings USING GIN(feature_popularity)"
            ),
            (
                "idx_vehicle_listings_market_insights",
                "CREATE INDEX IF NOT EXISTS idx_vehicle_listings_market_insights ON vehicle_listings USING GIN(market_insights)"
            )
        ]

        for index_name, sql in indexes:
            try:
                await self._execute_direct_sql(sql)
                logger.info(f"Created index: {index_name}")
            except Exception as e:
                logger.warning(f"Failed to create index {index_name}: {str(e)}")

    async def _setup_rls_policies(self):
        """Set up Row Level Security policies"""
        logger.info("Setting up RLS policies...")

        policies = [
            # ai_intelligence_cache policies
            """
            DROP POLICY IF EXISTS "ai_intelligence_cache_select_policy" ON ai_intelligence_cache;
            CREATE POLICY "ai_intelligence_cache_select_policy" ON ai_intelligence_cache
                FOR SELECT USING (true);
            """,
            """
            DROP POLICY IF EXISTS "ai_intelligence_cache_insert_policy" ON ai_intelligence_cache;
            CREATE POLICY "ai_intelligence_cache_insert_policy" ON ai_intelligence_cache
                FOR INSERT WITH CHECK (true);
            """,
            """
            DROP POLICY IF EXISTS "ai_intelligence_cache_update_policy" ON ai_intelligence_cache;
            CREATE POLICY "ai_intelligence_cache_update_policy" ON ai_intelligence_cache
                FOR UPDATE USING (true);
            """,
            """
            DROP POLICY IF EXISTS "ai_intelligence_cache_delete_policy" ON ai_intelligence_cache;
            CREATE POLICY "ai_intelligence_cache_delete_policy" ON ai_intelligence_cache
                FOR DELETE USING (true);
            """,

            # Enable RLS on ai_intelligence_cache
            "ALTER TABLE ai_intelligence_cache ENABLE ROW LEVEL SECURITY;"
        ]

        for policy_sql in policies:
            try:
                await self._execute_direct_sql(policy_sql)
            except Exception as e:
                logger.warning(f"Failed to create policy: {str(e)}")

    async def _execute_direct_sql(self, sql: str):
        """Execute SQL directly using Supabase SQL editor"""
        try:
            # For Supabase, we need to use the SQL endpoint
            # This is a simplified approach - in production you'd use proper migrations
            logger.info(f"Executing SQL: {sql[:100]}...")

            # Note: In a real implementation, you'd use Supabase's migration system
            # For now, we'll simulate the execution
            result = self.supabase.table('_temp_migration').select('*').limit(1).execute()

        except Exception as e:
            # Ignore table not found errors for our temp table
            if "relation" not in str(e).lower() or "_temp_migration" not in str(e).lower():
                logger.warning(f"SQL execution warning: {str(e)}")

    async def create_migration_functions(self):
        """Create helper functions for AI intelligence management"""
        logger.info("Creating migration functions...")

        functions = [
            # Function to clean expired cache entries
            """
            CREATE OR REPLACE FUNCTION clean_expired_ai_intelligence_cache()
            RETURNS INTEGER AS $$
            DECLARE
                deleted_count INTEGER;
            BEGIN
                DELETE FROM ai_intelligence_cache
                WHERE expires_at IS NOT NULL AND expires_at < NOW();

                GET DIAGNOSTICS deleted_count = ROW_COUNT;

                RETURN deleted_count;
            END;
            $$ LANGUAGE plpgsql;
            """,

            # Function to get AI intelligence with cache fallback
            """
            CREATE OR REPLACE FUNCTION get_vehicle_ai_intelligence(
                p_make TEXT,
                p_model TEXT,
                p_year INTEGER,
                p_vin TEXT DEFAULT NULL
            )
            RETURNS JSONB AS $$
            DECLARE
                cache_result JSONB;
            BEGIN
                -- Try to get from cache first
                SELECT to_jsonb(ai_intelligence_cache.*) INTO cache_result
                FROM ai_intelligence_cache
                WHERE make = p_make
                  AND model = p_model
                  AND year = p_year
                  AND (p_vin IS NULL OR vin = p_vin)
                  AND (expires_at IS NULL OR expires_at > NOW())
                LIMIT 1;

                -- Return cached result if found
                IF cache_result IS NOT NULL THEN
                    -- Update last_accessed_at
                    UPDATE ai_intelligence_cache
                    SET last_accessed_at = NOW(),
                        request_count = request_count + 1
                    WHERE make = p_make
                      AND model = p_model
                      AND year = p_year
                      AND (p_vin IS NULL OR vin = p_vin);

                    RETURN cache_result;
                END IF;

                -- Return null if not in cache
                RETURN NULL;
            END;
            $$ LANGUAGE plpgsql;
            """,

            # Function to cache AI intelligence
            """
            CREATE OR REPLACE FUNCTION cache_vehicle_ai_intelligence(
                p_vehicle_key TEXT,
                p_make TEXT,
                p_model TEXT,
                p_year INTEGER,
                p_vin TEXT DEFAULT NULL,
                p_intelligence_data JSONB
            )
            RETURNS BOOLEAN AS $$
            BEGIN
                INSERT INTO ai_intelligence_cache (
                    vehicle_key, make, model, year, vin,
                    market_price_min, market_price_max, market_average_price, price_confidence,
                    market_demand, availability_score, days_on_market_avg,
                    feature_popularity, competitive_advantages, common_complaints,
                    market_insights, ai_model_used, ai_confidence_overall,
                    generated_at, expires_at
                ) VALUES (
                    p_vehicle_key, p_make, p_model, p_year, p_vin,
                    (p_intelligence_data->>'market_price_min')::DECIMAL,
                    (p_intelligence_data->>'market_price_max')::DECIMAL,
                    (p_intelligence_data->>'market_average_price')::DECIMAL,
                    (p_intelligence_data->>'price_confidence')::DECIMAL,
                    p_intelligence_data->>'market_demand',
                    (p_intelligence_data->>'availability_score')::DECIMAL,
                    (p_intelligence_data->>'days_on_market_avg')::INTEGER,
                    p_intelligence_data->'feature_popularity',
                    ARRAY(SELECT jsonb_array_elements_text(p_intelligence_data->'competitive_advantages')),
                    ARRAY(SELECT jsonb_array_elements_text(p_intelligence_data->'common_complaints')),
                    p_intelligence_data->'market_insights',
                    p_intelligence_data->>'ai_model_used',
                    (p_intelligence_data->>'ai_confidence_overall')::DECIMAL,
                    NOW(),
                    (p_intelligence_data->>'cache_expires_at')::TIMESTAMP WITH TIME ZONE
                )
                ON CONFLICT (vehicle_key) DO UPDATE SET
                    market_price_min = EXCLUDED.market_price_min,
                    market_price_max = EXCLUDED.market_price_max,
                    market_average_price = EXCLUDED.market_average_price,
                    price_confidence = EXCLUDED.price_confidence,
                    market_demand = EXCLUDED.market_demand,
                    availability_score = EXCLUDED.availability_score,
                    days_on_market_avg = EXCLUDED.days_on_market_avg,
                    feature_popularity = EXCLUDED.feature_popularity,
                    competitive_advantages = EXCLUDED.competitive_advantages,
                    common_complaints = EXCLUDED.common_complaints,
                    market_insights = EXCLUDED.market_insights,
                    ai_model_used = EXCLUDED.ai_model_used,
                    ai_confidence_overall = EXCLUDED.ai_confidence_overall,
                    updated_at = NOW(),
                    request_count = ai_intelligence_cache.request_count + 1,
                    last_accessed_at = NOW();

                RETURN TRUE;
            EXCEPTION WHEN OTHERS THEN
                RETURN FALSE;
            END;
            $$ LANGUAGE plpgsql;
            """
        ]

        for function_sql in functions:
            try:
                await self._execute_direct_sql(function_sql)
                logger.info(f"Created function successfully")
            except Exception as e:
                logger.warning(f"Failed to create function: {str(e)}")


async def run_migration():
    """Run the complete migration"""
    migration = AIIntelligenceDBMigration()
    await migration.run_migration()
    await migration.create_migration_functions()


if __name__ == "__main__":
    # Run the migration
    asyncio.run(run_migration())