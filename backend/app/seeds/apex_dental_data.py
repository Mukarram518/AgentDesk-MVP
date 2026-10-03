"""Demo business seed data for Apex Dental Studio.

All data is fictional and designed strictly for demonstration and testing purposes.
"""

APEX_DENTAL_BUSINESS = {
    "name": "Apex Dental Studio",
    "description": (
        "Premier family and cosmetic dentistry clinic in downtown Seattle offering preventive, "
        "restorative, cosmetic, and emergency dental care with state-of-the-art technology."
    ),
    "address": "124 Pine Street, Suite 300, Seattle, WA 98101",
    "phone": "(555) 019-2831",
    "email": "contact@apexdentalstudio.demo",
    "website": "https://apexdentalstudio.demo",
    "timezone": "America/Los_Angeles",
}

APEX_DENTAL_DOCUMENTS = [
    {
        "title": "Business Overview & Facility",
        "source_type": "business_info",
        "source_name": "about_us.txt",
        "content": (
            "Apex Dental Studio is a state-of-the-art modern dental practice located at 124 Pine Street, "
            "Suite 300 in downtown Seattle, WA. Led by Dr. Sarah Jenkins and Dr. Michael Chen, our clinic "
            "specializes in gentle, comprehensive family dentistry, cosmetic smile transformations, and restorative care. "
            "Our facility features low-radiation 3D digital imaging, intraoral scanners, pain-minimized anesthetic delivery, "
            "and ergonomic treatment suites. Validated patient parking is available in the Pacific Plaza garage adjacent to our building."
        ),
    },
    {
        "title": "Operating Hours & Emergency Dental Policy",
        "source_type": "hours",
        "source_name": "hours_and_emergency.txt",
        "content": (
            "Apex Dental Studio Operating Hours:\n"
            "- Monday through Friday: 8:00 AM – 6:00 PM\n"
            "- Saturday: 9:00 AM – 2:00 PM\n"
            "- Sunday: Closed for routine appointments.\n\n"
            "Emergency Dental Care Policy:\n"
            "We reserve dedicated emergency appointment slots every business day for urgent conditions including "
            "severe toothaches, chipped or knocked-out teeth, lost crowns, or acute dental infections. "
            "For after-hours dental emergencies, registered patients can call our emergency line at (555) 019-2839 to reach the on-call dentist."
        ),
    },
    {
        "title": "Dental Services & Pricing Guide",
        "source_type": "services",
        "source_name": "services_and_prices.txt",
        "content": (
            "Apex Dental Studio Services and Pricing Guide:\n"
            "1. Comprehensive Exam & Cleaning: $180. Includes full digital X-rays, oral cancer screening, periodontal charting, and ultrasonic cleaning.\n"
            "2. Professional Teeth Whitening: $350 for in-office Zoom laser treatment (brightens teeth up to 8 shades in 60 minutes). Custom take-home trays with gel are $200.\n"
            "3. Invisalign Clear Aligners: Comprehensive initial consultation is FREE. Full orthodontic treatment packages range from $3,500 to $5,500.\n"
            "4. Dental Crowns: Custom porcelain or zirconia crowns range from $1,200 to $1,500 per tooth.\n"
            "5. Dental Implants: Complete titanium implant post, custom abutment, and lifelike porcelain crown ranges from $2,800 to $3,500.\n"
            "6. Root Canal Therapy: Anterior (front) teeth are $750; premolars and molars range from $950 to $1,150.\n"
            "7. Composite Tooth-Colored Fillings: $150 to $250 depending on the size and location of cavity.\n"
            "8. Deep Periodontal Cleaning (Scaling and Root Planing): $250 per quadrant.\n"
            "9. Emergency Consultation & Treatment: Emergency triage and examination begins at $150."
        ),
    },
    {
        "title": "Frequently Asked Questions (Insurance, Payments, and Policies)",
        "source_type": "faq",
        "source_name": "patient_faqs.txt",
        "content": (
            "Frequently Asked Questions at Apex Dental Studio:\n\n"
            "Q: What dental insurance plans do you accept?\n"
            "A: We are in-network with Delta Dental, Cigna, MetLife, Guardian, and Aetna PPO plans. We happily file claims for all out-of-network PPO providers.\n\n"
            "Q: What payment options do you offer for patients without insurance?\n"
            "A: We offer the Apex Dental Wellness Plan for $299/year (covers 2 preventative cleanings, annual exams, digital X-rays, and 20% off all other dental procedures). We also provide flexible 0% interest monthly financing via CareCredit.\n\n"
            "Q: What is your appointment cancellation policy?\n"
            "A: We kindly request at least 24 hours advance notice for cancellations or rescheduling. Cancellations made with less than 24 hours notice may incur a $50 late fee.\n\n"
            "Q: Do you treat children and pediatric patients?\n"
            "A: Yes! We welcome children aged 3 and older for routine checkups, pediatric cleanings, sealants, and gentle dental education.\n\n"
            "Q: What should I bring to my first dental appointment?\n"
            "A: Please arrive 15 minutes early and bring a government-issued photo ID, your dental insurance card (if applicable), and a list of current medications."
        ),
    },
]
