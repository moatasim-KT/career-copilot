"""Comprehensive test reporting system for generating and managing test results."""

import json
import logging
import sqlite3
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
import matplotlib.pyplot as plt
import seaborn as sns

from .test_orchestrator import TestPhase, TestResult, TestStatus

logger = logging.getLogger(__name__)


@dataclass
class TestExecutionMetrics:
    """Metrics for test execution."""
    total_tests: int
    passed_tests: int
    failed_tests: int
    error_tests: int
    skipped_tests: int
    total_time: float
    success_rate: float
    average_execution_time: float
    flaky_tests: List[str]


class TestReporter:
    """Manages test result reporting and history tracking."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = output_dir / 'test_history.db'
        self._init_database()
        self.template_dir = Path(__file__).parent / 'templates'

    def _init_database(self):
        """Initialize the SQLite database for test history."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_runs (
                    run_id TEXT PRIMARY KEY,
                    timestamp DATETIME,
                    total_tests INTEGER,
                    passed_tests INTEGER,
                    failed_tests INTEGER,
                    error_tests INTEGER,
                    skipped_tests INTEGER,
                    total_time REAL,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    run_id TEXT,
                    test_id TEXT,
                    phase TEXT,
                    status TEXT,
                    start_time DATETIME,
                    end_time DATETIME,
                    execution_time REAL,
                    error_message TEXT,
                    metadata TEXT,
                    FOREIGN KEY (run_id) REFERENCES test_runs (run_id)
                )
            """)

    def save_results(self, results: Dict[str, TestResult], run_id: str):
        """Save test results to the database."""
        metrics = self._calculate_metrics(results)
        
        with sqlite3.connect(self.db_path) as conn:
            # Save test run summary
            conn.execute(
                """
                INSERT INTO test_runs (
                    run_id, timestamp, total_tests, passed_tests,
                    failed_tests, error_tests, skipped_tests, total_time, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    datetime.now().isoformat(),
                    metrics.total_tests,
                    metrics.passed_tests,
                    metrics.failed_tests,
                    metrics.error_tests,
                    metrics.skipped_tests,
                    metrics.total_time,
                    json.dumps({'success_rate': metrics.success_rate})
                )
            )
            
            # Save individual test results
            for test_id, result in results.items():
                conn.execute(
                    """
                    INSERT INTO test_results (
                        run_id, test_id, phase, status, start_time,
                        end_time, execution_time, error_message, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        test_id,
                        result.phase.value,
                        result.status.value,
                        result.start_time.isoformat(),
                        result.end_time.isoformat() if result.end_time else None,
                        result.execution_time,
                        result.error_message,
                        json.dumps(result.metadata) if result.metadata else None
                    )
                )

    def generate_json_report(self, results: Dict[str, TestResult], run_id: str) -> Path:
        """Generate a JSON report of test results."""
        report_path = self.output_dir / f"test_report_{run_id}.json"
        
        report_data = {
            'run_id': run_id,
            'timestamp': datetime.now().isoformat(),
            'metrics': asdict(self._calculate_metrics(results)),
            'results': {
                test_id: {
                    'phase': result.phase.value,
                    'status': result.status.value,
                    'execution_time': result.execution_time,
                    'error_message': result.error_message,
                    'metadata': result.metadata
                }
                for test_id, result in results.items()
            }
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return report_path

    def generate_html_report(self, results: Dict[str, TestResult], run_id: str) -> Path:
        """Generate an HTML report of test results with visualizations."""
        report_path = self.output_dir / f"test_report_{run_id}.html"
        metrics = self._calculate_metrics(results)
        
        # Generate visualizations
        plots_dir = self.output_dir / 'plots'
        plots_dir.mkdir(exist_ok=True)
        
        self._generate_status_chart(results, plots_dir / 'status_chart.png')
        self._generate_timing_chart(results, plots_dir / 'timing_chart.png')
        self._generate_trend_chart(run_id, plots_dir / 'trend_chart.png')
        
        # Load and render template
        env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir)
        )
        template = env.get_template('test_report_template.html')
        
        html_content = template.render(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            results=results,
            plots={
                'status_chart': 'plots/status_chart.png',
                'timing_chart': 'plots/timing_chart.png',
                'trend_chart': 'plots/trend_chart.png'
            }
        )
        
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return report_path

    def _calculate_metrics(self, results: Dict[str, TestResult]) -> TestExecutionMetrics:
        """Calculate metrics from test results."""
        total = len(results)
        passed = sum(1 for r in results.values() if r.status == TestStatus.PASSED)
        failed = sum(1 for r in results.values() if r.status == TestStatus.FAILED)
        error = sum(1 for r in results.values() if r.status == TestStatus.ERROR)
        skipped = sum(1 for r in results.values() if r.status == TestStatus.SKIPPED)
        
        execution_times = [
            r.execution_time for r in results.values()
            if r.execution_time is not None
        ]
        
        return TestExecutionMetrics(
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            error_tests=error,
            skipped_tests=skipped,
            total_time=sum(execution_times),
            success_rate=passed / total if total > 0 else 0,
            average_execution_time=sum(execution_times) / len(execution_times) if execution_times else 0,
            flaky_tests=self._identify_flaky_tests(results)
        )

    def _identify_flaky_tests(self, results: Dict[str, TestResult]) -> List[str]:
        """Identify potentially flaky tests based on history."""
        flaky_tests = []
        
        with sqlite3.connect(self.db_path) as conn:
            for test_id in results:
                # Check if test has mixed results in recent history
                recent_results = conn.execute(
                    """
                    SELECT status FROM test_results
                    WHERE test_id = ?
                    ORDER BY start_time DESC
                    LIMIT 5
                    """,
                    (test_id,)
                ).fetchall()
                
                if len(recent_results) >= 3:
                    statuses = [r[0] for r in recent_results]
                    if len(set(statuses)) > 1:
                        flaky_tests.append(test_id)
        
        return flaky_tests

    def _generate_status_chart(self, results: Dict[str, TestResult], output_path: Path):
        """Generate a pie chart of test status distribution."""
        status_counts = {
            status: sum(1 for r in results.values() if r.status == status)
            for status in TestStatus
        }
        
        plt.figure(figsize=(8, 8))
        plt.pie(
            status_counts.values(),
            labels=[s.value for s in TestStatus],
            autopct='%1.1f%%'
        )
        plt.title('Test Status Distribution')
        plt.savefig(output_path)
        plt.close()

    def _generate_timing_chart(self, results: Dict[str, TestResult], output_path: Path):
        """Generate a box plot of test execution times by phase."""
        phase_times = {
            phase: [
                r.execution_time for r in results.values()
                if r.phase == phase and r.execution_time is not None
            ]
            for phase in TestPhase
        }
        
        plt.figure(figsize=(10, 6))
        sns.boxplot(data=phase_times)
        plt.title('Test Execution Times by Phase')
        plt.ylabel('Time (seconds)')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()

    def _generate_trend_chart(self, current_run_id: str, output_path: Path):
        """Generate a line chart showing test success rate trend."""
        with sqlite3.connect(self.db_path) as conn:
            trend_data = conn.execute(
                """
                SELECT timestamp,
                       CAST(passed_tests AS FLOAT) / CAST(total_tests AS FLOAT) * 100 as success_rate
                FROM test_runs
                ORDER BY timestamp DESC
                LIMIT 10
                """
            ).fetchall()
        
        dates = [datetime.fromisoformat(row[0]) for row in trend_data]
        rates = [row[1] for row in trend_data]
        
        plt.figure(figsize=(10, 6))
        plt.plot(dates, rates, marker='o')
        plt.title('Test Success Rate Trend')
        plt.ylabel('Success Rate (%)')
        plt.xlabel('Date')
        plt.xticks(rotation=45)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()