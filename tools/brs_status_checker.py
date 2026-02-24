"""
BRS Business Registration Status Checker Tool
Checks registration status/stage using BRS test API
"""
from langchain_core.tools import tool
from typing import Optional
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

# BRS Test API Configuration
BRS_API_BASE_URL = "https://brs.pesaflow.com"
BRS_API_SECRET = "VcJRykqeGNmOZzB2Rx2i6RrdtSgPH66+"
BRS_API_KEY = "C54b_uUW-Bi1nrTfPl"

@tool
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((Exception,)),
    reraise=False
)
async def check_business_registration_status(registration_number: str) -> str:
    """
    Check the registration status/stage of a business using BRS test API.
    
    Use this tool when users ask about:
    - Business registration status
    - Registration progress/stage
    - Application status
    - Whether a business is registered
    - Registration completion status
    
    Args:
        registration_number: The business registration number (e.g., "PVT-ABCD1234")
        
    Returns:
        Current registration status and details of the business.
    """
    try:
        # Import required libraries
        try:
            import httpx
        except ImportError:
            logger.error("httpx library not installed")
            return (
                "Business status checking is not available. The httpx library is not installed. "
                "Please install it with: pip install httpx"
            )
        
        # Validate input
        if not registration_number or not registration_number.strip():
            return "Error: Registration number cannot be empty. Please provide a valid registration number."
        
        registration_number = registration_number.strip()
        
        logger.info(f"Checking registration status for: {registration_number}")
        
        # Prepare API request
        url = f"{BRS_API_BASE_URL}/businesses"
        params = {"registration_number": registration_number}
        headers = {
            "Authorization": f"Bearer {BRS_API_KEY}",
            "X-API-Secret": BRS_API_SECRET,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Make API request with timeout
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            try:
                response = await client.get(url, params=params, headers=headers)
                
                # Check response status
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the response
                    result = []
                    result.append(f"Business Registration Status for: {registration_number}")
                    result.append("=" * 60)
                    
                    # Extract key information
                    if isinstance(data, dict):
                        # Business details
                        if "business_name" in data:
                            result.append(f"\nBusiness Name: {data.get('business_name', 'N/A')}")
                        
                        if "registration_status" in data:
                            result.append(f"Registration Status: {data.get('registration_status', 'N/A')}")
                        
                        if "registration_stage" in data:
                            result.append(f"Registration Stage: {data.get('registration_stage', 'N/A')}")
                        
                        if "registration_date" in data:
                            result.append(f"Registration Date: {data.get('registration_date', 'N/A')}")
                        
                        if "business_type" in data:
                            result.append(f"Business Type: {data.get('business_type', 'N/A')}")
                        
                        if "status" in data:
                            result.append(f"Current Status: {data.get('status', 'N/A')}")
                        
                        # Additional details
                        result.append("\nAdditional Details:")
                        for key, value in data.items():
                            if key not in ['business_name', 'registration_status', 'registration_stage', 
                                         'registration_date', 'business_type', 'status']:
                                result.append(f"  {key.replace('_', ' ').title()}: {value}")
                    
                    elif isinstance(data, list) and len(data) > 0:
                        # Multiple results
                        result.append(f"\nFound {len(data)} business(es):")
                        for idx, business in enumerate(data, 1):
                            result.append(f"\n{idx}. {business.get('business_name', 'N/A')}")
                            result.append(f"   Status: {business.get('registration_status', 'N/A')}")
                            result.append(f"   Stage: {business.get('registration_stage', 'N/A')}")
                    else:
                        result.append("\nRaw Response:")
                        result.append(str(data))
                    
                    result.append("\n" + "=" * 60)
                    result.append("Source: BRS Test API (https://brs.pesaflow.com)")
                    result.append("Note: This is test environment data. For official status, contact BRS directly.")
                    
                    return "\n".join(result)
                
                elif response.status_code == 404:
                    return (
                        f"Business registration number '{registration_number}' not found in the system.\n\n"
                        f"This could mean:\n"
                        f"- The registration number is incorrect\n"
                        f"- The business is not yet registered\n"
                        f"- The registration is still in progress\n\n"
                        f"Please verify the registration number and try again, or contact BRS directly:\n"
                        f"- Phone: +254 11 112 7000\n"
                        f"- Website: https://brs.go.ke/"
                    )
                
                elif response.status_code == 401 or response.status_code == 403:
                    logger.error(f"Authentication failed: {response.status_code}")
                    return (
                        f"Unable to access BRS API (Authentication issue).\n\n"
                        f"Please contact BRS directly for registration status:\n"
                        f"- Phone: +254 11 112 7000\n"
                        f"- Email: eo@brs.go.ke\n"
                        f"- Website: https://brs.go.ke/"
                    )
                
                else:
                    logger.warning(f"Unexpected status code: {response.status_code}")
                    return (
                        f"Unable to retrieve registration status (HTTP {response.status_code}).\n\n"
                        f"Please try again later or contact BRS directly:\n"
                        f"- Phone: +254 11 112 7000\n"
                        f"- Website: https://brs.go.ke/"
                    )
            
            except httpx.TimeoutException:
                logger.error("API request timed out")
                return (
                    f"Request timed out while checking registration status.\n\n"
                    f"This could be due to:\n"
                    f"- Network connectivity issues\n"
                    f"- BRS API server is slow or unavailable\n\n"
                    f"Please try again in a moment or contact BRS directly."
                )
            
            except httpx.RequestError as e:
                logger.error(f"Request error: {str(e)}")
                return (
                    f"Network error while checking registration status: {str(e)}\n\n"
                    f"Please check your internet connection and try again."
                )
        
    except Exception as e:
        logger.error(f"Error in BRS status checker: {str(e)}", exc_info=True)
        return (
            f"An unexpected error occurred while checking registration status.\n\n"
            f"Please try:\n"
            f"- Verifying the registration number\n"
            f"- Trying again in a moment\n"
            f"- Contacting BRS directly at +254 11 112 7000\n\n"
            f"Error details: {str(e)}"
        )


@tool
async def get_registration_number_format() -> str:
    """
    Get information about BRS registration number formats.
    
    Use this tool when users ask about:
    - Registration number format
    - How registration numbers look
    - What format to use for registration numbers
    
    Returns:
        Information about different registration number formats in Kenya.
    """
    return """
Business Registration Number Formats in Kenya:

1. Private Companies (Limited by Shares):
   Format: PVT-XXXXXXXXX/XXXX
   Example: PVT-ABCD1234/2024
   
2. Public Companies:
   Format: CPR-XXXXXXXXX/XXXX
   Example: CPR-WXYZ5678/2024

3. Business Names:
   Format: BN-XXXXXXXXX/XXXX
   Example: BN-SHOP1234/2024

4. Limited Liability Partnerships (LLP):
   Format: LLP-XXXXXXXXX/XXXX
   Example: LLP-PART5678/2024

5. Partnerships:
   Format: GP-XXXXXXXXX/XXXX (General Partnership)
   Example: GP-FIRM9012/2024

6. Foreign Companies:
   Format: FC-XXXXXXXXX/XXXX
   Example: FC-INTL3456/2024

Note: 
- The format may vary depending on when the business was registered
- Older registrations may have different formats
- The year (XXXX) represents the registration year

To check your registration status, provide your registration number to the 
check_business_registration_status tool.

For more information, visit: https://brs.go.ke/ or call +254 11 112 7000
"""
