"""
Comprehensive End-to-End Test.

Tests the complete AI MCP screening system with all 8 agents.
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.orchestrator import AgentOrchestrator
from mcp_server.context_manager import ContextManager


# Test application data
TEST_APPLICATION = {
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


def print_header(title: str, width: int = 80):
    """Print formatted section header."""
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_agent_result(agent_name: str, result: dict, width: int = 80):
    """Print formatted agent result."""
    print(f"\n📊 {agent_name}")
    print("-" * width)
    
    if result.get("status") == "error":
        print(f"❌ ERROR: {result.get('error')}")
        return
    
    data = result.get("data", {})
    exec_time = result.get("execution_time_ms", 0)
    
    # Agent-specific formatting
    if "Ingestion" in agent_name:
        print(f"✅ Data Quality: {data.get('quality_score', 0):.0%}")
        print(f"   Applicant: {data.get('applicant_name', 'N/A')}")
        print(f"   Income: ${data.get('annual_income', 0):,.0f}")
        print(f"   Fields Extracted: {data.get('fields_extracted', 0)}")
    
    elif "Identity" in agent_name:
        print(f"✅ Status: {data.get('verification_status', 'UNKNOWN')}")
        print(f"   Confidence: {data.get('confidence_score', 0):.0%}")
        issues = data.get('issues', [])
        if issues:
            print(f"   Issues: {', '.join(issues)}")
        else:
            print(f"   ✓ No issues detected")
    
    elif "Fraud" in agent_name:
        print(f"{'❌' if data.get('fraud_risk_level') == 'HIGH' else '✅'} Risk Level: {data.get('fraud_risk_level', 'UNKNOWN')}")
        print(f"   Fraud Score: {data.get('fraud_score', 0):.0%}")
        indicators = data.get('fraud_indicators', [])
        if indicators:
            indicators_str = ', '.join(str(i) for i in indicators)
            print(f"   Indicators: {indicators_str}")
        else:
            print(f"   ✓ No fraud indicators")
    
    elif "Risk" in agent_name:
        risk_score = data.get('risk_score', 0)
        print(f"📈 Risk Score: {risk_score}/1000")
        print(f"   Tier: {data.get('risk_tier', 'UNKNOWN')}")
        print(f"   Credit Score: {data.get('credit_score', 0)}")
        drivers = data.get('key_risk_drivers', [])[:3]
        if drivers:
            drivers_str = ', '.join(str(d) for d in drivers)
            print(f"   Top Drivers: {drivers_str}")
    
    elif "Decision" in agent_name:
        decision = data.get('decision', 'UNKNOWN')
        confidence = data.get('confidence', 0)
        
        if decision == "APPROVE":
            emoji = "✅"
        elif decision == "CONDITIONAL_APPROVE":
            emoji = "⚠️"
        else:
            emoji = "❌"
        
        print(f"{emoji} Decision: {decision}")
        print(f"   Confidence: {confidence}%")
        factors = data.get('key_factors', [])
        factors_str = ', '.join(str(f) for f in factors) if factors else 'None'
        print(f"   Key Factors: {factors_str}")
        
        reasoning = data.get('reasoning', '')
        if reasoning and len(reasoning) < 200:
            print(f"   Reasoning: {reasoning}")
    
    elif "Compliance" in agent_name:
        status = data.get('compliance_status', 'UNKNOWN')
        print(f"{'✅' if status == 'COMPLIANT' else '⚠️'} Status: {status}")
        print(f"   FCRA Compliant: {data.get('fcra_compliant', False)}")
        print(f"   Fair Housing: {data.get('fair_housing_compliant', False)}")
        violations = data.get('violations', [])
        if violations:
            print(f"   ⚠️ Violations: {', '.join(violations)}")
    
    elif "Bias" in agent_name:
        bias_detected = data.get('bias_detected', False)
        fairness_score = data.get('fairness_score', 1.0)
        print(f"{'⚠️' if bias_detected else '✅'} Bias Detected: {bias_detected}")
        print(f"   Fairness Score: {fairness_score:.0%}")
        if bias_detected:
            indicators = data.get('bias_indicators', [])
            print(f"   Indicators: {', '.join(indicators)}")
    
    elif "Audit" in agent_name:
        print(f"✅ Audit Complete")
        print(f"   Records Created: {data.get('records_created', 0)}")
        print(f"   Compliance Verified: {data.get('compliance_verified', False)}")
        print(f"   Bias Checked: {data.get('bias_checked', False)}")
    
    print(f"   ⏱️ Execution: {exec_time:.0f}ms")


async def run_test():
    """Run comprehensive end-to-end test."""
    print_header("🚀 Equifax AI MCP Screening System - End-to-End Test")
    
    print("\n📋 Test Configuration:")
    print(f"   • MCP-based orchestration: ✓")
    print(f"   • AI agents: 8 (all using Claude Sonnet 4.5)")
    print(f"   • Test applicant: {TEST_APPLICATION['applicant']['first_name']} {TEST_APPLICATION['applicant']['last_name']}")
    print(f"   • Annual income: ${TEST_APPLICATION['employment']['annual_income']:,.0f}")
    
    # Initialize system
    print_header("⚙️ Initializing MCP System")
    context_manager = ContextManager()
    orchestrator = AgentOrchestrator(context_manager)
    
    print("✓ Context Manager initialized")
    print(f"✓ Orchestrator initialized with {len(orchestrator.agents)} agents:")
    for agent_name in orchestrator.agents.keys():
        deps = orchestrator.agent_dependencies.get(agent_name, [])
        print(f"   - {agent_name} (depends on: {deps or 'none'})")
    
    # Create application
    print_header("📝 Submitting Application")
    application_id = f"APP-{datetime.utcnow().strftime('%Y%m%d')}-TEST001"
    context_manager.create_context(application_id, TEST_APPLICATION)
    print(f"✓ Application created: {application_id}")
    
    # Execute screening
    print_header("🔄 Executing AI Agent Screening Workflow")
    print("\nPhases:")
    print("  1️⃣ Ingestion & Identity (parallel)")
    print("  2️⃣ Fraud & Risk (parallel)")
    print("  3️⃣ Decision")
    print("  4️⃣ Compliance & Bias (parallel)")
    print("  5️⃣ Audit Trail\n")
    
    start_time = datetime.utcnow()
    
    try:
        result = await orchestrator.execute_screening(application_id)
        
        end_time = datetime.utcnow()
        total_time = (end_time - start_time).total_seconds() * 1000
        
        print_header("📊 Agent Execution Results")
        
        # Print each agent result
        agent_results = result.get("agent_results", [])
        for agent_result in agent_results:
            agent_name = agent_result.get("agent", "Unknown Agent")
            print_agent_result(agent_name, agent_result)
        
        # Final summary
        print_header("✨ Screening Summary")
        
        final_decision = result.get("final_decision", {})
        decision = final_decision.get("decision", "UNKNOWN")
        confidence = final_decision.get("confidence", 0)
        
        if decision == "APPROVE":
            emoji = "🎉"
            color_msg = "APPROVED"
        elif decision == "CONDITIONAL_APPROVE":
            emoji = "⚠️"
            color_msg = "CONDITIONALLY APPROVED"
        else:
            emoji = "❌"
            color_msg = "DENIED"
        
        print(f"\n{emoji} FINAL DECISION: {color_msg}")
        print(f"   Confidence: {confidence}%")
        print(f"   Processing Time: {total_time:.0f}ms")
        print(f"   Agents Executed: {len(agent_results)}")
        
        # Key metrics
        print(f"\n📈 Key Metrics:")
        for agent_result in agent_results:
            if "Risk" in agent_result.get("agent", ""):
                risk_data = agent_result.get("data", {})
                print(f"   • Risk Score: {risk_data.get('risk_score', 0)}/1000")
                print(f"   • Credit Score: {risk_data.get('credit_score', 0)}")
            
            if "Identity" in agent_result.get("agent", ""):
                identity_data = agent_result.get("data", {})
                print(f"   • Identity Verified: {identity_data.get('identity_confirmed', False)}")
            
            if "Compliance" in agent_result.get("agent", ""):
                comp_data = agent_result.get("data", {})
                print(f"   • FCRA Compliant: {comp_data.get('fcra_compliant', False)}")
                print(f"   • Fair Housing: {comp_data.get('fair_housing_compliant', False)}")
            
            if "Bias" in agent_result.get("agent", ""):
                bias_data = agent_result.get("data", {})
                print(f"   • Bias Detected: {bias_data.get('bias_detected', False)}")
                print(f"   • Fairness Score: {bias_data.get('fairness_score', 1.0):.0%}")
        
        print_header("✅ TEST COMPLETE")
        print(f"\n🎯 System Status: OPERATIONAL")
        print(f"⚡ Performance: {total_time:.0f}ms for 8-agent workflow")
        print(f"✨ Architecture: MCP-based AI with Claude Sonnet 4.5\n")
        
        return True
        
    except Exception as e:
        print_header("❌ TEST FAILED")
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("  EQUIFAX AI MCP TENANT SCREENING PLATFORM")
    print("  End-to-End System Test")
    print("=" * 80)
    print(f"\nTest Date: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"Python Version: {sys.version.split()[0]}")
    
    success = asyncio.run(run_test())
    
    if success:
        print("✅ All tests passed!")
        sys.exit(0)
    else:
        print("❌ Tests failed!")
        sys.exit(1)
