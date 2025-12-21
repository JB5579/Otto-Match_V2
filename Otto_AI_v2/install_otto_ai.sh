#!/bin/bash

# Otto.AI Installation Script
# Sets up the development environment for Otto.AI semantic search infrastructure

# Story: 1.1-initialize-semantic-search-infrastructure
# Task: Write installation script for development environment (AC: #4)

set -e  # Exit on any error

echo "🚀 Otto.AI Installation Script"
echo "=================================="
echo "Setting up development environment for semantic search infrastructure"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Python is installed
check_python() {
    print_info "Checking Python installation..."

    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed. Please install Python 3.8 or higher."
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"

    # Check if version is 3.8 or higher
    if ! $PYTHON_CMD -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)"; then
        print_error "Python 3.8 or higher is required. Current version: $PYTHON_VERSION"
        exit 1
    fi
}

# Check if pip is installed
check_pip() {
    print_info "Checking pip installation..."

    if command -v pip3 &> /dev/null; then
        PIP_CMD="pip3"
    elif command -v pip &> /dev/null; then
        PIP_CMD="pip"
    else
        print_error "pip is not installed. Please install pip."
        exit 1
    fi

    print_success "pip found"
}

# Create virtual environment
create_venv() {
    print_info "Creating virtual environment..."

    if [ ! -d "venv" ]; then
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_warning "Virtual environment already exists"
    fi

    # Activate virtual environment
    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        # Windows
        source venv/Scripts/activate
    else
        # Linux/Mac
        source venv/bin/activate
    fi

    print_success "Virtual environment activated"
}

# Upgrade pip
upgrade_pip() {
    print_info "Upgrading pip..."
    $PIP_CMD install --upgrade pip
    print_success "pip upgraded"
}

# Install dependencies
install_dependencies() {
    print_info "Installing Python dependencies..."

    if [ -f "requirements.txt" ]; then
        $PIP_CMD install -r requirements.txt
        print_success "Dependencies installed from requirements.txt"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Create necessary directories
create_directories() {
    print_info "Creating necessary directories..."

    mkdir -p src/semantic
    mkdir -p src/api
    mkdir -p tests/unit/semantic
    mkdir -p tests/integration/semantic
    mkdir -p tests/performance
    mkdir -p logs
    mkdir -p data/sample_vehicles

    print_success "Directories created"
}

# Check environment variables
check_env_vars() {
    print_info "Checking environment variables..."

    # Create .env file if it doesn't exist
    if [ ! -f ".env" ]; then
        print_warning ".env file not found. Creating template..."
        cat > .env << EOF
# Otto.AI Environment Variables
# Add your actual API keys and configuration values here

# Supabase Configuration
SUPABASE_URL=your_supabase_url_here
SUPABASE_PROJECT_ID=your_project_id_here
SUPABASE_DB_PASSWORD=your_db_password_here
SUPABASE_ANON_KEY=your_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# AI/ML APIs
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Optional APIs
MISTRAL_API_KEY=your_mistral_api_key_here
GROQ_API_KEY=your_groq_api_key_here

# NHTSA API (no key needed)
NHTSA_API_BASE_URL=https://vpic.nhtsa.dot.gov/api

# Zep Cloud (optional)
ZEP_API_KEY=your_zep_api_key_here
ZEP_PROJECT_UUID=your_zep_project_uuid_here
ZEP_API_URL=https://api.your-zep-cloud-instance.com

# Additional Configuration
EMBEDDING_MODEL=openai/text-embedding-3-large
EMBEDDING_DIM=3072
LLM_MODEL=google/gemini-2.5-flash-image
EOF
        print_warning "Please edit .env file with your actual API keys and configuration"
    else
        print_success ".env file found"
    fi

    # Check for required variables
    required_vars=("OPENROUTER_API_KEY" "SUPABASE_URL" "SUPABASE_ANON_KEY" "SUPABASE_DB_PASSWORD")
    missing_vars=()

    for var in "${required_vars[@]}"; do
        if ! grep -q "^$var=" .env || grep -q "^$var=your_" .env || grep -q "^$env_var=$" .env; then
            missing_vars+=($var)
        fi
    done

    if [ ${#missing_vars[@]} -gt 0 ]; then
        print_warning "The following environment variables need to be configured in .env:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
    else
        print_success "All required environment variables are configured"
    fi
}

# Run database setup
setup_database() {
    print_info "Setting up database schema..."

    if [ -f "src/semantic/setup_database.py" ]; then
        $PYTHON_CMD src/semantic/setup_database.py
        print_success "Database setup completed"
    else
        print_warning "Database setup script not found. Please run it manually."
    fi
}

# Run validation
run_validation() {
    print_info "Running setup validation..."

    if [ -f "src/semantic/validate_setup.py" ]; then
        $PYTHON_CMD src/semantic/validate_setup.py
        print_success "Setup validation completed"
    else
        print_warning "Validation script not found. Please run it manually."
    fi
}

# Test installation
test_installation() {
    print_info "Testing installation..."

    # Test import of main modules
    $PYTHON_CMD -c "
import sys
try:
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

    print_success "Installation test passed"
}

# Print next steps
print_next_steps() {
    echo ""
    echo "🎉 Installation completed successfully!"
    echo ""
    echo "📋 Next Steps:"
    echo "1. Edit .env file with your actual API keys and configuration"
    echo "2. Run the database setup: python src/semantic/setup_database.py"
    echo "3. Run validation: python src/semantic/validate_setup.py"
    echo "4. Test the embedding service: python src/semantic/test_gemini_integration.py"
    echo "5. Start the test API: python src/api/test_endpoints.py"
    echo ""
    echo "📖 Documentation:"
    echo "- API docs: http://localhost:8000/docs (after starting test API)"
    echo "- Sample queries: http://localhost:8000/sample_queries"
    echo ""
    echo "🔧 Development Commands:"
    echo "- Activate venv: source venv/bin/activate (Linux/Mac) or venv\\Scripts\\activate (Windows)"
    echo "- Install new packages: pip install package_name"
    echo "- Update requirements: pip freeze > requirements.txt"
    echo ""
}

# Main installation flow
main() {
    echo "Starting Otto.AI installation..."
    echo ""

    check_python
    check_pip
    create_venv
    upgrade_pip
    install_dependencies
    create_directories
    check_env_vars
    setup_database
    run_validation
    test_installation
    print_next_steps

    print_success "Otto.AI installation completed! 🎉"
}

# Handle script interruption
trap 'print_error "Installation interrupted"; exit 1' INT

# Run main function
main "$@"