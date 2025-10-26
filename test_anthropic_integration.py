#!/usr/bin/env python3
"""
Test script to verify Anthropic integration is working properly.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
backend_path = Path("backend").absolute()
sys.path.insert(0, str(backend_path))

from langchain.schema import HumanMessage, SystemMessage
from app.core.ai_models import ModelManager, ModelCapability


async def test_anthropic_integration():
    """Test Anthropic model integration."""
    print("🧪 Testing Anthropic Integration...")
    
    # Check if API key is available
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    if not anthropic_key:
        print("⚠️  ANTHROPIC_API_KEY not found in environment")
        print("   Set your API key to test Anthropic integration:")
        print("   export ANTHROPIC_API_KEY='your-api-key-here'")
        return False
    
    try:
        # Initialize model manager
        manager = ModelManager()
        
        # Check available models
        available_models = manager.get_available_models()
        print(f"📋 Available models: {available_models}")
        
        # Check for Anthropic models
        anthropic_models = [model for model in available_models if "claude" in model.lower()]
        if not anthropic_models:
            print("❌ No Anthropic models available")
            return False
        
        print(f"✅ Found Anthropic models: {anthropic_models}")
        
        # Test message generation
        messages = [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content="What is the capital of France? Please provide a brief answer.")
        ]
        
        # Try to get an Anthropic model
        anthropic_model = manager.get_model_by_capability(
            ModelCapability.TEXT_GENERATION, 
            preferred_model=anthropic_models[0]
        )
        
        if not anthropic_model:
            print("❌ Could not get Anthropic model instance")
            return False
        
        print(f"🤖 Testing with model: {anthropic_model.config.name}")
        
        # Generate response
        response = await anthropic_model.generate_response(messages)
        
        print(f"✅ Response generated successfully!")
        print(f"   Content: {response.content[:100]}...")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Tokens used: {response.tokens_used}")
        print(f"   Cost estimate: ${response.cost_estimate:.6f}")
        print(f"   Processing time: {response.processing_time:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing Anthropic integration: {e}")
        return False


async def test_model_comparison():
    """Test comparing OpenAI and Anthropic models."""
    print("\n🔄 Testing Model Comparison...")
    
    try:
        manager = ModelManager()
        
        messages = [
            SystemMessage(content="You are a helpful AI assistant."),
            HumanMessage(content="Explain quantum computing in one sentence.")
        ]
        
        # Compare models
        results = await manager.compare_models(
            messages, 
            ModelCapability.TEXT_GENERATION
        )
        
        print(f"📊 Comparison results:")
        for model_name, response in results.items():
            if response:
                print(f"   {model_name}:")
                print(f"     Content: {response.content[:80]}...")
                print(f"     Confidence: {response.confidence:.2f}")
                print(f"     Cost: ${response.cost_estimate:.6f}")
            else:
                print(f"   {model_name}: Failed")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in model comparison: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Anthropic Integration Tests")
    print("=" * 50)
    
    # Test basic integration
    basic_test = await test_anthropic_integration()
    
    # Test model comparison if basic test passed
    comparison_test = False
    if basic_test:
        comparison_test = await test_model_comparison()
    
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    print(f"   Basic Integration: {'✅ PASS' if basic_test else '❌ FAIL'}")
    print(f"   Model Comparison:  {'✅ PASS' if comparison_test else '❌ FAIL'}")
    
    if basic_test and comparison_test:
        print("\n🎉 All tests passed! Anthropic integration is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)