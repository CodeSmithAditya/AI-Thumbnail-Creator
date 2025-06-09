import os
import requests
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import textwrap
import time
from typing import Optional, List, Dict, Any

# --- Configuration ---
THUMBNAIL_WIDTH: int = 1024
THUMBNAIL_HEIGHT: int = 512
FONT_FILE: str = "Inter.ttf"
FONT_SIZE: int = 60

def generate_image(prompt_text: str, save_path: str = "thumbnail_base.png") -> Optional[str]:
    """
    Generates a base image using the ModelsLab v6 text2img API.
    """
    print(f"-> Generating image for prompt: '{prompt_text[:40]}...'")
    load_dotenv()
    api_key: Optional[str] = os.getenv("MODELSLAB_API_KEY")

    if not api_key:
        print("ERROR: MODELSLAB_API_KEY not found in .env file.")
        return None

    api_url: str = "https://modelslab.com/api/v6/realtime/text2img"
    
    headers: Dict[str, str] = {'Content-Type': 'application/json'}
    
    payload: Dict[str, Any] = {
        "key": api_key,
        "prompt": prompt_text,
        "negative_prompt": "ugly, blurry, bad anatomy, watermark, text, signature",
        "width": str(THUMBNAIL_WIDTH),
        "height": str(THUMBNAIL_HEIGHT),
        "samples": "1",
        "safety_checker": False,
        "enhance_prompt": True,
        "seed": None
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        data: Dict[str, Any] = response.json()

        if data.get('status') == 'success' and data.get('output'):
            image_url: str = data['output'][0]
            time.sleep(2) 
            image_response = requests.get(image_url)
            image_response.raise_for_status()
            
            with open(save_path, "wb") as f:
                f.write(image_response.content)
            print(f"   - Base image saved to {save_path}")
            return save_path
        else:
            print(f"   - API did not return a success status. Response: {data}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"   - An error occurred during API request: {e}")
        return None


def add_text_to_image(base_image_path: str, title_text: str, save_path: str) -> None:
    """
    Overlays title text onto the base image, with wrapping and a shadow.
    """
    print(f"-> Adding text to {base_image_path}...")
    try:
        image = Image.open(base_image_path)
        canvas = ImageDraw.Draw(image)
        font = ImageFont.truetype(FONT_FILE, FONT_SIZE)
    except FileNotFoundError:
        print(f"ERROR: Font file not found at '{FONT_FILE}'.")
        return
    except IOError:
        print(f"ERROR: Could not open image at '{base_image_path}'.")
        return

    margin: int = 60
    max_width_chars: int = 30
    wrapped_text: str = "\n".join(textwrap.wrap(title_text, width=max_width_chars))

    text_x: int = margin
    text_y: int = THUMBNAIL_HEIGHT - (margin + (wrapped_text.count('\n') + 1) * FONT_SIZE)
    
    shadow_offset: int = 2
    shadow_color: str = "black"
    canvas.text((text_x + shadow_offset, text_y + shadow_offset), wrapped_text, font=font, fill=shadow_color)
    
    text_color: str = "white"
    canvas.text((text_x, text_y), wrapped_text, font=font, fill=text_color)
    
    image.save(save_path)
    print(f"   - Final thumbnail saved to {save_path}")


def create_thumbnail_workflow(title: str, output_filename: str) -> None:
    """
    Runs the full process, with smarter prompt engineering.
    """
    base_prompt: str = f"{title}, digital art, professional, clean illustration, vibrant colors"
    
    title_lower: str = title.lower()
    
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

    base_image: Optional[str] = generate_image(image_prompt)
    
    if base_image:
        add_text_to_image(base_image, title, output_filename)


if __name__ == "__main__":
    # Note: The script is set to run with a short list of 2 titles for quick testing.
    # This is to respect API free tier limits and for faster execution during demonstration.
    # The full list of 50 titles is included below but is "commented out".
    # To run the full batch, you can uncomment the long list and comment out the short one.
    
    # --- Short list for testing ---
    blog_titles: List[str] = [
        "The Rise of Generative AI in Creative Industries",
        "Quantum Computing: What Is It and Why Does It Matter?",
    ]

    """
    # --- Full list of 50 titles for batch generation ---
    blog_titles: List[str] = [
        # Technology & AI
        "The Rise of Generative AI in Creative Industries",
        "Quantum Computing: What Is It and Why Does It Matter?",
        "A Beginner's Guide to Building Your First Neural Network",
        "Cybersecurity Trends to Watch in 2025",
        "The Ethical Implications of Artificial Intelligence",
        "How Blockchain is Revolutionizing Supply Chains",
        "Introduction to the Internet of Things (IoT)",
        "Rust vs. Go: Which Language is Right for Your Next Project?",
        "The Future of Augmented Reality Glasses",
        "How to Automate Your Life with Python Scripts",

        # Lifestyle & Wellness
        "A Guide to Mindful Meditation for Beginners",
        "10 Healthy Recipes You Can Make in Under 20 Minutes",
        "The Art of Minimalist Living: Declutter Your Life",
        "How to Build a Sustainable Morning Routine",
        "Digital Detox: Reclaiming Your Time from Your Smartphone",
        "The Benefits of a Plant-Based Diet",
        "Finding Your Perfect Workout Style",
        "Urban Gardening: How to Grow Food in Small Spaces",
        "The Science of Sleep: Getting a Better Night's Rest",
        "Financial Wellness: A Guide to Budgeting and Saving",

        # Travel & Adventure
        "A Backpacker's Guide to Southeast Asia",
        "The Most Beautiful Hiking Trails in North America",
        "Hidden Gems: Exploring the Coast of Italy",
        "How to Travel the World on a Budget",
        "Solo Travel: A Life-Changing Experience",
        "The Ultimate Road Trip Across the USA",
        "Exploring the Ancient Ruins of Machu Picchu",
        "A Cultural Tour of Kyoto, Japan",
        "The Best Islands to Visit in Greece",
        "Adventure Sports to Try Before You Die",

        # Business & Marketing
        "How to Launch a Successful E-commerce Store",
        "Content Marketing Strategies That Actually Work",
        "The Power of SEO for Small Businesses",
        "Building a Strong Personal Brand on LinkedIn",
        "The Art of Negotiation: Tips for a Better Deal",
        "Understanding the Stock Market: A Beginner's Guide",
        "How to Use Social Media to Grow Your Audience",
        "The Future of Remote Work and Distributed Teams",
        "Passive Income Streams You can Start Today",
        "Mastering the Art of the Perfect Sales Pitch",

        # Arts & Creativity
        "A Beginner's Guide to Watercolor Painting",
        "The History of Modern Graphic Design",
        "How to Write Your First Novel: A Step-by-Step Guide",
        "Getting Started with Digital Photography",
        "The Evolution of Hip Hop Music",
        "Understanding Color Theory for Artists",
        "The Magic of Stop-Motion Animation",
        "How to Start a Creative Journaling Habit",
        "An Introduction to Classical Music",
        "The Influence of Surrealism on Modern Art",
    ]
    """
    
    print("--- Starting Thumbnail Generation ---")
    
    if not os.path.exists("output"):
        os.makedirs("output")

    for i, title in enumerate(blog_titles):
        print(f"\nProcessing title {i+1}/{len(blog_titles)}: '{title}'")
        output_path: str = f"output/thumbnail_{i+1}.png"
        try:
            create_thumbnail_workflow(title, output_path)
        except Exception as e:
            print(f"An unexpected error occurred for title '{title}': {e}")
        
        if i < len(blog_titles) - 1:
            print("...Pausing for 5 seconds to respect API rate limits...")
            time.sleep(5) 
            
    print("\n--- All jobs completed. ---")