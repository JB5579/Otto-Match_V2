#!/usr/bin/env python3
"""
Otto.AI Database Setup Script
Sets up Supabase PostgreSQL with pgvector extension and creates schema for semantic search
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import subprocess
import logging
from typing import Optional, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseSetup:
    """Handles Supabase PostgreSQL setup with pgvector extension"""

    def __init__(self):
        self.connection_string = os.getenv('SUPABASE_DB_URL')
        if not self.connection_string:
            # Fallback to individual Supabase variables
            self.connection_string = self._build_connection_string()

        self.conn: Optional[psycopg2.extensions.connection] = None

    def _build_connection_string(self) -> str:
        """Build connection string from individual environment variables"""
        host = os.getenv('SUPABASE_DB_HOST', 'localhost')
        port = os.getenv('SUPABASE_DB_PORT', '5432')
        database = os.getenv('SUPABASE_DB_NAME', 'postgres')
        user = os.getenv('SUPABASE_DB_USER', 'postgres')
        password = os.getenv('SUPABASE_DB_PASSWORD')

        if not password:
            raise ValueError("SUPABASE_DB_PASSWORD environment variable is required")

        return f"postgresql://{user}:{password}@{host}:{port}/{database}"

    def connect(self) -> bool:
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(
                self.connection_string,
                cursor_factory=RealDictCursor
            )
            self.conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            logger.info("✅ Connected to Supabase PostgreSQL database")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            return False

    def check_pgvector_extension(self) -> bool:
        """Check if pgvector extension is installed"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM pg_extension WHERE extname = 'vector';")
            result = cursor.fetchone()
            cursor.close()

            if result:
                logger.info("✅ pgvector extension is already installed")
                return True
            else:
                logger.info("⚠️ pgvector extension not found, will install")
                return False
        except Exception as e:
            logger.error(f"❌ Error checking pgvector extension: {e}")
            return False

    def install_pgvector_extension(self) -> bool:
        """Install pgvector extension"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.close()
            logger.info("✅ pgvector extension installed successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to install pgvector extension: {e}")
            return False

    def verify_pgvector_functionality(self) -> bool:
        """Test pgvector functionality with a simple test"""
        try:
            cursor = self.conn.cursor()

            # Create a test table
            cursor.execute("""
                DROP TABLE IF EXISTS pgvector_test;
                CREATE TABLE pgvector_test (
                    id serial PRIMARY KEY,
                    embedding vector(3)
                );
            """)

            # Insert test data
            cursor.execute("""
                INSERT INTO pgvector_test (embedding)
                VALUES
                (ARRAY[1.0, 2.0, 3.0]),
                (ARRAY[4.0, 5.0, 6.0]);
            """)

            # Test similarity search
            cursor.execute("""
                SELECT id, embedding <-> ARRAY[1.1, 2.1, 3.1] as distance
                FROM pgvector_test
                ORDER BY embedding <-> ARRAY[1.1, 2.1, 3.1];
            """)
            result = cursor.fetchone()

            # Clean up
            cursor.execute("DROP TABLE pgvector_test;")
            cursor.close()

            if result and result['distance'] is not None:
                logger.info("✅ pgvector functionality verified successfully")
                return True
            else:
                logger.error("❌ pgvector functionality test failed")
                return False

        except Exception as e:
            logger.error(f"❌ Error testing pgvector functionality: {e}")
            return False

    def execute_schema(self, schema_file: str) -> bool:
        """Execute SQL schema from file"""
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()

            cursor = self.conn.cursor()
            cursor.execute(schema_sql)
            cursor.close()

            logger.info(f"✅ Database schema executed from {schema_file}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to execute schema from {schema_file}: {e}")
            return False

    def verify_tables_created(self) -> bool:
        """Verify that all required tables were created"""
        required_tables = [
            'vehicles',
            'vehicle_categories',
            'vehicle_categories_map',
            'search_history',
            'user_favorites',
            'vehicle_views'
        ]

        try:
            cursor = self.conn.cursor()
            for table in required_tables:
                cursor.execute(f"""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = '{table}'
                    );
                """)
                exists = cursor.fetchone()[0]
                if not exists:
                    logger.error(f"❌ Required table '{table}' was not created")
                    return False

            cursor.close()
            logger.info("✅ All required tables verified")
            return True

        except Exception as e:
            logger.error(f"❌ Error verifying tables: {e}")
            return False

    def verify_indexes_created(self) -> bool:
        """Verify that HNSW indexes were created"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE indexname LIKE '%_vehicles_%_embedding_cosine';
            """)

            indexes = cursor.fetchall()
            expected_indexes = [
                'idx_vehicles_title_embedding_cosine',
                'idx_vehicles_description_embedding_cosine',
                'idx_vehicles_features_embedding_cosine'
            ]

            index_names = [row[0] for row in indexes]

            for expected_index in expected_indexes:
                if expected_index not in index_names:
                    logger.error(f"❌ Required index '{expected_index}' was not created")
                    return False

            cursor.close()
            logger.info(f"✅ All {len(expected_indexes)} HNSW indexes verified")
            return True

        except Exception as e:
            logger.error(f"❌ Error verifying indexes: {e}")
            return False

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("✅ Database connection closed")

    def setup_database(self, schema_file: str = None) -> bool:
        """Complete database setup process"""
        if not schema_file:
            schema_file = os.path.join(os.path.dirname(__file__), 'database_schema.sql')

        logger.info("🚀 Starting Otto.AI database setup")

        # Connection check
        if not self.connect():
            return False

        try:
            # Install pgvector extension
            if not self.check_pgvector_extension():
                if not self.install_pgvector_extension():
                    return False

            # Verify pgvector functionality
            if not self.verify_pgvector_functionality():
                return False

            # Execute schema
            if not self.execute_schema(schema_file):
                return False

            # Verify tables
            if not self.verify_tables_created():
                return False

            # Verify indexes
            if not self.verify_indexes_created():
                return False

            logger.info("🎉 Database setup completed successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Database setup failed: {e}")
            return False
        finally:
            self.close()

def main():
    """Main setup function"""
    print("Otto.AI Database Setup")
    print("=" * 50)

    # Check environment variables
    required_vars = ['SUPABASE_DB_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set the following environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        sys.exit(1)

    # Setup database
    db_setup = DatabaseSetup()
    success = db_setup.setup_database()

    if success:
        print("\n✅ Database setup completed successfully!")
        print("The semantic search infrastructure is ready for development.")
        print("\nNext steps:")
        print("1. Configure OpenRouter API key in .env")
        print("2. Install Python dependencies")
        print("3. Implement the embedding service")
    else:
        print("\n❌ Database setup failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()