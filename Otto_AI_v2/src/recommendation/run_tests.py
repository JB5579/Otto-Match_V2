#!/usr/bin/env python3
"""
Test Runner for Vehicle Comparison and Recommendation Engine

Story 1-5: Build Vehicle Comparison and Recommendation Engine
Comprehensive test execution and reporting.
"""

import asyncio
import sys
import os
import time
import traceback
from datetime import datetime
from typing import List, Dict, Any
import subprocess

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

class TestRunner:
    """Comprehensive test runner for Story 1-5"""

    def __init__(self):
        self.test_files = [
            'test_comparison_engine.py',
            'test_recommendation_engine.py',
            'test_interaction_tracker.py',
            'test_integration.py'
        ]
        self.results = {}
        self.start_time = None

    def print_header(self):
        """Print test suite header"""
        print("=" * 80)
        print("OTTO.AI VEHICLE COMPARISON AND RECOMMENDATION ENGINE TESTS")
        print("Story 1-5: Build Vehicle Comparison and Recommendation Engine")
        print(f"Test Execution Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print()

    def run_test_file(self, test_file: str) -> Dict[str, Any]:
        """Run individual test file"""
        print(f"Running tests in {test_file}...")
        print("-" * 60)

        start_time = time.time()

        try:
            # Run pytest and capture output
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', test_file, '-v', '--tb=short'],
                capture_output=True,
                text=True,
                cwd=os.path.dirname(__file__)
            )

            execution_time = time.time() - start_time

            # Parse results
            output_lines = result.stdout.strip().split('\n')
            summary_lines = [line for line in output_lines if '=' in line and ('passed' in line or 'failed' in line or 'error' in line)]

            # Extract test counts
            total_tests = 0
            passed_tests = 0
            failed_tests = 0
            error_tests = 0
            skipped_tests = 0

            for line in summary_lines:
                if 'passed' in line or 'failed' in line or 'error' in line or 'skipped' in line:
                    parts = line.split()
                    for i, part in enumerate(parts):
                        if part.isdigit():
                            count = int(part)
                            if i > 0:
                                prev_part = parts[i-1]
                                if 'passed' in prev_part:
                                    passed_tests = count
                                elif 'failed' in prev_part:
                                    failed_tests = count
                                elif 'error' in prev_part:
                                    error_tests = count
                                elif 'skipped' in prev_part:
                                    skipped_tests = count
                                total_tests += count

            success = result.returncode == 0

            return {
                'file': test_file,
                'success': success,
                'execution_time': execution_time,
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'error_tests': error_tests,
                'skipped_tests': skipped_tests,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode
            }

        except Exception as e:
            execution_time = time.time() - start_time
            print(f"Error running {test_file}: {str(e)}")

            return {
                'file': test_file,
                'success': False,
                'execution_time': execution_time,
                'total_tests': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'error_tests': 0,
                'skipped_tests': 0,
                'stdout': '',
                'stderr': str(e),
                'return_code': -1,
                'exception': traceback.format_exc()
            }

    def print_test_result(self, result: Dict[str, Any]):
        """Print individual test result"""
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"{status} {result['file']}")
        print(f"   Execution Time: {result['execution_time']:.2f}s")
        print(f"   Total Tests: {result['total_tests']}")
        print(f"   Passed: {result['passed_tests']}")
        print(f"   Failed: {result['failed_tests']}")
        print(f"   Errors: {result['error_tests']}")
        print(f"   Skipped: {result['skipped_tests']}")

        if not result['success']:
            print("   Errors/Output:")
            if result.get('exception'):
                print(f"     Exception: {result.get('exception', 'Unknown')}")
            elif result['stderr']:
                for line in result['stderr'].split('\n')[:10]:  # First 10 lines
                    if line.strip():
                        print(f"     {line}")

        print()

    def print_summary(self):
        """Print comprehensive test summary"""
        total_time = time.time() - self.start_time
        total_files = len(self.results)
        successful_files = sum(1 for r in self.results if r['success'])
        total_tests = sum(r['total_tests'] for r in self.results)
        total_passed = sum(r['passed_tests'] for r in self.results)
        total_failed = sum(r['failed_tests'] for r in self.results)
        total_errors = sum(r['error_tests'] for r in self.results)
        total_skipped = sum(r['skipped_tests'] for r in self.results)

        print("=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"Total Execution Time: {total_time:.2f}s")
        print(f"Test Files: {total_files}")
        print(f"  Successful: {successful_files}")
        print(f"  Failed: {total_files - successful_files}")
        print()
        print(f"Total Tests: {total_tests}")
        print(f"  Passed: {total_passed}")
        print(f"  Failed: {total_failed}")
        print(f"  Errors: {total_errors}")
        print(f"  Skipped: {total_skipped}")

        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"  Success Rate: {success_rate:.1f}%")

        print()

        # Test coverage information
        print("TEST COVERAGE BY COMPONENT:")
        print("-" * 40)

        component_coverage = {
            'Comparison Engine': ['test_comparison_engine.py'],
            'Recommendation Engine': ['test_recommendation_engine.py'],
            'Interaction Tracker': ['test_interaction_tracker.py'],
            'Integration Tests': ['test_integration.py']
        }

        for component, files in component_coverage.items():
            component_results = [r for r in self.results if r['file'] in files]
            component_tests = sum(r['total_tests'] for r in component_results)
            component_passed = sum(r['passed_tests'] for r in component_results)

            if component_tests > 0:
                component_success_rate = (component_passed / component_tests) * 100
                status = "✅" if component_success_rate == 100 else "⚠️" if component_success_rate >= 80 else "❌"
                print(f"{status} {component}: {component_tests} tests, {component_success_rate:.1f}% success")
            else:
                print(f"❓ {component}: No tests executed")

        print()

        # Performance summary
        print("PERFORMANCE SUMMARY:")
        print("-" * 40)
        avg_time = sum(r['execution_time'] for r in self.results) / len(self.results) if self.results else 0
        slowest_file = max(self.results, key=lambda r: r['execution_time']) if self.results else None
        fastest_file = min(self.results, key=lambda r: r['execution_time']) if self.results else None

        print(f"Average test execution time: {avg_time:.2f}s")
        if slowest_file:
            print(f"Slowest test file: {slowest_file['file']} ({slowest_file['execution_time']:.2f}s)")
        if fastest_file:
            print(f"Fastest test file: {fastest_file['file']} ({fastest_file['execution_time']:.2f}s)")

        print()

        # Final verdict
        print("FINAL VERDICT:")
        print("-" * 40)
        if all(r['success'] for r in self.results):
            print("🎉 ALL TESTS PASSED! Story 1-5 implementation is ready for review.")
        else:
            failed_files = [r['file'] for r in self.results if not r['success']]
            print(f"❌ {len(failed_files)} test file(s) failed:")
            for file in failed_files:
                print(f"   - {file}")
            print("\nPlease review failed tests before proceeding with Story 1-5 completion.")

        print("=" * 80)
        print(f"Test Execution Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    def run_all_tests(self):
        """Run all test files"""
        self.start_time = time.time()
        self.print_header()

        for test_file in self.test_files:
            if os.path.exists(test_file):
                result = self.run_test_file(test_file)
                self.results[test_file] = result
                self.print_test_result(result)
            else:
                print(f"⚠️ Test file not found: {test_file}")
                self.results[test_file] = {
                    'file': test_file,
                    'success': False,
                    'execution_time': 0,
                    'total_tests': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'error_tests': 0,
                    'skipped_tests': 0,
                    'stdout': '',
                    'stderr': 'File not found',
                    'return_code': -1
                }

        self.print_summary()

        # Return overall success status
        return all(r['success'] for r in self.results)


class TestValidator:
    """Validate test coverage and quality"""

    def __init__(self):
        self.required_test_types = [
            'unit_tests',
            'integration_tests',
            'performance_tests',
            'error_handling_tests',
            'edge_case_tests'
        ]

    def validate_coverage(self, test_file: str, content: str) -> Dict[str, bool]:
        """Validate test coverage for a test file"""
        coverage = {
            'has_unit_tests': 'def test_' in content and 'class Test' in content,
            'has_async_tests': '@pytest.mark.asyncio' in content,
            'has_mock_usage': 'Mock' in content or 'mock_' in content,
            'has_error_tests': any(keyword in content.lower() for keyword in ['error', 'exception', 'invalid']),
            'has_edge_cases': any(keyword in content.lower() for keyword in ['empty', 'none', 'zero', 'negative', 'invalid']),
            'has_performance_tests': 'performance' in content.lower() or 'time' in content.lower(),
            'has_integration_tests': 'Integration' in content
        }
        return coverage

    def print_validation_report(self, all_results: List[Dict[str, Any]]):
        """Print validation report"""
        print("\nTEST VALIDATION REPORT:")
        print("-" * 50)

        total_files = len(all_results)
        files_with_full_coverage = 0

        for result in all_results:
            coverage = result.get('coverage', {})
            coverage_score = sum(coverage.values()) / len(coverage) if coverage else 0

            if coverage_score >= 0.8:  # 80% coverage threshold
                files_with_full_coverage += 1
                status = "✅"
            else:
                status = "⚠️"

            print(f"{status} {result['file']}: {coverage_score:.1%} coverage")

            # Show missing coverage areas
            missing_areas = [area for area, covered in coverage.items() if not covered]
            if missing_areas:
                print(f"   Missing: {', '.join(missing_areas)}")

        print(f"\nOverall Coverage: {files_with_full_coverage}/{total_files} files have adequate test coverage")


def main():
    """Main test execution function"""
    print("Starting Otto.AI Story 1-5 Test Suite...")

    # Check if pytest is available
    try:
        import pytest
        print(f"Using pytest version: {pytest.__version__}")
    except ImportError:
        print("❌ pytest is not installed. Please install it with: pip install pytest pytest-asyncio")
        return False

    # Run tests
    runner = TestRunner()
    success = runner.run_all_tests()

    # Validate test coverage
    validator = TestValidator()
    validation_results = []

    for test_file in runner.test_files:
        if os.path.exists(test_file):
            with open(test_file, 'r') as f:
                content = f.read()
            coverage = validator.validate_coverage(test_file, content)
            validation_results.append({
                'file': test_file,
                'coverage': coverage
            })

    validator.print_validation_report(validation_results)

    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)