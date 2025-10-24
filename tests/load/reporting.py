"""
Enhanced reporting module for load test results.
"""

import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from typing import Dict, Any, List
from datetime import datetime

class LoadTestReporter:
    """Enhanced load test results reporter."""
    
    def __init__(self, results_dir: str):
        """Initialize reporter with results directory."""
        self.results_dir = results_dir
        self.stats_file = os.path.join(results_dir, "stats_history.csv")
        self.config_file = os.path.join(os.path.dirname(__file__), "config.json")
        
        # Load configuration
        with open(self.config_file, "r") as f:
            self.config = json.load(f)
    
    def generate_comprehensive_report(self):
        """Generate comprehensive test report with visualizations."""
        if not os.path.exists(self.stats_file):
            print("No stats file found")
            return
        
        # Load test data
        df = pd.read_csv(self.stats_file)
        
        # Create report directory
        report_dir = os.path.join(self.results_dir, "report")
        os.makedirs(report_dir, exist_ok=True)
        
        # Generate visualizations
        self._generate_response_time_graph(df, report_dir)
        self._generate_requests_graph(df, report_dir)
        self._generate_error_rate_graph(df, report_dir)
        
        # Generate detailed report
        self._generate_detailed_report(df, report_dir)
    
    def _generate_response_time_graph(self, df: pd.DataFrame, report_dir: str):
        """Generate response time visualization."""
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Total Average Response Time'], label='Average')
        plt.plot(df.index, df['Total 95%'], label='95th Percentile')
        plt.plot(df.index, df['Total 99%'], label='99th Percentile')
        plt.axhline(y=self.config['thresholds']['response_time_p95'],
                   color='r', linestyle='--', label='P95 Threshold')
        plt.title('Response Time Over Time')
        plt.xlabel('Time')
        plt.ylabel('Response Time (ms)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(report_dir, 'response_times.png'))
        plt.close()
    
    def _generate_requests_graph(self, df: pd.DataFrame, report_dir: str):
        """Generate requests per second visualization."""
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df['Total Current RPS'], label='RPS')
        plt.axhline(y=self.config['thresholds']['requests_per_second'],
                   color='r', linestyle='--', label='Target RPS')
        plt.title('Requests Per Second Over Time')
        plt.xlabel('Time')
        plt.ylabel('Requests/Second')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(report_dir, 'requests.png'))
        plt.close()
    
    def _generate_error_rate_graph(self, df: pd.DataFrame, report_dir: str):
        """Generate error rate visualization."""
        error_rate = (df['Total Failure Count'] / df['Total Request Count']) * 100
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, error_rate, label='Error Rate')
        plt.axhline(y=self.config['thresholds']['error_rate'],
                   color='r', linestyle='--', label='Error Threshold')
        plt.title('Error Rate Over Time')
        plt.xlabel('Time')
        plt.ylabel('Error Rate (%)')
        plt.legend()
        plt.grid(True)
        plt.savefig(os.path.join(report_dir, 'error_rate.png'))
        plt.close()
    
    def _generate_detailed_report(self, df: pd.DataFrame, report_dir: str):
        """Generate detailed performance report."""
        report_file = os.path.join(report_dir, 'detailed_report.md')
        
        with open(report_file, 'w') as f:
            f.write('# Load Test Performance Report\n\n')
            f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n\n')
            
            # Overall Statistics
            f.write('## Overall Statistics\n\n')
            f.write('### Key Metrics\n')
            f.write(f'- Total Requests: {df["Total Request Count"].max():,.0f}\n')
            f.write(f'- Failed Requests: {df["Total Failure Count"].max():,.0f}\n')
            f.write(f'- Average Response Time: {df["Total Average Response Time"].mean():.2f}ms\n')
            f.write(f'- Peak Response Time: {df["Total Average Response Time"].max():.2f}ms\n')
            f.write(f'- Average RPS: {df["Total Current RPS"].mean():.2f}\n')
            f.write(f'- Peak RPS: {df["Total Current RPS"].max():.2f}\n\n')
            
            # Performance Analysis
            f.write('## Performance Analysis\n\n')
            f.write('### Response Time Distribution\n')
            f.write('| Percentile | Value (ms) |\n')
            f.write('|------------|------------|\n')
            f.write(f'| 50th | {df["Total 50%"].mean():.2f} |\n')
            f.write(f'| 90th | {df["Total 90%"].mean():.2f} |\n')
            f.write(f'| 95th | {df["Total 95%"].mean():.2f} |\n')
            f.write(f'| 99th | {df["Total 99%"].mean():.2f} |\n\n')
            
            # Threshold Analysis
            f.write('## Threshold Analysis\n\n')
            self._write_threshold_analysis(f, df)
            
            # Endpoint Performance
            f.write('## Endpoint Performance\n\n')
            self._write_endpoint_analysis(f, df)
            
            # Recommendations
            f.write('## Recommendations\n\n')
            self._write_recommendations(f, df)
    
    def _write_threshold_analysis(self, f, df: pd.DataFrame):
        """Write threshold analysis section."""
        thresholds = self.config['thresholds']
        
        # Response time analysis
        p95_max = df['Total 95%'].max()
        p99_max = df['Total 99%'].max()
        error_rate = (df['Total Failure Count'].max() / df['Total Request Count'].max()) * 100
        avg_rps = df['Total Current RPS'].mean()
        
        f.write('### Response Time Thresholds\n')
        status = '✅' if p95_max <= thresholds['response_time_p95'] else '❌'
        f.write(f'- P95 Response Time: {status} ({p95_max:.2f}ms vs {thresholds["response_time_p95"]}ms threshold)\n')
        
        status = '✅' if p99_max <= thresholds['response_time_p99'] else '❌'
        f.write(f'- P99 Response Time: {status} ({p99_max:.2f}ms vs {thresholds["response_time_p99"]}ms threshold)\n')
        
        f.write('\n### Error Rate Threshold\n')
        status = '✅' if error_rate <= thresholds['error_rate'] else '❌'
        f.write(f'- Error Rate: {status} ({error_rate:.2f}% vs {thresholds["error_rate"]}% threshold)\n')
        
        f.write('\n### Throughput Threshold\n')
        status = '✅' if avg_rps >= thresholds['requests_per_second'] else '❌'
        f.write(f'- Average RPS: {status} ({avg_rps:.2f} vs {thresholds["requests_per_second"]} threshold)\n\n')
    
    def _write_endpoint_analysis(self, f, df: pd.DataFrame):
        """Write endpoint-specific analysis."""
        endpoints = self.config['endpoints']
        
        f.write('| Endpoint | Avg Response Time | P95 | Error Rate | RPS |\n')
        f.write('|----------|-------------------|-----|------------|-----|\n')
        
        for endpoint, config in endpoints.items():
            endpoint_df = df[df['Name'] == endpoint]
            if not endpoint_df.empty:
                avg_rt = endpoint_df['Average Response Time'].mean()
                p95 = endpoint_df['95%'].mean()
                error_rate = (endpoint_df['Failure Count'].sum() / endpoint_df['Request Count'].sum()) * 100
                rps = endpoint_df['Current RPS'].mean()
                
                status = '✅' if avg_rt <= config['expected_response_time'] else '❌'
                f.write(f'| {endpoint} | {status} {avg_rt:.2f}ms | {p95:.2f}ms | {error_rate:.2f}% | {rps:.2f} |\n')
    
    def _write_recommendations(self, f, df: pd.DataFrame):
        """Generate performance recommendations."""
        recommendations = []
        
        # Response time recommendations
        if df['Total 95%'].max() > self.config['thresholds']['response_time_p95']:
            recommendations.append(
                "- Consider optimizing slow endpoints or adding caching to improve response times"
            )
        
        # Error rate recommendations
        error_rate = (df['Total Failure Count'].max() / df['Total Request Count'].max()) * 100
        if error_rate > self.config['thresholds']['error_rate']:
            recommendations.append(
                "- Investigate error patterns and implement better error handling or retry mechanisms"
            )
        
        # Throughput recommendations
        avg_rps = df['Total Current RPS'].mean()
        if avg_rps < self.config['thresholds']['requests_per_second']:
            recommendations.append(
                "- Consider scaling the application or optimizing database queries to handle higher throughput"
            )
        
        # Write recommendations
        if recommendations:
            f.write('### Performance Improvements\n')
            for rec in recommendations:
                f.write(f'{rec}\n')
        else:
            f.write('All performance metrics are within acceptable thresholds.\n')