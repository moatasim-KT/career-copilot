#!/usr/bin/env python3
"""
Demonstration script for the endpoint discovery and testing framework.

This script demonstrates the framework without requiring full app initialization.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi import FastAPI, Depends, Query
from pydantic import BaseModel
from typing import Optional, List

# Create a simple demo FastAPI app
app = FastAPI(title="Demo API", version="1.0.0")


class Item(BaseModel):
    """Demo item model"""

    name: str
    description: Optional[str] = None
    price: float
    tags: List[str] = []


class ItemResponse(BaseModel):
    """Demo item response"""

    id: int
    name: str
    price: float


# Demo endpoints
@app.get("/", tags=["root"])
async def root():
    """Root endpoint"""
    return {"message": "Demo API", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/items", response_model=List[ItemResponse], tags=["items"])
async def list_items(skip: int = 0, limit: int = Query(default=10, le=100)):
    """List all items"""
    return [{"id": 1, "name": "Item 1", "price": 10.99}, {"id": 2, "name": "Item 2", "price": 20.99}]


@app.get("/items/{item_id}", response_model=ItemResponse, tags=["items"])
async def get_item(item_id: int):
    """Get a specific item"""
    return {"id": item_id, "name": f"Item {item_id}", "price": 10.99}


@app.post("/items", response_model=ItemResponse, tags=["items"], status_code=201)
async def create_item(item: Item):
    """Create a new item"""
    return {"id": 1, "name": item.name, "price": item.price}


@app.put("/items/{item_id}", response_model=ItemResponse, tags=["items"])
async def update_item(item_id: int, item: Item):
    """Update an item"""
    return {"id": item_id, "name": item.name, "price": item.price}


@app.delete("/items/{item_id}", tags=["items"])
async def delete_item(item_id: int):
    """Delete an item"""
    return {"message": f"Item {item_id} deleted"}


@app.get("/search", tags=["search"])
async def search_items(
    query: str, category: Optional[str] = None, min_price: Optional[float] = None, max_price: Optional[float] = None, tags: List[str] = Query(default=[])
):
    """Search for items"""
    return {"query": query, "results": []}


def main():
    """Main demonstration function"""
    print("=" * 80)
    print("Endpoint Discovery and Testing Framework - Demo")
    print("=" * 80)

    # Import framework components
    from app.testing import EndpointDiscovery, EndpointTester, TestDataGenerator

    # 1. Endpoint Discovery
    print("\n" + "=" * 80)
    print("1. ENDPOINT DISCOVERY")
    print("=" * 80)

    discovery = EndpointDiscovery(app)
    endpoints = discovery.discover_endpoints()

    print(f"\n✅ Discovered {len(endpoints)} endpoints\n")

    # Show endpoint details
    for endpoint in endpoints:
        print(f"  {endpoint.method:6} {endpoint.path}")
        if endpoint.parameters:
            print(f"         Parameters: {len(endpoint.parameters)}")
            for param in endpoint.parameters:
                print(f"           - {param.name} ({param.location.value}, {'required' if param.required else 'optional'})")
        if endpoint.tags:
            print(f"         Tags: {', '.join(endpoint.tags)}")
        print()

    # Statistics
    print("\n📊 Statistics:")
    stats = discovery.get_statistics()
    print(f"  Total endpoints: {stats['total_endpoints']}")
    print(f"  Endpoints by method:")
    for method, count in stats["endpoints_by_method"].items():
        print(f"    {method}: {count}")
    print(f"  Endpoints by tag:")
    for tag, count in stats["endpoints_by_tag"].items():
        print(f"    {tag}: {count}")

    # 2. Test Data Generation
    print("\n" + "=" * 80)
    print("2. TEST DATA GENERATION")
    print("=" * 80)

    generator = TestDataGenerator(seed=42)

    # Generate data for an endpoint
    items_endpoint = discovery.get_endpoint_by_path("GET", "/items")
    if items_endpoint:
        print(f"\n📝 Generating test data for: GET /items")
        test_data = generator.generate_test_data(items_endpoint)
        print(f"  Generated data: {test_data}")

        # Generate multiple test cases
        test_cases = generator.generate_multiple_test_cases(items_endpoint)
        print(f"\n  Generated {len(test_cases)} test cases:")
        for i, case in enumerate(test_cases, 1):
            print(f"    {i}. Type: {case['type']}, Data: {case['data']}")

    # 3. Endpoint Testing
    print("\n" + "=" * 80)
    print("3. ENDPOINT TESTING")
    print("=" * 80)

    tester = EndpointTester(app)

    print("\n🧪 Testing all endpoints...\n")
    results = tester.test_all_endpoints()

    # Show results
    for result in results:
        status_symbol = "✅" if result.status.value == "passed" else "❌" if result.status.value == "failed" else "⚠️"
        print(f"  {status_symbol} {result.method:6} {result.endpoint:30} {result.status.value:10} ({result.response_time:.3f}s)")

    # 4. Test Report
    print("\n" + "=" * 80)
    print("4. TEST REPORT")
    print("=" * 80)

    report = tester.generate_test_report()
    summary = report["summary"]

    print(f"\n📈 Summary:")
    print(f"  Total tests: {summary['total_tests']}")
    print(f"  Passed: {summary['passed']} ({summary['pass_rate']:.1f}%)")
    print(f"  Failed: {summary['failed']}")
    print(f"  Errors: {summary['errors']}")
    print(f"  Average response time: {summary['average_response_time']:.3f}s")

    # Show failed tests if any
    failed_tests = tester.get_failed_tests()
    if failed_tests:
        print(f"\n❌ Failed Tests:")
        for test in failed_tests:
            print(f"  {test.method} {test.endpoint}: {test.error_message}")

    # Show slow tests
    slow_tests = tester.get_slow_tests(threshold=0.1)
    if slow_tests:
        print(f"\n🐌 Slow Tests (>0.1s):")
        for test in slow_tests:
            print(f"  {test.method} {test.endpoint}: {test.response_time:.3f}s")

    # 5. Export Reports
    print("\n" + "=" * 80)
    print("5. EXPORT REPORTS")
    print("=" * 80)

    # Export to JSON
    json_file = "demo_test_results.json"
    tester.export_results_to_json(json_file)
    print(f"\n✅ JSON report exported to: {json_file}")

    # Export to HTML
    html_file = "demo_test_results.html"
    tester.export_results_to_html(html_file)
    print(f"✅ HTML report exported to: {html_file}")

    # Export endpoint map
    import json

    endpoint_map_file = "demo_endpoint_map.json"
    endpoint_data = discovery.export_to_dict()
    with open(endpoint_map_file, "w") as f:
        json.dump(endpoint_data, f, indent=2)
    print(f"✅ Endpoint map exported to: {endpoint_map_file}")

    print("\n" + "=" * 80)
    print("✨ Demo Complete!")
    print("=" * 80)
    print("\nThe framework successfully:")
    print("  ✅ Discovered all endpoints with metadata")
    print("  ✅ Generated test data for various scenarios")
    print("  ✅ Tested all endpoints automatically")
    print("  ✅ Generated comprehensive reports")
    print("  ✅ Exported results in multiple formats")
    print("\nYou can now use this framework to test the full Career Copilot API!")
    print("=" * 80)


if __name__ == "__main__":
    main()
