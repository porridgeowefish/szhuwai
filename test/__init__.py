"""
Outdoor Agent Planner Test Suite
================================

This package contains comprehensive tests for the Outdoor Agent Planner system.

Test Structure:
---------------
- schemas/: Tests for Pydantic data models and validation
- api/: Tests for API client implementations (weather, map, search)
- integration/: Integration tests for full workflows

Test Categories:
---------------
1. **Model Tests** (`test/schemas/`)
   - Pydantic model validation
   - Data contract verification
   - Edge case handling

2. **API Tests** (`test/api/`)
   - Weather API (QWeather) - city forecasts, grid weather, hourly forecasts
   - Map API (Gaode) - geocoding, route planning
   - Search API (Tavily) - web search with context

3. **Integration Tests** (`test/integration/`)
   - End-to-end workflow testing
   - Multi-API coordination tests

Note: `test_all_apis_simple.py` is a standalone connectivity test
for manual API verification. It is NOT part of pytest test suite.

Running Tests:
---------------
```bash
# Run all tests (recommended)
pytest test/ -v

# Run specific test categories
pytest test/schemas/ -v
pytest test/api/ -v
pytest test/integration/ -v

# Run tests without slow tests
pytest test/ -v -m "not slow"

# Run tests with coverage report
pytest test/ --cov=schemas --cov=api --cov-report=html
```

CI/Continuous Integration:
------------------------------
These tests are designed to be part of CI pipeline.
Temporary connectivity tests (test_*.py files) should be
excluded from CI runs.

API Keys:
----------
All API tests require valid API keys in `.env` file.
Copy `.env.example` to `.env` and configure:
- QWEATHER_API_KEY (和风天气)
- AMAP_API_KEY (高德地图)
- TAVILY_API_KEY (Tavily 搜索)
- LLM_API_KEY (SiliconFlow/DeepSeek)
"""
