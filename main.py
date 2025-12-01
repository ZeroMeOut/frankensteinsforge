from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.models import (
    GenerateRequest,
    RefineRequest,
    GenerateResponse,
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
from app.services.graph_service import GraphProcessor
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
import json
from typing import List

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize application dependencies on startup"""
    deps = initialize_dependencies()
    logger = deps.get_logger()
    logger.info("Application starting up", version="1.1.0")
    
    # Setup error handlers
    setup_error_handlers(app, logger)
    
    yield
    
    # Cleanup on shutdown (if needed)
    logger.info("Application shutting down")

app = FastAPI(
    title="Frankenstein's Forge API",
    description="Multimodal AI API with node graph system for weighted multi-modal fusion",
    version="1.1.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    
    start_time = time.time()
    response = await call_next(request)
    latency_ms = (time.time() - start_time) * 1000
    
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
    """Serve the node-based graph interface"""
    return FileResponse("static/index-nodes.html")

@app.get("/classic")
async def classic():
    """Serve the classic form-based interface"""
    return FileResponse("static/index.html")

@app.get("/health", response_model=HealthResponse)
async def health(
    config: Config = Depends(get_config),
    gemini_client: GeminiClientProtocol = Depends(get_gemini_client),
    logger: StructuredLogger = Depends(get_logger)
):
    """Health check endpoint with dependency verification."""
    import asyncio
    from datetime import datetime
    
    dependencies = {}
    overall_status = "healthy"
    
    async def check_gemini_api():
        try:
            loop = asyncio.get_event_loop()
            
            def test_api():
                try:
                    gemini_client.generate_content(
                        model=config.ai_model,
                        contents=["test"],
                        config=types.GenerateContentConfig(max_output_tokens=10)
                    )
                    return True
                except Exception as e:
                    logger.error("Gemini API health check failed", error=str(e))
                    return False
            
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
    
    try:
        gemini_status = await check_gemini_api()
        dependencies["gemini_api"] = gemini_status
        
        if gemini_status["status"] != "accessible":
            overall_status = "unhealthy"
        
        dependencies["configuration"] = {
            "status": "loaded",
            "model": config.ai_model
        }
        
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        overall_status = "unhealthy"
        dependencies["error"] = str(e)
    
    status_code = 200 if overall_status == "healthy" else 503
    
    response = HealthResponse(
        status=overall_status,
        version="1.1.0",
        dependencies=dependencies,
        timestamp=datetime.utcnow().isoformat()
    )
    
    if status_code == 503:
        return JSONResponse(status_code=503, content=response.model_dump())
    
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
    """Generate a creative idea from image, audio, and text inputs (legacy endpoint)."""
    request_id = request.state.request_id
    
    logger.info(
        "Processing generate request (classic)",
        request_id=request_id,
        image_filename=image.filename,
        audio_filename=audio.filename,
        text_length=len(text)
    )
    
    validated_text = TextValidator.sanitize(text, max_length=5000)
    
    try:
        text_request = GenerateRequest(text=validated_text)
        validated_text = text_request.text
    except Exception as e:
        raise ValidationError("Text validation failed", details={"error": str(e)})
    
    image_bytes = FileValidator.validate_image(image, config.max_image_size)
    audio_bytes = FileValidator.validate_audio(audio, config.max_audio_size)
    
    result = forge_service.generate_idea(image_bytes, audio_bytes, validated_text)
    
    logger.info("Successfully generated idea", request_id=request_id, response_length=len(result))
    
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


@app.post("/generate-from-graph")
async def generate_from_graph(
    request: Request,
    graph_metadata: str = Form(..., description="JSON string of graph structure"),
    files: List[UploadFile] = File(..., description="Image and audio files"),
    config: Config = Depends(get_config),
    gemini_client: GeminiClientProtocol = Depends(get_gemini_client),
    logger: StructuredLogger = Depends(get_logger)
):
    """
    Generate idea from node graph with multi-modal fusion.
    
    This endpoint processes the complete graph structure, calculating
    influence scores for each node based on connections and weights.
    """
    request_id = request.state.request_id
    
    logger.info("Processing graph generation request", request_id=request_id, file_count=len(files))
    
    try:
        metadata = json.loads(graph_metadata)
        
        nodes = metadata.get('nodes', [])
        connections = metadata.get('connections', [])
        
        if not nodes:
            raise ValidationError("Graph must contain at least one node", details={"reason": "empty_graph"})
        
        if not connections:
            raise ValidationError("Graph must contain at least one connection", details={"reason": "no_connections"})
        
        logger.info("Graph structure", node_count=len(nodes), connection_count=len(connections))
        
        # Process files and match to nodes
        image_files = {}
        audio_files = {}
        
        for file in files:
            node_id = file.filename.split('-')[0] if '-' in file.filename else None
            
            if not node_id:
                continue
            
            file_content = await file.read()
            await file.seek(0)
            
            # Create a temporary UploadFile-like object for validation
            from io import BytesIO
            temp_file = type('obj', (object,), {
                'file': BytesIO(file_content),
                'filename': file.filename,
                'content_type': file.content_type
            })()
            
            if file.content_type and file.content_type.startswith('image/'):
                validated_image = FileValidator.validate_image(temp_file, config.max_image_size)
                image_files[node_id] = validated_image
                logger.debug(f"Added image for node {node_id}")
            elif file.content_type and file.content_type.startswith('audio/'):
                validated_audio = FileValidator.validate_audio(temp_file, config.max_audio_size)
                audio_files[node_id] = validated_audio
                logger.debug(f"Added audio for node {node_id}")
        
        # Validate text content
        for node in nodes:
            if node.get('type') == 'text':
                content = node.get('content', '')
                validated_content = TextValidator.sanitize(content, max_length=5000)
                node['content'] = validated_content
        
        # Create graph processor
        graph_processor = GraphProcessor(
            client=gemini_client,
            config=config,
            logger=logger
        )
        
        # Generate idea from graph
        idea = graph_processor.generate_from_graph(
            nodes=nodes,
            connections=connections,
            image_files=image_files,
            audio_files=audio_files
        )
        
        logger.info("Successfully generated idea from graph", request_id=request_id, idea_length=len(idea))
        
        return {
            "success": True,
            "idea": idea,
            "request_id": request_id,
            "graph_info": {
                "nodes": len(nodes),
                "connections": len(connections),
                "images_processed": len(image_files),
                "audio_processed": len(audio_files)
            }
        }
        
    except json.JSONDecodeError as e:
        raise ValidationError("Invalid graph metadata JSON", details={"error": str(e)})
    except Exception as e:
        logger.error("Failed to generate from graph", exc_info=e, request_id=request_id)
        raise


@app.post("/refine-idea", response_model=RefineResponse)
async def refine_idea(
    request: Request,
    request_body: RefineRequest,
    forge_service: ForgeService = Depends(get_forge_service),
    logger: StructuredLogger = Depends(get_logger)
):
    """Refine or create variations of an existing idea (legacy endpoint)."""
    request_id = request.state.request_id
    
    logger.info(
        "Processing refine-idea request",
        request_id=request_id,
        idea_length=len(request_body.idea),
        refinement_type=request_body.type
    )
    
    validated_idea = TextValidator.sanitize(request_body.idea, max_length=2000)
    refined = forge_service.refine_idea(validated_idea, request_body.type)
    
    logger.info("Successfully refined idea", request_id=request_id, refined_length=len(refined), refinement_type=request_body.type)
    
    return RefineResponse(
        success=True,
        refined_idea=refined,
        request_id=request_id
    )

@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    """Get API usage statistics."""
    return StatsResponse(
        success=True,
        stats={
            "version": "1.1.0",
            "model": "gemini-2.0-flash-exp",
            "features": [
                "multimodal_generation",
                "node_graph_system",
                "weighted_multi_modal_fusion",
                "influence_calculation",
                "idea_refinement"
            ]
        }
    )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get API metrics including request counts, error rates, and latency percentiles."""
    metrics_collector = get_metrics_collector()
    metrics_data = metrics_collector.get_metrics()
    
    return MetricsResponse(**metrics_data)

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )