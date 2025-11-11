"""
Gap Analysis Report Generator

Generates comprehensive reports of integration gaps between frontend and backend.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .gap_detector import Gap, GapDetector, GapSeverity, GapType


class GapReportGenerator:
    """
    Generates comprehensive gap analysis reports in multiple formats.

    Supports:
    - HTML reports with styling and interactivity
    - JSON reports for programmatic access
    - Markdown reports for documentation
    - CSV reports for spreadsheet analysis
    """

    def __init__(self, gap_detector: GapDetector):
        """
        Initialize the report generator.

        Args:
            gap_detector: GapDetector instance with detected gaps
        """
        self.gap_detector = gap_detector
        self.gaps = gap_detector.gaps
        self.statistics = gap_detector.get_statistics()

    def generate_html_report(self, output_file: str) -> None:
        """
        Generate an HTML report with styling and interactivity.

        Args:
            output_file: Path to output HTML file
        """
        html = self._generate_html_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html)

    def _generate_html_content(self) -> str:
        """
        Generate HTML content for the report.

        Returns:
            HTML string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Frontend-Backend Integration Gap Analysis Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}

        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
            font-size: 2.5em;
        }}

        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 1.1em;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}

        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}

        .stat-card.critical {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}

        .stat-card.high {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}

        .stat-card.medium {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        }}

        .stat-card.low {{
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        }}

        .stat-value {{
            font-size: 3em;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section-title {{
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }}

        .gap-card {{
            background: #fff;
            border: 1px solid #e0e0e0;
            border-left: 4px solid #3498db;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 4px;
            transition: box-shadow 0.3s;
        }}

        .gap-card:hover {{
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}

        .gap-card.critical {{
            border-left-color: #e74c3c;
        }}

        .gap-card.high {{
            border-left-color: #f39c12;
        }}

        .gap-card.medium {{
            border-left-color: #3498db;
        }}

        .gap-card.low {{
            border-left-color: #2ecc71;
        }}

        .gap-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .gap-title {{
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
        }}

        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .badge.critical {{
            background: #fee;
            color: #e74c3c;
        }}

        .badge.high {{
            background: #fef5e7;
            color: #f39c12;
        }}

        .badge.medium {{
            background: #ebf5fb;
            color: #3498db;
        }}

        .badge.low {{
            background: #eafaf1;
            color: #2ecc71;
        }}

        .gap-details {{
            margin-bottom: 15px;
        }}

        .detail-row {{
            display: flex;
            margin-bottom: 8px;
            font-size: 0.95em;
        }}

        .detail-label {{
            font-weight: 600;
            color: #7f8c8d;
            min-width: 150px;
        }}

        .detail-value {{
            color: #2c3e50;
            font-family: 'Courier New', monospace;
        }}

        .description {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            color: #555;
        }}

        .recommendation {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 4px;
            border-left: 3px solid #4caf50;
        }}

        .recommendation-title {{
            font-weight: 600;
            color: #2e7d32;
            margin-bottom: 8px;
        }}

        .recommendation-text {{
            color: #555;
        }}

        .features-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 10px;
        }}

        .feature-tag {{
            background: #e3f2fd;
            color: #1976d2;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
        }}

        .filter-buttons {{
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}

        .filter-btn {{
            padding: 8px 16px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            transition: all 0.3s;
        }}

        .filter-btn:hover {{
            background: #f5f5f5;
        }}

        .filter-btn.active {{
            background: #3498db;
            color: white;
            border-color: #3498db;
        }}

        .no-gaps {{
            text-align: center;
            padding: 40px;
            color: #7f8c8d;
            font-size: 1.1em;
        }}

        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
            .filter-buttons {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Frontend-Backend Integration Gap Analysis</h1>
        <div class="subtitle">Generated on {timestamp}</div>

        <div class="summary">
            <div class="stat-card">
                <div class="stat-value">{self.statistics['total_gaps']}</div>
                <div class="stat-label">Total Gaps</div>
            </div>
            <div class="stat-card critical">
                <div class="stat-value">{self.statistics['gaps_by_severity']['critical']}</div>
                <div class="stat-label">Critical</div>
            </div>
            <div class="stat-card high">
                <div class="stat-value">{self.statistics['gaps_by_severity']['high']}</div>
                <div class="stat-label">High Priority</div>
            </div>
            <div class="stat-card medium">
                <div class="stat-value">{self.statistics['gaps_by_severity']['medium']}</div>
                <div class="stat-label">Medium Priority</div>
            </div>
            <div class="stat-card low">
                <div class="stat-value">{self.statistics['gaps_by_severity']['low']}</div>
                <div class="stat-label">Low Priority</div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">📊 Gap Statistics</h2>
            <div class="gap-details">
                <div class="detail-row">
                    <div class="detail-label">Unique Endpoints Missing:</div>
                    <div class="detail-value">{self.statistics.get('unique_endpoints_missing', 0)}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Components Affected:</div>
                    <div class="detail-value">{self.statistics.get('unique_components_affected', 0)}</div>
                </div>
                <div class="detail-row">
                    <div class="detail-label">Gap Types:</div>
                    <div class="detail-value">{', '.join(f"{k}: {v}" for k, v in self.statistics.get('gaps_by_type', {}).items())}</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2 class="section-title">🚨 Detected Gaps</h2>
            <div class="filter-buttons">
                <button class="filter-btn active" onclick="filterGaps('all')">All Gaps</button>
                <button class="filter-btn" onclick="filterGaps('critical')">Critical</button>
                <button class="filter-btn" onclick="filterGaps('high')">High</button>
                <button class="filter-btn" onclick="filterGaps('medium')">Medium</button>
                <button class="filter-btn" onclick="filterGaps('low')">Low</button>
            </div>
            <div id="gaps-container">
                {self._generate_gap_cards()}
            </div>
        </div>
    </div>

    <script>
        function filterGaps(severity) {{
            const cards = document.querySelectorAll('.gap-card');
            const buttons = document.querySelectorAll('.filter-btn');

            buttons.forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');

            cards.forEach(card => {{
                if (severity === 'all' || card.classList.contains(severity)) {{
                    card.style.display = 'block';
                }} else {{
                    card.style.display = 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        return html

    def _generate_gap_cards(self) -> str:
        """
        Generate HTML for gap cards.

        Returns:
            HTML string with gap cards
        """
        if not self.gaps:
            return '<div class="no-gaps">✅ No integration gaps detected! Frontend and backend are in sync.</div>'

        # Sort gaps by severity
        prioritized_gaps = self.gap_detector.prioritize_gaps()

        cards = []
        for gap in prioritized_gaps:
            severity_class = gap.severity.value
            gap_type_display = gap.gap_type.value.replace("_", " ").title()

            features_html = ""
            if gap.affected_features:
                features_html = '<div class="features-list">'
                for feature in gap.affected_features:
                    features_html += f'<span class="feature-tag">{feature}</span>'
                features_html += "</div>"

            location_info = ""
            if gap.file_path:
                location_info = f"""
                <div class="detail-row">
                    <div class="detail-label">Location:</div>
                    <div class="detail-value">{gap.file_path}:{gap.line_number or '?'}</div>
                </div>
                """

            backend_info = ""
            if gap.backend_endpoint:
                backend_info = f"""
                <div class="detail-row">
                    <div class="detail-label">Backend Endpoint:</div>
                    <div class="detail-value">{gap.backend_method} {gap.backend_endpoint}</div>
                </div>
                """

            card = f"""
            <div class="gap-card {severity_class}">
                <div class="gap-header">
                    <div class="gap-title">{gap.expected_method} {gap.expected_endpoint}</div>
                    <span class="badge {severity_class}">{gap.severity.value}</span>
                </div>
                <div class="gap-details">
                    <div class="detail-row">
                        <div class="detail-label">Gap Type:</div>
                        <div class="detail-value">{gap_type_display}</div>
                    </div>
                    <div class="detail-row">
                        <div class="detail-label">Component:</div>
                        <div class="detail-value">{gap.frontend_component}</div>
                    </div>
                    {location_info}
                    {backend_info}
                    <div class="detail-row">
                        <div class="detail-label">Status:</div>
                        <div class="detail-value">{gap.backend_status}</div>
                    </div>
                </div>
                <div class="description">
                    <strong>Description:</strong> {gap.description}
                </div>
                <div class="recommendation">
                    <div class="recommendation-title">💡 Recommendation</div>
                    <div class="recommendation-text">{gap.recommendation}</div>
                </div>
                {features_html}
            </div>
            """
            cards.append(card)

        return "\n".join(cards)

    def generate_json_report(self, output_file: str) -> None:
        """
        Generate a JSON report.

        Args:
            output_file: Path to output JSON file
        """
        report_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_gaps": len(self.gaps),
                "statistics": self.statistics,
            },
            "gaps": [gap.to_dict() for gap in self.gap_detector.prioritize_gaps()],
            "categorized": {
                gap_type: [gap.to_dict() for gap in gaps]
                for gap_type, gaps in self.gap_detector.categorize_gaps().items()
            },
        }

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report_data, f, indent=2)

    def generate_markdown_report(self, output_file: str) -> None:
        """
        Generate a Markdown report.

        Args:
            output_file: Path to output Markdown file
        """
        md = self._generate_markdown_content()

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(md)

    def _generate_markdown_content(self) -> str:
        """
        Generate Markdown content for the report.

        Returns:
            Markdown string
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md = f"""# Frontend-Backend Integration Gap Analysis Report

**Generated:** {timestamp}

## Executive Summary

- **Total Gaps:** {self.statistics['total_gaps']}
- **Critical:** {self.statistics['gaps_by_severity']['critical']}
- **High Priority:** {self.statistics['gaps_by_severity']['high']}
- **Medium Priority:** {self.statistics['gaps_by_severity']['medium']}
- **Low Priority:** {self.statistics['gaps_by_severity']['low']}

## Statistics

- **Unique Endpoints Missing:** {self.statistics.get('unique_endpoints_missing', 0)}
- **Components Affected:** {self.statistics.get('unique_components_affected', 0)}

### Gaps by Type

"""
        for gap_type, count in self.statistics.get("gaps_by_type", {}).items():
            md += f"- **{gap_type}:** {count}\n"

        md += "\n## Detected Gaps\n\n"

        if not self.gaps:
            md += "✅ No integration gaps detected! Frontend and backend are in sync.\n"
        else:
            # Group by severity
            for severity in [GapSeverity.CRITICAL, GapSeverity.HIGH, GapSeverity.MEDIUM, GapSeverity.LOW]:
                gaps = self.gap_detector.get_gaps_by_severity(severity)
                if gaps:
                    md += f"\n### {severity.value.upper()} Priority Gaps\n\n"
                    for gap in gaps:
                        md += self._format_gap_markdown(gap)

        return md

    def _format_gap_markdown(self, gap: Gap) -> str:
        """
        Format a single gap as Markdown.

        Args:
            gap: Gap object

        Returns:
            Markdown string
        """
        gap_type_display = gap.gap_type.value.replace("_", " ").title()

        md = f"""#### {gap.expected_method} {gap.expected_endpoint}

**Type:** {gap_type_display}  
**Severity:** {gap.severity.value}  
**Component:** `{gap.frontend_component}`  
"""

        if gap.file_path:
            md += f"**Location:** `{gap.file_path}:{gap.line_number or '?'}`  \n"

        if gap.backend_endpoint:
            md += f"**Backend Endpoint:** `{gap.backend_method} {gap.backend_endpoint}`  \n"

        md += f"**Status:** {gap.backend_status}  \n\n"

        md += f"**Description:** {gap.description}\n\n"

        md += f"**Recommendation:** {gap.recommendation}\n\n"

        if gap.affected_features:
            md += f"**Affected Features:** {', '.join(gap.affected_features)}\n\n"

        md += "---\n\n"

        return md

    def generate_csv_report(self, output_file: str) -> None:
        """
        Generate a CSV report.

        Args:
            output_file: Path to output CSV file
        """
        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)

            # Write header
            writer.writerow(
                [
                    "Severity",
                    "Gap Type",
                    "Expected Method",
                    "Expected Endpoint",
                    "Component",
                    "File Path",
                    "Line Number",
                    "Backend Status",
                    "Backend Endpoint",
                    "Description",
                    "Recommendation",
                    "Affected Features",
                ]
            )

            # Write gaps
            for gap in self.gap_detector.prioritize_gaps():
                writer.writerow(
                    [
                        gap.severity.value,
                        gap.gap_type.value,
                        gap.expected_method,
                        gap.expected_endpoint,
                        gap.frontend_component,
                        gap.file_path or "",
                        gap.line_number or "",
                        gap.backend_status,
                        gap.backend_endpoint or "",
                        gap.description,
                        gap.recommendation,
                        ", ".join(gap.affected_features),
                    ]
                )

    def generate_all_reports(self, output_dir: str, base_name: str = "gap_analysis") -> Dict[str, str]:
        """
        Generate all report formats.

        Args:
            output_dir: Directory to save reports
            base_name: Base name for report files

        Returns:
            Dictionary mapping format to file path
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        reports = {}

        # HTML report
        html_file = output_path / f"{base_name}.html"
        self.generate_html_report(str(html_file))
        reports["html"] = str(html_file)

        # JSON report
        json_file = output_path / f"{base_name}.json"
        self.generate_json_report(str(json_file))
        reports["json"] = str(json_file)

        # Markdown report
        md_file = output_path / f"{base_name}.md"
        self.generate_markdown_report(str(md_file))
        reports["markdown"] = str(md_file)

        # CSV report
        csv_file = output_path / f"{base_name}.csv"
        self.generate_csv_report(str(csv_file))
        reports["csv"] = str(csv_file)

        return reports

    def print_summary(self) -> None:
        """Print a summary of the gap analysis to console."""
        print("\n" + "=" * 80)
        print("FRONTEND-BACKEND INTEGRATION GAP ANALYSIS SUMMARY")
        print("=" * 80)
        print(f"\nTotal Gaps: {self.statistics['total_gaps']}")
        print(f"  - Critical: {self.statistics['gaps_by_severity']['critical']}")
        print(f"  - High: {self.statistics['gaps_by_severity']['high']}")
        print(f"  - Medium: {self.statistics['gaps_by_severity']['medium']}")
        print(f"  - Low: {self.statistics['gaps_by_severity']['low']}")
        print(f"\nUnique Endpoints Missing: {self.statistics.get('unique_endpoints_missing', 0)}")
        print(f"Components Affected: {self.statistics.get('unique_components_affected', 0)}")

        print("\nGaps by Type:")
        for gap_type, count in self.statistics.get("gaps_by_type", {}).items():
            print(f"  - {gap_type}: {count}")

        if self.statistics["gaps_by_severity"]["critical"] > 0:
            print("\n⚠️  CRITICAL GAPS DETECTED - Immediate action required!")
            critical_gaps = self.gap_detector.get_gaps_by_severity(GapSeverity.CRITICAL)
            for gap in critical_gaps[:5]:  # Show first 5
                print(f"  - {gap.expected_method} {gap.expected_endpoint}")

        print("\n" + "=" * 80 + "\n")
