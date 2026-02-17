"""
Quick Demo Script - Run This First!

Minimal test to verify system is working without needing API keys.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))


async def quick_test():
    """Quick system test without API calls."""
    
    print("\n" + "=" * 70)
    print("  🚀 EQUIFAX AI MCP SCREENING - QUICK TEST")
    print("=" * 70)
    
    print("\n1. Testing imports...")
    try:
        from mcp_server.context_manager import ContextManager
        from mcp_server.orchestrator import AgentOrchestrator
        from agents import (
            get_ingestion_agent,
            get_identity_agent,
            get_decision_agent
        )
        print("   ✅ All imports successful")
    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("\n   Run: pip install -r requirements.txt")
        return False
    
    print("\n2. Initializing MCP system...")
    try:
        context_manager = ContextManager()
        orchestrator = AgentOrchestrator(context_manager)
        print(f"   ✅ Orchestrator initialized with {len(orchestrator.agents)} agents")
        
        # List agents
        for agent_name, agent in orchestrator.agents.items():
            deps = orchestrator.agent_dependencies.get(agent_name, [])
            print(f"      • {agent_name} (deps: {deps or 'none'})")
    
    except Exception as e:
        print(f"   ❌ Initialization error: {e}")
        return False
    
    print("\n3. Testing context management...")
    try:
        test_data = {
            "applicant": {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com"
            }
        }
        
        app_id = "TEST-001"
        context_manager.create_context(app_id, test_data)
        
        retrieved = context_manager.get_context(app_id)
        assert retrieved is not None
        assert retrieved["applicant"]["first_name"] == "Test"
        
        print("   ✅ Context management working")
    except Exception as e:
        print(f"   ❌ Context test failed: {e}")
        return False
    
    print("\n4. Testing agent initialization...")
    try:
        ingestion = get_ingestion_agent()
        identity = get_identity_agent()
        decision = get_decision_agent()
        
        assert ingestion.agent_name == "IngestionAIAgent"
        assert identity.agent_name == "IdentityAIAgent"
        assert decision.agent_name == "DecisionAIAgent"
        
        print("   ✅ All agents initialize correctly")
    except Exception as e:
        print(f"   ❌ Agent initialization error: {e}")
        return False
    
    print("\n5. System architecture check...")
    try:
        # Check dependency graph
        expected_agents = {
            "ingestion", "identity", "fraud", "risk",
            "decision", "compliance", "bias", "audit"
        }
        
        actual_agents = set(orchestrator.agents.keys())
        
        if expected_agents == actual_agents:
            print(f"   ✅ All 8 agents registered correctly")
        else:
            missing = expected_agents - actual_agents
            extra = actual_agents - expected_agents
            if missing:
                print(f"   ⚠️  Missing agents: {missing}")
            if extra:
                print(f"   ⚠️  Extra agents: {extra}")
    
    except Exception as e:
        print(f"   ❌ Architecture check failed: {e}")
        return False
    
    print("\n" + "=" * 70)
    print("  ✅ QUICK TEST PASSED - System is operational!")
    print("=" * 70)
    
    print("\n📋 Next Steps:")
    print("   1. Set ANTHROPIC_API_KEY in .env file")
    print("   2. Run full test: python test_full_system.py")
    print("   3. Start API server: python -m api.main")
    print("   4. Try endpoints: http://localhost:8000/docs")
    
    print("\n💡 Tip: Without API key, agents will use mock responses")
    print("   This is fine for testing the orchestration flow!\n")
    
    return True


if __name__ == "__main__":
    print(f"\nTest Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    
    try:
        success = asyncio.run(quick_test())
        
        if success:
            print("✅ System ready!")
            sys.exit(0)
        else:
            print("❌ System check failed!")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
