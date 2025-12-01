# Implementation Plan

## Important: Virtual Environment

**All terminal commands and Python operations must be executed within the `.venv` virtual environment.**

Before running any commands, ensure the virtual environment is activated:
```bash
source .venv/bin/activate  # On Linux/Mac
# or
.venv\Scripts\activate  # On Windows
```

When executing tasks, always activate the virtual environment first before running any Python commands, pip installs, or pytest commands.

---

- [x] 1. Set up project structure and testing infrastructure
  - Create new directory structure: `app/core/`, `app/services/`, `app/validators/`, `app/models/`, `tests/`
  - Install testing dependencies: pytest, pytest-asyncio, hypothesis, pytest-cov, httpx, pytest-mock
  - Create pytest configuration file with coverage settings
  - Set up test fixtures directory with sample files
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [x] 2. Implement configuration system
  - Create `app/core/config.py` with Pydantic BaseSettings class
  - Add all configuration fields with types and defaults
  - Implement environment variable loading with python-dotenv
  - Add configuration validation method
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2.1 Write property test for environment variable override
  - **Property 1: Environment variable override consistency**
  - **Validates: Requirements 1.2**

- [x] 2.2 Write property test for configuration type safety
  - **Property 2: Configuration type safety**
  - **Validates: Requirements 1.3**

- [x] 2.3 Write property test for missing configuration errors
  - **Property 3: Missing configuration error clarity**
  - **Validates: Requirements 1.4**

- [x] 2.4 Write property test for configuration validation
  - **Property 4: Configuration validation completeness**
  - **Validates: Requirements 1.5**

- [x] 3. Implement structured logging system
  - Create `app/core/logging.py` with StructuredLogger class
  - Configure JSON formatter using python-json-logger
  - Add request ID generation and context management
  - Implement log level configuration
  - Add sensitive data redaction utility
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 3.5_

- [x] 3.1 Write property test for JSON log format
  - **Property 38: JSON log format**
  - **Validates: Requirements 12.1**

- [x] 3.2 Write property test for request log metadata
  - **Property 39: Request log metadata**
  - **Validates: Requirements 12.2**

- [x] 3.3 Write property test for error log structure
  - **Property 40: Error log structure**
  - **Validates: Requirements 12.3**

- [x] 3.4 Write property test for log entry metadata
  - **Property 41: Log entry metadata**
  - **Validates: Requirements 12.4**

- [x] 3.5 Write property test for sensitive data redaction
  - **Property 14: Sensitive data redaction**
  - **Validates: Requirements 3.5**

- [x] 4. Create error handling framework
  - Create `app/core/exceptions.py` with custom exception classes
  - Implement AppException, ValidationError, ExternalAPIError classes
  - Create `app/core/error_handlers.py` with FastAPI exception handlers
  - Add consistent error response formatting
  - Integrate with structured logging
  - _Requirements: 3.1, 3.2, 3.3, 3.4_

- [x] 4.1 Write property test for exception logging completeness
  - **Property 10: Exception logging completeness**
  - **Validates: Requirements 3.1**

- [x] 4.2 Write property test for error response format consistency
  - **Property 11: Error response format consistency**
  - **Validates: Requirements 3.2**

- [x] 4.3 Write property test for API error classification
  - **Property 12: API error classification accuracy**
  - **Validates: Requirements 3.3**

- [x] 4.4 Write property test for error log metadata
  - **Property 13: Error log metadata completeness**
  - **Validates: Requirements 3.4**

- [x] 5. Implement input validation layer
  - Create `app/validators/file_validator.py` with FileValidator class
  - Implement MIME type verification using python-magic or filetype library
  - Add streaming file size validation
  - Create `app/validators/text_validator.py` with TextValidator class
  - Implement text sanitization for injection prevention
  - Add detailed validation error messages
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 5.1 Write property test for image MIME type verification
  - **Property 5: Image MIME type verification**
  - **Validates: Requirements 2.1**

- [x] 5.2 Write property test for audio MIME type verification
  - **Property 6: Audio MIME type verification**
  - **Validates: Requirements 2.2**

