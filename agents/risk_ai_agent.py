"""
Risk AI Agent

Combines Explainable Boosting Machine (EBM) with Claude reasoning 
for transparent, explainable risk scoring.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_ai_agent import BaseAIAgent

# Try importing ML libraries
try:
    from interpret.glassbox import ExplainableBoostingClassifier
    HAS_INTERPRET = True
except ImportError:
    HAS_INTERPRET = False
    logging.warning("InterpretML not available - using fallback scoring")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False


class RiskAIAgent(BaseAIAgent):
    """
    AI-powered risk scoring with explainability.
    
    Architecture:
    1. EBM model generates base risk score + feature importances
    2. Claude analyzes score + context to produce human explanations
    3. Output: risk_score (0-1000) + tier + AI reasoning
    """
    
    def __init__(self):
        super().__init__(
            agent_name="RiskAIAgent",
            model="claude-sonnet-4.5-20250514",
            max_tokens=3000,
            temperature=0.5
        )
        
        # Initialize EBM model (would load trained model in production)
        self.ebm_model = None
        if HAS_INTERPRET:
            self.logger.info("EBM model available")
        else:
            self.logger.warning("EBM not available - using rule-based fallback")
    
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate risk score with AI explanation.
        
        Args:
            input_data: Contains applicant profile, credit data, fraud results
            
        Returns:
            Risk assessment with score, tier, and reasoning
        """
        # Extract data from previous agents
        profile = input_data.get("IngestionAIAgent", {}).get("data", {})
        credit_data = input_data.get("CreditAgent", {}).get("data", {})
        fraud_data = input_data.get("FraudDetectionAgent", {}).get("data", {})
        
        self.logger.info(f"{self.agent_name}: Calculating risk score")
        
        # Step 1: Calculate base risk score using EBM or fallback
        if HAS_INTERPRET and self.ebm_model:
            risk_result = await self._calculate_ebm_risk(profile, credit_data, fraud_data)
        else:
            risk_result = self._calculate_fallback_risk(profile, credit_data, fraud_data)
        
        # Step 2: Use Claude to explain the risk assessment
        explanation = await self._generate_ai_explanation(
            risk_result, profile, credit_data, fraud_data
        )
        
        # Step 3: Combine score + explanation
        final_result = {
            "risk_score": risk_result["risk_score"],
            "risk_tier": risk_result["risk_tier"],
            "risk_factors": risk_result["risk_factors"],
            "ai_explanation": explanation,
            "score_breakdown": risk_result.get("score_breakdown", {})
        }
        
        self.logger.info(
            f"{self.agent_name}: Risk assessment complete "
            f"(score={final_result['risk_score']}, tier={final_result['risk_tier']})"
        )
        
        return final_result
    
    async def _calculate_ebm_risk(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any],
        fraud_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate risk using EBM model."""
        # Extract features for model
        features = self._extract_features(profile, credit_data, fraud_data)
        
        # Run EBM prediction
        # (In production, this would use a trained model)
        # For now, fallback to rule-based
        return self._calculate_fallback_risk(profile, credit_data, fraud_data)
    
    def _calculate_fallback_risk(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any],
        fraud_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Rule-based risk calculation (used when EBM not available)."""
        
        # Extract key metrics
        credit_score = credit_data.get("credit_score", 600)
        annual_income = profile.get("employment", {}).get("annual_income", 0)
        fraud_score = fraud_data.get("fraud_score", 0.0)
        
        # Calculate monthly rent from desired property
        # (In production, would come from application)
        monthly_rent = 1500  # Default for demo
        
        # Calculate income-to-rent ratio
        monthly_income = annual_income / 12 if annual_income > 0 else 0
        income_to_rent_ratio = monthly_income / monthly_rent if monthly_rent > 0 else 0
        
        # Risk factors with weights
        risk_factors = []
        base_score = 500  # Start at medium risk
        
        # Credit score impact (0-400 points)
        if credit_score >= 750:
            credit_impact = 150
            risk_factors.append({
                "factor": "Excellent credit score",
                "impact": "positive",
                "weight": 0.4
            })
        elif credit_score >= 700:
            credit_impact = 100
            risk_factors.append({
                "factor": "Good credit score",
                "impact": "positive",
                "weight": 0.3
            })
        elif credit_score >= 650:
            credit_impact = 50
            risk_factors.append({
                "factor": "Fair credit score",
                "impact": "neutral",
                "weight": 0.2
            })
        elif credit_score >= 600:
            credit_impact = -50
            risk_factors.append({
                "factor": "Below-average credit score",
                "impact": "negative",
                "weight": 0.2
            })
        else:
            credit_impact = -150
            risk_factors.append({
                "factor": "Poor credit score",
                "impact": "negative",
                "weight": 0.4
            })
        
        # Income ratio impact (0-300 points)
        if income_to_rent_ratio >= 3.5:
            income_impact = 150
            risk_factors.append({
                "factor": "Strong income-to-rent ratio",
                "impact": "positive",
                "weight": 0.3
            })
        elif income_to_rent_ratio >= 3.0:
            income_impact = 100
            risk_factors.append({
                "factor": "Adequate income-to-rent ratio",
                "impact": "positive",
                "weight": 0.2
            })
        elif income_to_rent_ratio >= 2.5:
            income_impact = 0
            risk_factors.append({
                "factor": "Minimum income-to-rent ratio",
                "impact": "neutral",
                "weight": 0.1
            })
        else:
            income_impact = -100
            risk_factors.append({
                "factor": "Insufficient income-to-rent ratio",
                "impact": "negative",
                "weight": 0.3
            })
        
        # Fraud score impact (0-200 points)
        if fraud_score > 0.7:
            fraud_impact = -200
            risk_factors.append({
                "factor": "High fraud risk detected",
                "impact": "negative",
                "weight": 0.5
            })
        elif fraud_score > 0.4:
            fraud_impact = -100
            risk_factors.append({
                "factor": "Moderate fraud indicators",
                "impact": "negative",
                "weight": 0.3
            })
        else:
            fraud_impact = 50
            risk_factors.append({
                "factor": "Low fraud risk",
                "impact": "positive",
                "weight": 0.1
            })
        
        # Rental history impact (0-100 points)
        years_at_current = profile.get("rental_history", {}).get("years_at_current", 0)
        if years_at_current >= 2:
            rental_impact = 50
            risk_factors.append({
                "factor": "Stable rental history",
                "impact": "positive",
                "weight": 0.15
            })
        elif years_at_current >= 1:
            rental_impact = 25
            risk_factors.append({
                "factor": "Some rental history",
                "impact": "neutral",
                "weight": 0.1
            })
        else:
            rental_impact = -25
            risk_factors.append({
                "factor": "Limited rental history",
                "impact": "negative",
                "weight": 0.1
            })
        
        # Calculate final score (0-1000)
        raw_score = base_score + credit_impact + income_impact + fraud_impact + rental_impact
        risk_score = max(0, min(1000, raw_score))
        
        # Determine risk tier
        if risk_score >= 700:
            risk_tier = "Low"
        elif risk_score >= 400:
            risk_tier = "Moderate"
        else:
            risk_tier = "High"
        
        return {
            "risk_score": int(risk_score),
            "risk_tier": risk_tier,
            "risk_factors": risk_factors,
            "score_breakdown": {
                "base_score": base_score,
                "credit_impact": credit_impact,
                "income_impact": income_impact,
                "fraud_impact": fraud_impact,
                "rental_impact": rental_impact,
                "raw_score": raw_score,
                "final_score": int(risk_score)
            }
        }
    
    async def _generate_ai_explanation(
        self,
        risk_result: Dict[str, Any],
        profile: Dict[str, Any],
        credit_data: Dict[str, Any],
        fraud_data: Dict[str, Any]
    ) -> str:
        """Use Claude to generate human-readable risk explanation."""
        
        if not self.has_claude:
            return self._generate_fallback_explanation(risk_result)
        
        system_prompt = """
You are an expert risk analyst for tenant screening.

Your task is to explain a risk assessment in clear, professional language.

Guidelines:
- Be concise (2-3 paragraphs maximum)
- Explain the key risk factors
- Use professional but accessible language
- Highlight both strengths and concerns
- Provide context for the risk tier
- Do NOT include the numerical score (already shown separately)
"""
        
        user_prompt = f"""
Explain this tenant risk assessment:

Risk Score: {risk_result['risk_score']} / 1000
Risk Tier: {risk_result['risk_tier']}

Applicant Profile:
{json.dumps(profile, indent=2)}

Credit Data:
Credit Score: {credit_data.get('credit_score', 'N/A')}
Payment History: {credit_data.get('payment_history', 'N/A')}

Fraud Analysis:
Fraud Score: {fraud_data.get('fraud_score', 'N/A')}
Fraud Indicators: {fraud_data.get('fraud_indicators', [])}

Risk Factors:
{json.dumps(risk_result['risk_factors'], indent=2)}

Provide a clear explanation of this risk assessment.
"""
        
        explanation = await self.call_claude(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        return explanation.strip()
    
    def _generate_fallback_explanation(self, risk_result: Dict[str, Any]) -> str:
        """Generate basic explanation without Claude."""
        risk_tier = risk_result['risk_tier']
        risk_score = risk_result['risk_score']
        
        tier_descriptions = {
            "Low": "This applicant presents a low risk profile with strong indicators of financial stability.",
            "Moderate": "This applicant presents a moderate risk profile with mixed financial indicators.",
            "High": "This applicant presents a high risk profile with concerning financial indicators."
        }
        
        explanation = tier_descriptions.get(risk_tier, "Risk assessment complete.")
        
        # Add key factors
        positive_factors = [f for f in risk_result['risk_factors'] if f['impact'] == 'positive']
        negative_factors = [f for f in risk_result['risk_factors'] if f['impact'] == 'negative']
        
        if positive_factors:
            factors_text = ", ".join([f['factor'].lower() for f in positive_factors[:2]])
            explanation += f" Strengths include {factors_text}."
        
        if negative_factors:
            factors_text = ", ".join([f['factor'].lower() for f in negative_factors[:2]])
            explanation += f" Areas of concern include {factors_text}."
        
        return explanation
    
    def _extract_features(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any],
        fraud_data: Dict[str, Any]
    ) -> List[float]:
        """Extract feature vector for ML model."""
        # Features for EBM model (normalized 0-1)
        features = []
        
        # Credit score (normalized 300-850 -> 0-1)
        credit_score = credit_data.get("credit_score", 600)
        features.append((credit_score - 300) / 550)
        
        # Income to rent ratio (normalized 0-5 -> 0-1)
        annual_income = profile.get("employment", {}).get("annual_income", 0)
        monthly_income = annual_income / 12
        monthly_rent = 1500  # Default
        income_ratio = min((monthly_income / monthly_rent) / 5, 1.0) if monthly_rent > 0 else 0
        features.append(income_ratio)
        
        # Fraud score (already 0-1)
        features.append(fraud_data.get("fraud_score", 0.0))
        
        # Years employed (normalized 0-10 -> 0-1)
        years_employed = profile.get("employment", {}).get("years_employed", 0)
        features.append(min(years_employed / 10, 1.0))
        
        # Rental history (normalized 0-5 -> 0-1)
        years_at_current = profile.get("rental_history", {}).get("years_at_current", 0)
        features.append(min(years_at_current / 5, 1.0))
        
        return features


# Export agent
def get_risk_agent() -> RiskAIAgent:
    """Get singleton instance of RiskAIAgent."""
    return RiskAIAgent()
