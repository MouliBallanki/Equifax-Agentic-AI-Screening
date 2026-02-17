"""
AI Agents for Tenant Screening.

All agents use Claude Sonnet 4.5 for AI-powered reasoning.
"""

from .base_ai_agent import BaseAIAgent
from .ingestion_ai_agent import get_ingestion_agent
from .identity_ai_agent import get_identity_agent
from .fraud_detection_agent import get_fraud_detection_agent
from .risk_ai_agent import get_risk_agent
from .compliance_ai_agent import get_compliance_agent
from .bias_ai_agent import get_bias_agent
from .decision_ai_agent import get_decision_agent
from .audit_agent import get_audit_agent

__version__ = "1.0.0"

__all__ = [
    "BaseAIAgent",
    "get_ingestion_agent",
    "get_identity_agent",
    "get_fraud_detection_agent",
    "get_risk_agent",
    "get_compliance_agent",
    "get_bias_agent",
    "get_decision_agent",
    "get_audit_agent"
]
