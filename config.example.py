"""
Configuration file for Frankenstein's Forge
Copy this to config.py and customize as needed
"""

# API Configuration
API_TITLE = "Frankenstein's Forge API"
API_DESCRIPTION = "Multimodal AI API that processes images, audio, and text to generate creative ideas"
API_VERSION = "1.1.0"

# Server Configuration
HOST = "0.0.0.0"
PORT = 8000
RELOAD = True  # Set to False in production

# File Upload Limits (in bytes)
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_AUDIO_SIZE = 20 * 1024 * 1024  # 20MB

# Allowed File Types
ALLOWED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/jpg"]
ALLOWED_AUDIO_TYPES = ["audio/wav", "audio/mpeg", "audio/mp3", "audio/webm"]

# Recording Configuration
MAX_RECORDING_TIME = 30  # seconds

# AI Model Configuration
AI_MODEL = "gemini-2.0-flash-exp"  # or "gemini-1.5-pro" for more advanced features

# CORS Configuration
CORS_ORIGINS = ["*"]  # Restrict in production: ["https://yourdomain.com"]
CORS_CREDENTIALS = True
CORS_METHODS = ["*"]
CORS_HEADERS = ["*"]

# History Configuration
MAX_HISTORY_ITEMS = 20  # Maximum items stored in browser localStorage

# Feature Flags
ENABLE_HISTORY = True
ENABLE_EXPORT = True
ENABLE_TEMPLATES = True
ENABLE_WAVEFORM = True
ENABLE_REFINEMENT = True

# Template Prompts
TEMPLATES = {
    "tech": "I want to build a web application that helps people solve everyday problems using modern technology.",
    "art": "I want to create an artistic project that combines traditional and digital media to express creativity.",
    "business": "I want to start a business that provides value to customers while being sustainable and scalable.",
    "education": "I want to create an educational tool that makes learning more engaging and accessible.",
    "health": "I want to develop a health and wellness solution that improves people's daily lives."
}

# UI Configuration
THEME = {
    "primary_bg": "#0a0a0a",
    "secondary_bg": "#151515",
    "accent_color": "#4ade80",
    "text_primary": "#e0e0e0",
    "text_secondary": "#888",
    "border_color": "#2a2a2a"
}

# Rate Limiting (for future implementation)
RATE_LIMIT_ENABLED = False
RATE_LIMIT_REQUESTS = 10  # requests per minute
RATE_LIMIT_PERIOD = 60  # seconds

# Logging Configuration
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Analytics (for future implementation)
ANALYTICS_ENABLED = False
ANALYTICS_PROVIDER = None  # "google", "plausible", etc.

# Security
REQUIRE_API_KEY = False  # Set to True to require API key for requests
API_KEY_HEADER = "X-API-Key"

# Cache Configuration (for future implementation)
CACHE_ENABLED = False
CACHE_TTL = 3600  # seconds

# Database (for future implementation)
DATABASE_ENABLED = False
DATABASE_URL = None

# Email Notifications (for future implementation)
EMAIL_ENABLED = False
SMTP_SERVER = None
SMTP_PORT = 587

# Backup Configuration (for future implementation)
BACKUP_ENABLED = False
BACKUP_INTERVAL = 86400  # 24 hours in seconds
BACKUP_LOCATION = "./backups"

# Development Settings
DEBUG = True  # Set to False in production
TESTING = False

# Custom Prompts
IDEA_GENERATION_PROMPT = """Analyze these inputs and create an achievable idea. Start with 'create a' or 'make a':

User text: {text}

Consider the image content and audio sentiment to generate a creative, actionable idea."""

STEPS_GENERATION_PROMPT = """Given this idea: "{idea}"

Generate a clear, actionable step-by-step implementation plan.

Format your response as a well-structured numbered list with:
- Main steps numbered (1, 2, 3, etc.)
- Sub-steps with letters (a, b, c, etc.) if needed
- Clear spacing between sections
- Concise but actionable descriptions

Include these phases:
1. Planning & Research
2. Design & Preparation
3. Core Implementation
4. Testing & Refinement
5. Launch & Next Steps

Keep each step clear and actionable."""

REFINEMENT_PROMPTS = {
    "variation": "Create a creative variation of this idea: '{idea}'. Keep the core concept but add a unique twist or different approach.",
    "simpler": "Simplify this idea to make it more achievable: '{idea}'. Focus on the MVP (Minimum Viable Product) version.",
    "more_ambitious": "Expand this idea to be more ambitious and impactful: '{idea}'. Think bigger scale and broader reach."
}
