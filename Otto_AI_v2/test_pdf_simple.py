"""
Simple test to check PDF processing with real files
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def test_pdf_import():
    """Test if PDF processing modules can be imported"""
    try:
        from src.services.pdf_ingestion_service import PDFIngestionService
        print("PDF ingestion service imported successfully")

        from src.services.enhanced_pdf_ingestion_with_ai import EnhancedPDFIngestionWithAI
        print("Enhanced PDF ingestion with AI imported successfully")

        return True
    except ImportError as e:
        print(f"Import failed: {e}")
        return False

def test_pdf_files():
    """Check if sample PDFs exist"""
    pdf_dir = Path("docs/Sample_Vehicle_Condition_Reports")
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"Found {len(pdf_files)} PDF files:")
        for pdf in pdf_files:
            print(f"   - {pdf.name}")
        return pdf_files
    else:
        print("Sample PDF directory not found")
        return []

def check_env_vars():
    """Check required environment variables"""
    required = ['OPENROUTER_API_KEY', 'SUPABASE_URL', 'SUPABASE_SERVICE_ROLE_KEY']
    missing = []
    present = []

    for var in required:
        if os.getenv(var):
            present.append(var)
        else:
            missing.append(var)

    print(f"\nEnvironment Variables:")
    print(f"   Present: {present}")
    print(f"   Missing: {missing}")

    return len(missing) == 0

if __name__ == "__main__":
    print("Testing PDF Processing Pipeline\n")

    # Test imports
    imports_ok = test_pdf_import()

    # Check PDF files
    pdf_files = test_pdf_files()

    # Check environment
    env_ok = check_env_vars()

    print(f"\nSummary:")
    print(f"   Imports: {'OK' if imports_ok else 'FAILED'}")
    print(f"   PDF Files: {'OK' if pdf_files else 'NONE'}")
    print(f"   Environment: {'OK' if env_ok else 'MISSING'}")

    if imports_ok and pdf_files and env_ok:
        print(f"\nReady to test real PDF processing!")
    elif imports_ok and pdf_files and not env_ok:
        print(f"\nCan only run in simulation mode (missing API keys)")