"""
Test GCP Vertex AI Integration.

Verifies that Vertex AI Claude is working correctly with service account.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from agents.base_ai_agent import BaseAIAgent
except ImportError:
    print("❌ Failed to import agents. Run: pip install -r requirements.txt")
    sys.exit(1)


class TestAgent(BaseAIAgent):
    """Simple test agent for Vertex AI."""
    
    def __init__(self):
        super().__init__(
            agent_name="TestAgent",
            model="claude-sonnet-4.5-20250514",
            temperature=0.7
        )
    
    async def _run(self, input_data):
        """Test runner."""
        return {"status": "success"}
    
    def _get_system_prompt(self):
        return "You are a test AI assistant for Vertex AI integration."


async def test_vertex_ai():
    """Test Vertex AI setup."""
    
    print("🧪 GCP Vertex AI Integration Test\n")
    print("=" * 60)
    
    # Check environment variables
    print("\n1️⃣  Checking Environment Variables:")
    print("-" * 60)
    
    gcp_project = os.getenv("GCP_PROJECT_ID")
    gcp_region = os.getenv("GCP_REGION", "us-central1")
    gcp_sa_json = os.getenv("GCP_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"   GCP_PROJECT_ID: {'✅ ' + gcp_project if gcp_project else '❌ Not set'}")
    print(f"   GCP_REGION: {gcp_region}")
    print(f"   GCP_SERVICE_ACCOUNT_JSON: {'✅ ' + gcp_sa_json if gcp_sa_json else '❌ Not set'}")
    
    if gcp_sa_json and not Path(gcp_sa_json).exists():
        print(f"   ⚠️  Warning: Service account file not found: {gcp_sa_json}")
    
    # Initialize agent
    print("\n2️⃣  Initializing Test Agent:")
    print("-" * 60)
    
    agent = TestAgent()
    
    print(f"   Provider: {agent.llm_provider}")
    print(f"   Has Claude: {'✅ Yes' if agent.has_claude else '❌ No'}")
    print(f"   Model: {agent.model}")
    
    if agent.llm_provider == "vertex-ai":
        print("   ✅ GCP Vertex AI successfully initialized!")
    elif agent.llm_provider == "anthropic":
        print("   ℹ️  Using Anthropic API (Vertex AI not configured)")
    else:
        print("   ⚠️  No AI provider - using mock responses")
    
    # Test API call
    print("\n3️⃣  Testing API Call:")
    print("-" * 60)
    
    try:
        response = await agent.call_llm(
            "What is 2+2? Answer with just the number.",
            max_tokens=100
        )
        
        print(f"   Request: What is 2+2?")
        print(f"   Response: {response.strip()}")
        print(f"   ✅ API call successful via {agent.llm_provider}!")
        
    except Exception as e:
        print(f"   ❌ API call failed: {e}")
        print(f"   Provider was: {agent.llm_provider}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:\n")
    
    if agent.llm_provider == "vertex-ai":
        print("✅ GCP Vertex AI is working correctly!")
        print(f"   Project: {gcp_project}")
        print(f"   Region: {gcp_region}")
        print(f"   Model: {agent.model}")
    else:
        print("⚠️  No AI provider configured - using mock responses")
        print("   To enable GCP Vertex AI:")
        print("      $env:GCP_PROJECT_ID = \"your-project-id\"")
        print("      $env:GCP_SERVICE_ACCOUNT_JSON = \"path\\to\\service-account.json\"")
        print("   📖 See GCP_VERTEX_AI_SETUP.md for detailed instructions")


if __name__ == "__main__":
    try:
        asyncio.run(test_vertex_ai())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
