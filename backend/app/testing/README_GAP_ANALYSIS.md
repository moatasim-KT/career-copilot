# Frontend-Backend Gap Analysis System

## Overview

The Gap Analysis System provides comprehensive tools for identifying and analyzing integration gaps between the frontend and backend of the Career Copilot application.

## Components

### 1. Frontend Scanner (`frontend_scanner.py`)

Scans frontend source code to identify all API client calls and extract endpoint information.

**Features:**
- Scans TypeScript/JavaScript files for API calls
- Identifies direct API client calls, fetch/axios calls, and React Query hooks
- Extracts endpoint paths, HTTP methods, and parameters
- Maps API calls to frontend components
- Identifies feature requirements based on API usage

**Usage:**
```python
from app.testing.frontend_scanner import FrontendScanner

scanner = FrontendScanner("frontend/src")
api_calls = scanner.scan_directory()
feature_requirements = scanner.identify_feature_requirements()
```

### 2. Gap Detector (`gap_detector.py`)

Compares frontend API calls with backend endpoints to identify integration gaps.

**Features:**
- Detects missing endpoints
- Identifies method mismatches
- Finds parameter mismatches
- Categorizes gaps by type and severity
- Provides actionable recommendations

**Usage:**
```python
from app.testing.gap_detector import GapDetector

detector = GapDetector()
gaps = detector.compare_frontend_backend(
    frontend_calls=api_calls,
    backend_endpoints=backend_endpoints,
    feature_requirements=feature_requirements
)
```

### 3. Gap Report Generator (`gap_report_generator.py`)

Generates comprehensive reports in multiple formats.

**Supported Formats:**
- HTML: Interactive report with filtering and styling
- JSON: Programmatic access to gap data
- Markdown: Documentation-friendly format
- CSV: Spreadsheet analysis

**Usage:**
```python
from app.testing.gap_report_generator import GapReportGenerator

generator = GapReportGenerator(detector)
generator.generate_all_reports("reports/gap_analysis")
```

## Running Gap Analysis

### Command Line

```bash
# Run complete gap analysis
python backend/scripts/testing/run_gap_analysis.py

# Specify custom directories
python backend/scripts/testing/run_gap_analysis.py \
    --frontend-dir frontend/src \
    --output-dir reports/gap_analysis

# Generate specific format
python backend/scripts/testing/run_gap_analysis.py --format html

# Verbose output
python backend/scripts/testing/run_gap_analysis.py --verbose
```

### Programmatic Usage

```python
from app.main import app
from app.testing.endpoint_discovery import EndpointDiscovery
from app.testing.frontend_scanner import FrontendScanner
from app.testing.gap_detector import GapDetector
from app.testing.gap_report_generator import GapReportGenerator

# Discover backend endpoints
discovery = EndpointDiscovery(app)
backend_endpoints = discovery.discover_endpoints()

# Scan frontend
scanner = FrontendScanner("frontend/src")
frontend_calls = scanner.scan_directory()
feature_requirements = scanner.identify_feature_requirements()

# Detect gaps
detector = GapDetector()
gaps = detector.compare_frontend_backend(
    frontend_calls, backend_endpoints, feature_requirements
)

# Generate reports
generator = GapReportGenerator(detector)
generator.generate_all_reports("reports")
```

## Gap Types

1. **Missing Endpoint**: Frontend expects an endpoint that doesn't exist
2. **Method Mismatch**: Endpoint exists but with different HTTP method
3. **Parameter Mismatch**: Parameters don't match between frontend and backend
4. **Incomplete Implementation**: Endpoint exists but missing required functionality
5. **Response Format Issue**: Response format doesn't match frontend expectations

## Severity Levels

- **Critical**: Core functionality broken, immediate action required
- **High**: Important features affected, should be fixed soon
- **Medium**: Non-critical features affected, fix when possible
- **Low**: Minor issues, low priority

## Output Files

When running gap analysis, the following files are generated:

- `gap_analysis.html`: Interactive HTML report
- `gap_analysis.json`: JSON data for programmatic access
- `gap_analysis.md`: Markdown documentation
- `gap_analysis.csv`: CSV for spreadsheet analysis
- `frontend_api_calls.json`: Complete frontend scan results
- `backend_endpoints.json`: Complete backend endpoint map

## Integration with CI/CD

Add gap analysis to your CI/CD pipeline:

```yaml
# .github/workflows/gap-analysis.yml
name: Gap Analysis
on: [push, pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Gap Analysis
        run: |
          python backend/scripts/testing/run_gap_analysis.py
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: gap-analysis-reports
          path: backend/reports/gap_analysis/
```

## Best Practices

1. **Run Regularly**: Run gap analysis after significant frontend or backend changes
2. **Review Reports**: Review HTML reports for detailed insights
3. **Prioritize Fixes**: Address critical and high-priority gaps first
4. **Track Progress**: Use JSON reports to track gap resolution over time
5. **Automate**: Integrate into CI/CD for continuous monitoring
