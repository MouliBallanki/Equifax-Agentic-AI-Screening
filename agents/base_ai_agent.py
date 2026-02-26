"""
Base AI Agent.

Foundation class for all AI-powered agents using Gemini 2.0 Flash.
"""

import os
import logging
import json
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
from datetime import datetime

try:
    import vertexai
    from vertexai.generative_models import GenerativeModel, GenerationConfig
    from google.auth import default
    HAS_VERTEX = True
except ImportError:
    HAS_VERTEX = False
    logging.warning("GCP Vertex AI SDK not available - install: pip install google-cloud-aiplatform")

logger = logging.getLogger(__name__)


class BaseAIAgent(ABC):
    """
    Base class for all AI agents.
    
    Provides common functionality:
    - Gemini 2.0 Flash API integration
    - Logging and error handling
    - Input/output standardization
    - Performance metrics
    """
    
    def __init__(
        self,
        agent_name: str,
        model: str = "gemini-2.5-flash",
        max_tokens: int = 8000,
        temperature: float = 0.7
    ):
        """
        Initialize AI agent.
        
        Args:
            agent_name: Unique agent identifier
            model: Gemini model to use (gemini-2.5-flash, gemini-1.5-flash, gemini-1.5-pro)
            max_tokens: Maximum tokens for response
            temperature: Model temperature (0-2 for Gemini)
        """
        self.agent_name = agent_name
        self.model = model
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.logger = logging.getLogger(f"agents.{agent_name}")
        
        # Initialize Gemini client (Vertex AI)
        self.gemini_model = None
        self.has_llm = False
        self.llm_provider = "none"
        
        # Try GCP Vertex AI with Application Default Credentials (gcloud auth login)
        if HAS_VERTEX and self._init_vertex_ai():
            self.has_llm = True
            self.llm_provider = "vertex-ai-gemini"
            self.logger.info(f"{agent_name}: Using GCP Vertex AI Gemini {self.model}")
        else:
            # Fallback to mock responses
            self.logger.warning(f"{agent_name}: No Vertex AI configured, using mock responses")
            self.logger.info(f"To enable GCP Vertex AI: 1) Run 'gcloud auth login' 2) Set GCP_PROJECT_ID env var")
    
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
                    "model_used": self.model if self.has_llm else "fallback",
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
        Initialize GCP Vertex AI with Gemini using Application Default Credentials.
        
        Environment variables:
            GCP_PROJECT_ID: GCP project ID (REQUIRED)
            GCP_REGION: GCP region (default: us-central1)
            
        Credentials: Uses Application Default Credentials from:
            - gcloud auth login (for local development)
            - Service account in production
            - GOOGLE_APPLICATION_CREDENTIALS env var
            
        Returns:
            True if successfully initialized
        """
        try:
            project_id = os.getenv("GCP_PROJECT_ID")
            region = os.getenv("GCP_REGION", "us-central1")
            
            if not project_id:
                self.logger.warning("GCP_PROJECT_ID not set. Please set it to use Gemini.")
                return False
            
            # Initialize Vertex AI - uses Application Default Credentials automatically
            vertexai.init(project=project_id, location=region)
            self.logger.info(f"Initialized Vertex AI: project={project_id}, region={region}")
            
            # Initialize Gemini model
            self.gemini_model = GenerativeModel(
                model_name=self.model,
                generation_config=GenerationConfig(
                    max_output_tokens=self.max_tokens,
                    temperature=self.temperature,
                )
            )
            
            self.logger.info(f"Initialized Gemini model: {self.model}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Vertex AI initialization failed: {e}")
            self.logger.info("Make sure you've run: gcloud auth login")
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
    
    async def call_gemini(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> str:
        """
        Call Gemini API with prompt.
        
        Args:
            system_prompt: System instructions
            user_prompt: User message
            **kwargs: Additional parameters
            
        Returns:
            Gemini's response text
        """
        if not self.has_llm:
            # Use fallback mock response
            self.logger.warning(f"{self.agent_name}: Using mock response (Vertex AI not configured)")
            return self._generate_mock_response(user_prompt)
        
        try:
            # Combine system and user prompts for Gemini
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Generate response
            response = await self.gemini_model.generate_content_async(
                full_prompt,
                generation_config=GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', self.max_tokens),
                    temperature=kwargs.get('temperature', self.temperature),
                )
            )
            
            # Extract text response
            text_content = response.text
            
            # Log usage (Gemini provides token counts in usage_metadata)
            if hasattr(response, 'usage_metadata'):
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                self.logger.info(
                    f"{self.agent_name}: Gemini call successful via {self.llm_provider} "
                    f"(input_tokens={input_tokens}, output_tokens={output_tokens})"
                )
            else:
                self.logger.info(f"{self.agent_name}: Gemini call successful via {self.llm_provider}")
            
            return text_content
            
        except Exception as e:
            self.logger.error(f"{self.agent_name}: Gemini API call failed: {e}")
            raise
    
    # Alias for backward compatibility
    async def call_claude(self, system_prompt: str, user_prompt: str, **kwargs) -> str:
        """Alias for call_gemini - for backward compatibility."""
        return await self.call_gemini(system_prompt, user_prompt, **kwargs)
    
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
            Mock JSON response with fallback indicator
        """
        import json
        
        # Log warning about fallback
        self.logger.warning(f"{self.agent_name}: ⚠️ Using fallback mock response - AI API unavailable")
        
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
                "recommendation": "Identity verified with high confidence (FALLBACK: mock response used).",
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Result generated without AI - mock/fallback logic used"
            })
        
        elif "decision" in self.agent_name.lower():
            return json.dumps({
                "decision": "APPROVE",
                "confidence": 85,
                "reasoning": "⚠️ FALLBACK DECISION: Strong credit profile, verified identity, no fraud indicators (AI API unavailable - using mock response).",
                "key_factors": ["Good credit score", "Stable employment", "Clean rental history"],
                "risk_mitigation": None,
                "conditions": None,
                "fair_housing_compliant": True,
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Decision made without AI - mock/fallback logic used"
            })
        
        elif "fraud" in self.agent_name.lower():
            return json.dumps({
                "fraud_risk_level": "LOW",
                "fraud_score": 0.15,
                "fraud_indicators": [],
                "synthetic_identity_probability": 0.05,
                "recommendation": "No significant fraud indicators detected (FALLBACK: mock response used).",
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Result generated without AI - mock/fallback logic used"
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
                "recommendation": "All compliance checks passed (FALLBACK: mock response used).",
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Result generated without AI - mock/fallback logic used"
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
                "recommendation": "No bias detected in decision factors (FALLBACK: mock response used).",
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Result generated without AI - mock/fallback logic used"
            })
        
        else:
            return json.dumps({
                "status": "success",
                "result": "Mock response - Gemini API not configured",
                "confidence": 0.5,
                "ai_used": False,
                "fallback_mode": "mock",
                "warning": "Result generated without AI - mock/fallback logic used"
            })
    
    async def call_gemini_with_json_response(
        self,
        system_prompt: str,
        user_prompt: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Call Gemini and parse JSON response.
        
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
        
        response_text = await self.call_gemini(system_prompt, user_prompt, **kwargs)
        
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
            self.logger.error(f"Failed to parse JSON from Gemini response: {e}")
            self.logger.debug(f"Response text: {response_text}")
            raise ValueError(f"Gemini response is not valid JSON: {e}")
    
    # Alias for backward compatibility
    async def call_claude_with_json_response(self, system_prompt: str, user_prompt: str, **kwargs) -> Dict[str, Any]:
        """Alias for call_gemini_with_json_response - for backward compatibility."""
        return await self.call_gemini_with_json_response(system_prompt, user_prompt, **kwargs)
    
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
