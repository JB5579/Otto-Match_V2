"""Quick script to run validation with a different PDF"""
import asyncio
import sys
from pathlib import Path

# Change to project root
import os
os.chdir(Path(__file__).parent.parent)

from scripts.validate_pipeline import PipelineValidator

async def main():
    pdf_path = "docs/Sample_Vehicle_Condition_Reports/2014BMWi3V28503 (1).pdf"

    print("="*60)
    print("Otto.AI Pipeline Validation - 2014 BMW i3")
    print("="*60)

    validator = PipelineValidator()
    await validator.initialize()

    results = await validator.validate_pipeline(pdf_path)

    await validator.close()

    sys.exit(0 if results['overall_status'] == 'success' else 1)

if __name__ == '__main__':
    asyncio.run(main())
