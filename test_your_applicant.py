"""
Manual Testing Script - Test Your Own Applicant
================================================
Modify the applicant data below and run: python test_your_applicant.py
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from mcp_server.orchestrator import MCPOrchestrator
from mcp_server.context_manager import ContextManager


# ===================================================================
# 👇 MODIFY YOUR APPLICANT DETAILS HERE 👇
# ===================================================================

YOUR_APPLICANT = {
    "first_name": "John",           # Change to your candidate's name
    "last_name": "Doe",
    
    "email": "john.doe@email.com",
    "phone": "555-0123",
    
    # Identity Information
    "ssn": "123-45-6789",          # Change to test SSN
    "date_of_birth": "1990-05-15",  # Format: YYYY-MM-DD
    "current_address": "123 Main Street, Apartment 4B, Chicago, IL 60601",
    
    # Employment Information
    "monthly_income": 5000,         # Monthly gross income
    "employer": "Tech Corporation",
    "employment_start_date": "2020-01-15",  # Format: YYYY-MM-DD
    
    # Optional: Rental History
    "rental_history": [
        {
            "address": "456 Oak Avenue, Chicago, IL",
            "landlord_name": "Property Management LLC",
            "start_date": "2018-01-01",
            "end_date": "2023-12-31",
            "monthly_rent": 1800,
            "payment_history": "On-time"  # or "Late", "Evicted"
        }
    ],
    
    # Optional: Desired Property
    "desired_property": {
        "address": "789 Elm Street, Chicago, IL 60602",
        "monthly_rent": 2200,
        "lease_term_months": 12
    }
}

# ===================================================================
# 👆 MODIFY YOUR APPLICANT DETAILS ABOVE 👆
# ===================================================================


async def test_applicant():
    """Run screening for your applicant"""
    
    print("=" * 80)
    print("🏢 EQUIFAX AI MCP TENANT SCREENING - MANUAL TEST")
    print("=" * 80)
    print()
    
    # Show applicant info
    print("📋 Applicant Information:")
    print("-" * 80)
    print(f"   Name: {YOUR_APPLICANT['first_name']} {YOUR_APPLICANT['last_name']}")
    print(f"   Email: {YOUR_APPLICANT['email']}")
    print(f"   Phone: {YOUR_APPLICANT['phone']}")
    print(f"   SSN: {YOUR_APPLICANT['ssn']}")
    print(f"   Date of Birth: {YOUR_APPLICANT['date_of_birth']}")
    print(f"   Current Address: {YOUR_APPLICANT['current_address']}")
    print(f"   Monthly Income: ${YOUR_APPLICANT['monthly_income']:,}")
    print(f"   Employer: {YOUR_APPLICANT['employer']}")
    print(f"   Employment Start: {YOUR_APPLICANT['employment_start_date']}")
    print()
    
    # Initialize MCP system
    print("🚀 Initializing MCP System...")
    context_manager = ContextManager()
    orchestrator = MCPOrchestrator(context_manager)
    print(f"✅ Orchestrator ready with {len(orchestrator.list_agents())} agents")
    print()
    
    # Run screening
    print("🔄 Starting AI Screening Workflow...")
    print("=" * 80)
    print()
    
    screening_id = f"MANUAL-TEST-{YOUR_APPLICANT['first_name'].upper()}-{YOUR_APPLICANT['last_name'].upper()}"
    
    try:
        # Execute all 8 agents
        results = await orchestrator.execute_screening(
            applicant_data=YOUR_APPLICANT,
            screening_id=screening_id
        )
        
        print()
        print("=" * 80)
        print("✅ SCREENING COMPLETE!")
        print("=" * 80)
        print()
        
        # Extract results
        ingestion = results.get("ingestion", {})
        identity = results.get("identity", {})
        fraud = results.get("fraud", {})
        risk = results.get("risk", {})
        decision = results.get("decision", {})
        compliance = results.get("compliance", {})
        bias = results.get("bias", {})
        audit = results.get("audit", {})
        
        # Display results in detail
        print("📊 DETAILED RESULTS")
        print("=" * 80)
        
        # 1. Identity Verification
        print("\n👤 IDENTITY VERIFICATION")
        print("-" * 80)
        print(f"   Status: {identity.get('status', 'N/A')}")
        print(f"   Verification Confidence: {identity.get('verification_confidence', 0)}%")
        print(f"   SSN Valid: {'✅ Yes' if identity.get('ssn_valid', False) else '❌ No'}")
        print(f"   Age Verification: {'✅ Pass' if identity.get('age_verified', False) else '❌ Fail'}")
        print(f"   Address Valid: {'✅ Yes' if identity.get('address_valid', False) else '❌ No'}")
        
        # 2. Fraud Detection
        print("\n🚨 FRAUD ASSESSMENT")
        print("-" * 80)
        print(f"   Risk Level: {fraud.get('risk_level', 'N/A')}")
        print(f"   Fraud Score: {fraud.get('fraud_score', 0)}%")
        print(f"   Synthetic Identity: {'⚠️ DETECTED' if fraud.get('synthetic_identity_detected', False) else '✅ Not Detected'}")
        print(f"   Duplicate Application: {'⚠️ Found' if fraud.get('duplicate_application', False) else '✅ None'}")
        fraud_indicators = fraud.get('fraud_indicators', [])
        if fraud_indicators:
            print(f"   Indicators: {', '.join(str(i) for i in fraud_indicators)}")
        
        # 3. Risk Scoring
        print("\n📈 RISK ASSESSMENT")
        print("-" * 80)
        risk_score = risk.get('risk_score', 0)
        risk_tier = risk.get('risk_tier', 'N/A')
        
        # Color code risk tier
        tier_emoji = "🟢" if risk_tier == "Low" else ("🟡" if risk_tier == "Moderate" else "🔴")
        print(f"   Risk Score: {risk_score}/1000")
        print(f"   Risk Tier: {tier_emoji} {risk_tier}")
        print(f"   Credit Score: {risk.get('credit_score', 'N/A')}")
        print(f"   Income-to-Rent Ratio: {risk.get('income_to_rent_ratio', 'N/A')}")
        
        risk_drivers = risk.get('key_drivers', [])
        if risk_drivers:
            print(f"   Key Risk Drivers:")
            for driver in risk_drivers[:5]:  # Top 5
                print(f"      • {driver}")
        
        # 4. Final Decision
        print("\n🎯 FINAL DECISION")
        print("-" * 80)
        final_decision = decision.get('decision', 'N/A')
        confidence = decision.get('confidence', 0)
        
        # Color code decision
        if final_decision == "APPROVE":
            decision_emoji = "✅"
            decision_color = "APPROVED"
        elif final_decision == "CONDITIONAL":
            decision_emoji = "⚠️"
            decision_color = "CONDITIONAL APPROVAL"
        else:
            decision_emoji = "❌"
            decision_color = "DENIED"
        
        print(f"   {decision_emoji} Decision: {decision_color}")
        print(f"   Confidence: {confidence}%")
        print(f"   Reasoning: {decision.get('reasoning', 'N/A')}")
        
        conditions = decision.get('conditions', [])
        if conditions:
            print(f"   Conditions:")
            for condition in conditions:
                print(f"      • {condition}")
        
        # 5. Compliance
        print("\n⚖️  COMPLIANCE CHECK")
        print("-" * 80)
        print(f"   Overall Status: {compliance.get('status', 'N/A')}")
        print(f"   FCRA Compliant: {'✅ Yes' if compliance.get('fcra_compliant', False) else '❌ No'}")
        print(f"   Fair Housing Compliant: {'✅ Yes' if compliance.get('fair_housing_compliant', False) else '❌ No'}")
        print(f"   Adverse Action Required: {'⚠️ Yes' if compliance.get('adverse_action_required', False) else '✅ No'}")
        
        # 6. Bias Detection
        print("\n🎭 BIAS & FAIRNESS ANALYSIS")
        print("-" * 80)
        bias_detected = bias.get('bias_detected', False)
        print(f"   Bias Detected: {'⚠️ YES' if bias_detected else '✅ NO'}")
        print(f"   Fairness Score: {bias.get('fairness_score', 0)}%")
        print(f"   Protected Classes Checked: {', '.join(bias.get('protected_classes_checked', []))}")
        
        if bias_detected:
            print(f"   ⚠️ Bias Concerns: {', '.join(bias.get('bias_concerns', []))}")
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 SUMMARY")
        print("=" * 80)
        print(f"   Applicant: {YOUR_APPLICANT['first_name']} {YOUR_APPLICANT['last_name']}")
        print(f"   Decision: {decision_emoji} {decision_color}")
        print(f"   Confidence: {confidence}%")
        print(f"   Risk Score: {risk_score}/1000 ({tier_emoji} {risk_tier})")
        print(f"   Identity Verified: {'✅' if identity.get('status') == 'VERIFIED' else '❌'}")
        print(f"   Fraud Risk: {fraud.get('risk_level', 'N/A')}")
        print(f"   Compliant: {'✅' if compliance.get('status') == 'COMPLIANT' else '❌'}")
        print(f"   Fair: {'✅' if not bias_detected else '⚠️'}")
        print("=" * 80)
        
        # Next steps
        print("\n💡 NEXT STEPS:")
        if final_decision == "APPROVE":
            print("   ✅ Applicant approved! Prepare lease agreement.")
        elif final_decision == "CONDITIONAL":
            print("   ⚠️ Review conditions with applicant:")
            for condition in conditions:
                print(f"      • {condition}")
        else:
            print("   ❌ Send adverse action notice (FCRA requirement)")
            if compliance.get('adverse_action_required'):
                print("      Include specific reasons for denial")
        
        print("\n" + "=" * 80)
        print("✨ Test Complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ Error during screening: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print()
    print("Starting manual applicant test...")
    print()
    asyncio.run(test_applicant())
