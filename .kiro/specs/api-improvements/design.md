# Design Document

## Overview

This design document outlines the architectural improvements for Frankenstein's Forge API to achieve production readiness. The improvements focus on configuration management, input validation, error handling, dependency injection, testing infrastructure, and operational monitoring. The design maintains backward compatibility while introducing robust patterns for scalability and maintainability.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        FastAPI Application                   │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │   Endpoints  │  │  Middleware  │  │ Dependencies │     │
│  │   (Routes)   │  │   (CORS,     │  │  (Injection) │     │
│  │              │  │   Logging)   │  │              │     │
│  └──────┬───────┘  └──────────────┘  └──────┬───────┘     │
│         │                                     │              │
│         └─────────────────┬───────────────────┘              │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐   │
│  │           Service Layer (Business Logic)            │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐ │   │
│  │  │ ForgeService │  │  Validators  │  │  Config  │ │   │
│  │  └──────┬───────┘  └──────────────┘  └──────────┘ │   │
│  └─────────┼─────────────────────────────────────────┘   │
│            │                                               │
│            ▼                                               │
│  ┌─────────────────────────────────────────────────────┐  │
│  │         Infrastructure Layer                         │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────┐  │  │
│  │  │ GeminiClient │  │ FileHandler  │  │  Logger  │  │  │
│  │  └──────────────┘  └──────────────┘  └──────────┘  │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Layer Responsibilities

**Presentation Layer (FastAPI Endpoints)**
- HTTP request/response handling
- Request validation using Pydantic models
- Dependency injection coordination
- Response formatting

**Service Layer**
- Business logic implementation
- Orchestration of infrastructure components
- Input validation and sanitization
- Response transformation

**Infrastructure Layer**
- External API communication (Gemini)
- File system operations
- Logging and monitoring
- Configuration management

## Components and Interfaces

### 1. Configuration System

**Purpose**: Centralized, type-safe configuration management with environment variable support.

**Interface**:
```python
class Config:
    """Application configuration with validation"""
    
    # API Settings
    api_title: str
    api_version: str
    host: str
    port: int
    
    # File Upload Limits
    max_image_size: int
    max_audio_size: int
    
    # AI Model Settings
    google_api_key: str
    ai_model: str
    
    # Feature Flags
    enable_rate_limiting: bool
    enable_structured_logging: bool
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables"""
        pass
    
    def validate(self) -> None:
        """Validate all configuration values"""
        pass
```

**Implementation Notes**:
- Use Pydantic BaseSettings for automatic environment variable loading
- Support .env file loading via python-dotenv
- Validate required fields at startup
- Provide sensible defaults for optional settings

### 2. Input Validation Layer

**Purpose**: Validate and sanitize all user inputs before processing.

**Interface**:
```python
class FileValidator:
    """Validates uploaded files"""
    
    @staticmethod
    def validate_image(file: UploadFile, max_size: int) -> bytes:
        """Validate image file and return bytes"""
        pass
    
    @staticmethod
    def validate_audio(file: UploadFile, max_size: int) -> bytes:
        """Validate audio file and return bytes"""
        pass
    
    @staticmethod
    def verify_mime_type(file_bytes: bytes, expected_type: str) -> bool:
        """Verify file signature matches MIME type"""
        pass

class TextValidator:
    """Validates and sanitizes text input"""
    
    @staticmethod
    def sanitize(text: str, max_length: int = 5000) -> str:
        """Sanitize text input"""
        pass
    
    @staticmethod
    def validate_length(text: str, min_len: int, max_len: int) -> bool:
        """Validate text length"""
        pass
```

**Implementation Notes**:
- Use python-magic or filetype library for MIME type verification
- Implement streaming validation to avoid loading entire files into memory
- Sanitize text to prevent injection attacks
- Return detailed validation error messages

### 3. Gemini Client Abstraction

**Purpose**: Abstract Gemini API interactions for testability and error handling.

**Interface**:
```python
class GeminiClientProtocol(Protocol):
    """Protocol for Gemini API clients"""
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate content from multimodal inputs"""
        pass

class GeminiClient:
    """Production Gemini API client with retry logic"""
    
    def __init__(self, api_key: str, max_retries: int = 3):
        self.api_key = api_key
        self.max_retries = max_retries
        self._client = genai.Client(api_key=api_key)
    
    def generate_content(
        self,
        model: str,
        contents: list,
        **kwargs
    ) -> str:
        """Generate content with retry logic"""
        pass
    
    def _retry_with_backoff(self, func, *args, **kwargs):
        """Retry with exponential backoff"""
        pass

class MockGeminiClient:
    """Mock client for testing"""
    
    def generate_content(self, model: str, contents: list, **kwargs) -> str:
        return "Mock generated content"
```