- [x] 5.3 Write property test for text injection prevention
  - **Property 7: Text injection prevention**
  - **Validates: Requirements 2.3**

- [x] 5.4 Write property test for early file size rejection
  - **Property 8: Early file size rejection**
  - **Validates: Requirements 2.4**

- [x] 5.5 Write property test for invalid file type error detail
  - **Property 9: Invalid file type error detail**
  - **Validates: Requirements 2.5**

- [x] 6. Create Gemini client abstraction
  - Create `app/core/gemini_client.py` with GeminiClientProtocol
  - Implement GeminiClient class with retry logic
  - Add exponential backoff for retries
  - Implement rate limit handling with retry-after support
  - Create MockGeminiClient for testing
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 6.1 Write property test for API retry with exponential backoff
  - **Property 15: API retry with exponential backoff**
  - **Validates: Requirements 4.4**

- [x] 6.2 Write property test for rate limit retry behavior
  - **Property 16: Rate limit retry behavior**
  - **Validates: Requirements 4.5**

- [x] 7. Refactor Forge service with dependency injection
  - Create `app/services/forge_service.py` with ForgeService class
  - Accept GeminiClientProtocol, Config, and Logger in constructor
  - Move generate_idea, generate_steps, refine_idea methods
  - Add response validation and sanitization
  - Implement fallback error messages
  - _Requirements: 4.1, 4.2, 5.1, 5.2, 5.4, 5.5_

- [x] 7.1 Write property test for response content validation
  - **Property 17: Response content validation**
  - **Validates: Requirements 5.1**

- [x] 7.2 Write property test for response character sanitization
  - **Property 18: Response character sanitization**
  - **Validates: Requirements 5.4**

- [x] 7.3 Write property test for validation failure fallback
  - **Property 19: Validation failure fallback**
  - **Validates: Requirements 5.5**

- [x] 8. Implement file processing safety
  - Create `app/core/file_handler.py` with temporary file management
  - Implement automatic cleanup using context managers
  - Add streaming file processing to prevent memory exhaustion
  - Implement cleanup on failure using try-finally blocks
  - Add file metadata sanitization
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 8.1 Write property test for temporary file cleanup
  - **Property 20: Temporary file cleanup**
  - **Validates: Requirements 6.1**

- [x] 8.2 Write property test for streaming memory safety
  - **Property 21: Streaming memory safety**
  - **Validates: Requirements 6.2**

- [x] 8.3 Write property test for cleanup on processing failure
  - **Property 22: Cleanup on processing failure**
  - **Validates: Requirements 6.3**

- [x] 8.4 Write property test for concurrent upload isolation
  - **Property 23: Concurrent upload isolation**
  - **Validates: Requirements 6.4**

- [x] 8.5 Write property test for metadata sanitization
  - **Property 24: Metadata sanitization**
  - **Validates: Requirements 6.5**

- [x] 9. Create dependency injection container
  - Create `app/core/dependencies.py` with Dependencies class
  - Initialize all dependencies at application startup
  - Create FastAPI dependency functions using Depends()
  - Add support for dependency overrides in testing
  - _Requirements: 8.1, 8.2, 8.3, 8.4_

- [x] 9.1 Write property test for dependency injection consistency
  - **Property 25: Dependency injection consistency**
  - **Validates: Requirements 8.2**

- [x] 10. Implement Pydantic request/response models
  - Create `app/models/requests.py` with GenerateRequest, StepsRequest, RefineRequest
  - Create `app/models/responses.py` with response models
  - Add field validation and examples
  - Update endpoints to use Pydantic models
  - _Requirements: 2.3, 2.5_

- [x] 11. Refactor API endpoints to use new architecture
  - Update `app.py` to use dependency injection
  - Replace direct Forge instantiation with ForgeService injection
  - Use FileValidator for file uploads
  - Use TextValidator for text inputs
  - Apply error handlers to all endpoints
  - Add request ID middleware
  - _Requirements: 8.2, 2.1, 2.2, 2.3, 3.2_

- [x] 11.1 Write integration tests for /generate endpoint
  - Test successful generation with valid inputs
  - Test validation errors with invalid files
  - Test error handling with mocked API failures
  - _Requirements: 7.2_

