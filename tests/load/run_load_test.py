#!/usr/bin/env python3
"""
Load test runner script for Career Copilot.
Executes different load testing scenarios based on configuration.
"""

import os
import json
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any

from monitoring import setup_prometheus_monitoring, get_current_metrics
from reporting import LoadTestReporter

def load_config() -> Dict[str, Any]:
    """Load test configuration."""
    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    with open(config_path, "r") as f:
        return json.load(f)

def run_load_test(scenario_name: str, config: Dict[str, Any]):
    """Run a load test scenario."""
    scenario = config["scenarios"].get(scenario_name)
    if not scenario:
        print(f"Error: Scenario '{scenario_name}' not found in configuration")
        return
    
    # Create results directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = os.path.join(
        os.path.dirname(__file__),
        "results",
        f"{scenario_name}_{timestamp}"
    )
    os.makedirs(results_dir, exist_ok=True)
    
    # Set up monitoring
    if config["monitoring"]["enable_prometheus"]:
        metrics_port = 9090
        setup_prometheus_monitoring(metrics_port)
        print(f"Prometheus metrics available at http://localhost:{metrics_port}/metrics")
    
    # Prepare Locust command
    cmd = [
        "locust",
        "-f", "locustfile.py",
        "--host", os.getenv("LOAD_TEST_HOST", "http://localhost:8000"),
        "--users", str(scenario["users"]),
        "--spawn-rate", str(scenario["spawn_rate"]),
        "--run-time", scenario["run_time"],
        "--html", os.path.join(results_dir, "report.html"),
        "--csv", os.path.join(results_dir, "stats"),
        "--headless"
    ]
    
    # Add Prometheus export if enabled
    if config["monitoring"]["enable_prometheus"]:
        cmd.extend([
            "--csv-full-history",
            "--print-stats",
            "--expect-workers", "1"
        ])
    
    print(f"\nStarting load test scenario: {scenario_name}")
    print(f"Description: {scenario['description']}")
    print(f"Configuration:")
    print(f"  Users: {scenario['users']}")
    print(f"  Spawn Rate: {scenario['spawn_rate']}")
    print(f"  Duration: {scenario['run_time']}")
    print(f"Results will be saved to: {results_dir}\n")
    
    try:
        # Run Locust
        subprocess.run(cmd, check=True)
        
        # Generate enhanced reports
        reporter = LoadTestReporter(results_dir)
        reporter.generate_comprehensive_report()
        
        # Collect final metrics if Prometheus is enabled
        if config["monitoring"]["enable_prometheus"]:
            metrics = get_current_metrics()
            metrics_file = os.path.join(results_dir, "prometheus_metrics.json")
            with open(metrics_file, "w") as f:
                json.dump(metrics, f, indent=2)
        
        print(f"\nLoad test completed successfully")
        print(f"Results and reports are available in: {results_dir}")
        print("\nGenerated artifacts:")
        print(f"- HTML Report: {os.path.join(results_dir, 'report.html')}")
        print(f"- CSV Stats: {os.path.join(results_dir, 'stats.csv')}")
        print(f"- Detailed Report: {os.path.join(results_dir, 'report/detailed_report.md')}")
        print(f"- Performance Graphs: {os.path.join(results_dir, 'report/*.png')}")
        if config["monitoring"]["enable_prometheus"]:
            print(f"- Prometheus Metrics: {metrics_file}")
        
    except subprocess.CalledProcessError as e:
        print(f"\nError running load test: {e}")
        print("Check the logs above for more details")

def generate_summary(results_dir: str, scenario: Dict[str, Any], config: Dict[str, Any]):
    """Generate a summary of the load test results."""
    stats_file = os.path.join(results_dir, "stats_history.csv")
    if not os.path.exists(stats_file):
        return
    
    summary_file = os.path.join(results_dir, "summary.txt")
    thresholds = config["thresholds"]
    
    import pandas as pd
    df = pd.read_csv(stats_file)
    
    with open(summary_file, "w") as f:
        f.write("Load Test Summary\n")
        f.write("================\n\n")
        
        f.write(f"Scenario: {scenario['description']}\n")
        f.write(f"Duration: {scenario['run_time']}\n")
        f.write(f"Users: {scenario['users']}\n")
        f.write(f"Spawn Rate: {scenario['spawn_rate']}\n\n")
        
        f.write("Performance Metrics\n")
        f.write("-----------------\n")
        f.write(f"Total Requests: {df['Total Request Count'].max()}\n")
        f.write(f"Failed Requests: {df['Total Failure Count'].max()}\n")
        f.write(f"Average Response Time: {df['Total Average Response Time'].mean():.2f}ms\n")
        f.write(f"95th Percentile: {df['Total 95%'].max():.2f}ms\n")
        f.write(f"99th Percentile: {df['Total 99%'].max():.2f}ms\n")
        f.write(f"Peak RPS: {df['Total Current RPS'].max():.2f}\n\n")
        
        # Check thresholds
        f.write("Threshold Analysis\n")
        f.write("-----------------\n")
        
        p95_ok = df['Total 95%'].max() <= thresholds["response_time_p95"]
        f.write(f"95th Percentile Response Time: {'✓' if p95_ok else '✗'} ")
        f.write(f"({df['Total 95%'].max():.2f}ms vs {thresholds['response_time_p95']}ms threshold)\n")
        
        p99_ok = df['Total 99%'].max() <= thresholds["response_time_p99"]
        f.write(f"99th Percentile Response Time: {'✓' if p99_ok else '✗'} ")
        f.write(f"({df['Total 99%'].max():.2f}ms vs {thresholds['response_time_p99']}ms threshold)\n")
        
        error_rate = (df['Total Failure Count'].max() / df['Total Request Count'].max()) * 100
        error_ok = error_rate <= thresholds["error_rate"]
        f.write(f"Error Rate: {'✓' if error_ok else '✗'} ")
        f.write(f"({error_rate:.2f}% vs {thresholds['error_rate']}% threshold)\n")
        
        rps_ok = df['Total Current RPS'].max() >= thresholds["requests_per_second"]
        f.write(f"Requests Per Second: {'✓' if rps_ok else '✗'} ")
        f.write(f"({df['Total Current RPS'].max():.2f} vs {thresholds['requests_per_second']} threshold)\n")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Career Copilot Load Test Runner")
    parser.add_argument(
        "scenario",
        choices=["smoke_test", "average_load", "peak_load", "stress_test", "endurance_test"],
        help="Load test scenario to run"
    )
    args = parser.parse_args()
    
    config = load_config()
    run_load_test(args.scenario, config)

if __name__ == "__main__":
    main()