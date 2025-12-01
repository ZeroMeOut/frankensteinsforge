"""File validation utilities for uploaded files."""

import filetype
from typing import Optional, Set
from fastapi import UploadFile
from app.core.exceptions import ValidationError


class FileValidator:
    """Validates uploaded files for type and size constraints."""
    
    # Supported MIME types
    SUPPORTED_IMAGE_TYPES: Set[str] = {
        "image/jpeg",
        "image/jpg", 
        "image/png",
        "image/gif",
        "image/webp"
    }
    
    SUPPORTED_AUDIO_TYPES: Set[str] = {
        "audio/mpeg",
        "audio/mp3",
        "audio/wav",
        "audio/wave",
        "audio/x-wav",
        "audio/ogg",
        "audio/webm",
        "audio/flac"
    }
    
    @staticmethod
    def validate_image(file: UploadFile, max_size: int) -> bytes:
        """Validate image file and return bytes.
        
        Args:
            file: Uploaded file to validate
            max_size: Maximum allowed file size in bytes
            
        Returns:
            File contents as bytes
            
        Raises:
            ValidationError: If validation fails
        """
        # Read file with size limit check
        file_bytes = FileValidator._read_file_with_size_check(
            file, max_size, "image"
        )
        
        # Verify MIME type
        if not FileValidator.verify_mime_type(file_bytes, "image"):
            detected_type = FileValidator._detect_mime_type(file_bytes)
            raise ValidationError(
                f"Invalid image file type",
                details={
                    "field": "image",
                    "reason": f"File signature does not match image type. Detected type: {detected_type or 'unknown'}",
                    "allowed_types": list(FileValidator.SUPPORTED_IMAGE_TYPES),
                    "filename": file.filename
                }
            )
        
        return file_bytes
    
    @staticmethod
    def validate_audio(file: UploadFile, max_size: int) -> bytes:
        """Validate audio file and return bytes.
        
        Args:
            file: Uploaded file to validate
            max_size: Maximum allowed file size in bytes
            
        Returns:
            File contents as bytes
            
        Raises:
            ValidationError: If validation fails
        """
        # Read file with size limit check
        file_bytes = FileValidator._read_file_with_size_check(
            file, max_size, "audio"
        )
        
        # Verify MIME type
        if not FileValidator.verify_mime_type(file_bytes, "audio"):
            detected_type = FileValidator._detect_mime_type(file_bytes)
            raise ValidationError(
                f"Invalid audio file type",
                details={
                    "field": "audio",
                    "reason": f"File signature does not match audio type. Detected type: {detected_type or 'unknown'}",
                    "allowed_types": list(FileValidator.SUPPORTED_AUDIO_TYPES),
                    "filename": file.filename
                }
            )
        
        return file_bytes
    
    @staticmethod
    def verify_mime_type(file_bytes: bytes, expected_category: str) -> bool:
        """Verify file signature matches expected MIME type category.
        
        Args:
            file_bytes: File contents to check
            expected_category: Expected category ("image" or "audio")
            
        Returns:
            True if file signature matches expected category, False otherwise
        """
        if not file_bytes:
            return False
        
        # Detect actual file type from signature
        kind = filetype.guess(file_bytes)
        
        if kind is None:
            return False
        
        detected_mime = kind.mime
        
        # Check if detected type matches expected category
        if expected_category == "image":
            return detected_mime in FileValidator.SUPPORTED_IMAGE_TYPES
        elif expected_category == "audio":
            return detected_mime in FileValidator.SUPPORTED_AUDIO_TYPES
        
        return False
    
    @staticmethod
    def _detect_mime_type(file_bytes: bytes) -> Optional[str]:
        """Detect MIME type from file bytes.
        
        Args:
            file_bytes: File contents to analyze
            
        Returns:
            Detected MIME type or None if unknown
        """
        if not file_bytes:
            return None
        
        kind = filetype.guess(file_bytes)
        return kind.mime if kind else None
    
    @staticmethod
    def _read_file_with_size_check(
        file: UploadFile,
        max_size: int,
        file_type: str
    ) -> bytes:
        """Read file with streaming size validation.
        
        This method reads the file in chunks to detect size violations
        early without loading the entire file into memory first.
        
        Args:
            file: Uploaded file to read
            max_size: Maximum allowed size in bytes
            file_type: Type of file for error messages ("image" or "audio")
            
        Returns:
            File contents as bytes
            
        Raises:
            ValidationError: If file exceeds size limit
        """
        # Reset file pointer to beginning
        file.file.seek(0)
        
        # Read in chunks to detect size violations early
        chunk_size = 8192  # 8KB chunks
        chunks = []
        total_size = 0
        
        while True:
            chunk = file.file.read(chunk_size)
            if not chunk:
                break
            
            total_size += len(chunk)
            
            # Check size limit before accumulating more data
            if total_size > max_size:
                raise ValidationError(
                    f"File size exceeds maximum allowed size",
                    details={
                        "field": file_type,
                        "reason": f"File size ({total_size} bytes) exceeds limit ({max_size} bytes)",
                        "max_size_bytes": max_size,
                        "max_size_mb": round(max_size / (1024 * 1024), 2),
                        "filename": file.filename
                    }
                )
            
            chunks.append(chunk)
        
        # Reset file pointer for potential re-reading
        file.file.seek(0)
        
        return b"".join(chunks)
