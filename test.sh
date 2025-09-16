#!/bin/bash

echo "🧪 Running Nightingale-Chat Test Suite..."

cd backend

# Activate virtual environment
source venv/bin/activate

# Run different test categories
echo "📋 Available test commands:"
echo "  ./test.sh all       - Run all tests"
echo "  ./test.sh unit      - Run only unit tests"
echo "  ./test.sh integration - Run only integration tests"
echo "  ./test.sh security  - Run only security tests"
echo "  ./test.sh coverage  - Run tests with coverage report"
echo "  ./test.sh watch     - Run tests in watch mode"
echo ""

case "${1:-all}" in
    "unit")
        echo "🔬 Running unit tests..."
        pytest tests/unit/ -m "not slow" --tb=short
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        pytest tests/integration/ --tb=short
        ;;
    "security")
        echo "🔒 Running security tests..."
        pytest tests/unit/test_security_utils.py -v
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        pip install coverage pytest-cov
        pytest --cov=. --cov-report=html --cov-report=term-missing
        echo "📁 Coverage report generated in htmlcov/"
        ;;
    "watch")
        echo "👀 Running tests in watch mode..."
        pip install pytest-watch
        ptw --runner "pytest --tb=short"
        ;;
    "all"|*)
        echo "🚀 Running all tests..."
        pytest --tb=short
        echo ""
        echo "✅ Test suite completed!"
        ;;
esac

echo ""
echo "🏥 Nightingale-Chat tests finished!"