# Product Overview

**Frankenstein's Forge** is a multimodal AI API that processes images, audio, and text to generate creative ideas using Google's Gemini AI.

## Core Features

- **Multimodal Input Processing**: Accepts images (JPEG/PNG), audio (WAV/MP3), and text inputs
- **Node Graph System**: Advanced weighted multi-modal fusion using a node-based graph interface
- **Idea Generation**: Creates actionable ideas from combined multimodal inputs
- **Idea Refinement**: Generates variations, simplifications, or more ambitious versions of ideas
- **Implementation Steps**: Produces step-by-step plans for executing ideas

## API Endpoints

- `/generate` - Classic multimodal idea generation (legacy)
- `/generate-from-graph` - Node graph-based generation with influence calculation
- `/refine-idea` - Refine or create variations of existing ideas
- `/health` - Health check with dependency verification
- `/metrics` - API usage metrics and performance data
- `/stats` - API statistics and feature information

## User Interfaces

- **Node Graph Interface** (`/`) - Visual node-based editor for complex multimodal workflows
- **Classic Interface** (`/classic`) - Simple form-based interface for basic generation
