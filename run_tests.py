#!/usr/bin/env python
"""
Test runner for Otto AI memory and preference learning tests
"""

import sys
import os
import subprocess
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")

    start_time = time.time()
    result = subprocess.run(cmd, capture_output=True, text=True)
    end_time = time.time()

    duration = end_time - start_time

    if result.returncode == 0:
        print(f"✅ SUCCESS - {description}")
        print(f"Duration: {duration:.2f}s")
        if result.stdout:
            print("\nOutput:")
            print(result.stdout[-1000:])  # Show last 1000 chars
    else:
        print(f"❌ FAILED - {description}")
        print(f"Duration: {duration:.2f}s")
        print("\nError:")
        print(result.stderr[-1000:])  # Show last 1000 chars

    return result.returncode == 0

def main():
    """Main test runner"""
    print("🚀 Otto AI Test Runner")
    print("="*60)

    # Ensure we're in the right directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)

    # Set Python path
    env = os.environ.copy()
    env["PYTHONPATH"] = str(script_dir)

    # Test categories to run
    test_categories = [
        {
            "name": "Unit Tests",
            "cmd": [
                sys.executable, "-m", "pytest",
                "src/memory/tests/",
                "src/intelligence/tests/",
                "src/services/tests/",
                "src/api/tests/",
                "-m", "unit",
                "-v",
                "--cov=src",
                "--cov-report=term-missing"
            ]
        },
        {
            "name": "Integration Tests",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/",
                "-m", "integration",
                "-v",
                "--tb=short"
            ]
        },
        {
            "name": "Performance Tests",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/test_performance.py",
                "-v",
                "--tb=short"
            ]
        },
        {
            "name": "User Acceptance Tests",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/test_user_acceptance.py",
                "-v",
                "--tb=short"
            ]
        },
        {
            "name": "Privacy Compliance Tests",
            "cmd": [
                sys.executable, "-m", "pytest",
                "tests/test_privacy_compliance.py",
                "-v",
                "--tb=short"
            ]
        }
    ]

    # Run all test categories
    results = {}
    overall_start = time.time()

    for test_category in test_categories:
        success = run_command(
            test_category["cmd"],
            test_category["name"]
        )
        results[test_category["name"]] = success

    overall_end = time.time()
    total_duration = overall_end - overall_start

    # Print summary
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for success in results.values() if success)
    total = len(results)

    for category, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {category}")

    print(f"\nOverall Results: {passed}/{total} test suites passed")
    print(f"Total Duration: {total_duration:.2f}s")

    # Check if all tests passed
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The comprehensive testing suite is complete and meets requirements.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed.")
        print("Please review the failures and fix issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
