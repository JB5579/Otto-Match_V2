"""
Test database-related imports
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_database_imports():
    """Test importing database-dependent components"""

    tests = [
        ("VehicleDatabaseService", "src.semantic.vehicle_database_service", "VehicleDatabaseService"),
        ("EmbeddingService", "src.semantic.embedding_service", "OttoAIEmbeddingService"),
        ("SemanticSearchAPI", "src.api.semantic_search_api", "app"),
        ("Realtime Module", "realtime", "__all__"),
    ]

    for name, module_path, import_name in tests:
        try:
            if name == "Realtime Module":
                from realtime import __all__
                print(f"✅ {name} - OK")
            else:
                module = __import__(module_path, fromlist=[import_name])
                getattr(module, import_name)
                print(f"[OK] {name}")
        except Exception as e:
            print(f"[FAILED] {name} - {e}")

if __name__ == "__main__":
    print("Testing Database Component Imports\n")
    test_database_imports()