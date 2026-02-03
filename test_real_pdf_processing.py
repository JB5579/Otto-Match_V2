"""
Test real PDF processing with sample files
"""
import os
import sys
import asyncio
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_basic_pdf_processing():
    """Test basic PDF processing without database requirements"""
    from src.services.pdf_ingestion_service import PDFIngestionService, get_pdf_ingestion_service

    print("Testing Basic PDF Processing")
    print("=" * 50)

    # Check environment
    if not os.getenv('OPENROUTER_API_KEY'):
        print("[WARNING] OPENROUTER_API_KEY not set - will use simulation")
        return test_simulation_mode()

    try:
        # Initialize the service
        service = await get_pdf_ingestion_service()
        print("[OK] PDF ingestion service initialized")

        # Find sample PDFs
        pdf_dir = Path("docs/Sample_Vehicle_Condition_Reports")
        if not pdf_dir.exists():
            print("[ERROR] Sample PDF directory not found")
            return False

        pdf_files = list(pdf_dir.glob("*.pdf"))
        print(f"[INFO] Found {len(pdf_files)} PDF files")

        # Process first PDF
        if pdf_files:
            pdf_path = pdf_files[0]
            print(f"\n[INFO] Processing: {pdf_path.name}")

            # Read PDF
            with open(pdf_path, 'rb') as f:
                pdf_bytes = f.read()

            print(f"[INFO] PDF size: {len(pdf_bytes):,} bytes")

            # Process
            try:
                result = await service.process_condition_report(
                    pdf_bytes=pdf_bytes,
                    filename=pdf_path.name
                )

                print("\n[SUCCESS] PDF Processing Results:")
                print(f"  Vehicle: {result.vehicle.year} {result.vehicle.make} {result.vehicle.model}")
                print(f"  VIN: {result.vehicle.vin}")
                print(f"  Odometer: {result.vehicle.odometer}")
                print(f"  Images: {len(result.images)}")
                print(f"  Issues: {len(result.condition.issues)}")

                # Check if it's simulated
                if hasattr(result, 'processing_metadata') and result.processing_metadata.get('simulated'):
                    print("\n[WARNING] This was simulated processing, not real AI extraction")
                    return False
                else:
                    print("\n[SUCCESS] Real PDF processing completed!")
                    return True

            except Exception as e:
                print(f"[ERROR] Processing failed: {e}")
                return False

    except Exception as e:
        print(f"[ERROR] Failed to initialize service: {e}")
        return False

def test_simulation_mode():
    """Test in simulation mode"""
    print("\nSimulation Mode Test:")
    print("-" * 30)

    pdf_dir = Path("docs/Sample_Vehicle_Condition_Reports")
    if pdf_dir.exists():
        pdf_files = list(pdf_dir.glob("*.pdf"))
        for pdf in pdf_files[:3]:  # Test first 3
            print(f"  Found: {pdf.name} ({pdf.stat().st_size:,} bytes)")

    print("\n[INFO] To test real processing:")
    print("1. Set OPENROUTER_API_KEY environment variable")
    print("2. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY")
    print("3. Run test again")
    return False

async def main():
    """Main test function"""
    print("Otto.AI PDF Processing Test")
    print("=" * 50)

    success = await test_basic_pdf_processing()

    print("\n" + "=" * 50)
    if success:
        print("[RESULT] PDF processing is WORKING with real AI!")
    else:
        print("[RESULT] PDF processing needs configuration or is simulated")

if __name__ == "__main__":
    asyncio.run(main())