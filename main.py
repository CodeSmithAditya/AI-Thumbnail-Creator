"""
This module contains the core logic for the AI Thumbnail Creator.
It handles the image generation via the Stability AI API and the
image processing for adding text overlays. It is designed to be
imported and used by the main Flask application (app.py).
"""
import os
import requests
import base64
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import textwrap
from typing import Optional, Dict, Any, List

# --- Configuration Constants ---
THUMBNAIL_WIDTH: int = 1024
THUMBNAIL_HEIGHT: int = 512
FONT_FILE: str = "Inter.ttf"
FONT_SIZE: int = 60

def generate_image(prompt_text: str, save_path: str = "thumbnail_base.png") -> Optional[str]:
    """
    Generates a base image using the official Stability AI API.
    """
    print(f"-> Generating image for prompt: '{prompt_text[:40]}...'")
    load_dotenv()
    api_key: Optional[str] = os.getenv("STABILITY_API_KEY")

    if not api_key:
        print("ERROR: STABILITY_API_KEY not found in .env file.")
        return None

    api_url: str = "https://api.stability.ai/v1/generation/stable-diffusion-v1-6/text-to-image"
    
    headers: Dict[str, str] = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload: Dict[str, Any] = {
        "text_prompts": [{"text": prompt_text}],
        "cfg_scale": 7,
        "height": THUMBNAIL_HEIGHT,
        "width": THUMBNAIL_WIDTH,
        "samples": 1,
        "steps": 30,
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        if data.get('artifacts'):
            for image_artifact in data["artifacts"]:
                image_data = base64.b64decode(image_artifact["base64"])
                with open(save_path, "wb") as f:
                    f.write(image_data)
                print(f"   - Base image saved to {save_path}")
                return save_path
        
        print(f"   - API did not return image artifacts. Response: {data}")
        return None

    except requests.exceptions.RequestException as e:
        print(f"   - An error occurred during API request: {e}")
        return None


def add_text_to_image(base_image_path: str, title_text: str, save_path: str) -> None:
    """
    Overlays title text onto a base image, with wrapping, a drop shadow,
    and a semi-transparent background for maximum readability.
    """
    print(f"-> Adding text to {base_image_path}...")
    try:
        image = Image.open(base_image_path).convert("RGBA")
        font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    except FileNotFoundError:
        print(f"ERROR: Font file not found at '{FONT_FILE}'.")
        return
    except IOError:
        print(f"ERROR: Could not open image at '{base_image_path}'.")
        return

    # Create a separate, transparent layer for drawing
    text_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    canvas = ImageDraw.Draw(text_layer)

    margin: int = 60
    max_width_chars: int = 30
    wrapped_text: str = "\n".join(textwrap.wrap(title_text, width=max_width_chars))

    # Get the bounding box of the text
    text_box = canvas.textbbox((0, 0), wrapped_text, font=font)
    text_height = text_box[3] - text_box[1]
    text_width = text_box[2] - text_box[0]

    # Calculate positions, explicitly casting all final values to integers
    text_x: int = margin
    text_y: int = int(THUMBNAIL_HEIGHT - text_height - margin)
    
    # Define coordinates for the background box
    box_padding: int = 20
    # The `rectangle` method requires a list of Ints, so we cast each one
    box_coords: List[int] = [
        int(text_x - box_padding),
        int(text_y - box_padding),
        int(text_x + text_width + box_padding),
        int(text_y + text_height + box_padding)
    ]
    canvas.rectangle(box_coords, fill=(0, 0, 0, 128))

    # Define positions for text and shadow, ensuring they are integers
    shadow_x = text_x + 2
    shadow_y = text_y + 2
    
    # Draw the text shadow and the main text
    canvas.text((shadow_x, shadow_y), wrapped_text, font=font, fill="black")
    canvas.text((text_x, text_y), wrapped_text, font=font, fill="white")
    
    # Composite the layer containing the box and text onto the original image
    final_image = Image.alpha_composite(image, text_layer)
    
    # Convert back to RGB for saving and better compatibility
    final_image = final_image.convert("RGB")
    final_image.save(save_path)
    print(f"   - Final thumbnail saved to {save_path}")


def create_thumbnail_workflow(title: str, output_filename: str) -> None:
    """
    Runs the full workflow from title to final thumbnail.
    """
    base_prompt: str = f"{title}, professional digital art, clean illustration, vibrant colors, cinematic lighting, 8k"
    
    title_lower: str = title.lower()
    
    # Enrich the prompt with contextual keywords for better image relevance
    if "python" in title_lower or "data structures" in title_lower:
        image_prompt: str = f"{base_prompt}, abstract code visualization, data nodes, network, python logo"
    elif "docker" in title_lower:
        image_prompt = f"{base_prompt}, software containers, code deployment, developer, server rack, whale logo"
    elif "ai" in title_lower or "machine learning" in title_lower or "neural network" in title_lower:
        image_prompt = f"{base_prompt}, artificial intelligence, neural network, futuristic technology, data flows"
    elif "virtual reality" in title_lower or "vr" in title_lower:
        image_prompt = f"{base_prompt}, person wearing a VR headset, immersive digital world, glowing neon interface"
    else:
        image_prompt = f"{base_prompt}, award-winning art"

    temp_base_image_path = "thumbnail_base.png"
    
    base_image_path: Optional[str] = generate_image(image_prompt, save_path=temp_base_image_path)
    
    if base_image_path:
        add_text_to_image(base_image_path, title, output_filename)
        if os.path.exists(base_image_path):
            os.remove(base_image_path)