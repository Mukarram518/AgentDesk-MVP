import re
from typing import Optional, Tuple
from pydantic import BaseModel, EmailStr


class ExtractedLeadInfo(BaseModel):
    """Structured extraction of customer details and intent from conversation."""
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    intent: Optional[str] = None
    raw_message: str


# Regex for email detection
EMAIL_REGEX = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b"
)

# Regex for standard phone numbers (US/international formats)
PHONE_REGEX = re.compile(
    r"(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b"
)

# Regex for name declaration patterns like "my name is Ali", "I'm Ali Khan", "name: Ali"
NAME_REGEX = re.compile(
    r"(?:my\s+name\s+is|i\s+am|i'm|name\s*[:\-])\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
    re.IGNORECASE,
)

# Intent keyword patterns
BOOKING_PATTERNS = [
    r"\bbook\b",
    r"\bschedule\b",
    r"\bappointment\b",
    r"\breserve\b",
    r"\bmake an appointment\b",
    r"\bset up (?:a |an )?(?:visit|consultation|appointment)\b",
    r"\bwant to come in\b",
]

AVAILABILITY_PATTERNS = [
    r"\bavailable\b",
    r"\bavailability\b",
    r"\bany openings\b",
    r"\bopen slots?\b",
    r"\bsoonest\b",
    r"\btomorrow\b",
    r"\bnext week\b",
]

PRICING_INTEREST_PATTERNS = [
    r"(?:how much|price|cost|quote).*(?:interested|want|need|get|sign|ready)",
    r"(?:interested|want|need).*(?:how much|price|cost|quote)",
    r"i'?m interested in (?:a |the )?(?:teeth |dental )?[a-z]+",
]

EXPRESS_SERVICE_PATTERNS = [
    r"\bi want to get\b",
    r"\bi need (?:a |an )?(?:teeth |dental )?[a-z]+",
    r"\blooking for (?:a |an )?[a-z]+",
    r"\btooth pain\b",
    r"\bemergency\b",
]

INFORMATIONAL_ONLY_PATTERNS = [
    r"^what services do you (?:offer|provide)",
    r"^what are your (?:opening )?hours",
    r"^where are you (?:located|based)",
    r"^are you open\b",
    r"^do you perform\b",
    r"^who are you\b",
]


class LeadExtractor:
    """Extracts contact information and intent signals deterministically from messages."""

    @staticmethod
    def extract_info(message: str) -> ExtractedLeadInfo:
        clean_msg = message.strip()

        # 1. Extract email
        email: Optional[str] = None
        email_match = EMAIL_REGEX.search(clean_msg)
        if email_match:
            email = email_match.group(0).strip()

        # 2. Extract phone
        phone: Optional[str] = None
        phone_match = PHONE_REGEX.search(clean_msg)
        if phone_match:
            phone = phone_match.group(0).strip()

        # 3. Extract name
        name: Optional[str] = None
        name_match = re.search(
            r"(?:my\s+name\s+is|i\s+am|i'm|name\s*[:\-])\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)",
            clean_msg,
            re.IGNORECASE,
        )
        if name_match:
            raw_candidate = name_match.group(1).strip()
            # Split and discard any stop words
            words = raw_candidate.split()
            clean_words = [
                w for w in words
                if w.lower() not in (
                    "and", "my", "email", "phone", "interested", "looking",
                    "here", "ready", "booking", "calling", "at", "a", "an", "the"
                )
            ]
            if clean_words:
                name = " ".join(clean_words).title()

        # 4. Classify intent
        intent = LeadExtractor.classify_intent(clean_msg)

        return ExtractedLeadInfo(
            name=name,
            email=email,
            phone=phone,
            intent=intent,
            raw_message=clean_msg,
        )

    @staticmethod
    def classify_intent(message: str) -> str:
        msg_lower = message.lower()

        # Check pure informational questions first
        for pat in INFORMATIONAL_ONLY_PATTERNS:
            if re.search(pat, msg_lower):
                # If they didn't also ask to book or provide contact info
                if not any(re.search(b_pat, msg_lower) for b_pat in BOOKING_PATTERNS):
                    return "informational"

        # Check booking intent
        for pat in BOOKING_PATTERNS:
            if re.search(pat, msg_lower):
                return "booking"

        # Check availability
        for pat in AVAILABILITY_PATTERNS:
            if re.search(pat, msg_lower):
                return "availability"

        # Check pricing + interest
        for pat in PRICING_INTEREST_PATTERNS:
            if re.search(pat, msg_lower):
                return "pricing_interest"

        # Check expressed service need
        for pat in EXPRESS_SERVICE_PATTERNS:
            if re.search(pat, msg_lower):
                return "service_inquiry"

        return "general"
