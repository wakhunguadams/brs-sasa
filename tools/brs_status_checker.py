"""
BRS Business Registration Status Checker Tool
Checks registration status using the BRS Pesaflow API with Basic Auth
"""
from langchain_core.tools import tool
from typing import Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)


# Status explanations for users
_STATUS_EXPLANATIONS = {
    "registered": {
        "meaning": "Your business/company has been successfully registered with BRS.",
        "details": "The registration process is complete. Your entity is officially recognized under Kenyan law.",
        "next_steps": [
            "Obtain your Certificate of Registration/Incorporation from the BRS portal or eCitizen",
            "Apply for a KRA PIN if not already done",
            "Apply for relevant licenses and permits for your business sector",
            "Open a business bank account using your registration documents",
            "Maintain annual compliance (file annual returns, update records as needed)",
        ],
    },
    "pending": {
        "meaning": "Your application is currently being reviewed by BRS.",
        "details": "Your application has been received and is in the processing queue. A registrar will review it.",
        "next_steps": [
            "Wait for BRS to complete the review (typically 3-7 working days)",
            "Check your email for any queries or requests for additional information",
            "You can check back here for status updates",
            "If it's been more than 14 days, contact BRS at +254 11 112 7000",
        ],
    },
    "queried": {
        "meaning": "BRS has raised a query on your application and needs more information or corrections.",
        "details": "The registrar has reviewed your application and found issues that need to be addressed before it can proceed.",
        "next_steps": [
            "Log in to the eCitizen portal to view the specific query raised",
            "Prepare the requested documents or corrections",
            "Respond to the query through the eCitizen portal",
            "After responding, the application will be re-reviewed",
            "If you need help understanding the query, contact BRS at +254 11 112 7000",
        ],
    },
    "rejected": {
        "meaning": "Your application has been rejected by BRS.",
        "details": "The registrar has determined that your application cannot be approved in its current form.",
        "next_steps": [
            "Log in to the eCitizen portal to view the rejection reason",
            "Address the issues cited in the rejection",
            "You may submit a fresh application with the corrections",
            "Consider consulting a lawyer if the rejection involves legal issues",
            "Contact BRS for clarification at +254 11 112 7000",
        ],
    },
    "approved": {
        "meaning": "Your application has been approved and is being processed for final registration.",
        "details": "The registrar has approved your application. It's now in the final processing stage.",
        "next_steps": [
            "Your Certificate of Registration/Incorporation will be issued shortly",
            "Check the eCitizen portal for your certificate",
            "Begin preparing for post-registration requirements (KRA PIN, licenses, etc.)",
        ],
    },
    "suspended": {
        "meaning": "Your business registration has been suspended.",
        "details": "BRS has suspended your registration, possibly due to non-compliance or legal issues.",
        "next_steps": [
            "Contact BRS immediately to understand the reason for suspension",
            "Address any compliance issues (e.g., overdue annual returns)",
            "Submit any required documents to lift the suspension",
            "Phone: +254 11 112 7000 | Email: eo@brs.go.ke",
        ],
    },
    "struck_off": {
        "meaning": "Your business has been struck off the register.",
        "details": "BRS has removed your business from the register, typically due to prolonged non-compliance.",
        "next_steps": [
            "Apply for restoration if you wish to continue operating",
            "Consult a lawyer to understand the restoration process",
            "You may need to pay outstanding fees and penalties",
            "Contact BRS at +254 11 112 7000 for guidance",
        ],
    },
}


def _get_status_explanation(status: str) -> dict:
    """Get a human-friendly explanation for a registration status."""
    status_lower = status.lower().strip().replace(" ", "_")
    return _STATUS_EXPLANATIONS.get(status_lower, {
        "meaning": f"Your application status is: {status}",
        "details": "This status indicates the current stage of your registration in the BRS system.",
        "next_steps": [
            "Log in to eCitizen portal for more details",
            "Contact BRS at +254 11 112 7000 for clarification",
            "Visit https://brs.go.ke/ for more information",
        ],
    })


