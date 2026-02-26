"""
Credit Agent

Mocked Equifax credit bureau integration.
Returns realistic credit report data for tenant screening.
"""

import random
from typing import Dict, Any
from datetime import datetime, timedelta
from .base_ai_agent import BaseAIAgent


class CreditAgent(BaseAIAgent):
    """
    Mock credit bureau (Equifax) integration.
    
    In production, this would connect to real Equifax API.
    For demo, generates realistic mock credit reports.
    """
    
    def __init__(self):
        super().__init__(
            agent_name="CreditAgent",
            model="gemini-2.5-flash",  # Not used for mock
            max_tokens=1000,
            temperature=0.0
        )
    
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Retrieve credit report for applicant.
        
        Args:
            input_data: Contains applicant profile with SSN
            
        Returns:
            Mock credit report with score, history, accounts
        """
        # Extract applicant info
        profile = input_data.get("IngestionAIAgent", {}).get("data", {})
        applicant = profile.get("applicant", {})
        
        ssn = applicant.get("ssn")
        if not ssn:
            raise ValueError("SSN required for credit check")
        
        self.logger.info(f"{self.agent_name}: Fetching credit report (MOCK)")
        
        # Generate mock credit report
        credit_report = self._generate_mock_credit_report(applicant)
        
        self.logger.info(
            f"{self.agent_name}: Credit report retrieved "
            f"(score={credit_report['credit_score']})"
        )
        
        return credit_report
    
    def _generate_mock_credit_report(self, applicant: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic mock credit report."""
        
        # Use SSN to seed random (consistent results for same applicant)
        ssn = applicant.get("ssn", "000-00-0000")
        seed_value = sum(ord(c) for c in ssn if c.isdigit())
        random.seed(seed_value)
        
        # Generate credit score (300-850 range, skew toward 600-750)
        score_distribution = [
            (300, 550, 0.05),  # Poor (5%)
            (550, 650, 0.25),  # Fair (25%)
            (650, 750, 0.50),  # Good (50%)
            (750, 850, 0.20),  # Excellent (20%)
        ]
        
        rand_val = random.random()
        cumulative = 0.0
        credit_score = 680  # Default
        
        for min_score, max_score, probability in score_distribution:
            cumulative += probability
            if rand_val <= cumulative:
                credit_score = random.randint(min_score, max_score)
                break
        
        # Payment history (% on-time)
        if credit_score >= 750:
            on_time_pct = random.randint(95, 100)
        elif credit_score >= 700:
            on_time_pct = random.randint(85, 95)
        elif credit_score >= 650:
            on_time_pct = random.randint(75, 85)
        elif credit_score >= 600:
            on_time_pct = random.randint(65, 75)
        else:
            on_time_pct = random.randint(40, 65)
        
        # Credit utilization (%)
        if credit_score >= 750:
            utilization = random.randint(5, 25)
        elif credit_score >= 700:
            utilization = random.randint(20, 40)
        elif credit_score >= 650:
            utilization = random.randint(35, 60)
        else:
            utilization = random.randint(60, 95)
        
        # Total accounts
        num_accounts = random.randint(3, 12)
        
        # Credit history length (years)
        if credit_score >= 750:
            history_years = random.randint(7, 20)
        elif credit_score >= 700:
            history_years = random.randint(5, 10)
        elif credit_score >= 650:
            history_years = random.randint(3, 7)
        else:
            history_years = random.randint(1, 5)
        
        # Derogatory marks
        if credit_score >= 700:
            derogatory_marks = 0
        elif credit_score >= 650:
            derogatory_marks = random.randint(0, 1)
        elif credit_score >= 600:
            derogatory_marks = random.randint(1, 2)
        else:
            derogatory_marks = random.randint(2, 5)
        
        # Hard inquiries (last 2 years)
        hard_inquiries = random.randint(0, 5)
        
        # Generate account details
        accounts = self._generate_mock_accounts(num_accounts, credit_score)
        
        # Compile report
        report = {
            "credit_score": credit_score,
            "score_factors": {
                "payment_history": on_time_pct,
                "credit_utilization": utilization,
                "length_of_history_years": history_years,
                "total_accounts": num_accounts,
                "hard_inquiries": hard_inquiries,
                "derogatory_marks": derogatory_marks
            },
            "accounts": accounts,
            "payment_history": f"{on_time_pct}% on-time payments",
            "total_debt": sum(acc.get("balance", 0) for acc in accounts),
            "available_credit": sum(
                acc.get("credit_limit", 0) - acc.get("balance", 0) 
                for acc in accounts if acc["type"] == "revolving"
            ),
            "oldest_account_date": (
                datetime.utcnow() - timedelta(days=history_years * 365)
            ).strftime("%Y-%m-%d"),
            "public_records": {
                "bankruptcies": 1 if derogatory_marks >= 3 and random.random() < 0.3 else 0,
                "liens": 1 if derogatory_marks >= 2 and random.random() < 0.2 else 0,
                "judgments": 1 if derogatory_marks >= 2 and random.random() < 0.2 else 0
            },
            "report_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "bureau": "Equifax (MOCK)"
        }
        
        # Reset random seed
        random.seed()
        
        return report
    
    def _generate_mock_accounts(self, num_accounts: int, credit_score: int) -> list:
        """Generate mock credit accounts."""
        accounts = []
        
        account_types = [
            ("revolving", "Credit Card", 0.6),
            ("installment", "Auto Loan", 0.2),
            ("mortgage", "Mortgage", 0.1),
            ("installment", "Personal Loan", 0.1)
        ]
        
        for i in range(num_accounts):
            # Choose account type
            rand_val = random.random()
            cumulative = 0.0
            acc_type = "revolving"
            acc_name = "Credit Card"
            
            for atype, aname, prob in account_types:
                cumulative += prob
                if rand_val <= cumulative:
                    acc_type = atype
                    acc_name = aname
                    break
            
            # Account details
            if acc_type == "revolving":
                credit_limit = random.choice([1000, 2500, 5000, 10000, 15000])
                if credit_score >= 700:
                    balance = int(credit_limit * random.uniform(0.1, 0.3))
                else:
                    balance = int(credit_limit * random.uniform(0.4, 0.9))
                payment_status = "Current" if random.random() < (credit_score / 850) else "Past Due"
            
            elif acc_type == "mortgage":
                credit_limit = 0
                balance = random.randint(150000, 400000)
                payment_status = "Current" if random.random() < (credit_score / 850) else "Past Due"
            
            else:  # installment
                credit_limit = 0
                balance = random.randint(5000, 30000)
                payment_status = "Current" if random.random() < (credit_score / 850) else "Past Due"
            
            # Account age
            months_open = random.randint(6, 120)
            
            account = {
                "type": acc_type,
                "name": acc_name,
                "balance": balance,
                "credit_limit": credit_limit if acc_type == "revolving" else 0,
                "payment_status": payment_status,
                "months_open": months_open,
                "late_payments_24mo": random.randint(0, 3) if payment_status == "Past Due" else 0
            }
            
            accounts.append(account)
        
        return accounts


# Export agent
def get_credit_agent() -> CreditAgent:
    """Get singleton instance of CreditAgent."""
    return CreditAgent()
