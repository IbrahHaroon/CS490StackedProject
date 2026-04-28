#!/bin/bash
# Quick script to run analytics tests

echo "📊 Dashboard Analytics Test Suite"
echo "=================================="
echo ""

# Check if pytest is installed
if ! command -v pytest &> /dev/null; then
    echo "❌ pytest not found. Installing dependencies..."
    pip install pytest pytest-asyncio sqlalchemy
fi

echo "Running analytics tests..."
echo ""

cd "$(dirname "$0")"

pytest tests/test_analytics.py -v --tb=short

echo ""
echo "✅ Test run complete!"