def _format_business_record(record: dict) -> str:
    """Format a single business record into a readable string."""
    lines = []

    business_name = record.get("business_name", "N/A")
    reg_number = record.get("registration_number", "N/A")
    status = record.get("status", "unknown")
    reg_date = record.get("registration_date", "N/A")
    kra_pin = record.get("kra_pin")
    postal_address = record.get("postal_address")
    physical_address = record.get("physical_address")
    phone = record.get("phone_number")
    email = record.get("email")
    partners = record.get("partners", [])
    branches = record.get("branches")

    lines.append(f"📋 Business Name: {business_name}")
    lines.append(f"🔢 Registration Number: {reg_number}")
    lines.append(f"📊 Status: {status.upper()}")
    lines.append(f"📅 Registration Date: {reg_date}")

    if kra_pin:
        lines.append(f"🏛️ KRA PIN: {kra_pin}")

    if postal_address:
        lines.append(f"📮 Postal Address: {postal_address}")

    if physical_address:
        lines.append(f"📍 Physical Address: {physical_address}")

    if phone:
        lines.append(f"📞 Phone: {phone}")

    if email:
        lines.append(f"📧 Email: {email}")

    if partners:
        lines.append(f"\n👥 Partners/Directors ({len(partners)}):")
        for p in partners:
            name = p.get("name", "N/A")
            id_type = p.get("id_type", "")
            lines.append(f"   • {name} ({id_type})")

    if branches:
        lines.append(f"\n🏢 Branches: {branches}")

    # Add status explanation
    explanation = _get_status_explanation(status)
    lines.append(f"\n{'─' * 50}")
    lines.append(f"ℹ️ What this means:")
    lines.append(f"   {explanation['meaning']}")
    lines.append(f"   {explanation['details']}")
    lines.append(f"\n📌 Next Steps:")
    for i, step in enumerate(explanation["next_steps"], 1):
        lines.append(f"   {i}. {step}")

    return "\n".join(lines)


