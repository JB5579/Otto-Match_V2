"""
Simple Database Connectivity Test for Story 1.2
Tests database connection and basic operations
"""

import os
import sys
import psycopg
from dotenv import load_dotenv

# Load environment variables
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
env_path = os.path.join(project_root, '.env')
print(f"Loading .env from: {env_path}")
load_dotenv(env_path)

def test_database_connection():
    """Test basic database connectivity to Story 1.2 tables"""

    print("Story 1.2 Database Connectivity Test")
    print("=" * 50)

    try:
        # Get credentials
        supabase_url = os.getenv('SUPABASE_URL')
        db_password = os.getenv('SUPABASE_DB_PASSWORD')

        print(f"Supabase URL: {supabase_url}")
        print(f"DB Password: {'SET' if db_password else 'NOT SET'}")

        if not all([supabase_url, db_password]):
            print("FAIL: Missing database credentials")
            return False

        # Create connection string
        project_ref = supabase_url.split('//')[1].split('.')[0]
        connection_string = f"postgresql://postgres:{db_password}@{project_ref}.supabase.co:5432/postgres"

        print(f"Connecting to: {project_ref}.supabase.co")

        # Test connection
        conn = psycopg.connect(connection_string)
        print("SUCCESS: Database connection established")

        # Test basic operations
        cursor = conn.cursor()

        # Check Story 1.2 tables exist
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name LIKE 'story_1_2_%'
        """)
        tables = cursor.fetchall()
        print(f"SUCCESS: Found {len(tables)} Story 1.2 tables")
        for table in tables:
            print(f"  - {table[0]}")

        # Test query on vehicles table
        cursor.execute("SELECT COUNT(*) FROM story_1_2_vehicles")
        vehicle_count = cursor.fetchone()[0]
        print(f"SUCCESS: Current vehicle count: {vehicle_count}")

        # Test insert
        print("\nTesting insert operation...")
        cursor.execute("""
            INSERT INTO story_1_2_vehicles (
                vehicle_id, make, model, year, description,
                verification_status, data_completeness_score, confidence_score
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, [
            'test-db-' + str(int(time.time())),
            'TestMake',
            'TestModel',
            2025,
            'Database connectivity test',
            'verified',
            0.95,
            0.90
        ])

        vehicle_id = cursor.fetchone()[0]
        print(f"SUCCESS: Inserted test vehicle with ID: {vehicle_id}")

        # Test embedding insert
        print("Testing 3072-dimension embedding insert...")
        test_embedding = [0.1] * 3072

        cursor.execute("""
            INSERT INTO story_1_2_vehicle_embeddings (
                vehicle_id, combined_embedding, source_text, embedding_model
            ) VALUES (%s, %s, %s, %s)
            RETURNING id
        """, [
            vehicle_id,
            test_embedding,
            'Test embedding for database validation',
            'test-model'
        ])

        embedding_id = cursor.fetchone()[0]
        print(f"SUCCESS: Inserted test embedding with ID: {embedding_id}")

        # Test verification
        cursor.execute("""
            SELECT v.vehicle_id, v.make, v.model,
                   ARRAY_LENGTH(e.combined_embedding::real[], 1) as embedding_dim
            FROM story_1_2_vehicles v
            JOIN story_1_2_vehicle_embeddings e ON v.id = e.vehicle_id
            WHERE v.id = %s
        """, [vehicle_id])

        result = cursor.fetchone()
        print(f"SUCCESS: Verified stored data:")
        print(f"  Vehicle: {result[0]} - {result[1]} {result[2]}")
        print(f"  Embedding dimensions: {result[3]}")

        # Commit and close
        conn.commit()
        cursor.close()
        conn.close()

        print("\nOVERALL RESULT: SUCCESS")
        print("Database connectivity and Story 1.2 tables are working correctly")
        print("Ready for complete validation testing")

        return True

    except Exception as e:
        print(f"\nFAIL: Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    import time
    success = test_database_connection()
    exit(0 if success else 1)