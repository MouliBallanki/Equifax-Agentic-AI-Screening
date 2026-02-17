"""
Proof-of-Concept Demo

Demonstrates the AI-powered tenant screening system end-to-end.
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp_server.orchestrator import AgentOrchestrator
from mcp_server.context_manager import ContextManager
from agents.ingestion_ai_agent import get_ingestion_agent
from agents.credit_agent import get_credit_agent
from agents.fraud_detection_agent import get_fraud_detection_agent
from agents.risk_ai_agent import get_risk_agent


# Sample application data
SAMPLE_APPLICATION = {
    "applicant": {
        "first_name": "Sarah",
        "last_name": "Johnson",
        "email": "sarah.johnson@email.com",
        "phone": "5551234567",
        "ssn": "123-45-6789",
        "date_of_birth": "1988-05-15",
        "current_address": {
            "street": "742 Evergreen Terrace",
            "city": "Springfield",
            "state": "IL",
            "zip": "62704"
        }
    },
    "employment": {
        "employer_name": "Tech Solutions Inc",
        "job_title": "Software Engineer",
        "employment_status": "full-time",
        "annual_income": 95000,
        "years_employed": 3.5,
        "employer_phone": "555-987-6543"
    },
    "rental_history": {
        "current_landlord": "Springfield Properties",
        "current_landlord_phone": "555-555-5555",
        "monthly_rent": 1800,
        "years_at_current": 2.5,
        "reason_for_leaving": "Seeking larger space"
    },
    "additional_info": {
        "pets": False,
        "smoker": False,
        "bankruptcy_history": False,
        "eviction_history": False
    }
}


def print_header(title: str):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_agent_result(agent_name: str, result: dict):
    """Print formatted agent result."""
    print(f"\n📊 {agent_name} Result:")
    print("-" * 60)
    
    if result.get("status") == "error":
        print(f"❌ ERROR: {result.get('error')}")
        return
    
    data = result.get("data", {})
    metadata = result.get("metadata", {})
    
    # Print key metrics
    if agent_name == "IngestionAIAgent":
        applicant = data.get("applicant", {})
        print(f"✓ Applicant: {applicant.get('first_name')} {applicant.get('last_name')}")
        print(f"✓ Income: ${data.get('employment', {}).get('annual_income', 0):,}")
        print(f"✓ Rent History: {data.get('rental_history', {}).get('years_at_current', 0)} years")
    
    elif agent_name == "CreditAgent":
        print(f"✓ Credit Score: {data.get('credit_score')}")
        print(f"✓ Payment History: {data.get('payment_history')}")
        print(f"✓ Total Debt: ${data.get('total_debt', 0):,}")
        print(f"✓ Total Accounts: {data.get('score_factors', {}).get('total_accounts', 0)}")
    
    elif agent_name == "FraudDetectionAgent":
        print(f"✓ Fraud Score: {data.get('fraud_score'):.3f}")
        print(f"✓ Risk Level: {data.get('risk_level')}")
        print(f"✓ Indicators Found: {data.get('total_indicators')}")
        if data.get('fraud_indicators'):
            print("\n  Fraud Indicators:")
            for indicator in data['fraud_indicators'][:3]:  # Show top 3
                print(f"    • {indicator.get('type')}: {indicator.get('description')}")
    
    elif agent_name == "RiskAIAgent":
        print(f"✓ Risk Score: {data.get('risk_score')} / 1000")
        print(f"✓ Risk Tier: {data.get('risk_tier')}")
        print(f"\n  AI Explanation:")
        explanation = data.get('ai_explanation', 'No explanation available')
        for line in explanation.split('\n'):
            if line.strip():
                print(f"    {line.strip()}")
    
    # Print execution metadata
    exec_time = metadata.get('execution_time_ms', 0)
    print(f"\n⏱️  Execution Time: {exec_time}ms")


async def run_demo():
    """Run end-to-end screening demo."""
    
    print_header("🚀 AI Tenant Screening System - Proof of Concept")
    
    print("\n📝 Sample Application:")
    print(json.dumps(SAMPLE_APPLICATION, indent=2))
    
    # Initialize system
    print_header("🔧 Initializing AI Agents & Orchestrator")
    
    context_manager = ContextManager()
    orchestrator = AgentOrchestrator(context_manager)
    
    # Register agents with dependencies
    print("\n✓ Registering IngestionAIAgent...")
    orchestrator.register_agent(
        agent=get_ingestion_agent(),
        dependencies=[]  # First agent, no dependencies
    )
    
    print("✓ Registering CreditAgent...")
    orchestrator.register_agent(
        agent=get_credit_agent(),
        dependencies=["IngestionAIAgent"]  # Needs profile from ingestion
    )
    
    print("✓ Registering FraudDetectionAgent...")
    orchestrator.register_agent(
        agent=get_fraud_detection_agent(),
        dependencies=["IngestionAIAgent", "CreditAgent"]  # Needs both
    )
    
    print("✓ Registering RiskAIAgent...")
    orchestrator.register_agent(
        agent=get_risk_agent(),
        dependencies=["IngestionAIAgent", "CreditAgent", "FraudDetectionAgent"]
    )
    
    print("\n✅ All agents registered!")
    print(f"   Total agents: {len(orchestrator.agents)}")
    
    # Start screening
    print_header("🎯 Starting Tenant Screening")
    
    screening_id = await orchestrator.start_screening(
        raw_application=SAMPLE_APPLICATION
    )
    
    print(f"\n📋 Screening ID: {screening_id}")
    print("⏳ Processing application through AI pipeline...")
    
    # Wait for completion
    try:
        result = await orchestrator.wait_for_completion(screening_id, timeout=60.0)
        
        if result["status"] == "completed":
            print_header("✅ Screening Complete")
            
            # Display results from each agent
            agent_results = result.get("agent_results", {})
            
            for agent_name in ["IngestionAIAgent", "CreditAgent", "FraudDetectionAgent", "RiskAIAgent"]:
                if agent_name in agent_results:
                    print_agent_result(agent_name, agent_results[agent_name])
            
            # Final summary
            print_header("📊 Final Assessment Summary")
            
            risk_data = agent_results.get("RiskAIAgent", {}).get("data", {})
            fraud_data = agent_results.get("FraudDetectionAgent", {}).get("data", {})
            credit_data = agent_results.get("CreditAgent", {}).get("data", {})
            
            print(f"""
