"""
Base AI Agent.

Foundation class for all AI-powered agents using Claude/GPT-4.
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

try:
    from anthropic import AsyncAnthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logging.warning("Anthropic SDK not available")

try:
    from google.auth import default
    from google.oauth2 import service_account
    from anthropic import AnthropicVertex
    HAS_VERTEX = True
except ImportError:
    HAS_VERTEX = False
    logging.warning("GCP Vertex AI SDK not available")

logger = logging.getLogger(__name__)


class BaseAIAgent(ABC):
    """
    Base class for all AI agents.
    
    Provides common functionality:
    - Claude API integration
    - Logging and error handling
    - Input/output standardization
    - Performance metrics
    """
    
    def __init__(
        self,
        agent_name: str,
        model: str = "claude-sonnet-4.5-20250514",
        max_tokens: int = 4000,
        temperature: float = 0.7
    ):
        """
        Initialize AI agent.
        
        Args:
            agent_name: Unique agent identifier
            model: Claude model to use
            max_tokens: Maximum tokens for response
            temperature: Model temperature (0-1)
        """
        self.agent_name = agent_name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logging.getLogger(f"agents.{agent_name}")
        
        # Initialize Claude client (Vertex AI only, fallback to mock)
        self.claude_client = None
        self.has_claude = False
        self.llm_provider = "none"
        
        # Try GCP Vertex AI (with service account)
        if HAS_VERTEX and self._init_vertex_ai():
            self.has_claude = True
            self.llm_provider = "vertex-ai"
            self.logger.info(f"{agent_name}: Using GCP Vertex AI Claude")
        else:
            # Fallback to mock responses (no Anthropic API)
            self.logger.warning(f"{agent_name}: No Vertex AI configured, using mock responses")
            self.logger.info(f"To enable GCP Vertex AI, set: GCP_PROJECT_ID, GCP_SERVICE_ACCOUNT_JSON")
    
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent.
        
        Args:
            input_data: Input context from orchestrator
            
        Returns:
            Agent result with status and data
        """
        start_time = datetime.utcnow()
        
        self.logger.info(f"{self.agent_name}: Starting execution")
        
        try:
            # Validate input
            self._validate_input(input_data)
            
            # Run agent logic
            result = await self._run(input_data)
            
            # Calculate execution time
            end_time = datetime.utcnow()
            execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Wrap result
            return {
                "status": "success",
                "agent": self.agent_name,
                "data": result,
                "metadata": {
                    "execution_time_ms": execution_time_ms,
                    "model_used": self.model if self.has_claude else "fallback",
                    "timestamp": end_time.isoformat()
                }
            }
            
        except Exception as e:
            self.logger.error(f"{self.agent_name}: Execution failed: {e}", exc_info=True)
            return {
                "status": "error",
                "agent": self.agent_name,
                "error": str(e),
                "error_type": type(e).__name__,
                "metadata": {
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    @abstractmethod
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Agent-specific logic implementation.
        
        Must be implemented by subclasses.
        
        Args:
            input_data: Validated input data
            
        Returns:
            Agent-specific result
        """
        pass
    
    def _init_vertex_ai(self) -> bool:
        """
        Initialize GCP Vertex AI with service account.
        
        Environment variables:
            GCP_PROJECT_ID: GCP project ID
            GCP_REGION: GCP region (default: us-central1)
            GCP_SERVICE_ACCOUNT_JSON: Path to service account JSON file
            GOOGLE_APPLICATION_CREDENTIALS: Alternative path to service account JSON
            
        Returns:
            True if successfully initialized
        """
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            region = os.getenv("GCP_REGION", "us-central1")
            
            if not project_id:
                return False
            
            # Load service account credentials
            sa_json_path = os.getenv("GCP_SERVICE_ACCOUNT_JSON") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            
            if sa_json_path and os.path.exists(sa_json_path):
                credentials = service_account.Credentials.from_service_account_file(
                    sa_json_path,
                    scopes=["https://www.googleapis.com/auth/cloud-platform"]
                )
                self.logger.info(f"Loaded service account from {sa_json_path}")
            else:
                # Use default credentials (if running on GCP)
                credentials, _ = default()
                self.logger.info("Using default GCP credentials")
            
            # Initialize Vertex AI Anthropic client
            self.claude_client = AnthropicVertex(
                project_id=project_id,
                region=region,
                credentials=credentials
            )
            
            # Map model names for Vertex AI
            if "claude-sonnet-4" in self.model or "sonnet-4" in self.model:
                self.model = "claude-3-5-sonnet-v2@20241022"
            elif "opus" in self.model:
                self.model = "claude-3-opus@20240229"
            elif "haiku" in self.model:
                self.model = "claude-3-5-haiku@20241022"
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Vertex AI initialization failed: {e}")
            return False
    
    def _validate_input(self, input_data: Dict[str, Any]) -> None:
        """
        Validate input data.
        
        Override in subclasses for specific validation.
        
        Args:
            input_data: Input to validate
            
        Raises:
            ValueError: If validation fails
        """
        if not input_data:
            raise ValueError("Input data is required")
    
    async def call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        Call Claude API with prompt.
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            **kwargs: Additional parameters
            
        Returns:
            Claude's response text
        """
        if not self.has_claude:
            # Use fallback mock response
            self.logger.warning(f"{self.agent_name}: Using mock response (no API key)")
            return self._generate_mock_response(user_prompt)
        
        try:
            response = await self.claude_client.messages.create(
                model=kwargs.get('model', self.model),
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Extract text response
            text_content = response.content[0].text
            
            self.logger.info(
                f"{self.agent_name}: Claude call successful via {self.llm_provider} "
                f"(input_tokens={response.usage.input_tokens}, "
                f"output_tokens={response.usage.output_tokens})"
            )
            
            return text_content
            
        except Exception as e:
            self.logger.error(f"{self.agent_name}: Claude API call failed: {e}")
            raise
    
    async def call_llm(self, user_prompt: str, **kwargs) -> str:
        """
        Call LLM with agent's system prompt.
        
        Convenience method that uses the agent's _get_system_prompt().
        
        Args:
            user_prompt: User message
            **kwargs: Additional parameters
            
        Returns:
            LLM response text
        """
        if hasattr(self, '_get_system_prompt'):
            system_prompt = self._get_system_prompt()
        else:
            system_prompt = "You are a helpful AI assistant."
        
        return await self.call_claude(system_prompt, user_prompt, **kwargs)
    
    def _generate_mock_response(self, prompt: str) -> str:
        """
        Generate mock response when API is unavailable.
        
        Args:
            prompt: User prompt
            
        Returns:
            Mock JSON response
        """
        import json
        
        # Generate appropriate mock based on agent type
        if "identity" in self.agent_name.lower() or "verify" in prompt.lower():
            return json.dumps({
                "verification_status": "VERIFIED",
                "confidence_score": 0.85,
                "identity_confirmed": True,
                "checks_performed": {
                    "ssn_valid": True,
                    "name_consistent": True,
                    "dob_valid": True,
                    "address_verified": True,
                    "age_18_plus": True
                },
                "issues": [],
                "fraud_indicators": [],
                "recommendation": "Identity verified with high confidence (mock response)."
            })
        
        elif "decision" in self.agent_name.lower():
            return json.dumps({
                "decision": "APPROVE",
                "confidence": 85,
                "reasoning": "Strong credit profile, verified identity, no fraud indicators (mock response).",
                "key_factors": ["Good credit score", "Stable employment", "Clean rental history"],
                "risk_mitigation": None,
                "conditions": None,
                "fair_housing_compliant": True
            })
        
        elif "fraud" in self.agent_name.lower():
            return json.dumps({
                "fraud_risk_level": "LOW",
                "fraud_score": 0.15,
                "fraud_indicators": [],
                "synthetic_identity_probability": 0.05,
                "recommendation": "No significant fraud indicators detected (mock response)."
            })
        
        elif "compliance" in self.agent_name.lower():
            return json.dumps({
                "compliance_status": "COMPLIANT",
                "fcra_compliant": True,
                "fair_housing_compliant": True,
                "state_law_compliant": True,
                "violations": [],
                "risk_level": "LOW",
                "required_actions": [],
                "adverse_action_required": False,
                "recommendation": "All compliance checks passed (mock response)."
            })
        
        elif "bias" in self.agent_name.lower():
            return json.dumps({
                "bias_detected": False,
                "fairness_score": 0.95,
                "bias_indicators": [],
                "protected_classes_affected": [],
                "bias_type": "NONE",
                "risk_level": "LOW",
                "mitigation_strategies": [],
                "recommendation": "No bias detected in decision factors (mock response)."
            })
        
        else:
            return json.dumps({
                "status": "success",
                "result": "Mock response - Claude API not configured",
                "confidence": 0.5
            })
    
    async def call_claude_with_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Claude and parse JSON response.
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            **kwargs: Additional parameters
            
        Returns:
            Parsed JSON response
        """
        import json
        
        # Add JSON instruction to system prompt
        system_prompt += "\n\nYou must respond with valid JSON only. No other text."
        
        response_text = await self.call_claude(system_prompt, user_prompt, **kwargs)
        
        # Try to extract JSON from response
        try:
            # Look for JSON in response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                return json.loads(response_text)
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse JSON from Claude response: {e}")
            self.logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Claude response is not valid JSON: {e}")
    
    def _create_success_response(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized success response."""
        return {"status": "success", "data": data}
    
    def _create_error_response(
        self,
        error_message: str,
        error_code: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create standardized error response."""
        return {
            "status": "error",
            "error": error_message,
            "error_code": error_code
        }
