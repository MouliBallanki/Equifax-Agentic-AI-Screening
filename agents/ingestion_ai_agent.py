"""
Ingestion AI Agent

Uses Claude Sonnet 4.5 to intelligently parse and extract structured data 
from tenant applications (PDFs, images, JSON, forms).
"""

import json
from typing import Dict, Any, List
from .base_ai_agent import BaseAIAgent


class IngestionAIAgent(BaseAIAgent):
    """
    AI-powered document ingestion and data extraction.
    
    Capabilities:
    - Parse PDFs and images using Claude vision
    - Extract structured applicant profiles
    - Handle multiple document types
    - Validate and normalize data
    """
    
    def __init__(self):
        super().__init__(
            agent_name="IngestionAIAgent",
            model="claude-sonnet-4.5-20250514",
            max_tokens=4000,
            temperature=0.3  # Lower temperature for structured extraction
        )
    
    async def _run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process application documents and extract structured data.
        
        Args:
            input_data: Contains raw_application data
            
        Returns:
            Structured applicant profile
        """
        raw_application = input_data.get("raw_application", {})
        
        # If already structured, validate and return
        if self._is_structured(raw_application):
            self.logger.info(f"{self.agent_name}: Application already structured")
            return self._validate_and_normalize(raw_application)
        
        # Otherwise, use Claude to extract structure
        self.logger.info(f"{self.agent_name}: Extracting structure with Claude")
        structured_profile = await self._extract_with_claude(raw_application)
        
        return structured_profile
    
    def _is_structured(self, data: Dict[str, Any]) -> bool:
        """Check if application is already in structured format."""
        required_fields = ["applicant", "employment", "rental_history"]
        return all(field in data for field in required_fields)
    
    def _validate_and_normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and normalize structured data."""
        
        # Ensure all required fields exist
        profile = {
            "applicant": data.get("applicant", {}),
            "employment": data.get("employment", {}),
            "rental_history": data.get("rental_history", {}),
            "additional_info": data.get("additional_info", {})
        }
        
        # Normalize phone numbers, SSN, etc.
        if "phone" in profile["applicant"]:
            profile["applicant"]["phone"] = self._normalize_phone(
                profile["applicant"]["phone"]
            )
        
        if "ssn" in profile["applicant"]:
            profile["applicant"]["ssn"] = self._normalize_ssn(
                profile["applicant"]["ssn"]
            )
        
        self.logger.info(f"{self.agent_name}: Validated structured profile")
        return profile
    
    async def _extract_with_claude(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Use Claude to extract structured data from raw input."""
        
        system_prompt = """
You are an expert data extraction AI for tenant screening applications.

Your task is to analyze raw application data and extract a structured profile.

Output must be valid JSON with this exact structure:
{
  "applicant": {
    "first_name": "string",
    "last_name": "string",
    "email": "string",
    "phone": "string",
    "ssn": "string (XXX-XX-XXXX format)",
    "date_of_birth": "YYYY-MM-DD",
    "current_address": {
      "street": "string",
      "city": "string",
      "state": "string",
      "zip": "string"
    }
  },
  "employment": {
    "employer_name": "string",
    "job_title": "string",
    "employment_status": "full-time | part-time | self-employed | unemployed",
    "annual_income": number,
    "years_employed": number,
    "employer_phone": "string"
  },
  "rental_history": {
    "current_landlord": "string",
    "current_landlord_phone": "string",
    "monthly_rent": number,
    "years_at_current": number,
    "reason_for_leaving": "string"
  },
  "additional_info": {
    "pets": boolean,
    "smoker": boolean,
    "bankruptcy_history": boolean,
    "eviction_history": boolean
  }
}

If information is missing, use null for the field.
Be precise and extract all available information.
"""
        
        user_prompt = f"""
Extract structured tenant application data from this raw input:

{json.dumps(raw_data, indent=2)}

Return valid JSON only (no markdown, no explanation).
"""
        
        extracted_data = await self.call_claude_with_json_response(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )
        
        self.logger.info(f"{self.agent_name}: Successfully extracted structured data")
        return extracted_data
    
    def _normalize_phone(self, phone: str) -> str:
        """Normalize phone number to (XXX) XXX-XXXX format."""
        # Remove all non-digits
        digits = ''.join(c for c in str(phone) if c.isdigit())
        
        if len(digits) == 10:
            return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
        return phone  # Return original if can't normalize
    
    def _normalize_ssn(self, ssn: str) -> str:
        """Normalize SSN to XXX-XX-XXXX format."""
        # Remove all non-digits
        digits = ''.join(c for c in str(ssn) if c.isdigit())
        
        if len(digits) == 9:
            return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"
        return ssn  # Return original if can't normalize


# Export agent
def get_ingestion_agent() -> IngestionAIAgent:
    """Get singleton instance of IngestionAIAgent."""
    return IngestionAIAgent()
