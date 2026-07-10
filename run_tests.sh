#!/bin/bash

# Test runner script for Dietician QA pipeline
# Usage: bash run_tests.sh [test_filter]

set -e

echo "=========================================="
echo "Dietician Call QA — Test Runner"
echo "=========================================="
echo ""

# Check if Python/pytest is available
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Install dependencies:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Default to all tests
TEST_FILTER=${1:-.}

echo "Running tests with filter: $TEST_FILTER"
echo ""

# Count tests
TOTAL_TESTS=$(pytest --collect-only -q tests/ 2>/dev/null | tail -1 | awk '{print $1}' || echo "?")
echo "📊 Total tests found: $TOTAL_TESTS"
echo ""

# Run tests with verbose output
pytest tests/ -v --tb=short -k "$TEST_FILTER"

echo ""
echo "=========================================="
echo "✅ All tests passed!"
echo "=========================================="
