from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.models import (
    GenerateRequest,
    StepsRequest,
    RefineRequest,
    GenerateResponse,
    StepsResponse,
    RefineResponse,
    ErrorResponse,
    HealthResponse,
    StatsResponse,
    MetricsResponse
)
from app.core.dependencies import (
    initialize_dependencies,
    get_forge_service,
    get_config,
    get_logger,
    get_gemini_client
)
from app.core.config import Config
from app.core.logging import StructuredLogger
from app.services.forge_service import ForgeService
from app.core.gemini_client import GeminiClientProtocol
from google.genai import types
from app.validators.file_validator import FileValidator
from app.validators.text_validator import TextValidator
from app.core.error_handlers import setup_error_handlers
from app.core.exceptions import ValidationError
from app.core.metrics import get_metrics_collector
import os
from dotenv import load_dotenv
import uuid
import time

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application dependencies on startup"""
    deps = initialize_dependencies()
    logger = deps.get_logger()
    logger.info("Application starting up", version="1.0.0")
    
    # Setup error handlers
    setup_error_handlers(app, logger)
    
    yield
    
    # Cleanup on shutdown (if needed)
    logger.info("Application shutting down")

app = FastAPI(
    title="Frankenstein's Forge API",
    description="Multimodal AI API that processes images, audio, and text to generate creative ideas",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this based on your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID and metrics middleware
@app.middleware("http")
async def add_request_id_and_metrics(request: Request, call_next):
    """Add unique request ID to each request for tracing and collect metrics"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Record start time for latency tracking
    start_time = time.time()
    
    # Process request
    response = await call_next(request)
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    
    # Record metrics
    metrics_collector = get_metrics_collector()
    error_msg = None
    if response.status_code >= 400:
        error_msg = f"HTTP {response.status_code}"
    
    metrics_collector.record_request(
        endpoint=request.url.path,
        method=request.method,
        status_code=response.status_code,
        latency_ms=latency_ms,
        error=error_msg
    )
    
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/")
async def root():
    """Serve the main website"""
    return FileResponse("static/index.html")

