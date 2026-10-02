"""
RAGE Image Generation Tool — Generates images using NVIDIA FLUX.
"""

import os
import requests
import base64
from typing import Dict, Any
from rage.tools.base import BaseTool, ToolResult
from rage.config import load_config, get_nvidia_api_key

class GenerateImageTool(BaseTool):
    """Generate an image using NVIDIA FLUX."""

    name = "generate_image"
    description = (
        "Generate an image based on a text prompt using NVIDIA FLUX. "
        "The generated image will be saved to the Downloads folder. "
        "Use this whenever the user asks you to create or generate an image."
    )
    parameters = {
        "type": "object",
        "properties": {
            "prompt": {
                "type": "string",
                "description": "The text prompt describing the image to generate.",
            },
            "filename": {
                "type": "string",
                "description": "The name of the file to save the image as (e.g., 'coffee_shop.jpg'). If not provided, a default name will be used.",
            },
        },
        "required": ["prompt"],
    }

    def execute(self, prompt: str, filename: str = "generated_image.jpg") -> ToolResult:
        config = load_config()
        api_key = get_nvidia_api_key(config)
        
        if not api_key:
            return ToolResult(
                success=False,
                output="",
                error="NVIDIA_API_KEY is not configured. Cannot generate image."
            )

        invoke_url = "https://ai.api.nvidia.com/v1/genai/black-forest-labs/flux.1-dev"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
        }
        payload = {
            "prompt": prompt,
            "mode": "base",
            "cfg_scale": 3.5,
            "width": 1024,
            "height": 1024,
            "seed": 0,
            "steps": 50
        }

        try:
            response = requests.post(invoke_url, headers=headers, json=payload)
            response.raise_for_status()
            response_body = response.json()
            
            # The response body likely contains base64 encoded image or a URL.
            # Assuming it contains base64 data under artifacts[0].base64 or similar standard formats.
            # Wait, NVIDIA genai payload typically returns data in {"data": [{"b64_json": "..."}]} or {"artifacts": [{"base64": "..."}]}
            # Wait, let's parse based on generic format.
            # Actually, standard OpenAI schema is {"data": [{"b64_json": "..."}]} or url.
            # We will try to extract base64.
            
            b64_image = None
            if "data" in response_body and len(response_body["data"]) > 0:
                if "b64_json" in response_body["data"][0]:
                    b64_image = response_body["data"][0]["b64_json"]
            elif "artifacts" in response_body and len(response_body["artifacts"]) > 0:
                if "base64" in response_body["artifacts"][0]:
                    b64_image = response_body["artifacts"][0]["base64"]
            
            # NVIDIA FLUX specifically returns:
            # {"artifacts": [{"base64": "...", "finishReason": "SUCCESS", "seed": 0}]}
            # Let's handle both.
            
            if not b64_image and "artifacts" in response_body:
                b64_image = response_body["artifacts"][0].get("base64")
            
            if b64_image:
                from rage.config import DOWNLOADS_DIR
                import uuid
                import os
                
                # Make sure the extension is correct, usually png or jpeg. Let's use jpg.
                if not filename.endswith((".jpg", ".jpeg", ".png")):
                    filename += ".jpg"
                    
                save_path = DOWNLOADS_DIR / filename
                
                # If the file already exists or it's the generic default name, make it unique
                if save_path.exists() or filename == "generated_image.jpg":
                    base, ext = os.path.splitext(filename)
                    filename = f"{base}_{uuid.uuid4().hex[:8]}{ext}"
                    save_path = DOWNLOADS_DIR / filename
                
                with open(save_path, "wb") as f:
                    f.write(base64.b64decode(b64_image))
                    
                try:
                    from rage.tools.browser import BrowserSession
                    session = BrowserSession.get_instance()
                    if not session.is_running:
                        session.launch(headless=False)
                    file_url = save_path.absolute().as_uri()
                    session.navigate(file_url, tab_name="generated_image")
                    output_msg = f"Successfully generated image, saved to: {save_path}, and opened in the browser."
                except Exception as e:
                    output_msg = f"Successfully generated image and saved to: {save_path}, but failed to open in browser: {e}"
                    
                return ToolResult(
                    success=True,
                    output=output_msg,
                    data={"path": str(save_path)}
                )
            else:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Could not find base64 image data in response: {response_body}"
                )

        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                error_msg += f"\nResponse: {e.response.text}"
            return ToolResult(
                success=False,
                output="",
                error=f"Failed to generate image: {error_msg}"
            )
