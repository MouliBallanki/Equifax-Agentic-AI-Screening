"""
Fraud Detection Agent

Pattern-based fraud detection using rule-based heuristics.
In production, would use XGBoost + SHAP for ML-based detection.
"""

from typing import Dict, Any, List
from .base_ai_agent import BaseAIAgent


class FraudDetectionAgent(BaseAIAgent):
    """
    Fraud detection using pattern analysis.
    
    Detects:
    - Identity inconsistencies
    - Suspicious employment patterns
    - Fabricated rental history
    - Document anomalies
    """
    
    def __init__(self):
        super().__init__(
            agent_name="FraudDetectionAgent",
            model="gemini-2.5-flash",
            max_tokens=2000,
            temperature=0.3
        )
        
        # Fraud detection rules (in production, would be ML model)
        self.fraud_rules = [
            self._check_income_inconsistency,
            self._check_employment_red_flags,
            self._check_identity_mismatch,
            self._check_rental_history_anomalies,
            self._check_credit_report_flags
        ]
    
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze application for fraud indicators.
        
        Args:
            input_data: Contains profile and credit data
            
        Returns:
            Fraud assessment with score and indicators
        """
        # Extract data from previous agents
        profile = input_data.get("IngestionAIAgent", {}).get("data", {})
        credit_data = input_data.get("CreditAgent", {}).get("data", {})
        
        self.logger.info(f"{self.agent_name}: Running fraud detection")
        
        # Run all fraud detection rules
        fraud_indicators = []
        fraud_score = 0.0
        
        for rule_func in self.fraud_rules:
            indicator = rule_func(profile, credit_data)
            if indicator:
                fraud_indicators.append(indicator)
                fraud_score += indicator["severity"]
        
        # Normalize fraud score to 0-1 range
        max_possible_score = len(self.fraud_rules) * 1.0  # Max severity per rule is 1.0
        fraud_score = min(fraud_score / max_possible_score, 1.0)
        
        # Determine fraud risk level
        if fraud_score >= 0.7:
            risk_level = "High"
        elif fraud_score >= 0.4:
            risk_level = "Moderate"
        else:
            risk_level = "Low"
        
        result = {
            "fraud_score": round(fraud_score, 3),
            "risk_level": risk_level,
            "fraud_indicators": fraud_indicators,
            "total_indicators": len(fraud_indicators),
            "requires_manual_review": fraud_score >= 0.6
        }
        
        self.logger.info(
            f"{self.agent_name}: Fraud check complete "
            f"(score={result['fraud_score']}, indicators={len(fraud_indicators)})"
        )
        
        return result
    
    def _check_income_inconsistency(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for income vs debt inconsistencies."""
        employment = profile.get("employment", {})
        annual_income = employment.get("annual_income", 0)
        total_debt = credit_data.get("total_debt", 0)
        
        # Check if income seems too high for job title
        job_title = employment.get("job_title", "").lower()
        
        # Simplified income expectations by job category
        income_expectations = {
            "manager": (50000, 150000),
            "engineer": (60000, 200000),
            "director": (80000, 250000),
            "analyst": (45000, 100000),
            "assistant": (30000, 60000),
            "consultant": (60000, 180000),
            "developer": (60000, 180000),
            "specialist": (45000, 90000)
        }
        
        # Check job title against income
        for job_keyword, (min_income, max_income) in income_expectations.items():
            if job_keyword in job_title:
                if annual_income < min_income * 0.5 or annual_income > max_income * 1.5:
                    return {
                        "type": "income_inconsistency",
                        "description": f"Income ${annual_income:,} unusual for position '{job_title}'",
                        "severity": 0.6,
                        "recommendation": "Verify employment and income documentation"
                    }
        
        # Check debt-to-income ratio
        if annual_income > 0:
            dti_ratio = total_debt / annual_income
            if dti_ratio > 0.5:  # DTI > 50%
                return {
                    "type": "high_debt_to_income",
                    "description": f"Debt-to-income ratio {dti_ratio:.1%} exceeds safe threshold",
                    "severity": 0.5,
                    "recommendation": "Review applicant's ability to take on additional rent expenses"
                }
        
        return None
    
    def _check_employment_red_flags(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for suspicious employment patterns."""
        employment = profile.get("employment", {})
        
        years_employed = employment.get("years_employed", 0)
        employment_status = employment.get("employment_status", "")
        annual_income = employment.get("annual_income", 0)
        
        # Very short employment with high income
        if years_employed < 0.5 and annual_income > 80000:
            return {
                "type": "new_employment_high_income",
                "description": f"Less than 6 months employment with ${annual_income:,} income",
                "severity": 0.4,
                "recommendation": "Verify employment start date and income documentation"
            }
        
        # Self-employed with very high income but poor credit
        credit_score = credit_data.get("credit_score", 700)
        if employment_status == "self-employed" and annual_income > 100000 and credit_score < 600:
            return {
                "type": "self_employed_inconsistency",
                "description": "High self-employed income inconsistent with credit profile",
                "severity": 0.7,
                "recommendation": "Request tax returns and business documentation"
            }
        
        # Unemployed with no apparent income source
        if employment_status == "unemployed" and annual_income > 0:
            return {
                "type": "unemployed_with_income",
                "description": "Reported income despite unemployment status",
                "severity": 0.5,
                "recommendation": "Clarify income source"
            }
        
        return None
    
    def _check_identity_mismatch(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for identity verification issues."""
        applicant = profile.get("applicant", {})
        
        # Very thin credit file (could indicate synthetic identity)
        total_accounts = credit_data.get("score_factors", {}).get("total_accounts", 0)
        history_years = credit_data.get("score_factors", {}).get("length_of_history_years", 0)
        
        if total_accounts < 2 and history_years < 2:
            return {
                "type": "thin_credit_file",
                "description": "Very limited credit history (possible synthetic identity)",
                "severity": 0.6,
                "recommendation": "Request additional identity verification documents"
            }
        
        # All accounts opened recently (identity theft indicator)
        accounts = credit_data.get("accounts", [])
        if accounts:
            recent_accounts = sum(1 for acc in accounts if acc.get("months_open", 999) < 12)
            if recent_accounts == len(accounts) and len(accounts) >= 3:
                return {
                    "type": "all_recent_accounts",
                    "description": "All credit accounts opened within last year",
                    "severity": 0.7,
                    "recommendation": "Verify identity and investigate account opening patterns"
                }
        
        return None
    
    def _check_rental_history_anomalies(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for suspicious rental history."""
        rental_history = profile.get("rental_history", {})
        
        years_at_current = rental_history.get("years_at_current", 0)
        monthly_rent = rental_history.get("monthly_rent", 0)
        annual_income = profile.get("employment", {}).get("annual_income", 0)
        
        # Rent too high for income
        if annual_income > 0 and monthly_rent > 0:
            monthly_income = annual_income / 12
            rent_to_income = monthly_rent / monthly_income
            
            if rent_to_income > 0.5:  # Rent > 50% of income
                return {
                    "type": "rent_to_income_excessive",
                    "description": f"Current rent ({rent_to_income:.1%} of income) seems unsustainable",
                    "severity": 0.4,
                    "recommendation": "Verify rental payment history and income sources"
                }
        
        # Very short rental history
        if years_at_current < 0.25:  # Less than 3 months
            return {
                "type": "minimal_rental_history",
                "description": "Less than 3 months at current residence",
                "severity": 0.3,
                "recommendation": "Request previous rental references"
            }
        
        return None
    
    def _check_credit_report_flags(
        self,
        profile: Dict[str, Any],
        credit_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check for red flags in credit report."""
        public_records = credit_data.get("public_records", {})
        
        # Recent bankruptcy
        if public_records.get("bankruptcies", 0) > 0:
            return {
                "type": "recent_bankruptcy",
                "description": "Bankruptcy record found",
                "severity": 0.8,
                "recommendation": "Review bankruptcy details and discharge date"
            }
        
        # Liens or judgments
        if public_records.get("liens", 0) > 0 or public_records.get("judgments", 0) > 0:
            return {
                "type": "public_records",
                "description": "Tax liens or judgments on record",
                "severity": 0.6,
                "recommendation": "Investigate public record details"
            }
        
        # High number of hard inquiries (credit seeking behavior)
        hard_inquiries = credit_data.get("score_factors", {}).get("hard_inquiries", 0)
        if hard_inquiries >= 6:
            return {
                "type": "excessive_credit_inquiries",
                "description": f"{hard_inquiries} hard inquiries in last 24 months",
                "severity": 0.4,
                "recommendation": "Applicant may be experiencing financial stress"
            }
        
        return None


# Export agent
def get_fraud_detection_agent() -> FraudDetectionAgent:
    """Get singleton instance of FraudDetectionAgent."""
    return FraudDetectionAgent()
