#!/usr/bin/env python3
"""
Otto.AI Setup Validation Script
Validates that all dependencies are installed and database connectivity works
"""

import os
import sys
import subprocess
import importlib
import asyncio
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SetupValidator:
    """Validates Otto.AI setup dependencies and connectivity"""

    def __init__(self):
        self.required_packages = [
            'raganything',
            'lightrag',
            'supabase',
            'pgvector',
            'psycopg',
            'fastapi',
            'pydantic',
            'requests',
            'numpy'
        ]
        self.validation_results: Dict[str, bool] = {}

    def check_package_installation(self) -> bool:
        """Check if all required Python packages are installed"""
        logger.info("🔍 Checking package installations...")

        all_installed = True
        for package in self.required_packages:
            try:
                importlib.import_module(package)
                logger.info(f"✅ {package} is installed")
                self.validation_results[f'package_{package}'] = True
            except ImportError:
                logger.error(f"❌ {package} is NOT installed")
                self.validation_results[f'package_{package}'] = False
                all_installed = False

        return all_installed

    def check_environment_variables(self) -> bool:
        """Check if required environment variables are set"""
        logger.info("🔍 Checking environment variables...")

        required_vars = [
            'SUPABASE_DB_PASSWORD'
        ]

        all_set = True
        for var in required_vars:
            if os.getenv(var):
                logger.info(f"✅ {var} is set")
                self.validation_results[f'env_{var}'] = True
            else:
                logger.error(f"❌ {var} is NOT set")
                self.validation_results[f'env_{var}'] = False
                all_set = False

        return all_set

    async def test_openrouter_api(self) -> bool:
        """Test OpenRouter API connectivity"""
        logger.info("🔍 Testing OpenRouter API connectivity...")

        try:
            import requests
            import json

            api_key = os.getenv('OPENROUTER_API_KEY')
            if not api_key:
                logger.warning("⚠️ OPENROUTER_API_KEY not set, skipping API test")
                self.validation_results['openrouter_api'] = None
                return True

            # Test API with a simple embedding request
            response = requests.post(
                url="https://openrouter.ai/api/v1/embeddings",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://otto-ai.com",
                    "X-Title": "Otto.AI Setup Validation",
                },
                data=json.dumps({
                    "model": "openai/text-embedding-3-large",
                    "input": "Test embedding generation for validation",
                    "encoding_format": "float"
                }),
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                embedding = result.get('data', [{}])[0].get('embedding', [])
                if len(embedding) == 3072:  # Expected dimension
                    logger.info(f"✅ OpenRouter API test successful (embedding dimension: {len(embedding)})")
                    self.validation_results['openrouter_api'] = True
                    return True
                else:
                    logger.error(f"❌ OpenRouter API returned incorrect embedding dimension: {len(embedding)} (expected 3072)")
                    self.validation_results['openrouter_api'] = False
                    return False
            else:
                logger.error(f"❌ OpenRouter API request failed with status {response.status_code}")
                self.validation_results['openrouter_api'] = False
                return False

        except Exception as e:
            logger.error(f"❌ OpenRouter API test failed: {e}")
            self.validation_results['openrouter_api'] = False
            return False

    def test_database_connectivity(self) -> bool:
        """Test database connectivity and pgvector functionality"""
        logger.info("🔍 Testing database connectivity...")

        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor

            # Build connection string
            connection_string = os.getenv('SUPABASE_DB_URL')
            if not connection_string:
                # Fallback to individual variables
                host = os.getenv('SUPABASE_DB_HOST', 'localhost')
                port = os.getenv('SUPABASE_DB_PORT', '5432')
                database = os.getenv('SUPABASE_DB_NAME', 'postgres')
                user = os.getenv('SUPABASE_DB_USER', 'postgres')
                password = os.getenv('SUPABASE_DB_PASSWORD')

                if not password:
                    logger.error("❌ SUPABASE_DB_PASSWORD is required")
                    self.validation_results['database_connection'] = False
                    return False

                connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"

            # Test connection
            conn = psycopg2.connect(
                connection_string,
                cursor_factory=RealDictCursor
            )

            # Test pgvector functionality
            cursor = conn.cursor()
            cursor.execute("""
                SELECT EXISTS (
                    SELECT 1 FROM pg_extension
                    WHERE extname = 'vector'
                );
            """)
            pgvector_exists = cursor.fetchone()[0]

            if not pgvector_exists:
                logger.error("❌ pgvector extension is not installed")
                self.validation_results['database_pgvector'] = False
                conn.close()
                return False

            # Test vector operations
            cursor.execute("""
                CREATE TEMPORARY TABLE test_vectors (
                    id serial PRIMARY KEY,
                    embedding vector(3072)
                );
            """)

            # Insert test vector with correct dimension
            test_embedding = [0.0] * 3072  # Zero vector of correct dimension
            cursor.execute(
                "INSERT INTO test_vectors (embedding) VALUES (%s);",
                (test_embedding,)
            )

            # Test similarity search
            cursor.execute("""
                SELECT id FROM test_vectors
                ORDER BY embedding <-> %s
                LIMIT 1;
            """, (test_embedding,))

            result = cursor.fetchone()
            cursor.execute("DROP TABLE test_vectors;")
            cursor.close()
            conn.close()

            if result:
                logger.info("✅ Database connectivity and pgvector functionality verified")
                self.validation_results['database_connection'] = True
                self.validation_results['database_pgvector'] = True
                return True
            else:
                logger.error("❌ Database vector operations test failed")
                self.validation_results['database_connection'] = False
                return False

        except Exception as e:
            logger.error(f"❌ Database connectivity test failed: {e}")
            self.validation_results['database_connection'] = False
            return False

    def test_basic_imports(self) -> bool:
        """Test basic imports for the embedding service"""
        logger.info("🔍 Testing basic imports...")

        import_tests = [
            ('raganything', 'RAGAnything'),
            ('lightrag', 'LightRAG'),
            ('supabase', 'Supabase client'),
            ('pgvector', 'pgvector'),
            ('fastapi', 'FastAPI'),
            ('pydantic', 'Pydantic'),
            ('requests', 'Requests'),
            ('numpy', 'NumPy')
        ]

        all_good = True
        for module, name in import_tests:
            try:
                importlib.import_module(module)
                logger.info(f"✅ {name} import successful")
                self.validation_results[f'import_{module}'] = True
            except ImportError as e:
                logger.error(f"❌ {name} import failed: {e}")
                self.validation_results[f'import_{module}'] = False
                all_good = False

        return all_good

    async def run_all_validations(self) -> bool:
        """Run all validation checks"""
        logger.info("🚀 Starting Otto.AI setup validation")

        # Check package installations
        if not self.check_package_installation():
            logger.error("Package validation failed")
            return False

        # Check environment variables
        if not self.check_environment_variables():
            logger.error("Environment variable validation failed")
            return False

        # Test basic imports
        if not self.test_basic_imports():
            logger.error("Import validation failed")
            return False

        # Test database connectivity
        if not self.test_database_connectivity():
            logger.error("Database validation failed")
            return False

        # Test OpenRouter API (if API key is set)
        if os.getenv('OPENROUTER_API_KEY'):
            if not await self.test_openrouter_api():
                logger.error("OpenRouter API validation failed")
                return False

        return True

    def print_summary(self):
        """Print validation summary"""
        logger.info("=" * 60)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 60)

        total_checks = len(self.validation_results)
        passed_checks = sum(1 for v in self.validation_results.values() if v is True)
        failed_checks = total_checks - passed_checks
        skipped_checks = sum(1 for v in self.validation_results.values() if v is None)

        print(f"Total Checks: {total_checks}")
        print(f"✅ Passed: {passed_checks}")
        print(f"❌ Failed: {failed_checks}")
        if skipped_checks > 0:
            print(f"⚠️  Skipped: {skipped_checks}")

        if failed_checks == 0:
            print("\n🎉 All validations passed! Otto.AI setup is ready for development.")
        else:
            print("\n⚠️  Some validations failed. Please fix the issues above.")
            print("\nRecommendations:")

            for check, result in self.validation_results.items():
                if not result and result is not None:
                    if check.startswith('package_'):
                        package = check.replace('package_', '')
                        print(f"  - Install {package}: pip install {package}")
                    elif check.startswith('env_'):
                        var = check.replace('env_', '')
                        print(f"  - Set {var} environment variable")
                    elif check == 'database_connection':
                        print("  - Check database credentials and connectivity")
                    elif check == 'openrouter_api':
                        print("  - Verify OPENROUTER_API_KEY is valid")

async def main():
    """Main validation function"""
    print("Otto.AI Setup Validation")
    print("=" * 50)

    validator = SetupValidator()
    success = await validator.run_all_validations()

    validator.print_summary()

    if not success:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())