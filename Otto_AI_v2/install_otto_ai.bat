@echo off
REM Otto.AI Installation Script (Windows)
REM Sets up the development environment for Otto.AI semantic search infrastructure

REM Story: 1.1-initialize-semantic-search-infrastructure
REM Task: Write installation script for development environment (AC: #4)

echo 🚀 Otto.AI Installation Script
echo ==================================
echo Setting up development environment for semantic search infrastructure
echo.

REM Check if Python is installed
echo ℹ️  Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Check if pip is installed
echo ℹ️  Checking pip installation...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not installed. Please install pip.
    pause
    exit /b 1
)
echo ✅ pip found

REM Create virtual environment
echo ℹ️  Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ⚠️  Virtual environment already exists
)

REM Activate virtual environment
echo ℹ️  Activating virtual environment...
call venv\Scripts\activate.bat
echo ✅ Virtual environment activated

REM Upgrade pip
echo ℹ️  Upgrading pip...
python -m pip install --upgrade pip
echo ✅ pip upgraded

REM Install dependencies
echo ℹ️  Installing Python dependencies...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo ✅ Dependencies installed from requirements.txt
) else (
    echo ❌ requirements.txt not found
    pause
    exit /b 1
)

REM Create necessary directories
echo ℹ️  Creating necessary directories...
if not exist "src\semantic" mkdir src\semantic
if not exist "src\api" mkdir src\api
if not exist "tests\unit\semantic" mkdir tests\unit\semantic
if not exist "tests\integration\semantic" mkdir tests\integration\semantic
if not exist "tests\performance" mkdir tests\performance
if not exist "logs" mkdir logs
if not exist "data\sample_vehicles" mkdir data\sample_vehicles
echo ✅ Directories created

REM Check environment variables
echo ℹ️  Checking environment variables...
if not exist ".env" (
    echo ⚠️  .env file not found. Creating template...
    (
    echo # Otto.AI Environment Variables
    echo # Add your actual API keys and configuration values here
    echo.
    echo # Supabase Configuration
    echo SUPABASE_URL=your_supabase_url_here
    echo SUPABASE_PROJECT_ID=your_project_id_here
    echo SUPABASE_DB_PASSWORD=your_db_password_here
    echo SUPABASE_ANON_KEY=your_anon_key_here
    echo SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here
    echo.
    echo # AI/ML APIs
    echo OPENROUTER_API_KEY=your_openrouter_api_key_here
    echo.
    echo # Optional APIs
    echo MISTRAL_API_KEY=your_mistral_api_key_here
    echo GROQ_API_KEY=your_groq_api_key_here
    echo.
    echo # NHTSA API ^(no key needed^)
    echo NHTSA_API_BASE_URL=https://vpic.nhtsa.dot.gov/api
    echo.
    echo # Zep Cloud ^(optional^)
    echo ZEP_API_KEY=your_zep_api_key_here
    echo ZEP_PROJECT_UUID=your_zep_project_uuid_here
    echo ZEP_API_URL=https://api.your-zep-cloud-instance.com
    echo.
    echo # Additional Configuration
    echo EMBEDDING_MODEL=openai/text-embedding-3-large
    echo EMBEDDING_DIM=3072
    echo LLM_MODEL=google/gemini-2.5-flash-image
    ) > .env
    echo ⚠️  Please edit .env file with your actual API keys and configuration
) else (
    echo ✅ .env file found
)

REM Run database setup
echo ℹ️  Setting up database schema...
if exist "src\semantic\setup_database.py" (
    python src\semantic\setup_database.py
    echo ✅ Database setup completed
) else (
    echo ⚠️  Database setup script not found. Please run it manually.
)

REM Run validation
echo ℹ️  Running setup validation...
if exist "src\semantic\validate_setup.py" (
    python src\semantic\validate_setup.py
    echo ✅ Setup validation completed
) else (
    echo ⚠️  Validation script not found. Please run it manually.
)

REM Test installation
echo ℹ️  Testing installation...
python -c "
import sys
try:
    import sys
    sys.path.append('.')
    import src.semantic.embedding_service
    print('✅ Embedding service module imports successfully')
except ImportError as e:
    print(f'❌ Failed to import embedding service: {e}')
    sys.exit(1)

try:
    import requests
    print('✅ requests library available')
except ImportError:
    print('❌ requests library not available')
    sys.exit(1)

try:
    import psycopg
    print('✅ psycopg library available')
except ImportError:
    print('❌ psycopg library not available')
    sys.exit(1)
"
echo ✅ Installation test passed

echo.
echo 🎉 Installation completed successfully!
echo.
echo 📋 Next Steps:
echo 1. Edit .env file with your actual API keys and configuration
echo 2. Run the database setup: python src\semantic\setup_database.py
echo 3. Run validation: python src\semantic\validate_setup.py
echo 4. Test the embedding service: python src\semantic\test_gemini_integration.py
echo 5. Start the test API: python src\api\test_endpoints.py
echo.
echo 📖 Documentation:
echo - API docs: http://localhost:8000/docs ^(after starting test API^)
echo - Sample queries: http://localhost:8000/sample_queries
echo.
echo 🔧 Development Commands:
echo - Activate venv: venv\Scripts\activate.bat
echo - Install new packages: pip install package_name
echo - Update requirements: pip freeze ^> requirements.txt
echo.

echo ✅ Otto.AI installation completed! 🎉
pause