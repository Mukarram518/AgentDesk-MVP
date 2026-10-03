import logging
from typing import Optional
from pydantic import BaseModel
from app.services.lead.extractor import ExtractedLeadInfo, LeadExtractor

logger = logging.getLogger(__name__)


class LeadScoreResult(BaseModel):
    """Deterministic lead scoring calculation output."""
    is_lead: bool
    status: Optional[str] = None  # "HOT", "WARM", "COLD", or None
    score: Optional[int] = None   # 0 to 100
    intent: str
    reason: str


class LeadScoringService:
    """Deterministic Lead Scoring Service.
    
    CRITICAL RULE:
    The LLM never sets or overrides the lead score.
    Scores are strictly computed by deterministic rules to guarantee 100% reproducibility.
    
    SCORING MATRIX:
    --------------------------------------------------------------------------
    Intent Category            Base Points   Signals
    --------------------------------------------------------------------------
    booking                    85            Explicit appointment / booking request
    availability               60            Inquiring about open slots / dates
    pricing_interest           55            Serious pricing inquiry with intent
    service_inquiry            50            Expressed personal need for a service
    informational              0             General hours, location, FAQ (No lead)
    general                    0             Unspecified queries (No lead)
    --------------------------------------------------------------------------
    Contact Multiplier Bonus:
    - Email provided:          +10 points
    - Phone provided:          +10 points
    - Name provided:           +5 points
    --------------------------------------------------------------------------
    STATUS THRESHOLDS:
    - Score >= 80:             "HOT"
    - Score 40 - 79:           "WARM"
    - Score 1 - 39:            "COLD"
    - Score 0 / Informational: No Lead Created
    """

    @staticmethod
    def evaluate(message: str, extracted_info: Optional[ExtractedLeadInfo] = None) -> LeadScoreResult:
        if extracted_info is None:
            extracted_info = LeadExtractor.extract_info(message)

        intent = extracted_info.intent or "general"

        # 1. Informational questions or general queries are NOT leads
        if intent in ("informational", "general"):
            # Check if user nonetheless provided contact info with an explicit desire
            if not (extracted_info.email or extracted_info.phone):
                return LeadScoreResult(
                    is_lead=False,
                    status=None,
                    score=None,
                    intent=intent,
                    reason="Informational or general query without purchase/booking signals.",
                )

        # 2. Determine base score from intent
        base_score = 0
        reason_parts = []

        if intent == "booking":
            base_score = 85
            reason_parts.append("Explicit booking or appointment request (+85)")
        elif intent == "availability":
            base_score = 60
            reason_parts.append("Availability or scheduling slot inquiry (+60)")
        elif intent == "pricing_interest":
            base_score = 55
            reason_parts.append("Pricing inquiry with expressed interest (+55)")
        elif intent == "service_inquiry":
            base_score = 50
            reason_parts.append("Personal dental service need expressed (+50)")
        else:
            base_score = 30
            reason_parts.append("Potential interest with contact information (+30)")

        # 3. Add deterministic contact bonuses
        contact_bonus = 0
        if extracted_info.name:
            contact_bonus += 5
            reason_parts.append("Customer name provided (+5)")
        if extracted_info.email:
            contact_bonus += 10
            reason_parts.append("Customer email provided (+10)")
        if extracted_info.phone:
            contact_bonus += 10
            reason_parts.append("Customer phone provided (+10)")

        total_score = min(100, max(0, base_score + contact_bonus))

        # 4. Map score to status
        if total_score >= 80:
            status = "HOT"
        elif total_score >= 40:
            status = "WARM"
        else:
            status = "COLD"

        logger.info(
            f"Lead evaluated for message '{message[:40]}...': "
            f"intent={intent}, score={total_score}, status={status}"
        )

        return LeadScoreResult(
            is_lead=True,
            status=status,
            score=total_score,
            intent=intent,
            reason="; ".join(reason_parts),
        )
