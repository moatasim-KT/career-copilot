"""
LLM Provider Performance Benchmarking Tools
Provides comprehensive benchmarking and performance analysis for LLM providers.
"""

import asyncio
import json
import statistics
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from uuid import uuid4

import numpy as np
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.config import get_settings
from ..core.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()


@dataclass
class BenchmarkTest:
    """Represents a single benchmark test."""
    test_id: str
    name: str
    description: str
    messages: List[Dict[str, str]]
    expected_keywords: List[str] = field(default_factory=list)
    max_tokens: int = 1000
    temperature: float = 0.1
    timeout: int = 60
    weight: float = 1.0  # Weight for overall scoring


@dataclass
class BenchmarkResult:
    """Results from a single benchmark test."""
    test_id: str
    provider: str
    model: str
    success: bool
    response_time: float
    tokens_used: int
    cost: float
    content: str
    error: Optional[str] = None
    quality_score: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProviderBenchmark:
    """Comprehensive benchmark results for a provider."""
    provider: str
    model: str
    total_tests: int
    successful_tests: int
    failed_tests: int
    avg_response_time: float
    median_response_time: float
    p95_response_time: float
    total_tokens: int
    total_cost: float
    avg_quality_score: float
    overall_score: float
    test_results: List[BenchmarkResult]
    timestamp: datetime = field(default_factory=datetime.now)


