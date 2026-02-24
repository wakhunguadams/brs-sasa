"""
Input Validation for BRS-SASA
Handles edge cases and validates user input before processing
"""
import re
from typing import Tuple, Optional

class InputValidator:
    """Validates and sanitizes user input"""
    
    MAX_LENGTH = 4000  # Maximum input length
    MIN_LENGTH = 1     # Minimum input length
    
    @staticmethod
    def validate(user_input: str) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validate user input
        
        Returns:
            (is_valid, sanitized_input, error_message)
        """
        # Check if input is None or empty
        if not user_input or not user_input.strip():
            return (False, None, "Your query cannot be empty. Please ask a question about business registration, legislation, or BRS services.")
        
        # Strip whitespace
        sanitized = user_input.strip()
        
        # Check length
        if len(sanitized) > InputValidator.MAX_LENGTH:
            return (False, None, f"Your query is too long ({len(sanitized)} characters). Please keep it under {InputValidator.MAX_LENGTH} characters.")
        
        if len(sanitized) < InputValidator.MIN_LENGTH:
            return (False, None, "Your query is too short. Please provide more details about what you need help with.")
        
        # Check for gibberish (no vowels or too many repeated characters)
        if not re.search(r'[aeiouAEIOU]', sanitized):
            return (False, None, "I don't understand your query. Please rephrase your question in English or Swahili.")
        
        # Check for excessive repeated characters (more than 5 in a row)
        if re.search(r'(.)\1{5,}', sanitized):
            return (False, None, "Your query contains unusual patterns. Please rephrase your question clearly.")
        
        # Sanitize special characters (but keep basic punctuation)
        # Remove potentially dangerous characters
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',  # Script tags
            r'javascript:',                 # JavaScript protocol
            r'on\w+\s*=',                  # Event handlers
            r'<iframe[^>]*>',              # Iframes
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                # Remove the dangerous content
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        # Check if query is too ambiguous
        ambiguous_queries = [
            r'^(how do i register|register|what are the fees|fees|tell me about)$',
            r'^(hi|hello|hey)$',
            r'^(help|info|information)$'
        ]
        
        for pattern in ambiguous_queries:
            if re.match(pattern, sanitized.lower()):
                # Add clarification prompt
                clarification = InputValidator._get_clarification(sanitized.lower())
                if clarification:
                    return (False, None, clarification)
        
        return (True, sanitized, None)
    
    @staticmethod
    def _get_clarification(query: str) -> Optional[str]:
        """Get clarification prompt for ambiguous queries"""
        if query in ['how do i register', 'register']:
            return (
                "I can help you with registration! Please specify what you want to register:\n"
                "- Private Limited Company\n"
                "- Public Limited Company\n"
                "- Business Name\n"
                "- Limited Liability Partnership (LLP)\n"
                "- Partnership\n"
                "- Foreign Company\n\n"
                "For example: 'How do I register a private limited company?'"
            )
        
        if query in ['what are the fees', 'fees']:
            return (
                "I can provide fee information! Please specify what fees you need:\n"
                "- Company registration fees\n"
                "- Business name registration fees\n"
                "- LLP registration fees\n"
                "- Partnership registration fees\n\n"
                "For example: 'What are the fees for registering a private company?'"
            )
        
        if query in ['tell me about']:
            return (
                "I can provide information about:\n"
                "- Business registration processes\n"
                "- Trust Administration Bill 2025\n"
                "- BRS services and contact information\n"
                "- Registration requirements and fees\n\n"
                "Please be more specific about what you'd like to know."
            )
        
        if query in ['hi', 'hello', 'hey']:
            return (
                "Hello! I'm BRS-SASA, your AI assistant for the Business Registration Service of Kenya. "
                "I can help you with:\n"
                "- Business registration processes and requirements\n"
                "- Trust Administration Bill 2025 and public participation\n"
                "- BRS services, fees, and contact information\n\n"
                "What would you like to know?"
            )
        
        if query in ['help', 'info', 'information']:
            return (
                "I'm BRS-SASA, your AI assistant for the Business Registration Service of Kenya. "
                "I can help you with:\n"
                "- Registering companies, business names, LLPs, and partnerships\n"
                "- Understanding the Trust Administration Bill 2025\n"
                "- Comparing Kenya's legislation with other countries\n"
                "- Providing feedback on proposed legislation\n"
                "- BRS contact information and services\n\n"
                "Please ask a specific question and I'll be happy to help!"
            )
        
        return None
    
    @staticmethod
    def is_out_of_scope(user_input: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query is out of scope for BRS-SASA
        
        Returns:
            (is_out_of_scope, response_message)
        """
        out_of_scope_keywords = [
            'weather', 'temperature', 'climate',
            'sports', 'football', 'soccer', 'basketball',
            'recipe', 'cooking', 'food',
            'movie', 'film', 'entertainment',
            'music', 'song', 'artist',
            'joke', 'funny', 'laugh',
            'game', 'play', 'gaming'
        ]
        
        user_input_lower = user_input.lower()
        
        for keyword in out_of_scope_keywords:
            if keyword in user_input_lower:
                return (True, (
                    f"I can only provide information related to the Business Registration Service (BRS) of Kenya. "
                    f"I cannot help with {keyword}-related queries.\n\n"
                    f"I can assist you with:\n"
                    f"- Business registration processes and requirements\n"
                    f"- Trust Administration Bill 2025 and public participation\n"
                    f"- BRS services, fees, and contact information\n\n"
                    f"Please ask a question related to BRS services."
                ))
        
        return (False, None)
