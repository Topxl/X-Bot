#!/bin/bash
set -e

echo "🚀 Twitter Bot Automated - Setup Script"
echo "========================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check Python version
check_python() {
    echo -e "${BLUE}Checking Python version...${NC}"
    if ! command -v python3.11 &> /dev/null; then
        echo -e "${RED}❌ Python 3.11+ is required${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Python 3.11+ found${NC}"
}

# Create virtual environment
setup_venv() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    if [ ! -d "venv" ]; then
        python3.11 -m venv venv
        echo -e "${GREEN}✅ Virtual environment created${NC}"
    else
        echo -e "${YELLOW}⚠️ Virtual environment already exists${NC}"
    fi
    
    # Activate virtual environment
    source venv/bin/activate || source venv/Scripts/activate
    echo -e "${GREEN}✅ Virtual environment activated${NC}"
}

# Install dependencies
install_deps() {
    echo -e "${BLUE}Installing dependencies...${NC}"
    pip install --upgrade pip
    pip install -r requirements.txt
    echo -e "${GREEN}✅ Dependencies installed${NC}"
}

# Setup configuration
setup_config() {
    echo -e "${BLUE}Setting up configuration...${NC}"
    
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo -e "${YELLOW}⚠️ Created .env file from template${NC}"
        echo -e "${YELLOW}📝 Please edit .env with your API credentials${NC}"
    else
        echo -e "${GREEN}✅ .env file already exists${NC}"
    fi
    
    if [ ! -f "config.json" ]; then
        echo -e "${RED}❌ config.json not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Configuration files ready${NC}"
}

# Create directories
create_dirs() {
    echo -e "${BLUE}Creating directories...${NC}"
    mkdir -p logs data tests
    echo -e "${GREEN}✅ Directories created${NC}"
}

# Setup database
setup_database() {
    echo -e "${BLUE}Setting up Supabase database...${NC}"
    echo -e "${YELLOW}📝 Make sure to run the SQL scripts in your Supabase dashboard:${NC}"
    echo "   1. Tables: tweets, replies, stats, configs"
    echo "   2. Storage bucket: generated-images"
    echo "   3. Enable realtime for replies table"
    echo -e "${GREEN}✅ Database setup instructions provided${NC}"
}

# Run tests
run_tests() {
    echo -e "${BLUE}Running initial tests...${NC}"
    if [ -d "tests" ] && [ "$(ls -A tests)" ]; then
        python -m pytest tests/ -v
        echo -e "${GREEN}✅ Tests passed${NC}"
    else
        echo -e "${YELLOW}⚠️ No tests found, skipping${NC}"
    fi
}

# Main setup process
main() {
    echo -e "${BLUE}Starting setup process...${NC}\n"
    
    check_python
    setup_venv
    install_deps
    create_dirs
    setup_config
    setup_database
    run_tests
    
    echo -e "\n${GREEN}🎉 Setup completed successfully!${NC}"
    echo -e "\n${YELLOW}Next steps:${NC}"
    echo "1. Edit .env with your API credentials"
    echo "2. Configure config.json for your needs"
    echo "3. Setup Supabase database tables"
    echo "4. Run: python main.py"
    echo -e "\n${BLUE}For Docker deployment:${NC}"
    echo "docker-compose up -d"
}

# Handle script arguments
case "${1:-setup}" in
    setup)
        main
        ;;
    clean)
        echo -e "${YELLOW}Cleaning up...${NC}"
        rm -rf venv logs/* data/* __pycache__ .pytest_cache
        echo -e "${GREEN}✅ Cleanup completed${NC}"
        ;;
    test)
        source venv/bin/activate || source venv/Scripts/activate
        run_tests
        ;;
    *)
        echo "Usage: $0 {setup|clean|test}"
        exit 1
        ;;
esac 