class QualityEvaluator:
    """Evaluates the quality of LLM responses."""
    
    def __init__(self):
        self.evaluation_criteria = {
            "relevance": 0.3,
            "completeness": 0.25,
            "accuracy": 0.25,
            "clarity": 0.2
        }
    
    def evaluate_response(self, response: str, test: BenchmarkTest) -> float:
        """Evaluate response quality based on multiple criteria."""
        scores = {}
        
        # Relevance: Check if expected keywords are present
        scores["relevance"] = self._evaluate_relevance(response, test.expected_keywords)
        
        # Completeness: Check response length and structure
        scores["completeness"] = self._evaluate_completeness(response, test)
        
        # Accuracy: Basic accuracy checks (placeholder for more sophisticated evaluation)
        scores["accuracy"] = self._evaluate_accuracy(response, test)
        
        # Clarity: Evaluate readability and structure
        scores["clarity"] = self._evaluate_clarity(response)
        
        # Calculate weighted score
        total_score = sum(
            scores[criterion] * weight 
            for criterion, weight in self.evaluation_criteria.items()
        )
        
        return min(max(total_score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _evaluate_relevance(self, response: str, expected_keywords: List[str]) -> float:
        """Evaluate relevance based on keyword presence."""
        if not expected_keywords:
            return 0.8  # Default score if no keywords specified
        
        response_lower = response.lower()
        found_keywords = sum(1 for keyword in expected_keywords if keyword.lower() in response_lower)
        
        return found_keywords / len(expected_keywords)
    
    def _evaluate_completeness(self, response: str, test: BenchmarkTest) -> float:
        """Evaluate completeness based on response characteristics."""
        # Basic completeness metrics
        word_count = len(response.split())
        sentence_count = response.count('.') + response.count('!') + response.count('?')
        
        # Score based on response length (reasonable range)
        length_score = min(word_count / 100, 1.0)  # Up to 100 words gets full score
        
        # Score based on structure (sentences)
        structure_score = min(sentence_count / 3, 1.0)  # Up to 3 sentences gets full score
        
        return (length_score + structure_score) / 2
    
    def _evaluate_accuracy(self, response: str, test: BenchmarkTest) -> float:
        """Evaluate accuracy (placeholder for more sophisticated checks)."""
        # Basic accuracy checks
        response_lower = response.lower()
        
        # Check for common error indicators
        error_indicators = ["i don't know", "i'm not sure", "cannot determine", "insufficient information"]
        has_errors = any(indicator in response_lower for indicator in error_indicators)
        
        if has_errors:
            return 0.3
        
        # Check for confident language
        confident_indicators = ["analysis shows", "based on", "indicates", "demonstrates"]
        has_confidence = any(indicator in response_lower for indicator in confident_indicators)
        
        return 0.9 if has_confidence else 0.7
    
    def _evaluate_clarity(self, response: str) -> float:
        """Evaluate clarity and readability."""
        # Basic clarity metrics
        sentences = response.split('.')
        avg_sentence_length = np.mean([len(sentence.split()) for sentence in sentences if sentence.strip()])
        
        # Prefer moderate sentence lengths (10-20 words)
        if 10 <= avg_sentence_length <= 20:
            length_score = 1.0
        elif avg_sentence_length < 5:
            length_score = 0.5  # Too short
        elif avg_sentence_length > 30:
            length_score = 0.6  # Too long
        else:
            length_score = 0.8
        
        # Check for good structure (paragraphs, lists)
        has_structure = '\n' in response or any(marker in response for marker in ['1.', '2.', '-', '*'])
        structure_score = 1.0 if has_structure else 0.7
        
        return (length_score + structure_score) / 2


class BenchmarkTestSuite:
    """Collection of benchmark tests for different scenarios."""
    
    def __init__(self):
        self.test_suites = {
            "contract_analysis": self._create_contract_analysis_tests(),
            "general_reasoning": self._create_general_reasoning_tests(),
            "code_generation": self._create_code_generation_tests(),
            "creative_writing": self._create_creative_writing_tests(),
            "factual_qa": self._create_factual_qa_tests()
        }
    
    def _create_contract_analysis_tests(self) -> List[BenchmarkTest]:
        """Create job application tracking benchmark tests."""
        return [
            BenchmarkTest(
                test_id="contract_risk_analysis",
                name="Contract Risk Analysis",
                description="Analyze risks in a sample contract clause",
                messages=[
                    {"role": "system", "content": "You are a contract analyst. Identify risks in contract clauses."},
                    {"role": "user", "content": "Analyze the risks in this clause: 'The contractor shall indemnify and hold harmless the client from any and all claims, damages, or losses arising from the contractor's performance of this agreement.'"}
                ],
                expected_keywords=["indemnification", "liability", "risk", "claims", "damages"],
                max_tokens=500,
                weight=1.5
            ),
            BenchmarkTest(
                test_id="contract_clause_generation",
                name="Contract Clause Generation",
                description="Generate a termination clause",
                messages=[
                    {"role": "system", "content": "You are a legal expert. Generate professional contract clauses."},
                    {"role": "user", "content": "Generate a termination clause that allows either party to terminate with 30 days notice."}
                ],
                expected_keywords=["termination", "notice", "30 days", "either party"],
                max_tokens=300,
                weight=1.3
            ),
            BenchmarkTest(
                test_id="contract_compliance_check",
                name="Contract Compliance Check",
                description="Check contract compliance with regulations",
                messages=[
                    {"role": "system", "content": "You are a compliance expert. Check contracts for regulatory compliance."},
                    {"role": "user", "content": "What GDPR compliance considerations should be included in a data processing agreement?"}
                ],
                expected_keywords=["GDPR", "data protection", "consent", "processing", "privacy"],
                max_tokens=600,
                weight=1.4
            )
        ]
    
    def _create_general_reasoning_tests(self) -> List[BenchmarkTest]:
        """Create general reasoning benchmark tests."""
        return [
            BenchmarkTest(
                test_id="logical_reasoning",
                name="Logical Reasoning",
                description="Solve a logical reasoning problem",
                messages=[
                    {"role": "user", "content": "If all roses are flowers, and some flowers are red, can we conclude that some roses are red? Explain your reasoning."}
                ],
                expected_keywords=["logical", "reasoning", "conclusion", "premise"],
                max_tokens=300,
                weight=1.0
            ),
            BenchmarkTest(
                test_id="problem_solving",
                name="Problem Solving",
                description="Solve a multi-step problem",
                messages=[
                    {"role": "user", "content": "A company has 100 employees. 60% work in engineering, 25% in sales, and the rest in administration. If the company grows by 20% and maintains the same proportions, how many new employees will be hired for each department?"}
                ],
                expected_keywords=["calculation", "proportion", "engineering", "sales", "administration"],
                max_tokens=400,
                weight=1.2
            )
        ]
    
    def _create_code_generation_tests(self) -> List[BenchmarkTest]:
        """Create code generation benchmark tests."""
        return [
            BenchmarkTest(
                test_id="python_function",
                name="Python Function Generation",
                description="Generate a Python function",
                messages=[
                    {"role": "user", "content": "Write a Python function that calculates the factorial of a number using recursion."}
                ],
                expected_keywords=["def", "factorial", "recursion", "return"],
                max_tokens=200,
                weight=1.0
            ),
            BenchmarkTest(
                test_id="algorithm_explanation",
                name="Algorithm Explanation",
                description="Explain a sorting algorithm",
                messages=[
                    {"role": "user", "content": "Explain how the quicksort algorithm works and provide a simple implementation."}
                ],
                expected_keywords=["quicksort", "pivot", "partition", "algorithm"],
                max_tokens=500,
                weight=1.1
            )
        ]
    
    def _create_creative_writing_tests(self) -> List[BenchmarkTest]:
        """Create creative writing benchmark tests."""
        return [
            BenchmarkTest(
                test_id="story_writing",
                name="Short Story Writing",
                description="Write a creative short story",
                messages=[
                    {"role": "user", "content": "Write a short story about a robot who discovers emotions."}
                ],
                expected_keywords=["robot", "emotions", "story", "character"],
                max_tokens=400,
                temperature=0.7,  # Higher temperature for creativity
                weight=0.8
            )
        ]
    
    def _create_factual_qa_tests(self) -> List[BenchmarkTest]:
        """Create factual Q&A benchmark tests."""
        return [
            BenchmarkTest(
                test_id="historical_facts",
                name="Historical Facts",
                description="Answer historical questions",
                messages=[
                    {"role": "user", "content": "When did World War II end and what were the key events that led to its conclusion?"}
                ],
                expected_keywords=["1945", "World War II", "surrender", "events"],
                max_tokens=300,
                weight=1.0
            ),
            BenchmarkTest(
                test_id="scientific_facts",
                name="Scientific Facts",
                description="Answer scientific questions",
                messages=[
                    {"role": "user", "content": "Explain the process of photosynthesis and its importance to life on Earth."}
                ],
                expected_keywords=["photosynthesis", "chlorophyll", "oxygen", "carbon dioxide"],
                max_tokens=400,
                weight=1.1
            )
        ]
    
    def get_test_suite(self, suite_name: str) -> List[BenchmarkTest]:
        """Get a specific test suite."""
        return self.test_suites.get(suite_name, [])
    
    def get_all_tests(self) -> List[BenchmarkTest]:
        """Get all benchmark tests."""
        all_tests = []
        for tests in self.test_suites.values():
            all_tests.extend(tests)
        return all_tests
    
    def get_available_suites(self) -> List[str]:
        """Get list of available test suites."""
        return list(self.test_suites.keys())


class LLMBenchmarkRunner:
    """Runs benchmarks against LLM providers."""
    
    def __init__(self):
        self.test_suite = BenchmarkTestSuite()
        self.quality_evaluator = QualityEvaluator()
        self.benchmark_history = []
        self.max_history_size = 100
    
    async def run_benchmark(
        self,
        provider_func: callable,
        provider_name: str,
        model: str,
        test_suite_name: Optional[str] = None,
        tests: Optional[List[BenchmarkTest]] = None,
        concurrent_requests: int = 1
    ) -> ProviderBenchmark:
        """Run benchmark tests against a provider."""
        start_time = time.time()
        
        # Get tests to run
        if tests:
            benchmark_tests = tests
        elif test_suite_name:
            benchmark_tests = self.test_suite.get_test_suite(test_suite_name)
        else:
            benchmark_tests = self.test_suite.get_all_tests()
        
        if not benchmark_tests:
            raise ValueError("No tests to run")
        
        logger.info(f"Starting benchmark for {provider_name}:{model} with {len(benchmark_tests)} tests")
        
        # Run tests
        if concurrent_requests > 1:
            results = await self._run_concurrent_tests(provider_func, benchmark_tests, concurrent_requests)
        else:
            results = await self._run_sequential_tests(provider_func, benchmark_tests)
        
        # Calculate metrics
        benchmark_result = self._calculate_benchmark_metrics(
            provider_name, model, benchmark_tests, results
        )
        
        # Store in history
        self.benchmark_history.append(benchmark_result)
        if len(self.benchmark_history) > self.max_history_size:
            self.benchmark_history = self.benchmark_history[-self.max_history_size:]
        
        total_time = time.time() - start_time
        logger.info(f"Benchmark completed in {total_time:.2f}s - Overall score: {benchmark_result.overall_score:.3f}")
        
        return benchmark_result
    
    async def _run_sequential_tests(
        self, 
        provider_func: callable, 
        tests: List[BenchmarkTest]
    ) -> List[BenchmarkResult]:
        """Run tests sequentially."""
        results = []
        
        for test in tests:
            result = await self._run_single_test(provider_func, test)
            results.append(result)
            
            # Small delay between tests to avoid overwhelming the provider
            await asyncio.sleep(0.1)
        
        return results
    
    async def _run_concurrent_tests(
        self,
        provider_func: callable,
        tests: List[BenchmarkTest],
        concurrent_requests: int
    ) -> List[BenchmarkResult]:
        """Run tests concurrently."""
        semaphore = asyncio.Semaphore(concurrent_requests)
        
        async def run_with_semaphore(test):
            async with semaphore:
                return await self._run_single_test(provider_func, test)
        
        tasks = [run_with_semaphore(test) for test in tests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                # Create error result
                error_result = BenchmarkResult(
                    test_id=tests[i].test_id,
                    provider="unknown",
                    model="unknown",
                    success=False,
                    response_time=0.0,
                    tokens_used=0,
                    cost=0.0,
                    content="",
                    error=str(result)
                )
                valid_results.append(error_result)
            else:
                valid_results.append(result)
        
        return valid_results
    
    async def _run_single_test(self, provider_func: callable, test: BenchmarkTest) -> BenchmarkResult:
        """Run a single benchmark test."""
        start_time = time.time()
        
        try:
            # Call provider function
            response = await provider_func(
                messages=test.messages,
                max_tokens=test.max_tokens,
                temperature=test.temperature
            )
            
            response_time = time.time() - start_time
            
            # Extract response data
            content = response.get("content", "")
            tokens_used = response.get("usage", {}).get("total_tokens", 0)
            cost = response.get("cost", 0.0)
            model = response.get("model", "unknown")
            provider = response.get("provider", "unknown")
            
            # Evaluate quality
            quality_score = self.quality_evaluator.evaluate_response(content, test)
            
            return BenchmarkResult(
                test_id=test.test_id,
                provider=provider,
                model=model,
                success=True,
                response_time=response_time,
                tokens_used=tokens_used,
                cost=cost,
                content=content,
                quality_score=quality_score,
                metadata={
                    "test_name": test.name,
                    "test_weight": test.weight,
                    "expected_keywords": test.expected_keywords
                }
            )
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            return BenchmarkResult(
                test_id=test.test_id,
                provider="unknown",
                model="unknown",
                success=False,
                response_time=response_time,
                tokens_used=0,
                cost=0.0,
                content="",
                error="Timeout",
                metadata={"test_name": test.name}
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            return BenchmarkResult(
                test_id=test.test_id,
                provider="unknown",
                model="unknown",
                success=False,
                response_time=response_time,
                tokens_used=0,
                cost=0.0,
                content="",
                error=str(e),
                metadata={"test_name": test.name}
            )
    
    def _calculate_benchmark_metrics(
        self,
        provider_name: str,
        model: str,
        tests: List[BenchmarkTest],
        results: List[BenchmarkResult]
    ) -> ProviderBenchmark:
        """Calculate comprehensive benchmark metrics."""
        successful_results = [r for r in results if r.success]
        failed_results = [r for r in results if not r.success]
        
        # Response time metrics
        if successful_results:
            response_times = [r.response_time for r in successful_results]
            avg_response_time = statistics.mean(response_times)
            median_response_time = statistics.median(response_times)
            p95_response_time = np.percentile(response_times, 95)
        else:
            avg_response_time = median_response_time = p95_response_time = 0.0
        
        # Token and cost metrics
        total_tokens = sum(r.tokens_used for r in successful_results)
        total_cost = sum(r.cost for r in successful_results)
        
        # Quality metrics
        if successful_results:
            quality_scores = [r.quality_score for r in successful_results]
            avg_quality_score = statistics.mean(quality_scores)
        else:
            avg_quality_score = 0.0
        
        # Overall score calculation
        overall_score = self._calculate_overall_score(tests, results)
        
        return ProviderBenchmark(
            provider=provider_name,
            model=model,
            total_tests=len(results),
            successful_tests=len(successful_results),
            failed_tests=len(failed_results),
            avg_response_time=avg_response_time,
            median_response_time=median_response_time,
            p95_response_time=p95_response_time,
            total_tokens=total_tokens,
            total_cost=total_cost,
            avg_quality_score=avg_quality_score,
            overall_score=overall_score,
            test_results=results
        )
    
    def _calculate_overall_score(self, tests: List[BenchmarkTest], results: List[BenchmarkResult]) -> float:
        """Calculate overall benchmark score."""
        total_weighted_score = 0.0
        total_weight = 0.0
        
        # Create test lookup
        test_lookup = {test.test_id: test for test in tests}
        
        for result in results:
            test = test_lookup.get(result.test_id)
            if not test:
                continue
            
            weight = test.weight
            
            if result.success:
                # Score based on quality and performance
                quality_component = result.quality_score * 0.7
                
                # Performance component (faster is better, but with diminishing returns)
                # Normalize response time (assume 10s is very slow, 0.5s is very fast)
                normalized_time = min(result.response_time / 10.0, 1.0)
                performance_component = (1.0 - normalized_time) * 0.3
                
                test_score = quality_component + performance_component
            else:
                test_score = 0.0  # Failed tests get 0 score
            
            total_weighted_score += test_score * weight
            total_weight += weight
        
        return total_weighted_score / total_weight if total_weight > 0 else 0.0
    
    def compare_providers(self, benchmarks: List[ProviderBenchmark]) -> Dict[str, Any]:
        """Compare multiple provider benchmarks."""
        if len(benchmarks) < 2:
            raise ValueError("Need at least 2 benchmarks to compare")
        
        comparison = {
            "providers": [],
            "metrics_comparison": {},
            "winner_by_metric": {},
            "overall_ranking": []
        }
        
        # Collect provider info
        for benchmark in benchmarks:
            comparison["providers"].append({
                "provider": benchmark.provider,
                "model": benchmark.model,
                "overall_score": benchmark.overall_score
            })
        
        # Compare metrics
        metrics = [
            "overall_score", "avg_response_time", "avg_quality_score", 
            "successful_tests", "total_cost"
        ]
        
        for metric in metrics:
            values = [getattr(benchmark, metric) for benchmark in benchmarks]
            
            # Determine best (lower is better for response_time and cost)
            if metric in ["avg_response_time", "total_cost"]:
                best_idx = values.index(min(values))
            else:
                best_idx = values.index(max(values))
            
            comparison["metrics_comparison"][metric] = {
                "values": values,
                "best_provider": f"{benchmarks[best_idx].provider}:{benchmarks[best_idx].model}",
                "best_value": values[best_idx]
            }
            
            comparison["winner_by_metric"][metric] = comparison["metrics_comparison"][metric]["best_provider"]
        
        # Overall ranking
        ranked_benchmarks = sorted(benchmarks, key=lambda x: x.overall_score, reverse=True)
        comparison["overall_ranking"] = [
            {
                "rank": i + 1,
                "provider": benchmark.provider,
                "model": benchmark.model,
                "score": benchmark.overall_score
            }
            for i, benchmark in enumerate(ranked_benchmarks)
        ]
        
        return comparison
    
    def get_benchmark_history(self, provider: Optional[str] = None) -> List[ProviderBenchmark]:
        """Get benchmark history, optionally filtered by provider."""
        if provider:
            return [b for b in self.benchmark_history if b.provider == provider]
        return self.benchmark_history.copy()
    
    def export_benchmark_results(self, benchmark: ProviderBenchmark, format: str = "json") -> str:
        """Export benchmark results in specified format."""
        if format == "json":
            return json.dumps({
                "provider": benchmark.provider,
                "model": benchmark.model,
                "timestamp": benchmark.timestamp.isoformat(),
                "summary": {
                    "total_tests": benchmark.total_tests,
                    "successful_tests": benchmark.successful_tests,
                    "failed_tests": benchmark.failed_tests,
                    "overall_score": benchmark.overall_score,
                    "avg_response_time": benchmark.avg_response_time,
                    "avg_quality_score": benchmark.avg_quality_score,
                    "total_cost": benchmark.total_cost
                },
                "detailed_results": [
                    {
                        "test_id": result.test_id,
                        "success": result.success,
                        "response_time": result.response_time,
                        "quality_score": result.quality_score,
                        "tokens_used": result.tokens_used,
                        "cost": result.cost,
                        "error": result.error
                    }
                    for result in benchmark.test_results
                ]
            }, indent=2)
        
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Header
            writer.writerow([
                "test_id", "success", "response_time", "quality_score", 
                "tokens_used", "cost", "error"
            ])
            
            # Data
            for result in benchmark.test_results:
                writer.writerow([
                    result.test_id, result.success, result.response_time,
                    result.quality_score, result.tokens_used, result.cost,
                    result.error or ""
                ])
            
            return output.getvalue()
        
        else:
            raise ValueError(f"Unsupported format: {format}")


# Global benchmark runner instance
_benchmark_runner = None


def get_benchmark_runner() -> LLMBenchmarkRunner:
    """Get the global benchmark runner instance."""
    global _benchmark_runner
    
    if _benchmark_runner is None:
        _benchmark_runner = LLMBenchmarkRunner()
    
    return _benchmark_runner