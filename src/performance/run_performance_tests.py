#!/usr/bin/env python3
"""
Performance Test Runner for Otto.AI
Comprehensive performance testing script for Story 1-8

Usage:
    python run_performance_tests.py --test-type all
    python run_performance_tests.py --test-type semantic_search
    python run_performance_tests.py --test-type cache
    python run_performance_tests.py --test-type regression
"""

import asyncio
import argparse
import json
import logging
import sys
import os
from datetime import datetime
from typing import Dict, Any, List

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from src.performance.performance_test_suite import (
    PerformanceTestSuite,
    PerformanceThresholds
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main performance test runner"""
    parser = argparse.ArgumentParser(description="Otto.AI Performance Test Runner")
    parser.add_argument(
        "--test-type",
        choices=["all", "semantic_search", "cache", "database", "connection_pool", "end_to_end", "regression"],
        default="all",
        help="Type of performance test to run"
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="Test duration in seconds (default: 30)"
    )
    parser.add_argument(
        "--concurrent-users",
        type=int,
        default=5,
        help="Number of concurrent users (default: 5)"
    )
    parser.add_argument(
        "--output",
        default="performance_results.json",
        help="Output file for results (default: performance_results.json)"
    )
    parser.add_argument(
        "--supabase-url",
        help="Supabase URL for database tests"
    )
    parser.add_argument(
        "--supabase-key",
        help="Supabase key for database tests"
    )
    parser.add_argument(
        "--redis-url",
        default="redis://localhost:6379",
        help="Redis URL for cache tests"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create performance test suite
    thresholds = PerformanceThresholds(
        max_avg_response_time_ms=500.0,
        max_p95_response_time_ms=1000.0,
        max_p99_response_time_ms=2000.0,
        min_requests_per_second=10.0,
        max_error_rate_percent=1.0,
        max_cpu_usage_percent=80.0,
        max_memory_usage_mb=1000.0
    )

    test_suite = PerformanceTestSuite(
        test_duration_seconds=args.duration,
        concurrent_users=args.concurrent_users,
        thresholds=thresholds
    )

    # Initialize test suite
    logger.info("🚀 Initializing Performance Test Suite...")
    success = await test_suite.initialize(
        supabase_url=args.supabase_url,
        supabase_key=args.supabase_key,
        redis_url=args.redis_url
    )

    if not success:
        logger.error("❌ Failed to initialize test suite")
        sys.exit(1)

    logger.info(f"✅ Test suite initialized")
    logger.info(f"📊 Test Configuration:")
    logger.info(f"   - Duration: {args.duration} seconds")
    logger.info(f"   - Concurrent Users: {args.concurrent_users}")
    logger.info(f"   - Test Type: {args.test_type}")

    # Run tests based on type
    results = []

    try:
        if args.test_type in ["all", "semantic_search"]:
            logger.info("\n🔍 Running Semantic Search Performance Test...")
            queries = [
                "SUV under 30000",
                "electric vehicles with good range",
                "luxury sedan with leather seats",
                "family friendly SUV",
                "fuel efficient compact car"
            ] * 20  # 100 total queries

            result = await test_suite.run_semantic_search_test(queries)
            evaluation = test_suite.evaluate_test_result(result)
            results.append({
                "test": "semantic_search",
                "result": result,
                "evaluation": evaluation
            })

            logger.info(f"   ✅ Completed: {result.requests_per_second:.2f} req/s, {result.avg_response_time_ms:.2f}ms avg")
            logger.info(f"   Status: {'PASS' if evaluation['passed'] else 'FAIL'}")

        if args.test_type in ["all", "cache"]:
            logger.info("\n💾 Running Cache Performance Test...")
            cache_keys = [f"vehicle_{i}" for i in range(100)]

            result = await test_suite.run_cache_performance_test(
                cache_operations=500,
                cache_keys=cache_keys
            )
            evaluation = test_suite.evaluate_test_result(result)
            results.append({
                "test": "cache",
                "result": result,
                "evaluation": evaluation
            })

            logger.info(f"   ✅ Completed: {result.requests_per_second:.2f} ops/s")
            logger.info(f"   Cache Hit Rate: {result.custom_metrics.get('cache_hit_rate', 0):.1f}%")
            logger.info(f"   Status: {'PASS' if evaluation['passed'] else 'FAIL'}")

        if args.test_type in ["all", "database"] and args.supabase_url:
            logger.info("\n🗄️ Running Database Stress Test...")
            query_templates = [
                "SELECT * FROM vehicles WHERE price < $1",
                "SELECT COUNT(*) FROM vehicles WHERE make = 'Toyota'",
                "SELECT * FROM vehicles ORDER BY year DESC LIMIT $1",
                "SELECT make, model, AVG(price) FROM vehicles GROUP BY make, model",
                "SELECT * FROM vehicles WHERE year >= 2020 AND mileage < 50000"
            ]

            result = await test_suite.run_database_stress_test(
                query_templates=query_templates,
                num_queries=200
            )
            evaluation = test_suite.evaluate_test_result(result)
            results.append({
                "test": "database",
                "result": result,
                "evaluation": evaluation
            })

            logger.info(f"   ✅ Completed: {result.requests_per_second:.2f} qps, {result.avg_response_time_ms:.2f}ms avg")
            logger.info(f"   Status: {'PASS' if evaluation['passed'] else 'FAIL'}")

        if args.test_type in ["all", "connection_pool"]:
            logger.info("\n🔌 Running Connection Pool Test...")
            from src.scaling.connection_pool import DatabaseConfig

            pool_config = DatabaseConfig(
                host="localhost",
                port=5432,
                database="test",
                username="test",
                password="test",
                max_connections=20,
                min_connections=2
            )

            result = await test_suite.run_connection_pool_test(
                pool_config=pool_config,
                operations=300
            )
            evaluation = test_suite.evaluate_test_result(result)
            results.append({
                "test": "connection_pool",
                "result": result,
                "evaluation": evaluation
            })

            logger.info(f"   ✅ Completed: {result.requests_per_second:.2f} ops/s")
            logger.info(f"   Status: {'PASS' if evaluation['passed'] else 'FAIL'}")

        if args.test_type in ["all", "end_to_end"]:
            logger.info("\n🔄 Running End-to-End Performance Test...")
            user_scenarios = [
                {
                    "name": "Vehicle Search Flow",
                    "steps": [
                        {"type": "cache_read", "key": "popular_searches"},
                        {"type": "search", "query": "SUV"},
                        {"type": "cache_read", "key": "vehicle_details_123"},
                        {"type": "delay", "duration": 0.1}
                    ]
                },
                {
                    "name": "Quick Search",
                    "steps": [
                        {"type": "search", "query": "electric"},
                        {"type": "delay", "duration": 0.05}
                    ]
                }
            ] * 25  # 50 total scenarios

            result = await test_suite.run_end_to_end_test(user_scenarios)
            evaluation = test_suite.evaluate_test_result(result)
            results.append({
                "test": "end_to_end",
                "result": result,
                "evaluation": evaluation
            })

            logger.info(f"   ✅ Completed: {result.requests_per_second:.2f} scenarios/s")
            logger.info(f"   Status: {'PASS' if evaluation['passed'] else 'FAIL'}")

        if args.test_type in ["all", "regression"]:
            logger.info("\n📊 Running Performance Regression Test...")
            regression_report = await test_suite.run_performance_regression_test()
            results.append({
                "test": "regression",
                "result": regression_report,
                "evaluation": {"passed": regression_report.get("overall_status") == "passed"}
            })

            logger.info(f"   ✅ Regression Test Status: {regression_report.get('overall_status', 'unknown')}")

    except Exception as e:
        logger.error(f"❌ Test execution failed: {e}")
        sys.exit(1)

    # Generate comprehensive report
    logger.info("\n📋 Generating Performance Report...")
    report = await test_suite.generate_performance_report()
    report["test_results"] = results

    # Save results to file
    output_data = {
        "test_run": {
            "timestamp": datetime.now().isoformat(),
            "configuration": {
                "test_type": args.test_type,
                "duration_seconds": args.duration,
                "concurrent_users": args.concurrent_users,
                "thresholds": {
                    "max_avg_response_time_ms": thresholds.max_avg_response_time_ms,
                    "max_p95_response_time_ms": thresholds.max_p95_response_time_ms,
                    "min_requests_per_second": thresholds.min_requests_per_second,
                    "max_error_rate_percent": thresholds.max_error_rate_percent
                }
            }
        },
        "report": report
    }

    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2, default=str)

    logger.info(f"✅ Results saved to {args.output}")

    # Print summary
    logger.info("\n📊 Performance Test Summary:")
    passed_tests = sum(1 for r in results if r["evaluation"]["passed"])
    total_tests = len(results)

    logger.info(f"   Total Tests: {total_tests}")
    logger.info(f"   Passed: {passed_tests}")
    logger.info(f"   Failed: {total_tests - passed_tests}")

    if total_tests > 0:
        logger.info(f"   Success Rate: {(passed_tests / total_tests) * 100:.1f}%")

    # Print failed tests
    failed_tests = [r for r in results if not r["evaluation"]["passed"]]
    if failed_tests:
        logger.info("\n❌ Failed Tests:")
        for test in failed_tests:
            logger.info(f"   - {test['test']}:")
            for violation in test["evaluation"].get("threshold_violations", []):
                logger.info(f"     • {violation}")

    logger.info(f"\n{'✅ All tests completed successfully!' if passed_tests == total_tests else '❌ Some tests failed'}")

    # Exit with appropriate code
    sys.exit(0 if passed_tests == total_tests else 1)

if __name__ == "__main__":
    asyncio.run(main())