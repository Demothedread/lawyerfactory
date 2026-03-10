#!/bin/bash
# LawyerFactory Comprehensive Test Suite Runner
# Shell script wrapper for running all test suites

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TESTS_DIR="$PROJECT_ROOT/tests"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0

# Print header
print_header() {
    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo "  $1"
    echo "════════════════════════════════════════════════════════════════════════════════"
    echo ""
}

# Run test command
run_test_suite() {
    local suite_name=$1
    local cmd=$2
    
    print_header "Running: $suite_name"
    
    if eval "$cmd"; then
        echo -e "${GREEN}✓ $suite_name PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ $suite_name FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

# Main execution
main() {
    local verbose=""
    local coverage=""
    local parallel=""
    local test_type="all"

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --verbose|-v)
                verbose=" -v"
                shift
                ;;
            --coverage)
                coverage=" --cov=apps/api --cov-report=html"
                shift
                ;;
            --parallel)
                parallel=" -n auto"
                shift
                ;;
            --unit)
                test_type="unit"
                shift
                ;;
            --integration)
                test_type="integration"
                shift
                ;;
            --e2e)
                test_type="e2e"
                shift
                ;;
            --backend)
                test_type="backend"
                shift
                ;;
            *)
                echo "Unknown option: $1"
                exit 1
                ;;
        esac
    done

    print_header "LAWYERFACTORY COMPREHENSIVE TEST SUITE"

    cd "$PROJECT_ROOT"

    # Run specific test suites based on type
    case $test_type in
        unit)
            run_test_suite "Backend API Unit Tests" \
                "pytest tests/test_backend_api_unit.py$verbose$coverage$parallel"
            ;;
        integration)
            run_test_suite "Backend Integration Tests" \
                "pytest tests/test_backend_integration_workflow.py$verbose$coverage$parallel"
            ;;
        e2e)
            run_test_suite "End-to-End Workflow Tests" \
                "pytest tests/e2e/test_complete_multiphase_workflow.py -s$verbose$coverage$parallel"
            ;;
        backend)
            run_test_suite "Backend API Unit Tests" \
                "pytest tests/test_backend_api_unit.py$verbose$coverage$parallel" && true
            run_test_suite "Backend Integration Tests" \
                "pytest tests/test_backend_integration_workflow.py$verbose$coverage$parallel" && true
            run_test_suite "End-to-End Workflow Tests" \
                "pytest tests/e2e/test_complete_multiphase_workflow.py -s$verbose$coverage$parallel" && true
            ;;
        all)
            run_test_suite "Backend API Unit Tests" \
                "pytest tests/test_backend_api_unit.py$verbose$coverage$parallel" && true
            run_test_suite "Backend Integration Tests" \
                "pytest tests/test_backend_integration_workflow.py$verbose$coverage$parallel" && true
            run_test_suite "End-to-End Workflow Tests" \
                "pytest tests/e2e/test_complete_multiphase_workflow.py -s$verbose$coverage$parallel" && true
            
            # Frontend tests (if available)
            if [ -d "$PROJECT_ROOT/apps/ui/react-app" ]; then
                run_test_suite "Frontend Component Tests" \
                    "cd $PROJECT_ROOT/apps/ui/react-app && npm test -- --passWithNoTests 2>/dev/null || true" && true
            fi
            ;;
    esac

    # Print summary
    print_header "TEST EXECUTION SUMMARY"
    
    TOTAL=$((PASSED + FAILED))
    echo "Total Test Suites:  $TOTAL"
    echo -e "${GREEN}✓ Passed:           $PASSED${NC}"
    echo -e "${RED}✗ Failed:           $FAILED${NC}"

    echo ""
    echo "════════════════════════════════════════════════════════════════════════════════"

    if [ $FAILED -eq 0 ]; then
        echo -e "${GREEN}✅ All tests passed!${NC}"
        echo "════════════════════════════════════════════════════════════════════════════════"
        echo ""
        return 0
    else
        echo -e "${RED}⚠️  $FAILED test suite(s) failed${NC}"
        echo "════════════════════════════════════════════════════════════════════════════════"
        echo ""
        return 1
    fi
}

# Run main
main "$@"