@tool
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=False
)
async def check_business_registration_status(registration_number: str) -> str:
    """
    Check the registration status of a business or company using the official BRS API.

    Use this tool when users:
    - Want to check business registration status
    - Provide a registration number (e.g., PVT-JZUA5QB, BN-YZC6PY7)
    - Ask about their application progress
    - Want to follow up on a registration
    - Ask what stage their business/company registration is at
    - Want to know if a business is registered

    Args:
        registration_number: The business registration number (e.g., "PVT-JZUA5QB", "BN-KDS3P7Q5")

    Returns:
        Business registration status with explanation and next steps.
    """
    try:
        try:
            import httpx
        except ImportError:
            return (
                "Business status checking is not available. "
                "Please install: pip install httpx"
            )

        # Validate input
        if not registration_number or not registration_number.strip():
            return (
                "Please provide a valid registration number.\n\n"
                "Registration number formats:\n"
                "  • Private Companies: PVT-XXXXXXX (e.g., PVT-JZUA5QB)\n"
                "  • Business Names: BN-XXXXXXX (e.g., BN-YZC6PY7)\n"
                "  • Public Companies: CPR-XXXXXXX\n"
                "  • LLPs: LLP-XXXXXXX\n"
                "  • Foreign Companies: FC-XXXXXXX"
            )

        registration_number = registration_number.strip().upper()
        logger.info(f"Checking registration status for: {registration_number}")

        # Get API credentials from settings
        from core.config import settings
        api_base = settings.BRS_API_BASE_URL
        username = settings.BRS_API_USERNAME
        password = settings.BRS_API_PASSWORD

        if not username or not password:
            return (
                "BRS API credentials are not configured. "
                "Please contact the administrator to set up API access."
            )

        # Make API request with Basic Auth
        url = f"{api_base}/api/businesses"
        params = {"registration_number": registration_number}
        auth = (username, password)

        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, auth=auth)

                if response.status_code == 200:
                    data = response.json()
                    records = data.get("records", [])
                    count = data.get("count", 0)

                    if count == 0 or not records:
                        return (
                            f"🔍 No records found for registration number: {registration_number}\n\n"
                            f"This could mean:\n"
                            f"  • The registration number may be incorrect — please double-check\n"
                            f"  • The application may still be in the early processing stage\n"
                            f"  • The business may not yet be in the system\n\n"
                            f"Registration number formats:\n"
                            f"  • Private Companies: PVT-XXXXXXX\n"
                            f"  • Business Names: BN-XXXXXXX\n"
                            f"  • Public Companies: CPR-XXXXXXX\n\n"
                            f"If you believe this is correct, please:\n"
                            f"  1. Check your eCitizen portal for the latest status\n"
                            f"  2. Contact BRS at +254 11 112 7000\n"
                            f"  3. Email: eo@brs.go.ke"
                        )

                    # Format results
                    result_lines = []
                    result_lines.append(f"✅ Business Registration Lookup Results")
                    result_lines.append("=" * 55)

                    for record in records:
                        result_lines.append("")
                        result_lines.append(_format_business_record(record))

                    result_lines.append("\n" + "=" * 55)
                    result_lines.append("Source: BRS Official API")
                    result_lines.append("For more details, visit: https://brs.go.ke/")

                    return "\n".join(result_lines)

                elif response.status_code == 403:
                    logger.error("BRS API authentication failed (403)")
                    return (
                        "Unable to access BRS API (authentication issue).\n\n"
                        "Please contact BRS directly:\n"
                        "  📞 Phone: +254 11 112 7000\n"
                        "  📧 Email: eo@brs.go.ke\n"
                        "  🌐 Website: https://brs.go.ke/"
                    )

                else:
                    logger.warning(f"BRS API returned status {response.status_code}")
                    return (
                        f"Unable to retrieve registration status (HTTP {response.status_code}).\n\n"
                        f"Please try again later or contact BRS:\n"
                        f"  📞 Phone: +254 11 112 7000\n"
                        f"  🌐 Website: https://brs.go.ke/"
                    )

            except httpx.TimeoutException:
                logger.error("BRS API request timed out")
                return (
                    "The request timed out. The BRS API may be experiencing high traffic.\n\n"
                    "Please try again in a moment or contact BRS directly:\n"
                    "  📞 Phone: +254 11 112 7000"
                )

            except httpx.RequestError as e:
                logger.error(f"BRS API request error: {str(e)}")
                return (
                    f"Network error while checking registration status.\n\n"
                    f"Please check your internet connection and try again."
                )

    except Exception as e:
        logger.error(f"Error in BRS status checker: {str(e)}", exc_info=True)
        return (
            f"An unexpected error occurred while checking registration status.\n\n"
            f"Please try again or contact BRS at +254 11 112 7000"
        )


@tool
async def get_registration_number_format() -> str:
    """
    Get information about BRS registration number formats.

    Use this tool when users ask about:
    - Registration number format
    - How registration numbers look
    - What format to use when checking status

    Returns:
        Information about different registration number formats in Kenya.
    """
    return """
Business Registration Number Formats in Kenya:

1. Private Companies (Limited by Shares):
   Format: PVT-XXXXXXX
   Example: PVT-JZUA5QB

2. Public Companies:
   Format: CPR-XXXXXXX
   Example: CPR-WXYZ5678

3. Business Names:
   Format: BN-XXXXXXX
   Example: BN-YZC6PY7

4. Limited Liability Partnerships (LLP):
   Format: LLP-XXXXXXX
   Example: LLP-PART5678

5. Partnerships:
   Format: GP-XXXXXXX (General Partnership)
   Example: GP-FIRM9012

6. Foreign Companies:
   Format: FC-XXXXXXX
   Example: FC-INTL3456

Note:
- Older registrations may use formats like BN/2001/00002
- The alphanumeric code is unique to each registration

To check your registration status, just provide your registration number
and I'll look it up for you!
"""
