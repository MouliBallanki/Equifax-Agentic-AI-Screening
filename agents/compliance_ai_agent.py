"""
Compliance AI Agent.

AI-powered compliance checking for FCRA, Fair Housing Act, and state regulations.
"""

import logging
from typing import Dict, Any
from .base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class ComplianceAIAgent(BaseAIAgent):
    """
    AI agent for regulatory compliance verification.
    
    Uses Claude to interpret FCRA, Fair Housing Act, and state regulations
    to ensure screening decisions are compliant.
    """
    
    def __init__(self):
        """Initialize ComplianceAIAgent."""
        super().__init__(
            agent_name="ComplianceAIAgent",
            model="claude-sonnet-4.5-20250514",
            max_tokens=3000,
            temperature=0.1  # Very low temperature for compliance accuracy
        )
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for compliance checking.
        
        Returns:
            Specialized prompt for regulatory compliance
        """
        return """You are an expert compliance agent for Equifax, specializing in tenant screening regulations.

Your role is to ensure all screening decisions comply with federal and state laws.

**Key Regulations:**

1. **Fair Credit Reporting Act (FCRA)**
   - Permissible purpose for credit check
   - Adverse action notice requirements
   - Dispute rights disclosure
   - Maximum credit inquiry retention (2 years)
   - Accuracy and completeness standards

2. **Fair Housing Act (FHA)**
   - Protected classes: race, color, religion, national origin, sex, familial status, disability
   - No discriminatory criteria in decisions
   - Consistent screening criteria application
   - Reasonable accommodations for disabilities
   - No steering or redlining

3. **State/Local Laws**
   - "Ban the Box" requirements (no criminal history in some states)
   - Income requirements (2.5-3x rent maximum in some areas)
   - Credit score minimums (some states prohibit blanket cutoffs)
   - Eviction history lookback periods

**Compliance Checks:**

✅ **PASS - Decision is compliant**
- All criteria are objective and job-related
- No protected class considerations
- Proper adverse action process if denial
- Income requirements reasonable
- Credit criteria justified

❌ **FAIL - Compliance violation detected**
- Discriminatory factors used
- Disproportionate impact on protected class
- Unreasonable requirements
- Missing adverse action notice
- FCRA violations

**Your Analysis Must:**
- Review screening criteria for discriminatory factors
- Check decision rationale for protected class bias
- Validate adverse action process compliance
- Ensure FCRA permissible purpose
- Flag any Fair Housing violations
- Verify state/local law compliance

**Output Format:**
{
    "compliance_status": "COMPLIANT" | "NEEDS_REVIEW" | "VIOLATION",
    "fcra_compliant": true | false,
    "fair_housing_compliant": true | false,
    "state_law_compliant": true | false,
    "violations": ["Violation 1", "Violation 2", ...],
    "risk_level": "LOW" | "MODERATE" | "HIGH",
    "required_actions": ["Action 1", "Action 2", ...],
    "adverse_action_required": true | false,
    "recommendation": "Detailed compliance recommendation"
}