🎯 Risk Score: {risk_data.get('risk_score', 'N/A')} / 1000
📊 Risk Tier: {risk_data.get('risk_tier', 'N/A')}
⚠️  Fraud Risk: {fraud_data.get('risk_level', 'N/A')} ({fraud_data.get('fraud_score', 0):.3f})
💳 Credit Score: {credit_data.get('credit_score', 'N/A')}

{'🟢 APPROVE' if risk_data.get('risk_tier') == 'Low' else '🟡 CONDITIONAL APPROVAL' if risk_data.get('risk_tier') == 'Moderate' else '🔴 DENY'}
            """)
            
            # Performance metrics
            metadata = result.get("metadata", {})
            print_header("⚡ Performance Metrics")
            print(f"""
Total Processing Time: {metadata.get('execution_time_ms', 0)}ms
Agents Executed: {metadata.get('total_agents', 0)}
Successfully Completed: {metadata.get('successful_agents', 0)}
Failed: {metadata.get('failed_agents', 0)}
            """)
            
        elif result["status"] == "failed":
            print_header("❌ Screening Failed")
            print(f"\nError: {result.get('error', 'Unknown error')}")
            
    except asyncio.TimeoutError:
        print_header("⏱️ Screening Timeout")
        print("\n❌ Screening did not complete within timeout period")


async def run_multiple_demo():
    """Run screening for multiple applicants to show variety."""
    
    print_header("🚀 Multi-Applicant Demo")
    
    # Additional test cases
    test_cases = [
        {
            "name": "High-Risk Applicant",
            "application": {
                **SAMPLE_APPLICATION,
                "applicant": {
                    **SAMPLE_APPLICATION["applicant"],
                    "first_name": "John",
                    "last_name": "Smith",
                    "ssn": "987-65-4321"
                },
                "employment": {
                    **SAMPLE_APPLICATION["employment"],
                    "annual_income": 35000,
                    "years_employed": 0.3
                }
            }
        },
        {
            "name": "Excellent Applicant",
            "application": {
                **SAMPLE_APPLICATION,
                "applicant": {
                    **SAMPLE_APPLICATION["applicant"],
                    "first_name": "Emily",
                    "last_name": "Chen",
                    "ssn": "456-78-9012"
                },
                "employment": {
                    **SAMPLE_APPLICATION["employment"],
                    "annual_income": 120000,
                    "years_employed": 8.0
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n\n{'='*70}")
        print(f"Testing: {test_case['name']}")
        print('='*70)
        
        context_manager = ContextManager()
        orchestrator = AgentOrchestrator(context_manager)
        
        # Register agents
        orchestrator.register_agent(get_ingestion_agent(), [])
        orchestrator.register_agent(get_credit_agent(), ["IngestionAIAgent"])
        orchestrator.register_agent(get_fraud_detection_agent(), ["IngestionAIAgent", "CreditAgent"])
        orchestrator.register_agent(get_risk_agent(), ["IngestionAIAgent", "CreditAgent", "FraudDetectionAgent"])
        
        screening_id = await orchestrator.start_screening(
            raw_application=test_case["application"]
        )
        
        result = await orchestrator.wait_for_completion(screening_id, timeout=60.0)
        
        if result["status"] == "completed":
            agent_results = result["agent_results"]
            risk_data = agent_results.get("RiskAIAgent", {}).get("data", {})
            
            print(f"\n✅ Risk Score: {risk_data.get('risk_score')} / 1000")
            print(f"   Risk Tier: {risk_data.get('risk_tier')}")


if __name__ == "__main__":
    print("""
╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   AI-Powered Tenant Screening System                            ║
║   Proof-of-Concept Demonstration                                ║
║                                                                  ║
║   Using: Claude Sonnet 4.5 + MCP + EBM                          ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Run main demo
    asyncio.run(run_demo())
    
    # Uncomment to run multiple applicant demo
    # print("\n\n")
    # asyncio.run(run_multiple_demo())
    
    print("\n\n✅ Demo complete!")
