#!/usr/bin/env python3
"""
Apply market data schema to Supabase database
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def apply_market_data_schema():
    """Apply the market data schema to the Supabase database"""

    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')

    if not supabase_url or not supabase_key:
        print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set")
        return False

    print(f"Connecting to Supabase: {supabase_url[:50]}...")

    # Initialize Supabase client
    supabase = create_client(supabase_url, supabase_key)

    # Read the schema file
    schema_file = Path(__file__).parent / 'market_data_schema.sql'
    if not schema_file.exists():
        print(f"ERROR: Schema file not found: {schema_file}")
        return False

    with open(schema_file, 'r') as f:
        schema_sql = f.read()

    print("Schema file loaded successfully")

    # Split SQL into individual statements
    # This is a simple approach - in production you might want a more sophisticated SQL parser
    statements = []
    current_statement = ""
    in_function = False
    in_trigger = False

    for line in schema_sql.split('\n'):
        line = line.strip()

        # Skip comments and empty lines
        if line.startswith('--') or not line:
            continue

        current_statement += line + '\n'

        # Track if we're in a function or trigger
        if line.startswith('CREATE OR REPLACE FUNCTION') or line.startswith('CREATE FUNCTION'):
            in_function = True
        elif line.startswith('CREATE TRIGGER'):
            in_trigger = True

        # End of function or trigger
        if (in_function and line == 'END;') or (in_trigger and line.endswith('EXECUTE FUNCTION;')):
            in_function = False
            in_trigger = False
            statements.append(current_statement)
            current_statement = ""
        # Regular statement end
        elif line.endswith(';') and not in_function and not in_trigger:
            statements.append(current_statement)
            current_statement = ""

    # Add any remaining statement
    if current_statement.strip():
        statements.append(current_statement)

    print(f"Found {len(statements)} SQL statements to execute")

    # Execute statements
    success_count = 0
    error_count = 0

    for i, statement in enumerate(statements, 1):
        try:
            # Use Supabase RPC to execute SQL
            result = supabase.rpc('execute_sql', {'sql_query': statement}).execute()

            if hasattr(result, 'data') and result.data:
                print(f"✅ Statement {i}/{len(statements)}: Success")
                success_count += 1
            else:
                print(f"⚠️  Statement {i}/{len(statements)}: No result returned")
                success_count += 1

        except Exception as e:
            print(f"❌ Statement {i}/{len(statements)}: Error - {str(e)}")
            error_count += 1

            # Check if it's a "already exists" error, which might be OK
            if 'already exists' in str(e).lower() or 'does not exist' in str(e).lower():
                print(f"   (This might be OK - object may already exist)")

    print(f"\nExecution Summary:")
    print(f"  ✅ Successful: {success_count}")
    print(f"  ❌ Errors: {error_count}")
    print(f"  📊 Total: {len(statements)}")

    # Test the new schema
    print("\nTesting new schema...")
    try:
        # Test if the new columns exist
        result = supabase.table('vehicle_listings').select('market_price_min, market_price_max, demand_indicator').limit(1).execute()
        print("✅ New columns accessible in vehicle_listings table")
    except Exception as e:
        print(f"❌ Error accessing new columns: {e}")

    try:
        # Test if the new tables exist
        result = supabase.table('market_data_updates').select('*').limit(1).execute()
        print("✅ market_data_updates table accessible")
    except Exception as e:
        print(f"❌ Error accessing market_data_updates table: {e}")

    try:
        # Test if the view exists
        result = supabase.rpc('execute_sql', {'sql_query': 'SELECT * FROM market_data_analytics LIMIT 1'}).execute()
        print("✅ market_data_analytics view accessible")
    except Exception as e:
        print(f"❌ Error accessing market_data_analytics view: {e}")

    print("\n✅ Market data schema application completed!")
    return error_count == 0

if __name__ == "__main__":
    success = asyncio.run(apply_market_data_schema())
    sys.exit(0 if success else 1)