Be thorough and conservative - flag anything questionable."""
    
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check compliance of screening decision.
        
        Args:
            context: Full screening context with all results
        
        Returns:
            Compliance check results
        """
        try:
            # Extract relevant data
            applicant = context.get("applicant", {})
            decision = context.get("decision_result", {})
            risk = context.get("risk_result", {})
            
            # Build compliance check prompt
            user_prompt = self._build_compliance_prompt(applicant, decision, risk)
            
            # Call Claude for compliance analysis
            compliance_raw = await self.call_llm(user_prompt)
            
            # Parse and validate
            compliance = self._parse_compliance(compliance_raw)
            
            # Log compliance status
            logger.info(
                f"Compliance check: {compliance.get('compliance_status')} "
                f"(FCRA: {compliance.get('fcra_compliant')}, "
                f"FHA: {compliance.get('fair_housing_compliant')})"
            )
            
            return compliance
            
        except Exception as e:
            logger.error(f"Compliance check error: {str(e)}", exc_info=True)
            raise
    
    def _build_compliance_prompt(
        self,
        applicant: Dict[str, Any],
        decision: Dict[str, Any],
        risk: Dict[str, Any]
    ) -> str:
        """
        Build compliance check prompt.
        
        Args:
            applicant: Applicant information
            decision: Decision result
            risk: Risk assessment result
        
        Returns:
            Formatted prompt for Claude
        """
        prompt = "# Compliance Review Request\n\nReview this screening decision for compliance:\n\n"
        
        # Applicant summary (no protected class info)
        prompt += f"## Applicant Profile\n"
        prompt += f"- Annual Income: ${applicant.get('employment', {}).get('annual_income', 0):,.0f}\n"
        prompt += f"- Employment: {applicant.get('employment', {}).get('employment_status', 'N/A')}\n"
        prompt += f"- Rental History: {applicant.get('rental_history', {}).get('years_at_current', 0):.1f} years\n\n"
        
        # Decision details
        decision_data = decision.get("data", {})
        prompt += f"## Screening Decision\n"
        prompt += f"- Decision: {decision_data.get('decision', 'UNKNOWN')}\n"
        prompt += f"- Confidence: {decision_data.get('confidence', 0)}%\n"
        prompt += f"- Reasoning: {decision_data.get('reasoning', 'N/A')}\n"
        factors = decision_data.get('key_factors', [])
        factors_str = ', '.join(str(f) for f in factors) if factors else 'None'
        prompt += f"- Key Factors: {factors_str}\n\n"
        
        # Risk factors
        risk_data = risk.get("data", {})
        prompt += f"## Risk Assessment\n"
        prompt += f"- Risk Score: {risk_data.get('risk_score', 0)}/1000\n"
        prompt += f"- Credit Score: {risk_data.get('credit_score', 0)}\n"
        prompt += f"- Risk Tier: {risk_data.get('risk_tier', 'UNKNOWN')}\n\n"
        
        # Criteria applied
        prompt += f"## Screening Criteria Applied\n"
        prompt += f"- Credit score threshold: 580+ (FCRA compliant)\n"
        prompt += f"- Income requirement: 2.5x monthly rent\n"
        prompt += f"- No criminal history consideration (compliant with 'Ban the Box')\n"
        prompt += f"- Fraud detection (permissible purpose)\n\n"
        
        prompt += "**Check compliance using the regulatory framework provided.**"
        
        return prompt
    
    def _parse_compliance(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse compliance check response.
        
        Args:
            raw_response: Raw text from Claude
        
        Returns:
            Structured compliance result
        """
        import json
        
        try:
            # Extract JSON
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = raw_response[start:end]
                compliance = json.loads(json_str)
                
                if "compliance_status" in compliance:
                    return compliance
            
            # Fallback parsing
            return self._manual_parse_compliance(raw_response)
            
        except json.JSONDecodeError:
            return self._manual_parse_compliance(raw_response)
    
    def _manual_parse_compliance(self, text: str) -> Dict[str, Any]:
        """
        Manually parse compliance from text.
        
        Args:
            text: Raw response text
        
        Returns:
            Best-effort compliance structure
        """
        text_upper = text.upper()
        
        # Determine compliance status
        if "VIOLATION" in text_upper:
            status = "VIOLATION"
            fcra = False
            fha = False
        elif "COMPLIANT" in text_upper:
            status = "COMPLIANT"
            fcra = True
            fha = True
        else:
            status = "NEEDS_REVIEW"
            fcra = "FCRA" not in text_upper or "PASS" in text_upper
            fha = "FAIR HOUSING" not in text_upper or "PASS" in text_upper
        
        # Look for violations
        violations = []
        if "DISCRIMINAT" in text_upper:
            violations.append("Potential discriminatory criteria")
        if "ADVERSE ACTION" in text_upper and "MISSING" in text_upper:
            violations.append("Missing adverse action notice")
        
        return {
            "compliance_status": status,
            "fcra_compliant": fcra,
            "fair_housing_compliant": fha,
            "state_law_compliant": True,
            "violations": violations,
            "risk_level": "HIGH" if violations else "LOW",
            "required_actions": ["Review decision manually"] if violations else [],
            "adverse_action_required": "DENY" in text_upper or "CONDITIONAL" in text_upper,
            "recommendation": text
        }


def get_compliance_agent() -> ComplianceAIAgent:
    """
    Factory function to get ComplianceAIAgent instance.
    
    Returns:
        Initialized ComplianceAIAgent
    """
    return ComplianceAIAgent()