@app.get("/health", response_model=HealthResponse)
async def health(
    config: Config = Depends(get_config),
    gemini_client: GeminiClientProtocol = Depends(get_gemini_client),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Health check endpoint with dependency verification.
    
    Checks:
    - API availability
    - Gemini API accessibility
    - Configuration validity
    
    Returns 200 if healthy, 503 if any dependency is unhealthy.
    """
    import asyncio
    from datetime import datetime
    
    dependencies = {}
    overall_status = "healthy"
    
    # Check Gemini API accessibility with timeout
    async def check_gemini_api():
        """Check if Gemini API is accessible"""
        try:
            # Use a simple test call with timeout
            loop = asyncio.get_event_loop()
            
            def test_api():
                # Try to generate minimal content as a health check
                try:
                    gemini_client.generate_content(
                        model=config.ai_model,
                        contents=["test"],
                        config=types.GenerateContentConfig(
                            max_output_tokens=10
                        )
                    )
                    return True
                except Exception as e:
                    logger.error("Gemini API health check failed", error=str(e))
                    return False
            
            # Run with 5 second timeout
            result = await asyncio.wait_for(
                loop.run_in_executor(None, test_api),
                timeout=5.0
            )
            
            if result:
                return {"status": "accessible", "message": "API responding normally"}
            else:
                return {"status": "error", "message": "API call failed"}
                
        except asyncio.TimeoutError:
            logger.error("Gemini API health check timed out")
            return {"status": "timeout", "message": "Health check timed out after 5 seconds"}
        except Exception as e:
            logger.error("Gemini API health check error", error=str(e))
            return {"status": "error", "message": str(e)}
    
    # Perform health checks
    try:
        gemini_status = await check_gemini_api()
        dependencies["gemini_api"] = gemini_status
        
        # Mark as unhealthy if Gemini API is not accessible
        if gemini_status["status"] != "accessible":
            overall_status = "unhealthy"
        
        # Add configuration status
        dependencies["configuration"] = {
            "status": "loaded",
            "model": config.ai_model
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        overall_status = "unhealthy"
        dependencies["error"] = str(e)
    
    # Return appropriate status code
    status_code = 200 if overall_status == "healthy" else 503
    
    response = HealthResponse(
        status=overall_status,
        version="1.0.0",
        dependencies=dependencies,
        timestamp=datetime.utcnow().isoformat()
    )
    
    if status_code == 503:
        return JSONResponse(
            status_code=503,
            content=response.model_dump()
        )
    
    return response

@app.post("/generate", response_model=GenerateResponse)
async def generate_idea(
    request: Request,
    image: UploadFile = File(..., description="Image file (JPEG, PNG)"),
    audio: UploadFile = File(..., description="Audio file (WAV, MP3)"),
    text: str = Form(..., description="User text input"),
    forge_service: ForgeService = Depends(get_forge_service),
    config: Config = Depends(get_config),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Generate a creative idea from image, audio, and text inputs.
    
    - **image**: Upload an image file
    - **audio**: Upload an audio file
    - **text**: Provide text description
    
    Returns a creative, achievable idea based on all inputs.
    """
    request_id = request.state.request_id
    
    logger.info(
        "Processing generate request",
        request_id=request_id,
        image_filename=image.filename,
        audio_filename=audio.filename,
        text_length=len(text)
    )
    
    # Validate and sanitize text input
    validated_text = TextValidator.sanitize(text, max_length=5000)
    
    # Validate text using Pydantic model
    try:
        text_request = GenerateRequest(text=validated_text)
        validated_text = text_request.text
    except Exception as e:
        # Convert Pydantic validation errors to our custom ValidationError
        raise ValidationError(
            "Text validation failed",
            details={"error": str(e)}
        )
    
    # Validate image file
    image_bytes = FileValidator.validate_image(image, config.max_image_size)
    
    # Validate audio file
    audio_bytes = FileValidator.validate_audio(audio, config.max_audio_size)
    
    # Generate idea using ForgeService
    result = forge_service.generate_idea(image_bytes, audio_bytes, validated_text)
    
    logger.info(
        "Successfully generated idea",
        request_id=request_id,
        response_length=len(result)
    )
    
    return GenerateResponse(
        success=True,
        idea=result,
        inputs={
            "text": validated_text,
            "image_filename": image.filename,
            "audio_filename": audio.filename
        },
        request_id=request_id
    )

@app.post("/generate-simple")
async def generate_idea_simple(
    request: Request,
    image: UploadFile = File(...),
    audio: UploadFile = File(...),
    text: str = Form(...),
    forge_service: ForgeService = Depends(get_forge_service),
    config: Config = Depends(get_config),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Simplified endpoint that returns just the generated idea text.
    """
    request_id = request.state.request_id
    
    logger.info(
        "Processing generate-simple request",
        request_id=request_id
    )
    
    # Validate and sanitize text input
    validated_text = TextValidator.sanitize(text, max_length=5000)
    
    # Validate image file
    image_bytes = FileValidator.validate_image(image, config.max_image_size)
    
    # Validate audio file
    audio_bytes = FileValidator.validate_audio(audio, config.max_audio_size)
    
    # Generate idea using ForgeService
    result = forge_service.generate_idea(image_bytes, audio_bytes, validated_text)
    
    return {"idea": result}

@app.post("/generate-steps", response_model=StepsResponse)
async def generate_steps(
    request: Request,
    request_body: StepsRequest,
    forge_service: ForgeService = Depends(get_forge_service),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Generate implementation steps for a given idea.
    """
    request_id = request.state.request_id
    
    logger.info(
        "Processing generate-steps request",
        request_id=request_id,
        idea_length=len(request_body.idea)
    )
    
    # Validate and sanitize idea text
    validated_idea = TextValidator.sanitize(request_body.idea, max_length=2000)
    
    # Generate steps using ForgeService
    steps = forge_service.generate_steps(validated_idea)
    
    logger.info(
        "Successfully generated steps",
        request_id=request_id,
        steps_length=len(steps)
    )
    
    return StepsResponse(
        success=True,
        steps=steps,
        request_id=request_id
    )

@app.post("/refine-idea", response_model=RefineResponse)
async def refine_idea(
    request: Request,
    request_body: RefineRequest,
    forge_service: ForgeService = Depends(get_forge_service),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Refine or create variations of an existing idea.
    """
    request_id = request.state.request_id
    
    logger.info(
        "Processing refine-idea request",
        request_id=request_id,
        idea_length=len(request_body.idea),
        refinement_type=request_body.type
    )
    
    # Validate and sanitize idea text
    validated_idea = TextValidator.sanitize(request_body.idea, max_length=2000)
    
    # Refine idea using ForgeService
    refined = forge_service.refine_idea(validated_idea, request_body.type)
    
    logger.info(
        "Successfully refined idea",
        request_id=request_id,
        refined_length=len(refined),
        refinement_type=request_body.type
    )
    
    return RefineResponse(
        success=True,
        refined_idea=refined,
        request_id=request_id
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get API usage statistics (for future analytics).
    """
    return StatsResponse(
        success=True,
        stats={
            "version": "1.0.0",
            "model": "gemini-2.0-flash-exp",
            "features": [
                "multimodal_generation",
                "step_generation",
                "idea_refinement",
                "history_tracking"
            ]
        }
    )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """
    Get API metrics including request counts, error rates, and latency percentiles.
    
    Returns:
    - Total request count
    - Total error count
    - Overall error rate
    - Latency percentiles (p50, p90, p95, p99, mean, min, max)
    - Per-endpoint metrics with request counts, error rates, and latency
    """
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()
    
    return MetricsResponse(**metrics_data)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )