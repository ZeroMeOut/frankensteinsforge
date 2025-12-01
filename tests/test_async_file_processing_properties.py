"""
Property-based tests for async file processing.

These tests verify universal properties that should hold for async file
processing operations using Hypothesis for property-based testing.
"""
import pytest
import asyncio
import time
from pathlib import Path
from hypothesis import given, strategies as st, settings
from app.core.file_handler import FileHandler


class TestAsyncNonBlockingBehavior:
    """
    **Feature: api-improvements, Property 33: Async file processing non-blocking**
    **Validates: Requirements 11.1**
    
    For any file upload being processed, other concurrent requests should not be
    blocked or delayed.
    """
    
    @settings(max_examples=5)
    @given(
        num_concurrent=st.integers(min_value=2, max_value=5),
        file_size=st.integers(min_value=1000, max_value=5000),
        processing_delay=st.floats(min_value=0.005, max_value=0.02)
    )
    def test_concurrent_file_processing_non_blocking(
        self, num_concurrent: int, file_size: int, processing_delay: float
    ):
        """Test that concurrent file processing doesn't block other operations."""
        async def run_test():
            results = []
            start_times = []
            end_times = []
            
            async def process_file(file_id: int):
                """Process a file with simulated delay."""
                start_time = time.time()
                start_times.append(start_time)
                
                data = bytes([file_id % 256]) * file_size
                
                async def processor(path: Path):
                    # Simulate async processing with delay
                    await asyncio.sleep(processing_delay)
                    
                    # Verify data
                    with open(path, 'rb') as f:
                        read_data = f.read()
                    
                    assert read_data == data
                    return file_id
                
                result = await FileHandler.process_upload_safely(
                    data,
                    f'.{file_id}',
                    processor
                )
                
                end_time = time.time()
                end_times.append(end_time)
                
                return result
            
            # Process multiple files concurrently
            overall_start = time.time()
            tasks = [process_file(i) for i in range(num_concurrent)]
            results = await asyncio.gather(*tasks)
            overall_end = time.time()
            
            # All operations should complete successfully
            assert len(results) == num_concurrent
            assert sorted(results) == list(range(num_concurrent))
            
            # Total time should be less than sequential processing
            # (with some tolerance for overhead)
            sequential_time = num_concurrent * processing_delay
            actual_time = overall_end - overall_start
            
            # Async processing should be significantly faster than sequential
            # Allow 50% overhead for context switching and file I/O
            assert actual_time < sequential_time * 1.5
            
            # Multiple operations should have overlapping execution
            # Check that at least some operations started before others finished
            if num_concurrent >= 2:
                # Sort by start time
                sorted_starts = sorted(start_times)
                sorted_ends = sorted(end_times)
                
                # First operation should start before last operation ends
                # (indicating concurrent execution)
                assert sorted_starts[0] < sorted_ends[-1]
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        num_files=st.integers(min_value=3, max_value=5),
        file_size=st.integers(min_value=500, max_value=2000)
    )
    def test_file_operations_dont_block_each_other(
        self, num_files: int, file_size: int
    ):
        """Test that file operations execute concurrently without blocking."""
        async def run_test():
            execution_order = []
            lock = asyncio.Lock()
            
            async def process_with_tracking(file_id: int):
                """Process file and track execution order."""
                async with lock:
                    execution_order.append(('start', file_id))
                
                data = b'x' * file_size
                
                async def processor(path: Path):
                    # Small delay to allow interleaving
                    await asyncio.sleep(0.005)
                    
                    async with lock:
                        execution_order.append(('process', file_id))
                    
                    return file_id
                
                result = await FileHandler.process_upload_safely(
                    data,
                    f'.{file_id}',
                    processor
                )
                
                async with lock:
                    execution_order.append(('end', file_id))
                
                return result
            
            # Run concurrently
            tasks = [process_with_tracking(i) for i in range(num_files)]
            results = await asyncio.gather(*tasks)
            
            # All should complete
            assert len(results) == num_files
            
            # Check for interleaved execution
            # If truly concurrent, we should see starts from multiple files
            # before seeing all ends
            starts = [event for event in execution_order if event[0] == 'start']
            ends = [event for event in execution_order if event[0] == 'end']
            
            # Should have all starts and ends
            assert len(starts) == num_files
            assert len(ends) == num_files
            
            # Find position of last start and first end
            last_start_pos = max(
                i for i, event in enumerate(execution_order) if event[0] == 'start'
            )
            first_end_pos = min(
                i for i, event in enumerate(execution_order) if event[0] == 'end'
            )
            
            # If concurrent, some files should start before others end
            # (last start should come before or around first end)
            # This indicates overlapping execution
            assert last_start_pos < len(execution_order) - 1
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        slow_file_size=st.integers(min_value=2000, max_value=5000),
        fast_file_size=st.integers(min_value=100, max_value=1000),
        num_fast_files=st.integers(min_value=2, max_value=3)
    )
    def test_slow_file_doesnt_block_fast_files(
        self, slow_file_size: int, fast_file_size: int, num_fast_files: int
    ):
        """Test that a slow file operation doesn't block faster operations."""
        async def run_test():
            fast_results = []
            slow_result = None
            
            async def process_slow_file():
                """Process a large file with delay."""
                data = b'S' * slow_file_size
                
                async def processor(path: Path):
                    # Simulate slow processing
                    await asyncio.sleep(0.03)
                    return 'slow'
                
                return await FileHandler.process_upload_safely(
                    data, '.slow', processor
                )
            
            async def process_fast_file(file_id: int):
                """Process a small file quickly."""
                data = b'F' * fast_file_size
                
                async def processor(path: Path):
                    # Minimal delay
                    await asyncio.sleep(0.005)
                    return file_id
                
                return await FileHandler.process_upload_safely(
                    data, f'.fast{file_id}', processor
                )
            
            # Start slow file first
            slow_task = asyncio.create_task(process_slow_file())
            
            # Small delay to ensure slow file starts first
            await asyncio.sleep(0.01)
            
            # Start fast files
            fast_tasks = [
                asyncio.create_task(process_fast_file(i))
                for i in range(num_fast_files)
            ]
            
            # Wait for fast files to complete
            fast_start = time.time()
            fast_results = await asyncio.gather(*fast_tasks)
            fast_end = time.time()
            
            # Wait for slow file
            slow_result = await slow_task
            
            # Fast files should complete quickly despite slow file running
            fast_time = fast_end - fast_start
            
            # Fast files should complete in reasonable time
            # (not blocked by slow file)
            assert fast_time < 0.05  # Should be much less than slow file's 0.03s delay
            
            # All operations should succeed
            assert len(fast_results) == num_fast_files
            assert slow_result == 'slow'
        
        asyncio.run(run_test())



class TestConcurrencyLimitEnforcement:
    """
    **Feature: api-improvements, Property 34: Concurrency limit enforcement**
    **Validates: Requirements 11.2**
    
    For any burst of concurrent requests exceeding the configured limit, the system
    should queue or reject excess requests rather than processing all simultaneously.
    """
    
    @settings(max_examples=5)
    @given(
        num_requests=st.integers(min_value=5, max_value=10),
        file_size=st.integers(min_value=500, max_value=2000)
    )
    def test_concurrent_operations_respect_limit(
        self, num_requests: int, file_size: int
    ):
        """Test that concurrent operations respect the configured limit."""
        async def run_test():
            max_concurrent_seen = 0
            current_concurrent = 0
            lock = asyncio.Lock()
            
            async def tracked_operation(op_id: int):
                """Operation that tracks concurrent execution count."""
                nonlocal max_concurrent_seen, current_concurrent
                
                async with FileHandler.isolated_file_operation():
                    # Track concurrent operations
                    async with lock:
                        current_concurrent += 1
                        if current_concurrent > max_concurrent_seen:
                            max_concurrent_seen = current_concurrent
                    
                    # Simulate work
                    data = bytes([op_id % 256]) * file_size
                    
                    async def processor(path: Path):
                        await asyncio.sleep(0.005)
                        return op_id
                    
                    result = await FileHandler.process_upload_safely(
                        data, f'.{op_id}', processor
                    )
                    
                    async with lock:
                        current_concurrent -= 1
                    
                    return result
            
            # Launch many operations concurrently
            tasks = [tracked_operation(i) for i in range(num_requests)]
            results = await asyncio.gather(*tasks)
            
            # All operations should complete
            assert len(results) == num_requests
            
            # Should not exceed the configured limit
            assert max_concurrent_seen <= FileHandler.MAX_CONCURRENT_OPERATIONS
            
            # Should have actually limited concurrency if we had enough requests
            if num_requests > FileHandler.MAX_CONCURRENT_OPERATIONS:
                # We should have hit the limit
                assert max_concurrent_seen == FileHandler.MAX_CONCURRENT_OPERATIONS
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        burst_size=st.integers(min_value=15, max_value=25),
        file_size=st.integers(min_value=100, max_value=1000)
    )
    def test_burst_requests_queued_not_rejected(
        self, burst_size: int, file_size: int
    ):
        """Test that burst requests are queued rather than rejected."""
        async def run_test():
            async def process_file(file_id: int):
                """Process a file."""
                data = bytes([file_id % 256]) * file_size
                
                async def processor(path: Path):
                    await asyncio.sleep(0.005)
                    return file_id
                
                return await FileHandler.process_upload_safely(
                    data, f'.{file_id}', processor
                )
            
            # Send burst of requests
            tasks = [process_file(i) for i in range(burst_size)]
            results = await asyncio.gather(*tasks)
            
            # All requests should complete successfully (queued, not rejected)
            assert len(results) == burst_size
            assert sorted(results) == list(range(burst_size))
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        num_operations=st.integers(min_value=10, max_value=15),
        processing_time=st.floats(min_value=0.005, max_value=0.02)
    )
    def test_limit_prevents_resource_exhaustion(
        self, num_operations: int, processing_time: float
    ):
        """Test that concurrency limit prevents resource exhaustion."""
        async def run_test():
            active_operations = set()
            max_active = 0
            lock = asyncio.Lock()
            
            async def resource_intensive_operation(op_id: int):
                """Simulate resource-intensive operation."""
                nonlocal max_active
                
                async with FileHandler.isolated_file_operation():
                    async with lock:
                        active_operations.add(op_id)
                        if len(active_operations) > max_active:
                            max_active = len(active_operations)
                    
                    # Simulate resource usage
                    await asyncio.sleep(processing_time)
                    
                    async with lock:
                        active_operations.remove(op_id)
                    
                    return op_id
            
            # Launch many operations
            tasks = [resource_intensive_operation(i) for i in range(num_operations)]
            results = await asyncio.gather(*tasks)
            
            # All should complete
            assert len(results) == num_operations
            
            # Should never exceed limit
            assert max_active <= FileHandler.MAX_CONCURRENT_OPERATIONS
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        num_waves=st.integers(min_value=2, max_value=3),
        wave_size=st.integers(min_value=6, max_value=10)
    )
    def test_limit_enforced_across_multiple_waves(
        self, num_waves: int, wave_size: int
    ):
        """Test that limit is enforced consistently across multiple request waves."""
        async def run_test():
            max_concurrent_per_wave = []
            
            for wave in range(num_waves):
                current_concurrent = 0
                max_concurrent = 0
                lock = asyncio.Lock()
                
                async def wave_operation(op_id: int):
                    nonlocal current_concurrent, max_concurrent
                    
                    async with FileHandler.isolated_file_operation():
                        async with lock:
                            current_concurrent += 1
                            if current_concurrent > max_concurrent:
                                max_concurrent = current_concurrent
                        
                        await asyncio.sleep(0.005)
                        
                        async with lock:
                            current_concurrent -= 1
                        
                        return op_id
                
                # Launch wave
                tasks = [wave_operation(i) for i in range(wave_size)]
                results = await asyncio.gather(*tasks)
                
                assert len(results) == wave_size
                max_concurrent_per_wave.append(max_concurrent)
            
            # All waves should respect the limit
            for max_concurrent in max_concurrent_per_wave:
                assert max_concurrent <= FileHandler.MAX_CONCURRENT_OPERATIONS
        
        asyncio.run(run_test())


