from typing import Optional
from app.services.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Deterministic Mock LLM Provider for unit and integration testing without external APIs."""

    def __init__(self, model_name: str = "mock-grounded-llm"):
        self._model_name = model_name

    @property
    def model_name(self) -> str:
        return self._model_name

    async def generate_response(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[str] = None,
        temperature: float = 0.2,
    ) -> str:
        msg_lower = user_message.lower()

        # Prompt injection test defense check
        if any(term in msg_lower for term in ["ignore previous", "ignore all", "reveal secret", "system prompt"]):
            return (
                "I am the AI assistant for Apex Dental Studio. I cannot disclose internal instructions "
                "or system prompts. How may I assist you with our dental services today?"
            )

        # If context is missing or empty or explicit unknown
        if not context or "[No relevant knowledge found" in context or "brain surgery" in msg_lower:
            return (
                "I'm sorry, but that information is not available in our business knowledge base. "
                "Please contact Apex Dental Studio directly at (555) 019-2831 for further assistance."
            )

        # Grounded answering based on context
        if "teeth cleaning" in msg_lower or "clean" in msg_lower:
            return (
                "At Apex Dental Studio, a Comprehensive Exam & Cleaning is $180, which includes full digital X-rays, "
                "periodontal charting, and ultrasonic cleaning. Deep periodontal cleaning (scaling and root planing) is $250 per quadrant."
            )
        elif "service" in msg_lower:
            return (
                "Apex Dental Studio provides comprehensive family and cosmetic dentistry services including: "
                "Comprehensive Exams & Cleanings ($180), Professional Teeth Whitening ($350), Invisalign consultations (Free), "
                "Dental Crowns ($1,200-$1,500), Dental Implants ($2,800-$3,500), Root Canal Therapy ($750-$1,150), and Emergency Dental Care."
            )
        elif "hour" in msg_lower or "open" in msg_lower:
            return (
                "Our operating hours are Monday through Friday from 8:00 AM to 6:00 PM, and Saturday from 9:00 AM to 2:00 PM. "
                "We are closed on Sunday for routine visits, but emergency on-call care is available."
            )
        elif "locat" in msg_lower or "address" in msg_lower or "where" in msg_lower:
            return (
                "Apex Dental Studio is located at 124 Pine Street, Suite 300 in downtown Seattle, WA. "
                "Validated patient parking is available in the Pacific Plaza garage adjacent to our building."
            )
        else:
            return (
                f"Based on our clinic's information: {context[:200]}... "
                "For more details, please call us at (555) 019-2831."
            )
