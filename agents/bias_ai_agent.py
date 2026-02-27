"""
Bias AI Agent.

AI-powered fairness checking to detect and mitigate algorithmic bias.
"""

import logging
from typing import Dict, Any
from .base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class BiasAIAgent(BaseAIAgent):
    """
    AI agent for bias detection and fairness monitoring.
    
    Uses Claude to analyze screening decisions for potential bias
    against protected classes, ensuring algorithmic fairness.
    """
    
    def __init__(self):
        """Initialize BiasAIAgent."""
        super().__init__(
            agent_name="BiasAIAgent",
            model="gemini-2.5-flash",
            max_tokens=2500,
            temperature=0.2
        )
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for bias detection.
        
        Returns:
            Specialized prompt for fairness analysis
        """
        return """You are an AI fairness expert specializing in detecting algorithmic bias in tenant screening.

Your role is to analyze tenant screening decisions for potential bias against protected classes.

**Protected Classes (Fair Housing Act):**
- Race / Color
- National Origin
- Religion
- Sex / Gender
- Familial Status (families with children)
- Disability

**Additional Protected Classes (State/Local):**
- Source of Income (Section 8, housing vouchers)
- Sexual Orientation / Gender Identity
- Age
- Veteran Status
- Marital Status

**Bias Detection Framework:**

1. **Disparate Treatment** - Direct discrimination
   - Are protected class characteristics being used in decisions?
   - Are similar applicants treated differently based on group membership?

2. **Disparate Impact** - Neutral policies with discriminatory effects
   - Do credit score requirements disproportionately exclude minorities?
   - Do income requirements create barriers for protected groups?
   - Are fraud models biased against certain demographics?

3. **Proxy Discrimination** - Indirect discrimination via correlated features
   - ZIP code correlates with race
   - First/last names correlate with ethnicity
   - Education level correlates with socioeconomic status

4. **Feedback Loops** - Historical bias amplification
   - Are past biased decisions reinforcing current bias?
   - Is training data representative?

**Fairness Metrics:**
- **Demographic Parity**: Approval rates similar across groups
- **Equal Opportunity**: False negative rates equal across groups
- **Predictive Parity**: Positive predictive value equal across groups

**Your Analysis Must:**
- Check if decision factors correlate with protected classes
- Identify proxy variables that may introduce bias
- Calculate fairness scores
- Flag any suspicious patterns
- Recommend bias mitigation strategies

**Output Format:**
{
    "bias_detected": true | false,
    "fairness_score": 0.0-1.0,
    "bias_indicators": ["Indicator 1", "Indicator 2", ...],
    "protected_classes_affected": ["Class 1", "Class 2", ...],
    "bias_type": "DISPARATE_TREATMENT" | "DISPARATE_IMPACT" | "PROXY_DISCRIMINATION" | "NONE",
    "risk_level": "LOW" | "MODERATE" | "HIGH" | "CRITICAL",
    "mitigation_strategies": ["Strategy 1", "Strategy 2", ...],
    "recommendation": "Detailed fairness recommendation"
}

