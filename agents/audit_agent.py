"""
Audit Agent.

Non-AI agent for logging, governance, and audit trail generation.
"""

import logging
import json
from typing import Dict, Any, List
from datetime import datetime
from .base_ai_agent import BaseAIAgent

logger = logging.getLogger(__name__)


class AuditAgent(BaseAIAgent):
    """
    Audit and logging agent.
    
    NOT dependent on AI - handles logging, audit trails, and governance.
    Records all agent decisions for compliance and explainability.
    """
    
    def __init__(self):
        """Initialize AuditAgent."""
        super().__init__(
            agent_name="AuditAgent",
            model="none",  # Not using AI
            max_tokens=0,
            temperature=0
        )
        self.audit_log: List[Dict[str, Any]] = []
    
    async def _run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate audit trail for screening.
        
        Args:
            context: Full screening context with all agent results
        
        Returns:
            Audit trail summary
        """
        try:
            application_id = context.get("application_id", "unknown")
            
            # Build comprehensive audit trail
            audit_entry = {
                "application_id": application_id,
                "audit_timestamp": datetime.utcnow().isoformat(),
                "screening_summary": self._build_summary(context),
                "agent_executions": self._extract_agent_logs(context),
                "compliance_check": self._extract_compliance(context),
                "bias_check": self._extract_bias(context),
                "final_decision": self._extract_decision(context),
                "data_sources": self._list_data_sources(context),
                "explainability": self._build_explainability(context)
            }
            
            # Store audit log
            self.audit_log.append(audit_entry)
            
            logger.info(f"Audit trail generated for {application_id}")
            
            return {
                "audit_id": f"AUDIT-{len(self.audit_log)}",
                "audit_complete": True,
                "records_created": len(audit_entry["agent_executions"]),
                "compliance_verified": audit_entry["compliance_check"]["compliant"],
                "bias_checked": audit_entry["bias_check"]["checked"],
                "audit_summary": audit_entry
            }
            
        except Exception as e:
            logger.error(f"Audit agent error: {str(e)}", exc_info=True)
            raise
    
    def _build_summary(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build screening summary."""
        return {
            "application_id": context.get("application_id"),
            "applicant_name": self._get_applicant_name(context),
            "screening_date": datetime.utcnow().date().isoformat(),
            "total_agents_executed": self._count_agents(context),
            "screening_duration_ms": context.get("total_execution_time_ms", 0)
        }
    
    def _extract_agent_logs(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract execution logs from all agents."""
        agents = [
            "ingestion_result",
            "identity_result",
            "fraud_result",
            "risk_result",
            "compliance_result",
            "bias_result",
            "decision_result"
        ]
        
        logs = []
        for agent_key in agents:
            result = context.get(agent_key)
            if result:
                logs.append({
                    "agent_name": result.get("agent", agent_key),
                    "status": result.get("status", "unknown"),
                    "execution_time_ms": result.get("execution_time_ms", 0),
                    "timestamp": datetime.utcnow().isoformat(),
                    "result_summary": self._summarize_result(result)
                })
        
        return logs
    
    def _extract_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract compliance check results."""
        compliance = context.get("compliance_result", {})
        compliance_data = compliance.get("data", {})
        
        return {
            "checked": compliance.get("status") == "success",
            "compliant": compliance_data.get("compliance_status") == "COMPLIANT",
            "fcra_compliant": compliance_data.get("fcra_compliant", False),
            "fair_housing_compliant": compliance_data.get("fair_housing_compliant", False),
            "violations": compliance_data.get("violations", [])
        }
    
    def _extract_bias(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract bias check results."""
        bias = context.get("bias_result", {})
        bias_data = bias.get("data", {})
        
        return {
            "checked": bias.get("status") == "success",
            "bias_detected": bias_data.get("bias_detected", False),
            "fairness_score": bias_data.get("fairness_score", 1.0),
            "bias_indicators": bias_data.get("bias_indicators", []),
            "risk_level": bias_data.get("risk_level", "UNKNOWN")
        }
    
    def _extract_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract final decision."""
        decision = context.get("decision_result", {})
        decision_data = decision.get("data", {})
        
        return {
            "decision": decision_data.get("decision", "UNKNOWN"),
            "confidence": decision_data.get("confidence", 0),
            "key_factors": decision_data.get("key_factors", []),
            "reasoning": decision_data.get("reasoning", ""),
            "conditions": decision_data.get("conditions")
        }
    
    def _list_data_sources(self, context: Dict[str, Any]) -> List[str]:
        """List all data sources used."""
        sources = [
            "Applicant-provided information",
            "Credit bureau data (mock)",
            "Identity verification service",
            "Fraud detection models",
            "Risk scoring model (EBM)"
        ]
        return sources
    
    def _build_explainability(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Build explainability summary for transparency."""
        decision = context.get("decision_result", {})
        decision_data = decision.get("data", {})
        
        risk = context.get("risk_result", {})
        risk_data = risk.get("data", {})
        
        return {
            "decision_factors": decision_data.get("key_factors", []),
            "risk_drivers": risk_data.get("key_risk_drivers", []),
            "credit_score": risk_data.get("credit_score", 0),
            "risk_score": risk_data.get("risk_score", 0),
            "ai_models_used": [
                "Claude Sonnet 4.5 (Decision, Identity, Fraud, Compliance, Bias)",
                "EBM (Risk Scoring)",
                "XGBoost (Fraud Detection)"
            ],
            "decision_rationale": decision_data.get("reasoning", ""),
            "adverse_action_required": decision_data.get("decision") in ["DENY", "CONDITIONAL_APPROVE"]
        }
    
    def _get_applicant_name(self, context: Dict[str, Any]) -> str:
        """Get applicant name."""
        applicant = context.get("applicant", {})
        first = applicant.get("first_name", "")
        last = applicant.get("last_name", "")
        return f"{first} {last}".strip() or "Unknown"
    
    def _count_agents(self, context: Dict[str, Any]) -> int:
        """Count executed agents."""
        agent_keys = [
            "ingestion_result", "identity_result", "fraud_result",
            "risk_result", "compliance_result", "bias_result", "decision_result"
        ]
        return sum(1 for key in agent_keys if context.get(key, {}).get("status") == "success")
    
    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create brief summary of agent result."""
        if result.get("status") == "error":
            return f"Error: {result.get('error', 'Unknown error')}"
        
        data = result.get("data", {})
        agent = result.get("agent", "Unknown")
        
        # Agent-specific summaries
        if "Identity" in agent:
            return f"Status: {data.get('verification_status', 'UNKNOWN')}"
        elif "Risk" in agent:
            return f"Score: {data.get('risk_score', 0)}/1000, Tier: {data.get('risk_tier', 'UNKNOWN')}"
        elif "Decision" in agent:
            return f"Decision: {data.get('decision', 'UNKNOWN')}, Confidence: {data.get('confidence', 0)}%"
        elif "Fraud" in agent:
            return f"Risk: {data.get('fraud_risk_level', 'UNKNOWN')}"
        elif "Compliance" in agent:
            return f"Status: {data.get('compliance_status', 'UNKNOWN')}"
        elif "Bias" in agent:
            return f"Bias: {'Detected' if data.get('bias_detected') else 'Not Detected'}"
        
        return "Completed successfully"
    
    def get_audit_logs(self, application_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs.
        
        Args:
            application_id: Filter by application ID (optional)
        
        Returns:
            List of audit log entries
        """
        if application_id:
            return [
                log for log in self.audit_log
                if log.get("application_id") == application_id
            ]
        return self.audit_log


def get_audit_agent() -> AuditAgent:
    """
    Factory function to get AuditAgent instance.
    
    Returns:
        Initialized AuditAgent
    """
    return AuditAgent()
