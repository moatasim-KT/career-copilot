#!/usr/bin/env python3
"""
Example usage of the Anthropic integration in the Career Copilot AI models system.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
backend_path = Path("backend").absolute()
sys.path.insert(0, str(backend_path))

from langchain.schema import HumanMessage, SystemMessage
from app.core.ai_models import ModelManager, ModelCapability


async def basic_anthropic_usage():
    """Basic example of using Anthropic models."""
    print("🤖 Basic Anthropic Usage Example")
    print("-" * 40)
    
    # Initialize model manager
    manager = ModelManager()
    
    # Create messages
    messages = [
        SystemMessage(content="You are a career counselor AI assistant."),
        HumanMessage(content="What are the key skills needed for a data scientist role in 2024?")
    ]
    
    try:
        # Get Anthropic model for text generation
        model = manager.get_model_by_capability(
            ModelCapability.TEXT_GENERATION,
            preferred_model="claude-3-sonnet-20240229"
        )
        
        if not model:
            print("❌ Anthropic model not available")
            return
        
        print(f"Using model: {model.config.name}")
        
        # Generate response
        response = await model.generate_response(messages)
        
        print(f"\n📝 Response:")
        print(response.content)
        print(f"\n📊 Metrics:")
        print(f"   Confidence: {response.confidence:.2f}")
        print(f"   Tokens: {response.tokens_used}")
        print(f"   Cost: ${response.cost_estimate:.6f}")
        print(f"   Time: {response.processing_time:.2f}s")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def fallback_example():
    """Example of using fallback between models."""
    print("\n🔄 Fallback Example")
    print("-" * 40)
    
    manager = ModelManager()
    
    messages = [
        SystemMessage(content="You are a technical interviewer."),
        HumanMessage(content="Create a challenging Python coding question for a senior developer interview.")
    ]
    
    try:
        # Try to use Anthropic first, fallback to OpenAI if needed
        response = await manager.generate_with_fallback(
            messages=messages,
            capability=ModelCapability.TEXT_GENERATION,
            preferred_model="claude-3-opus-20240229",  # Try the most capable model first
            min_confidence=0.8,
            max_attempts=3
        )
        
        print(f"✅ Generated with: {response.model_name}")
        print(f"📝 Response: {response.content[:200]}...")
        print(f"📊 Confidence: {response.confidence:.2f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def model_comparison_example():
    """Example of comparing responses from different models."""
    print("\n⚖️  Model Comparison Example")
    print("-" * 40)
    
    manager = ModelManager()
    
    messages = [
        SystemMessage(content="You are a resume reviewer."),
        HumanMessage(content="What are the top 3 mistakes people make on their resumes?")
    ]
    
    try:
        # Compare responses from all available models
        results = await manager.compare_models(
            messages=messages,
            capability=ModelCapability.ANALYSIS
        )
        
        print("📊 Comparison Results:")
        for model_name, response in results.items():
            if response:
                print(f"\n🤖 {model_name}:")
                print(f"   Content: {response.content[:150]}...")
                print(f"   Confidence: {response.confidence:.2f}")
                print(f"   Cost: ${response.cost_estimate:.6f}")
                print(f"   Time: {response.processing_time:.2f}s")
            else:
                print(f"\n❌ {model_name}: Failed to generate response")
        
    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all examples."""
    print("🚀 Anthropic Integration Usage Examples")
    print("=" * 50)
    
    await basic_anthropic_usage()
    await fallback_example()
    await model_comparison_example()
    
    print("\n" + "=" * 50)
    print("✅ Examples completed!")
    print("\n💡 Tips:")
    print("   - Set ANTHROPIC_API_KEY in your .env file to use Anthropic models")
    print("   - Claude models are excellent for reasoning and analysis tasks")
    print("   - Use fallback functionality for production reliability")
    print("   - Compare models to find the best one for your specific use case")


if __name__ == "__main__":
    asyncio.run(main())