"""
File processing safety utilities for handling uploaded files.

This module provides safe file processing with automatic cleanup,
streaming support, and metadata sanitization.
"""
import os
import tempfile
import asyncio
from typing import Optional, Dict, Any, AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
import re


class FileHandler:
    """
    Handles safe file processing with automatic cleanup.
    
    Provides context managers for temporary file management,
    streaming file processing, and metadata sanitization.
    """
    
    # Chunk size for streaming operations (64KB)
    CHUNK_SIZE = 64 * 1024
    
    # Maximum concurrent file operations
    MAX_CONCURRENT_OPERATIONS = 10
    
    # Semaphore for limiting concurrent operations (per event loop)
    _semaphores: Dict[Any, asyncio.Semaphore] = {}
    
    @classmethod
    def _get_semaphore(cls) -> asyncio.Semaphore:
        """Get or create the semaphore for concurrent operation limiting."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create a new semaphore
            return asyncio.Semaphore(cls.MAX_CONCURRENT_OPERATIONS)
        
        # Get or create semaphore for this event loop
        if loop not in cls._semaphores:
            cls._semaphores[loop] = asyncio.Semaphore(cls.MAX_CONCURRENT_OPERATIONS)
        
        return cls._semaphores[loop]
    
    @staticmethod
    @asynccontextmanager
    async def temporary_file(
        suffix: Optional[str] = None,
        prefix: Optional[str] = None,
        dir: Optional[str] = None
    ) -> AsyncIterator[Path]:
        """
        Context manager for temporary file with automatic cleanup.
        
        Creates a temporary file that is automatically deleted when the
        context exits, even if an exception occurs.
        
        Args:
            suffix: Optional file suffix (e.g., '.jpg')
            prefix: Optional file prefix
            dir: Optional directory for temp file
            
        Yields:
            Path: Path to the temporary file
            
        Example:
            async with FileHandler.temporary_file(suffix='.jpg') as temp_path:
                # Use temp_path
                with open(temp_path, 'wb') as f:
                    f.write(data)
            # File is automatically deleted here
        """
        # Create temporary file
        fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix=prefix, dir=dir)
        temp_path_obj = Path(temp_path)
        
        try:
            # Close the file descriptor (we'll use the path)
            os.close(fd)
            
            # Yield the path for use
            yield temp_path_obj
            
        finally:
            # Ensure cleanup happens even on exception
            try:
                if temp_path_obj.exists():
                    temp_path_obj.unlink()
            except Exception:
                # Log but don't raise - cleanup failure shouldn't break flow
                pass
    
    @staticmethod
    async def stream_file_chunks(
        file_path: Path,
        chunk_size: Optional[int] = None
    ) -> AsyncIterator[bytes]:
        """
        Stream file contents in chunks to prevent memory exhaustion.
        
        Reads file in chunks rather than loading entire file into memory.
        
        Args:
            file_path: Path to file to stream
            chunk_size: Size of chunks to read (default: CHUNK_SIZE)
            
        Yields:
            bytes: Chunks of file data
            
        Example:
            async for chunk in FileHandler.stream_file_chunks(path):
                process_chunk(chunk)
        """
        if chunk_size is None:
            chunk_size = FileHandler.CHUNK_SIZE
        
        # Use asyncio to read file without blocking
        loop = asyncio.get_event_loop()
        
        def read_chunk(f):
            return f.read(chunk_size)
        
        with open(file_path, 'rb') as f:
            while True:
                # Read chunk in executor to avoid blocking
                chunk = await loop.run_in_executor(None, read_chunk, f)
                if not chunk:
                    break
                yield chunk
    
    @staticmethod
    async def write_file_streaming(
        file_path: Path,
        data: bytes,
        chunk_size: Optional[int] = None
    ) -> None:
        """
        Write data to file in streaming fashion.
        
        Writes data in chunks to avoid blocking and handle large files.
        
        Args:
            file_path: Path where file should be written
            data: Data to write
            chunk_size: Size of chunks to write (default: CHUNK_SIZE)
        """
        if chunk_size is None:
            chunk_size = FileHandler.CHUNK_SIZE
        
        loop = asyncio.get_event_loop()
        
        def write_chunk(f, chunk):
            f.write(chunk)
        
        with open(file_path, 'wb') as f:
            # Write in chunks
            for i in range(0, len(data), chunk_size):
                chunk = data[i:i + chunk_size]
                await loop.run_in_executor(None, write_chunk, f, chunk)
    
    @staticmethod
    @asynccontextmanager
    async def isolated_file_operation():
        """
        Context manager for isolated file operations.
        
        Limits concurrent file operations to prevent resource exhaustion
        and ensure isolation between concurrent uploads.
        
        Example:
            async with FileHandler.isolated_file_operation():
                # Perform file operation
                # Only MAX_CONCURRENT_OPERATIONS will run simultaneously
                pass
        """
        semaphore = FileHandler._get_semaphore()
        async with semaphore:
            yield
    
    @staticmethod
    def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize file metadata to remove potentially malicious content.
        
        Removes or escapes dangerous characters and patterns from metadata
        fields to prevent injection attacks.
        
        Args:
            metadata: Dictionary of metadata fields
            
        Returns:
            Dict[str, Any]: Sanitized metadata
            
        Example:
            metadata = {"filename": "test<script>.jpg", "size": 1024}
            safe_metadata = FileHandler.sanitize_metadata(metadata)
            # safe_metadata["filename"] == "testscript.jpg"
        """
        sanitized = {}
        
        for key, value in metadata.items():
            # Sanitize key
            safe_key = FileHandler._sanitize_string(str(key))
            
            # Sanitize value based on type
            if isinstance(value, str):
                safe_value = FileHandler._sanitize_string(value)
            elif isinstance(value, (int, float, bool)):
                # Numeric and boolean values are safe
                safe_value = value
            elif isinstance(value, dict):
                # Recursively sanitize nested dicts
                safe_value = FileHandler.sanitize_metadata(value)
            elif isinstance(value, list):
                # Sanitize list items
                safe_value = [
                    FileHandler._sanitize_string(str(item)) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                # Convert unknown types to string and sanitize
                safe_value = FileHandler._sanitize_string(str(value))
            
            sanitized[safe_key] = safe_value
        
        return sanitized
    
    @staticmethod
    def _sanitize_string(text: str) -> str:
        """
        Sanitize a string by removing dangerous characters and patterns.
        
        Args:
            text: String to sanitize
            
        Returns:
            str: Sanitized string
        """
        if not text:
            return text
        
        # Remove null bytes
        text = text.replace('\x00', '')
        
        # Remove control characters except newline and tab
        text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
        
        # Remove script tags and content (do this before removing other tags)
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove style tags and content
        text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove javascript: protocol
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        
        # Remove SQL comment markers
        text = text.replace('--', '')
        text = text.replace('/*', '')
        text = text.replace('*/', '')
        
        # Remove shell metacharacters
        dangerous_chars = ['|', ';', '&', '$', '`', '\n', '\r']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        # Limit length to prevent DoS
        max_length = 1000
        if len(text) > max_length:
            text = text[:max_length]
        
        return text.strip()
    
    @staticmethod
    async def process_upload_safely(
        file_data: bytes,
        file_extension: str,
        processor_func,
        *args,
        **kwargs
    ) -> Any:
        """
        Process an uploaded file safely with automatic cleanup.
        
        Creates a temporary file, processes it, and ensures cleanup
        even if processing fails.
        
        Args:
            file_data: Raw file data
            file_extension: File extension (e.g., '.jpg')
            processor_func: Async function to process the file
            *args: Additional args for processor_func
            **kwargs: Additional kwargs for processor_func
            
        Returns:
            Any: Result from processor_func
            
        Raises:
            Exception: Any exception from processor_func
            
        Example:
            async def process_image(path: Path) -> str:
                # Process image
                return "result"
            
            result = await FileHandler.process_upload_safely(
                image_bytes,
                '.jpg',
                process_image
            )
        """
        async with FileHandler.isolated_file_operation():
            async with FileHandler.temporary_file(suffix=file_extension) as temp_path:
                try:
                    # Write file data
                    await FileHandler.write_file_streaming(temp_path, file_data)
                    
                    # Process the file
                    result = await processor_func(temp_path, *args, **kwargs)
                    
                    return result
                    
                except Exception:
                    # Cleanup is handled by context manager
                    # Re-raise the exception
                    raise