- [x] 11.2 Write integration tests for /generate-steps endpoint
  - Test successful step generation
  - Test validation errors
  - _Requirements: 7.2_

- [x] 11.3 Write integration tests for /refine-idea endpoint
  - Test all refinement types
  - Test validation errors
  - _Requirements: 7.2_

- [x] 12. Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 13. Implement rate limiting middleware
  - Create `app/middleware/rate_limiter.py` with rate limiting logic
  - Track requests per IP address using in-memory store
  - Implement sliding window rate limiting
  - Add per-user rate limiting support
  - Return 429 with retry-after header when limits exceeded
  - Add rate limit window reset logic
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 13.1 Write property test for request tracking per IP
  - **Property 26: Request tracking per IP**
  - **Validates: Requirements 9.1**

- [x] 13.2 Write property test for rate limit response format
  - **Property 27: Rate limit response format**
  - **Validates: Requirements 9.2**

- [x] 13.3 Write property test for rate limit window reset
  - **Property 28: Rate limit window reset**
  - **Validates: Requirements 9.3**

- [x] 13.4 Write property test for per-user rate limiting
  - **Property 29: Per-user rate limiting**
  - **Validates: Requirements 9.4**

- [x] 13.5 Write property test for rate limit configuration compliance
  - **Property 30: Rate limit configuration compliance**
  - **Validates: Requirements 9.5**

- [x] 14. Enhance health check endpoint
  - Update `/health` endpoint to check Gemini API accessibility
  - Add dependency health checks
  - Return 503 for unhealthy dependencies with details
  - Add component status details to response
  - Implement timeout for health checks
  - _Requirements: 10.1, 10.2, 10.3, 10.4_

- [x] 14.1 Write property test for unhealthy dependency response
  - **Property 31: Unhealthy dependency response**
  - **Validates: Requirements 10.2**

- [x] 15. Implement metrics collection
  - Create `app/core/metrics.py` with metrics tracking
  - Track request counts, error rates, and latency
  - Add `/metrics` endpoint to expose metrics
  - Implement Prometheus-compatible format (optional)
  - _Requirements: 10.5_

- [x] 15.1 Write property test for metrics exposure completeness
  - **Property 32: Metrics exposure completeness**
  - **Validates: Requirements 10.5**

- [-] 16. Optimize async file processing
  - Ensure all file operations use async I/O
  - Implement concurrency limits for file processing
  - Add endpoint isolation to prevent blocking
  - Verify streaming for large files
  - Ensure resource cleanup on completion
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 16.1 Write property test for async non-blocking behavior
  - **Property 33: Async file processing non-blocking**
  - **Validates: Requirements 11.1**

- [ ] 16.2 Write property test for concurrency limit enforcement
  - **Property 34: Concurrency limit enforcement**
  - **Validates: Requirements 11.2**

- [ ] 16.3 Write property test for endpoint isolation
  - **Property 35: Endpoint isolation**
  - **Validates: Requirements 11.3**

- [ ] 16.4 Write property test for large file streaming
  - **Property 36: Large file streaming**
  - **Validates: Requirements 11.4**

- [ ] 16.5 Write property test for resource release
  - **Property 37: Resource release on completion**
  - **Validates: Requirements 11.5**

- [x] 17. Update requirements.txt with new dependencies
  - Add pydantic[dotenv] for configuration
  - Add python-json-logger for structured logging
  - Add python-magic or filetype for MIME verification
  - Add pytest, pytest-asyncio, hypothesis, pytest-cov for testing
  - Add httpx for test client
  - Pin all dependency versions
  - _Requirements: 1.1, 3.1, 2.1_

- [ ] 18. Create comprehensive test suite
  - Organize tests by component in tests/ directory
  - Create test fixtures for sample files
  - Set up Hypothesis profiles for CI and development
  - Configure pytest for coverage reporting
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ] 19. Final checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 20. Update documentation
  - Update README.md with new architecture details
  - Document configuration options
  - Add testing instructions
  - Document error response formats
  - Add deployment considerations
  - _Requirements: All_