**Implementation Notes**:
- Use Protocol for type checking without inheritance
- Implement exponential backoff for retries
- Handle rate limiting with appropriate delays
- Log all API interactions for debugging

### 4. Forge Service

**Purpose**: Core business logic for idea generation with proper dependency injection.

**Interface**:
```python
class ForgeService:
    """Service for AI-powered idea generation"""
    
    def __init__(
        self,
        client: GeminiClientProtocol,
        config: Config,
        logger: logging.Logger
    ):
        self.client = client
        self.config = config
        self.logger = logger
    
    def generate_idea(
        self,
        image_bytes: bytes,
        audio_bytes: bytes,
        text: str
    ) -> str:
        """Generate idea from multimodal inputs"""
        pass
    
    def generate_steps(self, idea: str) -> str:
        """Generate implementation steps"""
        pass
    
    def refine_idea(self, idea: str, refinement_type: str) -> str:
        """Refine or vary an idea"""
        pass
    
    def _validate_response(self, response: str) -> str:
        """Validate and sanitize AI response"""
        pass
```

**Implementation Notes**:
- Accept dependencies through constructor
- Validate all inputs before API calls
- Validate all outputs before returning
- Log all operations with context

### 5. Error Handling System

**Purpose**: Centralized error handling with structured logging.

**Interface**:
```python
class AppException(Exception):
    """Base exception for application errors"""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)

class ValidationError(AppException):
    """Raised when input validation fails"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=400, details=details)

class ExternalAPIError(AppException):
    """Raised when external API calls fail"""
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, status_code=502, details=details)

def create_error_handler(app: FastAPI):
    """Register error handlers with FastAPI"""
    
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "details": exc.details,
                "request_id": request.state.request_id
            }
        )
```

**Implementation Notes**:
- Create exception hierarchy for different error types
- Include request context in all error responses
- Log errors with full stack traces
- Redact sensitive information from error messages

### 6. Structured Logging

**Purpose**: JSON-formatted logging for easy parsing and analysis.

**Interface**:
```python
class StructuredLogger:
    """Structured JSON logger"""
    
    def __init__(self, name: str, level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self._configure(level)
    
    def info(self, message: str, **kwargs):
        """Log info with structured data"""
        pass
    
    def error(self, message: str, exc_info=None, **kwargs):
        """Log error with structured data"""
        pass
    
    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """Format log as JSON"""
        pass

def setup_logging(config: Config) -> StructuredLogger:
    """Setup application logging"""
    pass
```

**Implementation Notes**:
- Use python-json-logger for JSON formatting
- Include request ID in all logs
- Add correlation IDs for tracing
- Support log level configuration

### 7. Dependency Injection Container

**Purpose**: Centralized dependency management for the application.

**Interface**:
```python
class Dependencies:
    """Application dependencies container"""
    
    def __init__(self):
        self.config = Config.from_env()
        self.logger = setup_logging(self.config)
        self.gemini_client = GeminiClient(
            api_key=self.config.google_api_key,
            max_retries=3
        )
        self.forge_service = ForgeService(
            client=self.gemini_client,
            config=self.config,
            logger=self.logger
        )
    
    def get_forge_service(self) -> ForgeService:
        """Get ForgeService instance"""
        return self.forge_service
    
    def get_config(self) -> Config:
        """Get Config instance"""
        return self.config

# FastAPI dependency functions
def get_dependencies() -> Dependencies:
    """Get application dependencies"""
    return app.state.dependencies

def get_forge_service(deps: Dependencies = Depends(get_dependencies)) -> ForgeService:
    """Inject ForgeService"""
    return deps.get_forge_service()
```

**Implementation Notes**:
- Initialize all dependencies at startup
- Use FastAPI's Depends for injection
- Support dependency overrides for testing
- Implement singleton pattern for shared resources

## Data Models

### Request Models

