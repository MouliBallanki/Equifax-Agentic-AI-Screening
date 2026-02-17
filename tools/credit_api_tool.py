"""
Credit API Tool.

Mock Equifax credit API client for tenant screening.
"""

import logging
import random
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CreditAPITool:
    """
    Mock Equifax credit API client.
    
    In production, this would call real Equifax API endpoints.
    For now, generates realistic mock credit data.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize credit API tool.
        
        Args:
            api_key: Equifax API key (mock for now)
        """
        self.api_key = api_key
        self.call_count = 0
    
    async def get_credit_report(
        self,
        ssn: str,
        first_name: str,
        last_name: str,
        dob: str
    ) -> Dict[str, Any]:
        """
        Retrieve credit report for applicant.
        
        Args:
            ssn: Social Security Number
            first_name: First name
            last_name: Last name
            dob: Date of birth (YYYY-MM-DD)
        
        Returns:
            Credit report data
        """
        self.call_count += 1
        
        logger.info(f"Fetching credit report for {first_name} {last_name}")
        
        # Generate realistic mock credit data
        credit_score = self._generate_credit_score(ssn)
        
        report = {
            "report_id": f"CR{random.randint(100000, 999999)}",
            "requested_at": datetime.utcnow().isoformat(),
            "applicant": {
                "ssn": ssn,
                "name": f"{first_name} {last_name}",
                "dob": dob
            },
            "credit_score": {
                "fico_score": credit_score,
                "vantage_score": credit_score + random.randint(-20, 20),
                "score_date": datetime.utcnow().date().isoformat()
            },
            "credit_accounts": self._generate_accounts(credit_score),
            "payment_history": self._generate_payment_history(credit_score),
            "public_records": self._generate_public_records(credit_score),
            "inquiries": self._generate_inquiries(),
            "summary": {
                "total_accounts": random.randint(5, 15),
                "open_accounts": random.randint(3, 10),
                "total_balance": random.randint(5000, 50000),
                "available_credit": random.randint(10000, 100000),
                "credit_utilization": random.uniform(0.1, 0.6),
                "oldest_account_age_months": random.randint(24, 240),
                "delinquent_accounts": 0 if credit_score > 650 else random.randint(0, 3)
            }
        }
        
        logger.info(f"Credit report retrieved: FICO {credit_score}")
        return report
    
    def _generate_credit_score(self, ssn: str) -> int:
        """Generate realistic credit score based on SSN hash."""
        # Use SSN to seed for consistency
        hash_val = sum(ord(c) for c in ssn)
        random.seed(hash_val)
        
        # Generate score in realistic ranges
        score_range = random.choice([
            (580, 669),   # Fair
            (670, 739),   # Good
            (740, 799),   # Very Good
            (800, 850)    # Excellent
        ])
        
        score = random.randint(*score_range)
        random.seed()  # Reset seed
        return score
    
    def _generate_accounts(self, credit_score: int) -> list:
        """Generate realistic credit accounts."""
        num_accounts = 3 if credit_score < 600 else 5 if credit_score < 700 else 8
        
        accounts = []
        account_types = ["Credit Card", "Auto Loan", "Mortgage", "Student Loan", "Personal Loan"]
        
        for i in range(num_accounts):
            account = {
                "account_id": f"ACC{random.randint(10000, 99999)}",
                "account_type": random.choice(account_types),
                "creditor": f"{random.choice(['Bank of', 'Capital', 'Chase', 'Discover'])} {random.choice(['America', 'One', 'Financial', 'Bank'])}",
                "opened_date": (datetime.now() - timedelta(days=random.randint(365, 3650))).date().isoformat(),
                "balance": random.randint(100, 25000),
                "credit_limit": random.randint(1000, 50000) if "Card" in account_types[0] else None,
                "status": "Current" if credit_score > 650 else random.choice(["Current", "30 Days Late"]),
                "payment_status": "OK" if credit_score > 650 else random.choice(["OK", "Late"])
            }
            accounts.append(account)
        
        return accounts
    
    def _generate_payment_history(self, credit_score: int) -> Dict[str, Any]:
        """Generate payment history."""
        total_payments = 24
        on_time = total_payments if credit_score > 700 else random.randint(18, 23)
        
        return {
            "total_payments": total_payments,
            "on_time_payments": on_time,
            "late_30_days": total_payments - on_time if credit_score < 650 else 0,
            "late_60_days": 0 if credit_score > 600 else random.randint(0, 2),
            "late_90_days": 0 if credit_score > 550 else random.randint(0, 1),
            "payment_performance": f"{(on_time / total_payments) * 100:.1f}%"
        }
    
    def _generate_public_records(self, credit_score: int) -> list:
        """Generate public records (bankruptcies, liens, etc.)."""
        if credit_score > 650:
            return []
        
        # Low scores might have public records
        if random.random() < 0.3:
            return [{
                "type": random.choice(["Bankruptcy Chapter 7", "Tax Lien", "Judgment"]),
                "filed_date": (datetime.now() - timedelta(days=random.randint(730, 2190))).date().isoformat(),
                "status": "Satisfied" if random.random() > 0.5 else "Unsatisfied"
            }]
        
        return []
    
    def _generate_inquiries(self) -> list:
        """Generate credit inquiries."""
        num_inquiries = random.randint(0, 5)
        
        inquiries = []
        for _ in range(num_inquiries):
            inquiries.append({
                "inquiry_date": (datetime.now() - timedelta(days=random.randint(1, 365))).date().isoformat(),
                "creditor": random.choice(["Auto Loan", "Credit Card", "Mortgage", "Personal Loan"]),
                "inquiry_type": "Hard"
            })
        
        return inquiries
    
    async def verify_employment(
        self,
        employer_name: str,
        employer_phone: str
    ) -> Dict[str, Any]:
        """
        Verify employment (mock).
        
        Args:
            employer_name: Employer name
            employer_phone: Employer contact
        
        Returns:
            Employment verification result
        """
        logger.info(f"Verifying employment: {employer_name}")
        
        # Mock verification
        return {
            "verified": True,
            "employer_name": employer_name,
            "verification_method": "Phone",
            "verification_date": datetime.utcnow().date().isoformat(),
            "notes": "Employment verified via HR department"
        }
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return {
            "total_calls": self.call_count,
            "estimated_cost_usd": self.call_count * 2.50  # Mock $2.50 per credit pull
        }
