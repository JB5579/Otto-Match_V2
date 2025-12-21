#!/usr/bin/env python3
"""
Validation script for Stories 1-1 through 1-5
Checks if implementations meet acceptance criteria and are properly structured.
"""

import sys
import os
import importlib
import inspect
from typing import Dict, List, Any, Tuple
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

class StoryValidator:
    """Validator for story implementations"""

    def __init__(self):
        self.validation_results = {}
        self.errors = []
        self.warnings = []

    def log(self, message: str, level: str = "INFO"):
        """Log validation message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")

    def validate_story_1_1(self) -> Dict[str, Any]:
        """Validate Story 1-1: Initialize Semantic Search Infrastructure"""
        self.log("\n=== VALIDATING STORY 1-1: Initialize Semantic Search Infrastructure ===")
        results = {"story": "1-1", "status": "FAIL", "checks": {}}

        # Check 1: Embedding service exists and has required methods
        try:
            from src.semantic.embedding_service import EmbeddingService
            cls = EmbeddingService
            required_methods = [
                "__init__",
                "generate_embedding",
                "batch_generate_embeddings",
                "calculate_similarity",
                "find_similar_vehicles"
            ]

            missing_methods = []
            for method in required_methods:
                if not hasattr(cls, method):
                    missing_methods.append(method)

            if missing_methods:
                results["checks"]["embedding_service_methods"] = f"FAIL: Missing {missing_methods}"
                self.errors.append("Story 1-1: EmbeddingService missing required methods")
            else:
                results["checks"]["embedding_service_methods"] = "PASS"
                self.log("EmbeddingService has all required methods")
        except Exception as e:
            results["checks"]["embedding_service_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-1: Cannot import EmbeddingService: {str(e)}")
            return results

        # Check 2: Vehicle database service exists
        try:
            from src.semantic.vehicle_database_service import VehicleDatabaseService
            results["checks"]["database_service_import"] = "PASS"
            self.log("VehicleDatabaseService imported successfully")
        except Exception as e:
            results["checks"]["database_service_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-1: Cannot import VehicleDatabaseService: {str(e)}")

        # Check 3: Database schema exists
        schema_path = "src/semantic/database_schema.sql"
        if os.path.exists(schema_path):
            results["checks"]["database_schema"] = "PASS"
            self.log("Database schema file exists")
        else:
            results["checks"]["database_schema"] = "FAIL: Schema file missing"
            self.errors.append("Story 1-1: Database schema file not found")

        # Check 4: Setup script exists
        setup_path = "src/semantic/setup_database.py"
        if os.path.exists(setup_path):
            results["checks"]["setup_script"] = "PASS"
            self.log("Database setup script exists")
        else:
            results["checks"]["setup_script"] = "FAIL: Setup script missing"
            self.errors.append("Story 1-1: Database setup script not found")

        # Determine overall status
        all_pass = all(v == "PASS" for v in results["checks"].values())
        results["status"] = "PASS" if all_pass else "FAIL"

        return results

    def validate_story_1_2(self) -> Dict[str, Any]:
        """Validate Story 1-2: Implement Multimodal Vehicle Data Processing"""
        self.log("\n=== VALIDATING STORY 1-2: Implement Multimodal Vehicle Data Processing ===")
        results = {"story": "1-2", "status": "FAIL", "checks": {}}

        # Check 1: Vehicle processing service exists
        try:
            from src.semantic.vehicle_processing_service import VehicleProcessingService
            cls = VehicleProcessingService
            required_methods = [
                "__init__",
                "process_vehicle_data",
                "process_image",
                "process_pdf",
                "extract_text_features",
                "normalize_data"
            ]

            missing_methods = []
            for method in required_methods:
                if not hasattr(cls, method):
                    missing_methods.append(method)

            if missing_methods:
                results["checks"]["processing_service_methods"] = f"FAIL: Missing {missing_methods}"
            else:
                results["checks"]["processing_service_methods"] = "PASS"
                self.log("VehicleProcessingService has all required methods")
        except Exception as e:
            results["checks"]["processing_service_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-2: Cannot import VehicleProcessingService: {str(e)}")

        # Check 2: Batch processing engine exists
        try:
            from src.semantic.batch_processing_engine import BatchProcessingEngine
            results["checks"]["batch_engine_import"] = "PASS"
            self.log("BatchProcessingEngine imported successfully")
        except Exception as e:
            results["checks"]["batch_engine_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-2: Cannot import BatchProcessingEngine: {str(e)}")

        # Check 3: PDF analyzer exists
        if os.path.exists("src/semantic/analyze_lexus_pdf.py"):
            results["checks"]["pdf_analyzer"] = "PASS"
            self.log("PDF analyzer script exists")
        else:
            results["checks"]["pdf_analyzer"] = "FAIL: PDF analyzer missing"
            self.errors.append("Story 1-2: PDF analyzer not found")

        # Determine overall status
        all_pass = all(v == "PASS" for v in results["checks"].values())
        results["status"] = "PASS" if all_pass else "FAIL"

        return results

    def validate_story_1_3(self) -> Dict[str, Any]:
        """Validate Story 1-3: Build Semantic Search API Endpoints"""
        self.log("\n=== VALIDATING STORY 1-3: Build Semantic Search API Endpoints ===")
        results = {"story": "1-3", "status": "FAIL", "checks": {}}

        # Check 1: Semantic search API exists
        try:
            from src.api.semantic_search_api import app
            results["checks"]["api_import"] = "PASS"
            self.log("Semantic search API imported successfully")
        except Exception as e:
            results["checks"]["api_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-3: Cannot import semantic search API: {str(e)}")

        # Check 2: Test endpoints exist
        if os.path.exists("src/api/test_semantic_search_api.py"):
            results["checks"]["test_endpoints"] = "PASS"
            self.log("Test endpoints file exists")
        else:
            results["checks"]["test_endpoints"] = "FAIL: Test endpoints missing"
            self.errors.append("Story 1-3: Test endpoints not found")

        # Check 3: Validation script exists
        if os.path.exists("src/api/validate_semantic_search_api.py"):
            results["checks"]["validation_script"] = "PASS"
            self.log("Validation script exists")
        else:
            results["checks"]["validation_script"] = "FAIL: Validation script missing"
            self.errors.append("Story 1-3: Validation script not found")

        # Determine overall status
        all_pass = all(v == "PASS" for v in results["checks"].values())
        results["status"] = "PASS" if all_pass else "FAIL"

        return results

    def validate_story_1_4(self) -> Dict[str, Any]:
        """Validate Story 1-4: Implement Intelligent Vehicle Filtering with Context"""
        self.log("\n=== VALIDATING STORY 1-4: Implement Intelligent Vehicle Filtering with Context ===")
        results = {"story": "1-4", "status": "FAIL", "checks": {}}

        # Check 1: Filter service exists
        try:
            from src.search.filter_service import FilterService
            results["checks"]["filter_service_import"] = "PASS"
            self.log("FilterService imported successfully")
        except Exception as e:
            results["checks"]["filter_service_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-4: Cannot import FilterService: {str(e)}")

        # Check 2: Filter management API exists
        try:
            from src.api.filter_management_api import app
            results["checks"]["filter_api_import"] = "PASS"
            self.log("Filter management API imported successfully")
        except Exception as e:
            results["checks"]["filter_api_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-4: Cannot import filter management API: {str(e)}")

        # Determine overall status
        all_pass = all(v == "PASS" for v in results["checks"].values())
        results["status"] = "PASS" if all_pass else "FAIL"

        return results

    def validate_story_1_5(self) -> Dict[str, Any]:
        """Validate Story 1-5: Build Vehicle Comparison and Recommendation Engine"""
        self.log("\n=== VALIDATING STORY 1-5: Build Vehicle Comparison and Recommendation Engine ===")
        results = {"story": "1-5", "status": "FAIL", "checks": {}}

        # Check 1: Comparison engine exists
        try:
            from src.recommendation.comparison_engine import ComparisonEngine
            results["checks"]["comparison_engine_import"] = "PASS"
            self.log("ComparisonEngine imported successfully")
        except Exception as e:
            results["checks"]["comparison_engine_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-5: Cannot import ComparisonEngine: {str(e)}")

        # Check 2: Recommendation engine exists
        try:
            from src.recommendation.recommendation_engine import RecommendationEngine
            results["checks"]["recommendation_engine_import"] = "PASS"
            self.log("RecommendationEngine imported successfully")
        except Exception as e:
            results["checks"]["recommendation_engine_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-5: Cannot import RecommendationEngine: {str(e)}")

        # Check 3: Interaction tracker exists
        try:
            from src.recommendation.interaction_tracker import InteractionTracker
            results["checks"]["interaction_tracker_import"] = "PASS"
            self.log("InteractionTracker imported successfully")
        except Exception as e:
            results["checks"]["interaction_tracker_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-5: Cannot import InteractionTracker: {str(e)}")

        # Check 4: Vehicle comparison API exists
        try:
            from src.api.vehicle_comparison_api import app
            results["checks"]["comparison_api_import"] = "PASS"
            self.log("Vehicle comparison API imported successfully")
        except Exception as e:
            results["checks"]["comparison_api_import"] = f"FAIL: {str(e)}"
            self.errors.append(f"Story 1-5: Cannot import vehicle comparison API: {str(e)}")

        # Determine overall status
        all_pass = all(v == "PASS" for v in results["checks"].values())
        results["status"] = "PASS" if all_pass else "FAIL"

        return results

    def generate_remadiation_plan(self, validation_results: List[Dict[str, Any]]) -> str:
        """Generate a remediation plan based on validation results"""
        plan = ["# REMEDIATION PLAN FOR STORIES 1-1 THROUGH 1-5\n"]
        plan.append(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        total_stories = len(validation_results)
        passed_stories = sum(1 for r in validation_results if r["status"] == "PASS")
        failed_stories = total_stories - passed_stories

        plan.append("## SUMMARY")
        plan.append(f"- Total Stories: {total_stories}")
        plan.append(f"- Passed: {passed_stories}")
        plan.append(f"- Failed: {failed_stories}\n")

        if self.errors:
            plan.append("## CRITICAL ERRORS\n")
            for error in self.errors:
                plan.append(f"- ❌ {error}\n")

        if self.warnings:
            plan.append("## WARNINGS\n")
            for warning in self.warnings:
                plan.append(f"- ⚠️ {warning}\n")

        plan.append("\n## REMEDIATION ACTIONS\n")

        # Group by type of issue
        import_issues = [e for e in self.errors if "Cannot import" in e]
        missing_methods = [e for e in self.errors if "Missing" in e and "methods" in e]
        missing_files = [e for e in self.errors if "not found" in e or "missing" in e.lower()]

        if import_issues:
            plan.append("### 1. Fix Import Issues\n")
            plan.append("Many modules have circular import dependencies. Follow these steps:\n")
            plan.append("1. Move all shared data models to `src/models/` package\n")
            plan.append("2. Ensure all `__init__.py` files are properly created\n")
            plan.append("3. Use relative imports for intra-package references\n")
            plan.append("4. Run `python -m pytest` to validate fixes\n\n")

        if missing_methods:
            plan.append("### 2. Implement Missing Methods\n")
            plan.append("The following classes need methods implemented:\n")
            for issue in missing_methods:
                plan.append(f"- {issue}\n")
            plan.append("\n")

        if missing_files:
            plan.append("### 3. Create Missing Files\n")
            plan.append("The following files are missing:\n")
            for issue in missing_files:
                plan.append(f"- {issue}\n")
            plan.append("\n")

        # Story-specific recommendations
        plan.append("### 4. Story-Specific Actions\n")

        for result in validation_results:
            if result["status"] == "FAIL":
                plan.append(f"\n#### Story {result['story']}:\n")
                for check, status in result["checks"].items():
                    if status.startswith("FAIL"):
                        plan.append(f"- Fix: {check} - {status.replace('FAIL: ', '')}\n")

        plan.append("\n### 5. Testing and Validation\n")
        plan.append("After fixing issues:\n")
        plan.append("1. Run all validation scripts to ensure imports work\n")
        plan.append("2. Execute unit tests for each module\n")
        plan.append("3. Run integration tests to verify API endpoints\n")
        plan.append("4. Perform end-to-end testing of the full workflow\n")

        return "\n".join(plan)

    def run_all_validations(self) -> Tuple[List[Dict[str, Any]], str]:
        """Run validations for all stories and return results with remediation plan"""
        self.log("Starting validation of Stories 1-1 through 1-5...")

        results = []
        results.append(self.validate_story_1_1())
        results.append(self.validate_story_1_2())
        results.append(self.validate_story_1_3())
        results.append(self.validate_story_1_4())
        results.append(self.validate_story_1_5())

        # Generate summary
        passed = sum(1 for r in results if r["status"] == "PASS")
        total = len(results)

        self.log(f"\n=== VALIDATION SUMMARY ===")
        self.log(f"Stories validated: {total}")
        self.log(f"Passed: {passed}")
        self.log(f"Failed: {total - passed}")

        # Generate remediation plan
        remediation_plan = self.generate_remadiation_plan(results)

        # Save remediation plan
        with open("remediation_plan_stories_1_5.md", "w") as f:
            f.write(remediation_plan)

        self.log("\nRemediation plan saved to: remediation_plan_stories_1_5.md")

        return results, remediation_plan


def main():
    """Main validation runner"""
    validator = StoryValidator()
    results, plan = validator.run_all_validations()

    # Print final status
    print("\n" + "="*60)
    print("VALIDATION COMPLETE")
    print("="*60)

    for result in results:
        status_emoji = "✅" if result["status"] == "PASS" else "❌"
        print(f"{status_emoji} Story {result['story']}: {result['status']}")

    return all(r["status"] == "PASS" for r in results)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)