```python
class GenerateRequest(BaseModel):
    """Request model for idea generation"""
    text: str = Field(..., min_length=1, max_length=5000)
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "I want to build something creative"
            }
        }

class StepsRequest(BaseModel):
    """Request model for step generation"""
    idea: str = Field(..., min_length=1, max_length=2000)

class RefineRequest(BaseModel):
    """Request model for idea refinement"""
    idea: str = Field(..., min_length=1, max_length=2000)
    type: str = Field(default="variation", pattern="^(variation|simpler|more_ambitious)$")
```

### Response Models

```python
class GenerateResponse(BaseModel):
    """Response model for idea generation"""
    success: bool
    idea: str
    inputs: dict
    request_id: str

class StepsResponse(BaseModel):
    """Response model for step generation"""
    success: bool
    steps: str
    request_id: str

class ErrorResponse(BaseModel):
    """Response model for errors"""
    success: bool = False
    error: str
    details: dict = {}
    request_id: str

class HealthResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    dependencies: dict
    timestamp: str
```

## Correctnes
s Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


Property 1: Environment variable override consistency
*For any* configuration key that exists in both file and environment variables, the environment variable value should always take precedence
**Validates: Requirements 1.2**

Property 2: Configuration type safety
*For any* configuration value accessed, the returned value should match the declared type in the configuration schema
**Validates: Requirements 1.3**

Property 3: Missing configuration error clarity
*For any* required configuration field that is missing, the system should raise an error message that explicitly names the missing field
**Validates: Requirements 1.4**

Property 4: Configuration validation completeness
*For any* invalid configuration value, validation at startup should detect and report the invalidity before the application starts processing requests
**Validates: Requirements 1.5**

Property 5: Image MIME type verification
*For any* uploaded file claiming to be an image, if the file signature does not match the declared MIME type, the validation should reject the file
**Validates: Requirements 2.1**

Property 6: Audio MIME type verification
*For any* uploaded file claiming to be audio, if the file signature does not match the declared MIME type, the validation should reject the file
**Validates: Requirements 2.2**

Property 7: Text injection prevention
*For any* text input containing injection payloads (SQL, XSS, command injection patterns), the sanitization should neutralize the malicious content
**Validates: Requirements 2.3**

Property 8: Early file size rejection
*For any* file upload exceeding the configured size limit, the rejection should occur before the entire file is read into memory
**Validates: Requirements 2.4**

Property 9: Invalid file type error detail
*For any* invalid file type upload, the error response should include specific details about why the file was rejected and what types are allowed
**Validates: Requirements 2.5**

Property 10: Exception logging completeness
*For any* exception that occurs during request processing, the logged entry should include the full stack trace and request context
**Validates: Requirements 3.1**

Property 11: Error response format consistency
*For any* error that occurs in the API, the response should follow a consistent structure with success=false, error message, and request ID
**Validates: Requirements 3.2**

Property 12: API error classification accuracy
*For any* Gemini API failure, the error handler should correctly classify it as either a client error (4xx) or server error (5xx) based on the response
**Validates: Requirements 3.3**

Property 13: Error log metadata completeness
*For any* error that is logged, the log entry should contain request ID, timestamp, and available user context
**Validates: Requirements 3.4**

Property 14: Sensitive data redaction
*For any* log entry containing API keys or personal identifiable information, the sensitive data should be redacted before writing to logs
**Validates: Requirements 3.5**

Property 15: API retry with exponential backoff
*For any* API call that fails with a retryable error, the system should retry up to 3 times with exponentially increasing delays between attempts
**Validates: Requirements 4.4**

Property 16: Rate limit retry behavior
*For any* API response indicating rate limit exceeded, the system should wait according to the retry-after header before retrying
**Validates: Requirements 4.5**

Property 17: Response content validation
*For any* response from the Gemini API, the validation should verify that the response contains non-empty text content
**Validates: Requirements 5.1**

Property 18: Response character sanitization
*For any* response containing invalid or dangerous characters, the sanitization should remove or escape those characters
**Validates: Requirements 5.4**

Property 19: Validation failure fallback
*For any* response that fails validation, the system should provide a user-friendly fallback error message instead of exposing internal errors
**Validates: Requirements 5.5**

Property 20: Temporary file cleanup
*For any* file upload, all temporary files created during processing should be automatically deleted after processing completes or fails
**Validates: Requirements 6.1**

Property 21: Streaming memory safety
*For any* file being read, the system should use streaming to prevent loading the entire file into memory at once
**Validates: Requirements 6.2**

