"""
Status Mapper - Standardized status value conversion.

Converts AI agent decision values to database status values.

AI Agent Decisions (from DecisionAI):
- APPROVE
- CONDITIONAL_APPROVE
- DENY

Database Status Values:
- APPROVED
- REJECTED
- PENDING
"""

def decision_to_status(decision: str) -> str:
    """
    Convert AI agent decision to database status.
    
    Args:
        decision: AI agent decision (APPROVE, CONDITIONAL_APPROVE, DENY, etc.)
        
    Returns:
        Database status value (APPROVED, REJECTED, PENDING)
    """
    if not decision:
        return 'PENDING'
    
    decision_upper = str(decision).upper().strip()
    
    # Map AI decisions to database status
    if 'APPROVE' in decision_upper and 'DENY' not in decision_upper:
        return 'APPROVED'  # Both APPROVE and CONDITIONAL_APPROVE map to APPROVED
    elif 'DENY' in decision_upper or 'REJECT' in decision_upper:
        return 'REJECTED'
    else:
        return 'PENDING'


def status_to_decision(status: str) -> str:
    """
    Convert database status to AI agent decision format (for display purposes).
    
    Args:
        status: Database status (APPROVED, REJECTED, PENDING)
        
    Returns:
        AI decision format (APPROVE, DENY, PENDING)
    """
    if not status:
        return 'PENDING'
    
    status_upper = str(status).upper().strip()
    
    if status_upper == 'APPROVED':
        return 'APPROVE'
    elif status_upper == 'REJECTED':
        return 'DENY'
    else:
        return 'PENDING'
