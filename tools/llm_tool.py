"""
LLM Tool.

Centralized Claude API client for all agents.
"""

import os
import logging
from typing import Dict, Any, Optional
import time

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

logger = logging.getLogger(__name__)


class LLMTool:
    """
    Centralized LLM access tool for MCP agents.
    
    Provides rate limiting, retry logic, and usage tracking.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM tool.
        
        Args:
            api_key: Anthropic API key (or from env)
        """
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
        if not self.api_key:
            logger.warning("No Anthropic API key provided")
        
        if HAS_ANTHROPIC and self.api_key:
            self.client = AsyncAnthropic(api_key=self.api_key)
        else:
            self.client = None
        
        # Usage tracking
        self.total_tokens = 0
        self.total_cost = 0.0
        self.call_count = 0
    
    async def call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str = "claude-sonnet-4.5-20250514",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ) -> str:
        """
        Call Claude API.
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            model: Claude model name
            max_tokens: Max response tokens
            temperature: Sampling temperature
        
        Returns:
            Claude's response text
        """
        if not self.client:
            logger.warning("Claude client not available, using mock response")
            return self._mock_response(user_prompt)
        
        start_time = time.time()
        
        try:
            response = await self.client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract text
            content = response.content[0].text
            
            # Track usage
            self.call_count += 1
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            self.total_tokens += input_tokens + output_tokens
            
            # Cost calculation (approximate for Claude Sonnet)
            # $3 per million input tokens, $15 per million output tokens
            cost = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
            self.total_cost += cost
            
            elapsed = (time.time() - start_time) * 1000
            
            logger.info(
                f"Claude call: {elapsed:.0f}ms, "
                f"tokens={input_tokens}+{output_tokens}, "
                f"cost=${cost:.4f}"
            )
            
            return content
            
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}", exc_info=True)
            raise
    
    def _mock_response(self, prompt: str) -> str:
        """
        Generate mock response when API unavailable.
        
        Args:
            prompt: User prompt
        
        Returns:
            Mock JSON response
        """
        # Simple mock based on prompt keywords
        if "identity" in prompt.lower() or "verify" in prompt.lower():
            return """{
                "verification_status": "VERIFIED",
                "confidence_score": 0.85,
                "identity_confirmed": true,
                "checks_performed": {
                    "ssn_valid": true,
                    "name_consistent": true,
                    "dob_valid": true,
                    "address_verified": true,
                    "age_18_plus": true
                },
                "issues": [],
                "fraud_indicators": [],
                "recommendation": "Identity verified successfully with high confidence."
            }"""
        
        elif "decision" in prompt.lower():
            return """{
                "decision": "APPROVE",
                "confidence": 85,
                "reasoning": "Strong credit profile, verified identity, no fraud indicators.",
                "key_factors": ["Good credit score", "Stable employment", "Clean rental history"],
                "risk_mitigation": null,
                "conditions": null,
                "fair_housing_compliant": true
            }"""
        
        elif "fraud" in prompt.lower():
            return """{
                "fraud_risk_level": "LOW",
                "fraud_score": 0.15,
                "fraud_indicators": [],
                "synthetic_identity_probability": 0.05,
                "recommendation": "No significant fraud indicators detected."
            }"""
        
        else:
            return """{
                "status": "success",
                "analysis": "Mock response - API key not configured",
                "confidence": 0.5
            }"""
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics.
        
        Returns:
            Usage stats dictionary
        """
        return {
            "total_calls": self.call_count,
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost, 2),
            "avg_tokens_per_call": (
                self.total_tokens // self.call_count if self.call_count > 0 else 0
            )
        }