Property 22: Cleanup on processing failure
*For any* file processing operation that fails, all temporary files associated with that operation should be deleted
**Validates: Requirements 6.3**

Property 23: Concurrent upload isolation
*For any* set of concurrent file uploads, each upload should be processed in isolation without interfering with others
**Validates: Requirements 6.4**

Property 24: Metadata sanitization
*For any* file metadata extracted during processing, all metadata fields should be sanitized to remove potentially malicious content
**Validates: Requirements 6.5**

Property 25: Dependency injection consistency
*For any* API endpoint, dependencies should be injected through FastAPI's dependency system rather than being created within the endpoint
**Validates: Requirements 8.2**

Property 26: Request tracking per IP
*For any* request received, the system should increment the request count for the source IP address
**Validates: Requirements 9.1**

Property 27: Rate limit response format
*For any* request that exceeds rate limits, the response should have status code 429 and include a retry-after header
**Validates: Requirements 9.2**

Property 28: Rate limit window reset
*For any* client that was previously rate limited, once the rate limit window expires, new requests should be allowed
**Validates: Requirements 9.3**

Property 29: Per-user rate limiting
*For any* authenticated user, rate limits should be tracked and enforced separately from other users
**Validates: Requirements 9.4**

Property 30: Rate limit configuration compliance
*For any* configured rate limit setting, the system should enforce exactly that limit and time window
**Validates: Requirements 9.5**

Property 31: Unhealthy dependency response
*For any* dependency that is unhealthy during a health check, the response should have status 503 and include specific details about which dependency failed
**Validates: Requirements 10.2**

Property 32: Metrics exposure completeness
*For any* request processed, the metrics system should track and expose request count, error rate, and latency
**Validates: Requirements 10.5**

Property 33: Async file processing non-blocking
*For any* file upload being processed, other concurrent requests should not be blocked or delayed
**Validates: Requirements 11.1**

Property 34: Concurrency limit enforcement
*For any* burst of concurrent requests exceeding the configured limit, the system should queue or reject excess requests rather than processing all simultaneously
**Validates: Requirements 11.2**

Property 35: Endpoint isolation
*For any* slow file processing operation, other API endpoints should remain responsive and not be blocked
**Validates: Requirements 11.3**

Property 36: Large file streaming
*For any* file larger than a threshold size, the system should use streaming rather than loading the entire file into memory
**Validates: Requirements 11.4**

Property 37: Resource release on completion
*For any* request that completes processing, all associated resources (file handles, memory buffers, connections) should be released immediately
**Validates: Requirements 11.5**

Property 38: JSON log format
*For any* log entry written, the output should be valid JSON with structured fields
**Validates: Requirements 12.1**

Property 39: Request log metadata
*For any* request processed, the log should include request ID, HTTP method, path, and processing duration
**Validates: Requirements 12.2**

Property 40: Error log structure
*For any* error logged, the entry should include error type, message, and stack trace as separate structured fields
**Validates: Requirements 12.3**

Property 41: Log entry metadata
*For any* log entry, it should include timestamp, log level, and source location information
**Validates: Requirements 12.4**

## Error Handling

### Error Categories

**Validation Errors (400)**
- Invalid file types or sizes
- Malformed request data
- Missing required fields
- Text input exceeding limits

**Authentication Errors (401)**
- Missing or invalid API keys (future)
- Expired tokens (future)

**Rate Limiting Errors (429)**
- Too many requests from IP
- Per-user quota exceeded

**External Service Errors (502)**
- Gemini API failures
- Network timeouts
- Service unavailable

**Internal Errors (500)**
- Unexpected exceptions
- Configuration errors
- Resource exhaustion

### Error Response Format

All errors follow a consistent structure:

```json
{
  "success": false,
  "error": "Human-readable error message",
  "details": {
    "field": "specific_field",
    "reason": "detailed_reason"
  },
  "request_id": "uuid-v4-string",
  "timestamp": "ISO-8601-timestamp"
}
```

### Retry Strategy

**Retryable Errors**:
- Network timeouts (503, 504)
- Rate limits (429)
- Temporary service unavailability (503)

**Non-Retryable Errors**:
- Validation failures (400)
- Authentication failures (401)
- Permanent failures (404, 410)

