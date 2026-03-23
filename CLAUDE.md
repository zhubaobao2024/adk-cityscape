# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Cityscape Agent built with Google's Application Development Kit (ADK). It's an agent that generates AI-powered cityscape images based on user input, combining multiple MCP servers and LLMs to research city landmarks, fetch weather data, and generate images.

## Architecture

The agent uses a **Sequential + Parallel + LLM Agent architecture**:

1. **Root Agent** (`cityscape_agent`): Sequential orchestrator
   - Runs two phases in sequence: information gathering → image generation

2. **City Info Phase** (Parallel): Gathers data about the city
   - `city_profile`: Uses Google Search tool to research iconic landmarks and geographical attributes
   - `city_current_weather`: Fetches current weather via Maps Grounding Lite MCP server

3. **City Drawer Phase** (LLM Agent): Generates the image
   - Uses the Nano Banana image model (`gemini-3-pro-image-preview`) via GenMedia MCP server
   - Saves images to `generated/{city_name}/` directory
   - Displays generated images in the chat interface

### Key Files

- **`main.py`**: FastAPI application entry point configured via `get_fast_api_app()`. Sets up session management, CORS, and web interface based on environment variables.
- **`agents/cityscape/agent.py`**: Agent definitions and orchestration. Contains the sequential/parallel agent structure and tool configurations.
- **`agents/cityscape/agent.json`**: Agent metadata and capabilities declaration for the ADK framework.
- **`.gemini/settings.json`**: MCP server configuration for Maps Grounding Lite (with API key header).

## Development Setup

```sh
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running Locally

### Prerequisites

1. Set up GCP project and APIs:
   ```sh
   export PROJECT_ID="your-project-id"
   gcloud services enable aiplatform.googleapis.com artifactregistry.googleapis.com \
       cloudbuild.googleapis.com run.googleapis.com --project $PROJECT_ID
   ```

2. Set up Maps API Key:
   ```sh
   gcloud beta services enable mapstools.googleapis.com --project=$PROJECT_ID
   gcloud beta services mcp enable mapstools.googleapis.com --project=$PROJECT_ID
   gcloud services api-keys create --display-name="Cityscape Maps MCP" \
       --key-id="cityscape-maps-mcp" \
       --api-target="service=mapstools.googleapis.com" --project $PROJECT_ID
   export MAPS_API_KEY="$(gcloud services api-keys get-key-string "cityscape-maps-mcp" \
       --project $PROJECT_ID --format "value(keyString)")"
   ```

3. Install GenMedia MCP server (see README for full details)

### Start Development Server

```sh
adk web ./agents
```

This launches the ADK web interface where you can test the agent. Try: `Generate a cityscape for Zurich`

## Key Environment Variables

- `SESSION_SERVICE_URI`: Database URI for sessions (default: `sqlite:///./sessions.db`)
- `ALLOWED_ORIGINS`: CORS allowed origins (default: `*`)
- `SERVE_WEB_INTERFACE`: Enable web UI (default: `false`)
- `ENABLE_A2A`: Enable agent-to-agent communication (default: `false`)
- `MAPS_API_KEY`: Google Maps API key (required)
- `GOOGLE_CLOUD_PROJECT`: GCP project ID (required)
- `PORT`: Server port (default: `8080`)

## Deployment

Deploys to Google Cloud Run. The Dockerfile builds the GenMedia MCP server from source and packages the Python application.

Key setup steps:
1. Create service account with necessary IAM roles (Vertex AI User, Logging, Monitoring)
2. Store Maps API Key in Secret Manager
3. Deploy via: `gcloud run deploy cityscape-agent --source . --region $REGION --project $PROJECT_ID ...`

See README for full deployment instructions with IAM permissions.

## Model Configuration

- **Default Model**: `gemini-3-flash-preview` (used for research and planning agents)
- **Image Generation Model**: `gemini-3-pro-image-preview` (Nano Banana, used by city_drawer)

Change these constants in `agents/cityscape/agent.py` if needed.
