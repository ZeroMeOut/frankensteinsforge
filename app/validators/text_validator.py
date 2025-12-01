"""Text validation and sanitization utilities."""

import re
from typing import Optional
from app.core.exceptions import ValidationError


class TextValidator:
    """Validates and sanitizes text input to prevent injection attacks."""
    
    # Patterns for detecting potential injection attacks
    SQL_INJECTION_PATTERNS = [
        r"(\bUNION\b.*\bSELECT\b)",
        r"(\bDROP\b.*\bTABLE\b)",
        r"(\bINSERT\b.*\bINTO\b)",
        r"(\bDELETE\b.*\bFROM\b)",
        r"(\bUPDATE\b.*\bSET\b)",
        r"(--\s*$)",
        r"(;\s*DROP\b)",
        r"('\s*OR\s*'1'\s*=\s*'1)",
        r"('\s*OR\s*1\s*=\s*1)",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",  # Event handlers like onclick=
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$]",  # Shell metacharacters
        r"\$\([^)]*\)",  # Command substitution
        r"`[^`]*`",  # Backtick command substitution
    ]
    
    @staticmethod
    def sanitize(text: str, max_length: int = 5000) -> str:
        """Sanitize text input to prevent injection attacks.
        
        Args:
            text: Text to sanitize
            max_length: Maximum allowed text length
            
        Returns:
            Sanitized text
            
        Raises:
            ValidationError: If text validation fails
        """
        if not text:
            return ""
        
        # Check length
        if len(text) > max_length:
            raise ValidationError(
                f"Text exceeds maximum length",
                details={
                    "field": "text",
                    "reason": f"Text length ({len(text)}) exceeds limit ({max_length})",
                    "max_length": max_length,
                    "actual_length": len(text)
                }
            )
        
        # Detect potential injection attacks
        injection_type = TextValidator._detect_injection(text)
        if injection_type:
            # Neutralize the malicious content
            sanitized = TextValidator._neutralize_injection(text)
            return sanitized
        
        # Basic sanitization: normalize whitespace
        sanitized = " ".join(text.split())
        
        return sanitized
    
    @staticmethod
    def validate_length(text: str, min_len: int, max_len: int) -> bool:
        """Validate text length is within bounds.
        
        Args:
            text: Text to validate
            min_len: Minimum allowed length
            max_len: Maximum allowed length
            
        Returns:
            True if length is valid, False otherwise
        """
        if not text:
            return min_len == 0
        
        text_len = len(text)
        return min_len <= text_len <= max_len
    
    @staticmethod
    def _detect_injection(text: str) -> Optional[str]:
        """Detect potential injection attacks in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Type of injection detected ("sql", "xss", "command") or None
        """
        text_upper = text.upper()
        
        # Check for SQL injection patterns
        for pattern in TextValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, text_upper, re.IGNORECASE):
                return "sql"
        
        # Check for XSS patterns
        for pattern in TextValidator.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return "xss"
        
        # Check for command injection patterns
        for pattern in TextValidator.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, text):
                return "command"
        
        return None
    
    @staticmethod
    def _neutralize_injection(text: str) -> str:
        """Neutralize potential injection attacks by escaping/removing dangerous content.
        
        Args:
            text: Text containing potential injection
            
        Returns:
            Neutralized text
        """
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        
        # Escape shell metacharacters
        text = re.sub(r"[;&|`$]", "", text)
        
        # Remove SQL comment markers
        text = re.sub(r"--", "", text)
        
        # Remove backticks
        text = re.sub(r"`", "", text)
        
        # Escape quotes
        text = text.replace("'", "''")
        
        # Remove javascript: protocol
        text = re.sub(r"javascript:", "", text, flags=re.IGNORECASE)
        
        # Remove event handlers
        text = re.sub(r"on\w+\s*=", "", text, flags=re.IGNORECASE)
        
        # Normalize whitespace
        text = " ".join(text.split())
        
        return text
