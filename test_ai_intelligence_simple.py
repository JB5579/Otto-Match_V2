"""
Simple test to verify AI intelligence components are working
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_imports():
    """Test importing key AI components"""

    try:
        # Test semantic search
        from src.semantic.embedding_service import EmbeddingService
        print("1. EmbeddingService - OK")
    except Exception as e:
        print(f"1. EmbeddingService - FAILED: {e}")

    try:
        from src.conversation.groq_client import GroqClient
        print("2. GroqClient - OK")
    except Exception as e:
        print(f"2. GroqClient - FAILED: {e}")

    try:
        from src.semantic.vehicle_database_service import VehicleDatabaseService
        print("3. VehicleDatabaseService - OK")
    except Exception as e:
        print(f"3. VehicleDatabaseService - FAILED: {e}")

    try:
        from src.api.semantic_search_api import app
        print("4. Semantic Search API - OK")
    except Exception as e:
        print(f"4. Semantic Search API - FAILED: {e}")

def check_sample_data():
    """Check for sample vehicle data"""
    sample_files = [
        "src/semantic/sample_vehicle_data.py",
        "docs/Sample_Vehicle_Condition_Reports"
    ]

    for file_path in sample_files:
        if Path(file_path).exists():
            print(f"   Found: {file_path}")
        else:
            print(f"   Missing: {file_path}")

def main():
    print("Otto.AI Component Status Check\n")
    print("Testing Core Imports:")
    test_imports()

    print("\nChecking Sample Data:")
    check_sample_data()

    print("\nEnvironment Check:")
    print(f"   OPENROUTER_API_KEY: {'SET' if os.getenv('OPENROUTER_API_KEY') else 'MISSING'}")
    print(f"   SUPABASE_URL: {'SET' if os.getenv('SUPABASE_URL') else 'MISSING'}")

if __name__ == "__main__":
    main()
