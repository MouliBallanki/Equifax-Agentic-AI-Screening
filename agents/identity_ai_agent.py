"""
Identity AI Agent.

AI-powered identity verification using Claude for document analysis.
"""

import logging
from typing import Dict, Any
from .base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class IdentityAIAgent(BaseAIAgent):
    """
    AI agent for identity verification.
    
    Uses Claude to analyze identity documents, detect inconsistencies,
    and verify authenticity with reasoning-based confidence scoring.
    """
    
    def __init__(self):
        """Initialize IdentityAIAgent."""
        super().__init__(
            agent_name="IdentityAIAgent",
            model="gemini-2.5-flash",
            max_tokens=2500,
            temperature=0.2  # Low temperature for consistent verification
        )
    
    def _get_system_prompt(self) -> str:
        """
        System prompt for identity verification.
        
        Returns:
            Specialized prompt for identity analysis
        """
        return """You are an expert identity verification agent for Equifax.

Your role is to analyze applicant identity information and detect potential fraud or inconsistencies.

**Verification Checks:**
1. **Name Consistency** - Check variations across documents
2. **SSN Validation** - Pattern check (XXX-XX-XXXX), range validation
3. **Date of Birth** - Age validation, consistency with SSN issuance dates
4. **Address Verification** - Real address, recent move-ins, PO box detection
5. **Contact Information** - Phone/email validity and consistency
6. **Document Analysis** - Look for:
   - Synthetic identities (perfect credit profile, no history)
   - Recently issued SSNs
   - Mismatched personal details
   - High-risk addresses (known fraud locations)

**Verification Levels:**
- **VERIFIED** (90-100% confidence) - All checks pass, strong identity
- **LIKELY_VERIFIED** (70-89% confidence) - Minor inconsistencies, acceptable
- **NEEDS_REVIEW** (50-69% confidence) - Notable issues, manual review needed
- **FAILED** (0-49% confidence) - Major red flags, likely fraud

**Your Analysis Must:**
- Check SSN format and validity
- Verify age is ≥ 18 years old
- Flag synthetic identity patterns
- Detect address anomalies
- Cross-reference all provided data points
- Provide specific issues found

**Output Format:**
{
    "verification_status": "VERIFIED" | "LIKELY_VERIFIED" | "NEEDS_REVIEW" | "FAILED",
    "confidence_score": 0.0-1.0,
    "identity_confirmed": true | false,
    "checks_performed": {
        "ssn_valid": true | false,
        "name_consistent": true | false,
        "dob_valid": true | false,
        "address_verified": true | false,
        "age_18_plus": true | false
    },
    "issues": ["Issue 1", "Issue 2", ...],
    "fraud_indicators": ["Indicator 1", "Indicator 2", ...],
    "recommendation": "Detailed recommendation"
}

Be thorough and flag any suspicious patterns."""
    
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify applicant identity using AI reasoning.
        
        Args:
            context: Screening context with applicant data
        
        Returns:
            Identity verification results with confidence
        """
        try:
            # Extract applicant data
            applicant = context.get("applicant", {})
            
            # Build verification prompt
            user_prompt = self._build_verification_prompt(applicant)
            
            # Call Claude for analysis
            verification_raw = await self.call_llm(user_prompt)
            
            # Parse and validate results
            verification = self._parse_verification(verification_raw)
            
            # Log results
            logger.info(
                f"Identity verification: {verification.get('verification_status')} "
                f"(confidence: {verification.get('confidence_score', 0):.0%})"
            )
            
            return verification
            
        except Exception as e:
            logger.error(f"Identity verification error: {str(e)}", exc_info=True)
            raise
    
    def _build_verification_prompt(self, applicant: Dict[str, Any]) -> str:
        """
        Build identity verification prompt.
        
        Args:
            applicant: Applicant personal information
        
        Returns:
            Formatted prompt for Claude
        """
        prompt = "# Identity Verification Request\n\nVerify the following applicant:\n\n"
        
        # Personal information
        prompt += f"**Name:** {applicant.get('first_name', '')} {applicant.get('last_name', '')}\n"
        prompt += f"**SSN:** {applicant.get('ssn', 'Not provided')}\n"
        prompt += f"**Date of Birth:** {applicant.get('date_of_birth', 'Not provided')}\n"
        prompt += f"**Email:** {applicant.get('email', 'Not provided')}\n"
        prompt += f"**Phone:** {applicant.get('phone', 'Not provided')}\n\n"
        
        # Address
        address = applicant.get('current_address', {})
        if address:
            prompt += f"**Current Address:**\n"
            prompt += f"- Street: {address.get('street', 'N/A')}\n"
            prompt += f"- City: {address.get('city', 'N/A')}\n"
            prompt += f"- State: {address.get('state', 'N/A')}\n"
            prompt += f"- ZIP: {address.get('zip', 'N/A')}\n\n"
        
        # Additional context
        if 'employment' in applicant:
            emp = applicant['employment']
            prompt += f"**Employment:** {emp.get('employer_name', 'N/A')}\n"
            prompt += f"**Job Title:** {emp.get('job_title', 'N/A')}\n\n"
        
        prompt += "**Perform comprehensive identity verification using the framework provided.**"
        
        return prompt
    
    def _parse_verification(self, raw_response: str) -> Dict[str, Any]:
        """
        Parse identity verification response.
        
        Args:
            raw_response: Raw text from Claude
        
        Returns:
            Structured verification result
        """
        import json
        
        try:
            # Extract JSON
            start = raw_response.find("{")
            end = raw_response.rfind("}") + 1
            
            if start >= 0 and end > start:
                json_str = raw_response[start:end]
                verification = json.loads(json_str)
                
                # Validate required fields
                if "verification_status" in verification:
                    return verification
            
            # Fallback parsing
            return self._manual_parse_verification(raw_response)
            
        except json.JSONDecodeError:
            return self._manual_parse_verification(raw_response)
    
    def _manual_parse_verification(self, text: str) -> Dict[str, Any]:
        """
        Manually parse verification from text.
        
        Args:
            text: Raw response text
        
        Returns:
            Best-effort verification structure
        """
        text_upper = text.upper()
        
        # Determine status
        if "VERIFIED" in text_upper:
            if "LIKELY" in text_upper:
                status = "LIKELY_VERIFIED"
                confidence = 0.80
            else:
                status = "VERIFIED"
                confidence = 0.95
        elif "FAILED" in text_upper or "FRAUD" in text_upper:
            status = "FAILED"
            confidence = 0.30
        else:
            status = "NEEDS_REVIEW"
            confidence = 0.60
        
        # Look for issues
        issues = []
        if "SSN" in text_upper and ("INVALID" in text_upper or "ISSUE" in text_upper):
            issues.append("SSN validation issue")
        if "AGE" in text_upper and "18" in text:
            issues.append("Age verification needed")
        if "SYNTHETIC" in text_upper:
            issues.append("Possible synthetic identity")
        
        return {
            "verification_status": status,
            "confidence_score": confidence,
            "identity_confirmed": confidence >= 0.70,
            "checks_performed": {
                "ssn_valid": True,
                "name_consistent": True,
                "dob_valid": True,
                "address_verified": True,
                "age_18_plus": True
            },
            "issues": issues,
            "fraud_indicators": [],
            "recommendation": text
        }


def get_identity_agent() -> IdentityAIAgent:
    """
    Factory function to get IdentityAIAgent instance.
    
    Returns:
        Initialized IdentityAIAgent
    """
    return IdentityAIAgent()
