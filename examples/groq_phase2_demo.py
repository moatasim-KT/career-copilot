"""
GROQ Phase 2 Demo
Demonstrates the optimizer, router, and monitor working together.
"""

import asyncio
from backend.app.services.groq_service import GROQTaskType
from backend.app.services.groq_optimizer import get_groq_optimizer
from backend.app.services.groq_router import get_groq_router, RoutingStrategy
from backend.app.services.groq_monitor import get_groq_monitor


async def demo_optimizer():
    """Demonstrate GROQ optimizer."""
    print("\n=== GROQ Optimizer Demo ===\n")
    
    optimizer = get_groq_optimizer()
    
    messages = [
        {"role": "system", "content": "You are a contract analysis expert."},
        {"role": "user", "content": "Analyze the risks in this clause: The contractor shall indemnify the client."}
    ]
    
    print("Generating optimized completion...")
    result = await optimizer.optimized_completion(
        messages=messages,
        task_type=GROQTaskType.FAST_ANALYSIS,
        priority="balanced"
    )
    
    print(f"Model used: {result['model']}")
    print(f"Processing time: {result['processing_time']:.2f}s")
    print(f"Cost: ${result['cost']:.6f}")
    print(f"Confidence: {result['confidence_score']:.2f}")
    print(f"\nResponse: {result['content'][:200]}...")
    
    # Get optimization report
    report = await optimizer.get_optimization_report()
    print(f"\nOptimization Stats:")
    print(f"  Cache hit rate: {report['metrics']['cache_hit_rate']:.2%}")
    print(f"  Cost savings: ${report['metrics']['cost_savings']:.6f}")


async def demo_router():
    """Demonstrate GROQ router."""
    print("\n=== GROQ Router Demo ===\n")
    
    router = get_groq_router()
    
    # Test different routing strategies
    strategies = [
        RoutingStrategy.PERFORMANCE_BASED,
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.QUALITY_FOCUSED,
        RoutingStrategy.ADAPTIVE
    ]
    
    for strategy in strategies:
        decision = await router.select_model(
            task_type=GROQTaskType.FAST_ANALYSIS,
            strategy=strategy
        )
        
        print(f"{strategy.value}:")
        print(f"  Selected: {decision.selected_model.value}")
        print(f"  Confidence: {decision.confidence:.2f}")
        print(f"  Est. cost: ${decision.estimated_cost:.6f}")
        print(f"  Est. time: {decision.estimated_time:.2f}s")
        print(f"  Reasoning: {decision.reasoning}\n")


async def demo_monitor():
    """Demonstrate GROQ monitor."""
    print("\n=== GROQ Monitor Demo ===\n")
    
    monitor = get_groq_monitor()
    
    # Simulate some requests
    print("Recording sample requests...")
    from backend.app.services.groq_service import GROQModel
    
    for i in range(5):
        monitor.record_request(
            model=GROQModel.LLAMA3_1_8B,
            task_type=GROQTaskType.FAST_ANALYSIS,
            response_time=1.0 + i * 0.2,
            token_count=500 + i * 50,
            cost=0.000025 + i * 0.000005,
            quality_score=0.85 + i * 0.02,
            success=True
        )
    
    # Get dashboard data
    dashboard = monitor.get_dashboard_data("1h")
    
    print(f"\nDashboard Summary:")
    print(f"  Total requests: {dashboard['summary']['total_requests']}")
    print(f"  Success rate: {dashboard['summary']['success_rate']:.2%}")
    print(f"  Total cost: ${dashboard['summary']['total_cost']:.6f}")
    print(f"  Avg response time: {dashboard['summary']['avg_response_time']:.2f}s")
    print(f"  Avg quality: {dashboard['summary']['avg_quality_score']:.2f}")
    
    # Get cost report
    cost_report = monitor.get_cost_report("hourly")
    print(f"\nCost Report:")
    print(f"  Total cost: ${cost_report['total_cost']:.6f}")
    print(f"  Cost breakdown: {len(cost_report['cost_breakdown'])} models tracked")


async def demo_integration():
    """Demonstrate full integration."""
    print("\n=== Full Integration Demo ===\n")
    
    optimizer = get_groq_optimizer()
    router = get_groq_router()
    monitor = get_groq_monitor()
    
    # Step 1: Route
    print("Step 1: Routing to optimal model...")
    decision = await router.select_model(
        task_type=GROQTaskType.FAST_ANALYSIS,
        strategy=RoutingStrategy.ADAPTIVE,
        context={
            "urgency": "high",
            "budget_constraint": "normal",
            "quality_requirement": "high"
        }
    )
    print(f"  Selected: {decision.selected_model.value}")
    
    # Step 2: Optimize and execute
    print("\nStep 2: Generating optimized completion...")
    messages = [
        {"role": "user", "content": "What are the key risks in employment contracts?"}
    ]
    
    result = await optimizer.optimized_completion(
        messages=messages,
        task_type=GROQTaskType.FAST_ANALYSIS,
        priority="balanced"
    )
    print(f"  Completed in {result['processing_time']:.2f}s")
    
    # Step 3: Monitor
    print("\nStep 3: Recording metrics...")
    monitor.record_request(
        model=decision.selected_model,
        task_type=GROQTaskType.FAST_ANALYSIS,
        response_time=result['processing_time'],
        token_count=result['usage']['total_tokens'],
        cost=result['cost'],
        quality_score=result['confidence_score'],
        success=True
    )
    
    # Step 4: Update router
    router.record_request_result(
        model=decision.selected_model,
        task_type=GROQTaskType.FAST_ANALYSIS,
        response_time=result['processing_time'],
        quality_score=result['confidence_score'],
        cost=result['cost'],
        success=True
    )
    print("  Metrics recorded and router updated")
    
    # Get final stats
    print("\nFinal Statistics:")
    opt_report = await optimizer.get_optimization_report()
    routing_stats = router.get_routing_statistics()
    dashboard = monitor.get_dashboard_data("1h")
    
    print(f"  Optimizer cache hits: {opt_report['metrics']['cache_hits']}")
    print(f"  Router total models: {routing_stats['total_models']}")
    print(f"  Monitor total requests: {dashboard['summary']['total_requests']}")


async def main():
    """Run all demos."""
    print("=" * 60)
    print("GROQ Phase 2 Demonstration")
    print("=" * 60)
    
    try:
        await demo_optimizer()
        await demo_router()
        await demo_monitor()
        await demo_integration()
        
        print("\n" + "=" * 60)
        print("Demo completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
