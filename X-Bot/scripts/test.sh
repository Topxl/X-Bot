#!/bin/bash
set -e

echo "🧪 Twitter Bot - Test Suite"
echo "==========================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Test configuration
TEST_DIR="tests"
COVERAGE_THRESHOLD=80

# Check if pytest is available
check_pytest() {
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}❌ pytest not found. Installing...${NC}"
        pip install pytest pytest-cov pytest-asyncio
    fi
}

# Run unit tests
run_unit_tests() {
    echo -e "${BLUE}Running unit tests...${NC}"
    pytest $TEST_DIR -m "not integration and not slow" -v
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Unit tests passed${NC}"
    else
        echo -e "${RED}❌ Unit tests failed${NC}"
        return 1
    fi
}

# Run integration tests
run_integration_tests() {
    echo -e "${BLUE}Running integration tests...${NC}"
    pytest $TEST_DIR -m "integration" -v --timeout=60
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Integration tests passed${NC}"
    else
        echo -e "${RED}❌ Integration tests failed${NC}"
        return 1
    fi
}

# Run slow tests
run_slow_tests() {
    echo -e "${BLUE}Running slow tests...${NC}"
    pytest $TEST_DIR -m "slow" -v --timeout=120
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Slow tests passed${NC}"
    else
        echo -e "${RED}❌ Slow tests failed${NC}"
        return 1
    fi
}

# Run all tests with coverage
run_all_tests() {
    echo -e "${BLUE}Running all tests with coverage...${NC}"
    pytest $TEST_DIR -v \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=html:htmlcov \
        --cov-report=xml \
        --cov-fail-under=$COVERAGE_THRESHOLD
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ All tests passed with sufficient coverage${NC}"
        echo -e "${BLUE}Coverage report generated in htmlcov/index.html${NC}"
    else
        echo -e "${RED}❌ Tests failed or coverage below $COVERAGE_THRESHOLD%${NC}"
        return 1
    fi
}

# Run specific test file or function
run_specific_test() {
    local test_target="$1"
    echo -e "${BLUE}Running specific test: $test_target${NC}"
    pytest "$test_target" -v
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Test passed${NC}"
    else
        echo -e "${RED}❌ Test failed${NC}"
        return 1
    fi
}

# Check test quality
check_test_quality() {
    echo -e "${BLUE}Checking test quality...${NC}"
    
    # Count test files
    test_files=$(find $TEST_DIR -name "test_*.py" | wc -l)
    echo "Test files: $test_files"
    
    # Count test functions
    test_functions=$(grep -r "def test_" $TEST_DIR | wc -l)
    echo "Test functions: $test_functions"
    
    # Check for common test patterns
    echo -e "${BLUE}Test patterns analysis:${NC}"
    
    # Fixtures usage
    fixture_count=$(grep -r "@pytest.fixture" $TEST_DIR | wc -l)
    echo "Fixtures defined: $fixture_count"
    
    # Mock usage
    mock_count=$(grep -r "Mock\|patch" $TEST_DIR | wc -l)
    echo "Mock usage: $mock_count"
    
    # Parametrized tests
    param_count=$(grep -r "@pytest.mark.parametrize" $TEST_DIR | wc -l)
    echo "Parametrized tests: $param_count"
}

# Lint test code
lint_tests() {
    echo -e "${BLUE}Linting test code...${NC}"
    
    # Check if flake8 is available
    if command -v flake8 &> /dev/null; then
        flake8 $TEST_DIR --max-line-length=100 --ignore=E203,W503
        if [[ $? -eq 0 ]]; then
            echo -e "${GREEN}✅ Test code linting passed${NC}"
        else
            echo -e "${YELLOW}⚠️ Test code has linting issues${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️ flake8 not found, skipping lint${NC}"
    fi
}

# Generate test report
generate_test_report() {
    echo -e "${BLUE}Generating test report...${NC}"
    
    # Create reports directory
    mkdir -p reports
    
    # Run tests with JUnit XML output
    pytest $TEST_DIR \
        --junitxml=reports/test-results.xml \
        --cov=. \
        --cov-report=xml:reports/coverage.xml \
        --html=reports/test-report.html \
        --self-contained-html
    
    echo -e "${GREEN}✅ Test reports generated in reports/ directory${NC}"
}

# Clean test artifacts
clean_test_artifacts() {
    echo -e "${BLUE}Cleaning test artifacts...${NC}"
    
    # Remove cache and coverage files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name ".coverage" -delete 2>/dev/null || true
    rm -rf htmlcov/ 2>/dev/null || true
    rm -rf reports/ 2>/dev/null || true
    
    echo -e "${GREEN}✅ Test artifacts cleaned${NC}"
}

# Watch mode for continuous testing
watch_tests() {
    echo -e "${BLUE}Starting test watch mode...${NC}"
    echo -e "${YELLOW}Watching for file changes. Press Ctrl+C to stop.${NC}"
    
    if command -v ptw &> /dev/null; then
        ptw --runner "pytest -x"
    else
        echo -e "${RED}❌ pytest-watch not found. Install with: pip install pytest-watch${NC}"
        echo -e "${YELLOW}Running tests once instead...${NC}"
        run_unit_tests
    fi
}

# Main execution
main() {
    case "${1:-all}" in
        unit)
            check_pytest
            run_unit_tests
            ;;
        integration)
            check_pytest
            run_integration_tests
            ;;
        slow)
            check_pytest
            run_slow_tests
            ;;
        all)
            check_pytest
            run_all_tests
            ;;
        coverage)
            check_pytest
            run_all_tests
            ;;
        quality)
            check_test_quality
            lint_tests
            ;;
        report)
            check_pytest
            generate_test_report
            ;;
        clean)
            clean_test_artifacts
            ;;
        watch)
            check_pytest
            watch_tests
            ;;
        lint)
            lint_tests
            ;;
        *)
            if [[ -f "$1" ]] || [[ "$1" == *"::"* ]]; then
                check_pytest
                run_specific_test "$1"
            else
                echo "Usage: $0 {unit|integration|slow|all|coverage|quality|report|clean|watch|lint|<test_file>}"
                echo ""
                echo "Commands:"
                echo "  unit        - Run unit tests only"
                echo "  integration - Run integration tests only"
                echo "  slow        - Run slow tests only"
                echo "  all         - Run all tests with coverage"
                echo "  coverage    - Same as 'all'"
                echo "  quality     - Check test quality and lint"
                echo "  report      - Generate detailed test reports"
                echo "  clean       - Clean test artifacts"
                echo "  watch       - Run tests in watch mode"
                echo "  lint        - Lint test code only"
                echo "  <test_file> - Run specific test file or function"
                echo ""
                echo "Examples:"
                echo "  $0 tests/test_config.py"
                echo "  $0 tests/test_twitter_api.py::TestTwitterAPI::test_post_tweet"
                exit 1
            fi
            ;;
    esac
}

# Run main function
main "$@" 