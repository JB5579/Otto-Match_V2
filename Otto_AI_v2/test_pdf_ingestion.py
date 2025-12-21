"""
Test PDF ingestion with real dependencies
"""
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_pdf_ingestion_import():
    """Test PDF ingestion imports"""
    try:
        from src.services.pdf_ingestion_service import PDFIngestionService, VehicleListingArtifact
        print("[OK] PDFIngestionService imported")
        return True
    except Exception as e:
        print(f"[FAILED] PDFIngestionService: {e}")
        return False

def test_enhanced_pdf_import():
    """Test enhanced PDF ingestion"""
    try:
        from src.services.enhanced_pdf_ingestion_with_ai import EnhancedPDFIngestionWithAI
        print("[OK] EnhancedPDFIngestionWithAI imported")
        return True
    except Exception as e:
        print(f"[FAILED] EnhancedPDFIngestionWithAI: {e}")
        # Show the import chain if it fails
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PDF Ingestion Imports\n")

    basic_ok = test_pdf_ingestion_import()
    enhanced_ok = test_enhanced_pdf_import()

    if basic_ok:
        print("\nBasic PDF ingestion is working!")
    if enhanced_ok:
        print("Enhanced PDF ingestion with AI is working!")