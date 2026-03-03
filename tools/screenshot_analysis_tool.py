"""
Screenshot Analysis Tool for BRS SASA
Analyzes screenshots to identify issues and extract information
"""
from langchain_core.tools import tool
from typing import Optional, Dict, Any
import json
from core.logger import setup_logger
from core.config import settings

logger = setup_logger(__name__)

@tool
async def analyze_screenshot(
    image_path: str,
    user_description: str
) -> str:
    """
    Analyze a screenshot from BRS system to identify issues and provide troubleshooting.
    
    Args:
        image_path: Path to the screenshot image file
        user_description: User's description of the issue
    
    Returns:
        JSON string with analysis results including error messages, troubleshooting steps
    """
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        # Load image
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        # Create analysis prompt
        prompt = f"""
        You are analyzing a screenshot from the Business Registration Service (BRS) of Kenya system.
        
        User's description of the issue: {user_description}
        
        Please analyze this screenshot and provide a detailed analysis:
        
        1. **Page Identification**: What page or feature of the BRS system is shown?
        2. **Error Messages**: Extract any error messages, error codes, or warnings visible (exact text)
        3. **Form Validation Errors**: Identify any form field validation errors
        4. **User Intent**: What is the user trying to accomplish?
        5. **Likely Cause**: What might be causing the issue based on the visual information?
        6. **Troubleshooting Steps**: Provide specific, actionable steps to resolve the issue
        7. **Escalation Needed**: Does this require human agent assistance? (yes/no)
        
        Format your response as JSON with these keys:
        - page_identified: string
        - error_messages: array of strings
        - form_validation_errors: array of objects with field and error
        - user_intent: string
        - likely_cause: string
        - troubleshooting_steps: array of strings
        - escalation_needed: boolean
        - confidence_score: number (0-1)
        """
        
        # Call Gemini Vision API
        response = await client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(
                    data=image_bytes,
                    mime_type='image/png'
                ),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        logger.info(f"Screenshot analyzed successfully: {image_path}")
        return response.text
        
    except Exception as e:
        logger.error(f"Error analyzing screenshot: {str(e)}")
        return json.dumps({
            "error": str(e),
            "page_identified": "Unknown",
            "error_messages": [],
            "troubleshooting_steps": [
                "Unable to analyze screenshot automatically",
                "Please contact BRS support directly:",
                "Phone: +254 11 112 7000",
                "Email: eo@brs.go.ke"
            ],
            "escalation_needed": True,
            "confidence_score": 0.0
        })


@tool
async def extract_error_code(image_path: str) -> str:
    """
    Extract error codes and error messages from a screenshot.
    
    Args:
        image_path: Path to the screenshot image file
    
    Returns:
        JSON string with extracted error information
    """
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        prompt = """
        Extract all error-related information from this screenshot:
        
        1. Error codes (e.g., BRS-ERR-001, PAY-4032)
        2. Error messages (exact text)
        3. Warning messages
        4. Form validation errors (field name and error message)
        5. System messages
        
        Return JSON with:
        - error_codes: array of error codes found
        - error_messages: array of error message texts
        - warnings: array of warning texts
        - form_validation_errors: array of {field, error}
        - system_messages: array of system message texts
        """
        
        response = await client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        logger.info(f"Error codes extracted from: {image_path}")
        return response.text
        
    except Exception as e:
        logger.error(f"Error extracting error codes: {str(e)}")
        return json.dumps({
            "error": str(e),
            "error_codes": [],
            "error_messages": [],
            "warnings": [],
            "form_validation_errors": []
        })


@tool
async def identify_brs_page(image_path: str) -> str:
    """
    Identify which page of the BRS system is shown in the screenshot.
    
    Args:
        image_path: Path to the screenshot image file
    
    Returns:
        JSON string with page identification
    """
    try:
        from google import genai
        from google.genai import types
        
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
        
        prompt = """
        Identify which page or feature of the Business Registration Service (BRS) system is shown:
        
        Common BRS pages:
        - Home/Dashboard
        - Company Registration Form
        - Business Name Registration
        - Name Search/Reservation
        - Payment Page
        - Application Status/Tracking
        - Document Upload
        - Certificate Download
        - User Profile/Account
        
        Return JSON with:
        - page_name: identified page name
        - page_type: registration/payment/status/other
        - visible_elements: array of UI elements visible
        - current_step: if multi-step process, which step
        - confidence: confidence score 0-1
        """
        
        response = await client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
                prompt
            ],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        logger.info(f"Page identified from: {image_path}")
        return response.text
        
    except Exception as e:
        logger.error(f"Error identifying page: {str(e)}")
        return json.dumps({
            "error": str(e),
            "page_name": "Unknown",
            "page_type": "unknown",
            "visible_elements": [],
            "confidence": 0.0
        })


# Tool list for agent integration
SCREENSHOT_ANALYSIS_TOOLS = [
    analyze_screenshot,
    extract_error_code,
    identify_brs_page
]