Be vigilant - flag anything that could indicate bias."""
    
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze screening decision for bias.
        
        Args:
            context: Full screening context
        
        Returns:
            Bias detection results
        """
        try:
            # Extract relevant data (excluding protected class info)
            decision = context.get("decision_result", {})
            risk = context.get("risk_result", {})
            applicant = context.get("applicant", {})
            
            # Build bias detection prompt
            user_prompt = self._build_bias_prompt(decision, risk, applicant)
            
            # Call Claude for bias analysis
            bias_raw = await self.call_llm(user_prompt)
            
            # Parse and validate
            bias = self._parse_bias(bias_raw)
            
            # Log bias check
            logger.info(
                f"Bias check: {'DETECTED' if bias.get('bias_detected') else 'NOT DETECTED'} "
                f"(fairness score: {bias.get('fairness_score', 1.0):.0%})"
            )
            
            return bias
            
        except Exception as e:
            logger.error(f"Bias detection error: {str(e)}", exc_info=True)
            raise
    
    def _build_bias_prompt(
        self,
        decision: Dict[str, Any],
        risk: Dict[str, Any],
        applicant: Dict[str, Any]
    ) -> str:
        """
        Build bias detection prompt.
        
        Args:
            decision: Decision result
            risk: Risk assessment
            applicant: Applicant info (sanitized)
        
        Returns:
            Formatted prompt for Claude
        """
        prompt = "# Bias Detection Request\n\nAnalyze this screening for potential bias:\n\n"
        
        # Decision details
        decision_data = decision.get("data", {})
        prompt += f"## Decision Made\n"
        prompt += f"- Decision: {decision_data.get('decision', 'UNKNOWN')}\n"
        prompt += f"- Confidence: {decision_data.get('confidence', 0)}%\n"
        prompt += f"- Key Factors: {', '.join(decision_data.get('key_factors', []))}\n\n"
        
        # Check for potentially biased factors
        prompt += f"## Factors to Review for Bias\n"
        
        # Income requirements
        income = applicant.get("employment", {}).get("annual_income", 0)
        prompt += f"- Income: ${income:,.0f} (check if requirement is disproportionate)\n"
        
        # Credit score
        risk_data = risk.get("data", {})
        credit_score = risk_data.get("credit_score", 0)
        prompt += f"- Credit Score: {credit_score} (credit scores can have disparate impact)\n"
        
        # Address (potential proxy for race)
        address = applicant.get("current_address", {})
        prompt += f"- ZIP Code: {address.get('zip', 'N/A')} (geographic proxies for protected classes)\n"
        
        # Employment type
        emp_status = applicant.get("employment", {}).get("employment_status", "N/A")
        prompt += f"- Employment Type: {emp_status} (check if gig workers disadvantaged)\n"
        
        # Rental history
        rental_history = applicant.get("rental_history", {})
        years_at_current = rental_history.get("years_at_current", 0)
        prompt += f"- Rental Stability: {years_at_current:.1f} years (may disadvantage younger applicants)\n\n"
        
        # Risk drivers
        prompt += f"## Risk Assessment Drivers\n"
        risk_drivers = risk_data.get("key_risk_drivers", [])
        for driver in risk_drivers:
            prompt += f"- {driver}\n"
        
        prompt += f"\n**Analyze these factors for potential bias against protected classes.**"
        
        return prompt
    
    def _parse_bias(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse bias detection response.
        
        Args:
            raw_response: Raw text from Claude
        
        Returns:
            Structured bias analysis
        """
        import json
        
        try:
            # Extract JSON
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = raw_response[start:end]
                bias = json.loads(json_str)
                
                if "bias_detected" in bias:
                    return bias
            
            # Fallback parsing
            return self._manual_parse_bias(raw_response)
            
        except json.JSONDecodeError:
            return self._manual_parse_bias(raw_response)
    
    def _manual_parse_bias(self, text: str) -> Dict[str, Any]:
        """
        Manually parse bias from text.
        
        Args:
            text: Raw response text
        
        Returns:
            Best-effort bias structure
        """
        text_upper = text.upper()
        
        # Determine if bias detected
        bias_detected = any(keyword in text_upper for keyword in [
            "BIAS DETECTED",
            "DISPARATE",
            "DISCRIMINAT",
            "UNFAIR"
        ])
        
        # Fairness score
        if bias_detected:
            fairness_score = 0.60  # Low fairness if bias found
            risk_level = "HIGH"
        else:
            fairness_score = 0.95  # High fairness if no bias
            risk_level = "LOW"
        
        # Look for specific indicators
        indicators = []
        if "INCOME" in text_upper and "BIAS" in text_upper:
            indicators.append("Income requirement may have disparate impact")
        if "CREDIT" in text_upper and "DISPARATE" in text_upper:
            indicators.append("Credit score requirement affects protected classes")
        if "ZIP" in text_upper or "GEOGRAPHIC" in text_upper:
            indicators.append("Geographic proxy for race detected")
        
        return {
            "bias_detected": bias_detected,
            "fairness_score": fairness_score,
            "bias_indicators": indicators,
            "protected_classes_affected": [],
            "bias_type": "DISPARATE_IMPACT" if bias_detected else "NONE",
            "risk_level": risk_level,
            "mitigation_strategies": [
                "Review decision factors for less discriminatory alternatives",
                "Consider applicant context holistically"
            ] if bias_detected else [],
            "recommendation": text
        }


def get_bias_agent() -> BiasAIAgent:
    """
    Factory function to get BiasAIAgent instance.
    
    Returns:
        Initialized BiasAIAgent
    """
    return BiasAIAgent()
