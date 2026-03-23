from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset, StreamableHTTPConnectionParams, StdioConnectionParams
from mcp import StdioServerParameters
from google.adk.tools import google_search
from google.adk.tools.tool_context import ToolContext

import datetime
from google.genai import types
import os

DEFAULT_MODEL='gemini-2.5-flash'
NANO_BANANA_MODEL='gemini-3-pro-image-preview'


get_weather = McpToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="https://mapstools.googleapis.com/mcp",
        headers={"X-Goog-Api-Key": os.environ.get("MAPS_API_KEY", "") }
    ),
)

nano_banana = McpToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=os.path.join(os.getcwd(), "tools", "mcp-gemini-go"),
            env=dict(os.environ, PROJECT_ID=os.environ.get("GOOGLE_CLOUD_PROJECT", "")),
        ),
        timeout=60,
    ),
)

async def display_image_with_adk(image_path: str, tool_context: ToolContext):
    """Reads an image file from the local disk and displays it in the chat as an artifact."""

    try:
        with open(image_path, "rb") as f:
            image_bytes = f.read()

        await tool_context.save_artifact(
            os.path.basename(image_path),
            types.Part.from_bytes(data=image_bytes, mime_type='image/png'),
        )
        return {
            'status': 'success',
            'detail': f'Image "{os.path.basename(image_path)}" displayed successfully.',
        }
    except FileNotFoundError:
        return {"status": "failed", "detail": f"Image file not found at path: {image_path}"}
    except Exception as e:
        return {"status": "failed", "detail": f"An error occurred: {e}"}

moodrun_planner_agent = LlmAgent(
    model=DEFAULT_MODEL,
    name='moodrun_planner_agent',
    description="Finds most iconic city attributes or handles specific user-provided landmarks.",
    instruction="Use the Google search tool to figure out the top 3 most iconic landmarks and immediate geographical attributes (lakes, major rivers, hills etc.) in a given city. If the user provided a specific list of landmarks in their request, use those instead of searching broadly. Return an ordered list of the landmarks to be featured.",
    tools=[google_search],
    output_key="city_profile"
)

moodrun_current_weather = LlmAgent(
    model=DEFAULT_MODEL,
    name='moodrun_current_weather',
    description="Looks up the current weather to be used in the city image.",
    instruction="Use the available tool to get a summary of current weather conditions in a city to provide the image with up to date atmospheric information.",
    tools=[get_weather],
    output_key="city_weather"
)

moodrun_info = ParallelAgent(
    name="moodrun_info",
    sub_agents=[moodrun_planner_agent, moodrun_current_weather]
)

moodrun_drawer = LlmAgent(
    model=DEFAULT_MODEL,
    name='moodrun_drawer',
    description="Draws the souvenir postcard picture featuring the specified landmarks.",
    instruction=f"""
    Image Context:
    - Current Date: {datetime.date.today().strftime("%A, %B %d, %Y")}
    - Current Weather
    - List of Landmarks (either specifically provided by user or top 3 defaulted by planner agent)

    Image Model: {NANO_BANANA_MODEL}

    Instructions:
    1. Come up with an absolute file path for the souvenir postcard of the current city 
        and make sure it's added to the current folders 'generated' folder 
        e.g. {os.getcwd()}/generated/zurich/ for a cityscape of Zurich. Ensure that the directory exists.
    2. Use the `nano_banana` tool with the specified image model to create the image
        in the above path by following these instructions carefully: 
        
        Generate a vibrant souvenir postcard of [CITY]. Present a clear, 45° top-down isometric 
        miniature 3D cartoon scene, prominently featuring the specific requested landmarks or the 
        top 3 default landmarks. Use soft, refined textures with realistic PBR materials and gentle, 
        lifelike lighting and shadows. Integrate the current weather conditions directly into 
        the environment to create an immersive atmospheric mood. Use a clean, minimalistic 
        composition with a soft, solid-colored background. At the top-center, place the title 
        “[CITY]” in large bold text, a prominent weather icon beneath it, then the current date 
        and temperature (medium text). All text must be centered with consistent spacing, and 
        may subtly overlap the tops of the architectural elements.
        Square 1080x1080 dimension.
        
    3. Use the `display_image_with_adk` tool with the absolute file path of the generated image.
    """,
    tools=[nano_banana, display_image_with_adk]
)

root_agent = SequentialAgent(
    name='moodrun_agent',
    description="Creates AI-generated souvenir postcards of cities featuring landmarks, based on current weather.",
    sub_agents=[moodrun_info, moodrun_drawer],
)
