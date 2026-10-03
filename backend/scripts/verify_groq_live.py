import asyncio
import os
import sys

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings

from app.services.llm.groq import GroqProvider
from app.services.llm.mock import MockLLMProvider
from app.services.prompt import get_grounded_system_prompt


async def main():
    print("=" * 60)
    print("AgentDesk MVP — Live Groq Integration Verification")
    print("=" * 60)
    print(f"Configured Model : {settings.GROQ_MODEL}")

    has_key = bool(
        settings.GROQ_API_KEY
        and settings.GROQ_API_KEY.strip() not in ("", "your_groq_api_key_here")
    )

    if not has_key:
        print("\n[INFO] GROQ_API_KEY is not set or contains the default placeholder.")
        print("[INFO] Testing with safe fallback MockLLMProvider...")
        provider = MockLLMProvider()
        status_msg = "MockLLMProvider (active offline fallback)"
    else:
        # Mask the key for safe display (never log or expose raw keys)
        masked_key = settings.GROQ_API_KEY[:4] + "..." + settings.GROQ_API_KEY[-4:]
        print(f"[INFO] GROQ_API_KEY detected: {masked_key}")
        print("[INFO] Connecting to Groq API via GroqProvider...")
        provider = GroqProvider()
        status_msg = f"GroqProvider ({settings.GROQ_MODEL})"

    system_prompt = get_grounded_system_prompt(
        business_name="Apex Dental Studio",
        phone="(555) 019-2831",
        email="contact@apexdentalstudio.demo",
    )
    context = (
        "[Dental Services & Pricing Guide]\n"
        "Comprehensive Exam & Cleaning: $180 (includes full digital X-rays, periodontal charting, and ultrasonic cleaning).\n"
        "Professional Teeth Whitening: $350 (in-office treatment, includes custom take-home maintenance trays).\n"
        "Dental Crowns: $1,200 - $1,500 (all-ceramic porcelain crowns, same-day digital impressions available)."
    )
    question = "How much is teeth whitening and what does it include?"

    print(f"\nProvider   : {status_msg}")
    print(f"Question   : {question}")
    print("Context    : [Supplied 3 pricing entries from Apex Dental Studio knowledge]")
    print("\nGenerating grounded completion...")

    try:
        response = await provider.generate_response(
            system_prompt=system_prompt,
            user_message=question,
            context=context,
            temperature=0.2,
        )
        print("\n" + "-" * 60)
        print("ASSISTANT RESPONSE:")
        print(response)
        print("-" * 60)
        print("\nVerification SUCCESSFUL.")
    except Exception as e:
        print(f"\n[ERROR] Live Groq call failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