**Backoff Strategy**:
- Attempt 1: Immediate
- Attempt 2: 1 second delay
- Attempt 3: 2 seconds delay
- Attempt 4: 4 seconds delay (if configured)

## Testing Strategy

### Unit Testing

Unit tests verify individual components in isolation:

**Configuration System**
- Test environment variable loading
- Test validation logic
- Test default value handling
- Test error messages for missing config

**Validators**
- Test MIME type verification with various file types
- Test text sanitization with injection payloads
- Test file size validation
- Test error message generation

**Forge Service**
- Test with mocked Gemini client
- Test input validation
- Test response validation
- Test error handling

**Error Handlers**
- Test exception to response conversion
- Test sensitive data redaction
- Test error logging

### Property-Based Testing

Property-based tests verify universal properties across many generated inputs using the Hypothesis library for Python:

**Configuration Properties**
- Generate random config keys and verify environment override behavior
- Generate invalid config values and verify validation catches them
- Generate missing required fields and verify error messages

**Validation Properties**
- Generate files with mismatched MIME types and verify rejection
- Generate various injection payloads and verify sanitization
- Generate files of various sizes and verify size limit enforcement

**Error Handling Properties**
- Generate various exceptions and verify logging includes stack traces
- Generate various errors and verify response format consistency
- Generate log entries with sensitive data and verify redaction

**Retry Logic Properties**
- Generate various API failures and verify retry count and backoff timing
- Generate rate limit responses and verify proper waiting behavior

**File Processing Properties**
- Generate concurrent uploads and verify isolation
- Generate large files and verify streaming behavior
- Generate processing failures and verify cleanup

**Rate Limiting Properties**
- Generate request bursts and verify rate limit enforcement
- Generate requests over time and verify window reset behavior

### Integration Testing

Integration tests verify component interactions:

**API Endpoint Tests**
- Test full request/response cycle with test client
- Test file upload handling
- Test error responses
- Test dependency injection

**Health Check Tests**
- Test with healthy dependencies
- Test with unhealthy Gemini API
- Test response format and timing

**End-to-End Tests**
- Test complete idea generation flow
- Test steps generation flow
- Test refinement flow
- Test with real (or realistic mock) multimodal inputs

### Test Configuration

**Property-Based Testing Setup**:
```python
from hypothesis import given, strategies as st, settings

# Configure Hypothesis
settings.register_profile("ci", max_examples=100, deadline=5000)
settings.register_profile("dev", max_examples=20, deadline=None)
settings.load_profile("dev")  # or "ci" in CI environment
```

**Test Fixtures**:
- Sample image files (JPEG, PNG)
- Sample audio files (WAV, MP3)
- Mock Gemini API responses
- Test configuration files

**Coverage Goals**:
- Minimum 80% code coverage
- 100% coverage for critical paths (validation, error handling)
- Property tests should run minimum 100 iterations each

### Testing Tools

- **pytest**: Test framework
- **pytest-asyncio**: Async test support
- **hypothesis**: Property-based testing library
- **pytest-cov**: Coverage reporting
- **httpx**: Test client for FastAPI
- **pytest-mock**: Mocking utilities

## Implementation Notes

### Phase 1: Foundation
1. Set up configuration system with Pydantic
2. Implement structured logging
3. Create error handling framework
4. Set up testing infrastructure

### Phase 2: Core Improvements
1. Implement input validators
2. Refactor Forge with dependency injection
3. Add Gemini client abstraction
4. Implement retry logic

### Phase 3: Operational Features
1. Add rate limiting
2. Enhance health checks
3. Implement metrics collection
4. Add request tracing

### Phase 4: Testing & Documentation
1. Write unit tests for all components
2. Write property-based tests
3. Write integration tests
4. Update API documentation

### Migration Strategy

The improvements should be implemented incrementally without breaking existing functionality:

1. Add new components alongside existing code
2. Gradually migrate endpoints to use new components
3. Maintain backward compatibility during transition
4. Remove old code only after full migration and testing

### Performance Considerations

- Use async/await throughout for non-blocking I/O
- Implement connection pooling for Gemini API
- Use streaming for large file processing
- Cache configuration after initial load
- Minimize memory allocations in hot paths

### Security Considerations

- Validate all inputs before processing
- Sanitize all outputs before returning
- Redact sensitive data from logs
- Use secure temporary file handling
- Implement rate limiting to prevent abuse
- Add request size limits
- Validate file signatures, not just extensions