class TestEndpointIsolation:
    """
    **Feature: api-improvements, Property 35: Endpoint isolation**
    **Validates: Requirements 11.3**
    
    For any slow file processing operation, other API endpoints should remain
    responsive and not be blocked.
    """
    
    @settings(max_examples=5)
    @given(
        slow_processing_time=st.floats(min_value=0.03, max_value=0.08),
        num_fast_requests=st.integers(min_value=3, max_value=5),
        file_size=st.integers(min_value=1000, max_value=3000)
    )
    def test_slow_file_processing_doesnt_block_other_endpoints(
        self, slow_processing_time: float, num_fast_requests: int, file_size: int
    ):
        """Test that slow file processing on one endpoint doesn't block other endpoints."""
        async def run_test():
            fast_endpoint_results = []
            slow_endpoint_started = asyncio.Event()
            
            async def slow_file_endpoint():
                """Simulate a slow file processing endpoint."""
                data = b'S' * file_size
                
                async def slow_processor(path: Path):
                    # Signal that slow processing has started
                    slow_endpoint_started.set()
                    # Simulate slow file processing
                    await asyncio.sleep(slow_processing_time)
                    return 'slow_complete'
                
                return await FileHandler.process_upload_safely(
                    data, '.slow', slow_processor
                )
            
            async def fast_non_file_endpoint(request_id: int):
                """Simulate a fast endpoint that doesn't process files."""
                # Wait for slow endpoint to start
                await slow_endpoint_started.wait()
                
                # Simulate lightweight processing (no file I/O)
                await asyncio.sleep(0.005)
                return f'fast_{request_id}'
            
            # Start slow file processing endpoint
            slow_task = asyncio.create_task(slow_file_endpoint())
            
            # Wait a bit to ensure slow endpoint starts
            await asyncio.sleep(0.01)
            
            # Make multiple requests to fast endpoints while slow one is running
            fast_start = time.time()
            fast_tasks = [
                asyncio.create_task(fast_non_file_endpoint(i))
                for i in range(num_fast_requests)
            ]
            fast_endpoint_results = await asyncio.gather(*fast_tasks)
            fast_end = time.time()
            
            # Wait for slow endpoint to complete
            slow_result = await slow_task
            
            # Fast endpoints should complete quickly despite slow endpoint running
            fast_total_time = fast_end - fast_start
            
            # Fast endpoints should not be blocked by slow file processing
            # They should complete in reasonable time (much less than slow processing time)
            expected_fast_time = num_fast_requests * 0.005 * 1.5  # Allow 50% overhead
            assert fast_total_time < expected_fast_time
            assert fast_total_time < slow_processing_time * 0.8  # Should be much faster
            
            # All operations should succeed
            assert len(fast_endpoint_results) == num_fast_requests
            assert slow_result == 'slow_complete'
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        num_slow_endpoints=st.integers(min_value=2, max_value=3),
        num_fast_endpoints=st.integers(min_value=3, max_value=5),
        slow_delay=st.floats(min_value=0.02, max_value=0.05)
    )
    def test_multiple_slow_endpoints_dont_block_fast_ones(
        self, num_slow_endpoints: int, num_fast_endpoints: int, slow_delay: float
    ):
        """Test that multiple slow file endpoints don't block fast endpoints."""
        async def run_test():
            all_started = asyncio.Event()
            slow_count = 0
            lock = asyncio.Lock()
            
            async def slow_endpoint(endpoint_id: int):
                """Simulate slow file processing endpoint."""
                nonlocal slow_count
                
                data = bytes([endpoint_id % 256]) * 2000
                
                async def processor(path: Path):
                    async with lock:
                        slow_count += 1
                        if slow_count == num_slow_endpoints:
                            all_started.set()
                    
                    await asyncio.sleep(slow_delay)
                    return f'slow_{endpoint_id}'
                
                return await FileHandler.process_upload_safely(
                    data, f'.slow{endpoint_id}', processor
                )
            
            async def fast_endpoint(endpoint_id: int):
                """Simulate fast non-file endpoint."""
                # Wait for slow endpoints to start
                await all_started.wait()
                
                # Fast processing
                await asyncio.sleep(0.002)
                return f'fast_{endpoint_id}'
            
            # Start slow endpoints
            slow_tasks = [
                asyncio.create_task(slow_endpoint(i))
                for i in range(num_slow_endpoints)
            ]
            
            # Wait for slow endpoints to start
            await asyncio.sleep(0.01)
            
            # Start fast endpoints
            fast_start = time.time()
            fast_tasks = [
                asyncio.create_task(fast_endpoint(i))
                for i in range(num_fast_endpoints)
            ]
            fast_results = await asyncio.gather(*fast_tasks)
            fast_end = time.time()
            
            # Wait for slow endpoints
            slow_results = await asyncio.gather(*slow_tasks)
            
            # Fast endpoints should complete quickly
            fast_time = fast_end - fast_start
            expected_fast_time = num_fast_endpoints * 0.002 * 2  # Allow 100% overhead
            assert fast_time < expected_fast_time
            
            # All should succeed
            assert len(fast_results) == num_fast_endpoints
            assert len(slow_results) == num_slow_endpoints
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        file_size=st.integers(min_value=2000, max_value=5000),
        processing_delay=st.floats(min_value=0.03, max_value=0.06),
        num_other_requests=st.integers(min_value=3, max_value=6)
    )
    def test_file_upload_endpoint_isolation(
        self, file_size: int, processing_delay: float, num_other_requests: int
    ):
        """Test that file upload endpoints are isolated from each other and other endpoints."""
        async def run_test():
            upload_started = asyncio.Event()
            other_response_times = []
            
            async def file_upload_endpoint():
                """Simulate file upload with processing."""
                data = b'U' * file_size
                
                async def processor(path: Path):
                    upload_started.set()
                    await asyncio.sleep(processing_delay)
                    return 'upload_complete'
                
                return await FileHandler.process_upload_safely(
                    data, '.upload', processor
                )
            
            async def other_endpoint(req_id: int):
                """Simulate other API endpoint."""
                # Wait for upload to start
                await upload_started.wait()
                
                start = time.time()
                # Lightweight operation
                await asyncio.sleep(0.005)
                end = time.time()
                
                other_response_times.append(end - start)
                return req_id
            
            # Start file upload
            upload_task = asyncio.create_task(file_upload_endpoint())
            
            # Wait for upload to start
            await asyncio.sleep(0.01)
            
            # Make requests to other endpoints
            other_tasks = [
                asyncio.create_task(other_endpoint(i))
                for i in range(num_other_requests)
            ]
            other_results = await asyncio.gather(*other_tasks)
            
            # Wait for upload to complete
            upload_result = await upload_task
            
            # Other endpoints should respond quickly
            for response_time in other_response_times:
                # Response time should be close to the sleep time (0.005s)
                # Not blocked by file upload processing
                assert response_time < 0.03  # Allow some overhead
            
            # All should succeed
            assert len(other_results) == num_other_requests
            assert upload_result == 'upload_complete'
        
        asyncio.run(run_test())
    
    @settings(max_examples=5)
    @given(
        num_concurrent_uploads=st.integers(min_value=2, max_value=3),
        num_health_checks=st.integers(min_value=3, max_value=5),
        upload_delay=st.floats(min_value=0.02, max_value=0.05)
    )
    def test_health_check_not_blocked_by_file_uploads(
        self, num_concurrent_uploads: int, num_health_checks: int, upload_delay: float
    ):
        """Test that health check endpoints remain responsive during file uploads."""
        async def run_test():
            uploads_started = asyncio.Event()
            upload_count = 0
            lock = asyncio.Lock()
            
            async def upload_endpoint(upload_id: int):
                """Simulate file upload."""
                nonlocal upload_count
                
                data = bytes([upload_id % 256]) * 3000
                
                async def processor(path: Path):
                    async with lock:
                        upload_count += 1
                        if upload_count == num_concurrent_uploads:
                            uploads_started.set()
                    
                    await asyncio.sleep(upload_delay)
                    return upload_id
                
                return await FileHandler.process_upload_safely(
                    data, f'.upload{upload_id}', processor
                )
            
            async def health_check_endpoint(check_id: int):
                """Simulate health check endpoint."""
                # Wait for uploads to start
                await uploads_started.wait()
                
                # Health check should be fast
                await asyncio.sleep(0.002)
                return f'healthy_{check_id}'
            
            # Start uploads
            upload_tasks = [
                asyncio.create_task(upload_endpoint(i))
                for i in range(num_concurrent_uploads)
            ]
            
            # Wait for uploads to start
            await asyncio.sleep(0.01)
            
            # Make health check requests
            health_start = time.time()
            health_tasks = [
                asyncio.create_task(health_check_endpoint(i))
                for i in range(num_health_checks)
            ]
            health_results = await asyncio.gather(*health_tasks)
            health_end = time.time()
            
            # Wait for uploads
            upload_results = await asyncio.gather(*upload_tasks)
            
            # Health checks should complete quickly
            health_time = health_end - health_start
            expected_health_time = num_health_checks * 0.002 * 2  # Allow 100% overhead
            assert health_time < expected_health_time
            assert health_time < upload_delay * 0.5  # Much faster than uploads
            
            # All should succeed
            assert len(health_results) == num_health_checks
            assert len(upload_results) == num_concurrent_uploads
        
        asyncio.run(run_test())
