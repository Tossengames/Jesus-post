#!/usr/bin/env python3
"""
Kindness Coach: Generate inspirational posts about Jesus's teachings, kindness, and support 
with Gemini AI, create images with text overlay, and post to Facebook Page.
"""

import os
import requests
import random
import textwrap
import json
import hashlib
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
from io import BytesIO
import time
from datetime import datetime

# Try the new Google GenAI SDK import first
try:
    from google import genai
    print("✅ Using new Google GenAI SDK")
    SDK_TYPE = "new"
except ImportError:
    try:
        # Fallback to old import style
        import google.generativeai as genai
        print("✅ Using old Google Generative AI SDK")
        SDK_TYPE = "old"
    except ImportError as e:
        print(f"❌ Failed to import Google AI libraries: {e}")
        print("💡 Please install the required package:")
        print("   pip install google-genai  # For new SDK")
        print("   or")
        print("   pip install google-generativeai  # For old SDK")
        exit(1)

# File to store posted tips for duplication check - in repository root
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
POST_HISTORY_FILE = os.path.join(REPO_ROOT, "posted.json")

# Content parameters for variety
CONTENT_THEMES = [
    "kindness", "forgiveness", "compassion", "love", "peace", 
    "hope", "grace", "mercy", "service", "healing",
    "mental_health", "animal_care", "community", "faith", "trust"
]

POST_TONES = [
    "gentle_teacher", "compassionate_friend", "wise_mentor", 
    "encouraging_guide", "peaceful_companion"
]

POST_STRUCTURES = [
    "message_explanation_verse",
    "verse_message_application", 
    "question_reflection_verse",
    "story_lesson_application",
    "challenge_encouragement_verse"
]

def load_posted_posts():
    """Load history of posted messages from JSON file"""
    try:
        print(f"📁 Looking for history file at: {POST_HISTORY_FILE}")
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    data = json.loads(content)
                    # Handle both old format (list of hashes) and new format (list of posts)
                    if isinstance(data, list) and data and isinstance(data[0], dict):
                        return data
                    else:
                        # Convert old format to new format
                        return []
                else:
                    return []
        print("📝 No existing history file found, starting fresh")
        return []
    except (json.JSONDecodeError, FileNotFoundError, Exception) as e:
        print(f"❌ Error loading history file: {e}")
        return []

def save_posted_post(post_data):
    """Save a posted message to JSON history file"""
    try:
        posted_posts = load_posted_posts()
        
        # Create post record with metadata
        post_record = {
            'main_message': post_data['main_message'],
            'explanation': post_data.get('explanation', ''),
            'bible_verse': post_data.get('bible_verse', ''),
            'hashtags': post_data.get('hashtags', ''),
            'theme': post_data.get('theme', 'general'),
            'tone': post_data.get('tone', 'gentle_teacher'),
            'structure': post_data.get('structure', 'message_explanation_verse'),
            'timestamp': datetime.now().isoformat(),
            'message_hash': hashlib.md5(post_data['main_message'].encode()).hexdigest()
        }
        
        # Add to history
        posted_posts.append(post_record)
        
        # Keep only last 1000 posts to prevent file from growing too large
        if len(posted_posts) > 1000:
            posted_posts = posted_posts[-1000:]
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
        
        # Write to file with proper formatting
        with open(POST_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(posted_posts, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved post to history: {post_data['main_message'][:50]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error saving to history: {e}")
        return False

def is_duplicate_post(post_data):
    """Check if a message has already been posted"""
    try:
        posted_posts = load_posted_posts()
        current_hash = hashlib.md5(post_data['main_message'].encode()).hexdigest()
        
        # Check if this exact message has been posted before
        for post in posted_posts:
            if post.get('message_hash') == current_hash:
                print(f"❌ Duplicate detected: {post_data['main_message'][:50]}...")
                return True
        
        # Also check for similar messages (same theme in recent posts)
        recent_posts = posted_posts[-20:]  # Check last 20 posts
        current_theme = post_data.get('theme', 'general')
        
        theme_count = 0
        for post in recent_posts:
            if post.get('theme') == current_theme:
                theme_count += 1
        
        # If this theme was used too recently, consider it a duplicate for variety
        if theme_count >= 3:  # Same theme used 3 times in last 20 posts
            print(f"🔄 Theme '{current_theme}' used recently, trying different theme...")
            return True
            
        print(f"✅ New post with theme '{current_theme}': {post_data['main_message'][:50]}...")
        return False
        
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def get_content_parameters():
    """Generate parameters for content variety"""
    theme = random.choice(CONTENT_THEMES)
    tone = random.choice(POST_TONES)
    structure = random.choice(POST_STRUCTURES)
    
    # Get recent posts to avoid repetition
    posted_posts = load_posted_posts()
    recent_themes = [p.get('theme', 'general') for p in posted_posts[-10:]]
    
    # If a theme was used recently, try to pick a different one
    if recent_themes and theme in recent_themes:
        available_themes = [t for t in CONTENT_THEMES if t not in recent_themes]
        if available_themes:
            theme = random.choice(available_themes)
    
    return {
        'theme': theme,
        'tone': tone,
        'structure': structure
    }

def generate_kindness_message():
    """Generate an inspirational message about kindness and Jesus's teachings using Gemini"""
    max_retries = 5  # Increased retries for better variety
    retry_count = 0
    
    # Get content parameters for variety
    params = get_content_parameters()
    
    while retry_count < max_retries:
        try:
            # Initialize client based on available SDK
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            # Different prompt templates based on parameters
            prompt_templates = {
                "gentle_teacher": """
                As a gentle teacher of Jesus's way, share wisdom about {theme} with warmth and compassion.
                Speak as if guiding a dear friend who needs encouragement today.
                """,
                "compassionate_friend": """
                As a compassionate friend walking alongside others, share about {theme} with genuine care.
                Your words should feel like a comforting conversation with someone who understands.
                """,
                "wise_mentor": """
                As a wise mentor who has found peace in Jesus's teachings, share insights about {theme}.
                Offer practical wisdom that comes from lived experience and deep reflection.
                """,
                "encouraging_guide": """
                As an encouraging guide, help others see the beauty in {theme} through Jesus's eyes.
                Your tone should be uplifting, hopeful, and full of practical encouragement.
                """,
                "peaceful_companion": """
                As a peaceful companion on life's journey, share quiet wisdom about {theme}.
                Speak with the calm assurance of someone who has found rest in God's love.
                """
            }
            
            structure_templates = {
                "message_explanation_verse": """
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [A heartfelt message about {theme} - under 15 words]
                EXPLANATION: [1-2 sentences in a {tone} tone explaining why this matters]
                BIBLE_VERSE: [A relevant Bible verse that supports the message]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                "verse_message_application": """
                Create ONE inspirational post with these components:
                BIBLE_VERSE: [Start with a relevant Bible verse about {theme}]
                MAIN_MESSAGE: [Connect the verse to daily life - under 15 words]
                EXPLANATION: [1-2 sentences applying this truth with a {tone} tone]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                "question_reflection_verse": """
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [Pose a thoughtful question about {theme} - under 15 words]
                EXPLANATION: [1-2 sentences of reflection with a {tone} tone]
                BIBLE_VERSE: [A relevant Bible verse that guides the reflection]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                "story_lesson_application": """
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [Share a brief insight about {theme} - under 15 words]
                EXPLANATION: [1-2 sentences drawing out the lesson with a {tone} tone]
                BIBLE_VERSE: [A relevant Bible verse that illuminates the insight]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                "challenge_encouragement_verse": """
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [Offer gentle encouragement about {theme} - under 15 words]
                EXPLANATION: [1-2 sentences of practical application with a {tone} tone]
                BIBLE_VERSE: [A relevant Bible verse that provides foundation]
                HASHTAGS: [3-4 relevant hashtags]
                """
            }
            
            tone_intro = prompt_templates.get(params['tone'], prompt_templates['gentle_teacher'])
            structure_template = structure_templates.get(params['structure'], structure_templates['message_explanation_verse'])
            
            prompt = tone_intro.format(theme=params['theme']) + "\n" + structure_template.format(
                theme=params['theme'], tone=params['tone']
            )
            
            prompt += "\n\nFormat the response exactly with the component labels shown above."
            
            # Generate content based on available SDK - USE CORRECT MODEL NAME
            if SDK_TYPE == "new":
                response = client.models.generate_content(
                    model='gemini-1.5-flash',
                    contents=prompt,
                )
                response_text = response.text
            else:
                model = genai.GenerativeModel('gemini-1.5-flash')  # Updated model name
                response = model.generate_content(prompt)
                response_text = response.text
            
            response_text = response_text.strip()
            print(f"🎯 Generating {params['tone']} post about {params['theme']}")
            print(f"📝 Structure: {params['structure']}")
            print(f"Gemini response:\n{response_text}")
            
            # Parse the response
            tip_data = {'theme': params['theme'], 'tone': params['tone'], 'structure': params['structure']}
            lines = response_text.split('\n')
            
            for line in lines:
                if line.startswith('MAIN_MESSAGE:'):
                    tip_data['main_message'] = line.replace('MAIN_MESSAGE:', '').strip()
                elif line.startswith('EXPLANATION:'):
                    tip_data['explanation'] = line.replace('EXPLANATION:', '').strip()
                elif line.startswith('BIBLE_VERSE:'):
                    tip_data['bible_verse'] = line.replace('BIBLE_VERSE:', '').strip()
                elif line.startswith('HASHTAGS:'):
                    tip_data['hashtags'] = line.replace('HASHTAGS:', '').strip()
            
            if 'main_message' in tip_data:
                # Check if this is a duplicate before returning
                if is_duplicate_post(tip_data):
                    print(f"🔄 Generated message is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    # Change parameters for next attempt
                    params = get_content_parameters()
                    continue
                
                return tip_data
            else:
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            print(f"❌ Error generating kindness message: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)
            # Change parameters for next attempt
            params = get_content_parameters()
    
    # Fallback with parameter-based variety
    print("🔄 Using parameter-based fallback messages...")
    return generate_fallback_message()

def generate_fallback_message():
    """Generate fallback message using parameters for variety"""
    params = get_content_parameters()
    
    theme_messages = {
        'kindness': [
            {'main_message': 'Love your neighbor as yourself, starting with small acts of kindness.',
             'explanation': 'My friend, even the smallest acts of love can ripple out and transform entire communities.',
             'bible_verse': '"Love your neighbor as yourself." - Mark 12:31'}
        ],
        'forgiveness': [
            {'main_message': 'Forgiveness is a gift you give your own heart.',
             'explanation': 'When we release others from our judgments, we free ourselves to receive peace.',
             'bible_verse': '"Forgive as the Lord forgave you." - Colossians 3:13'}
        ],
        'compassion': [
            {'main_message': 'Be gentle with yourself and others on this journey.',
             'explanation': 'We are all learning and growing. Grace meets us exactly where we are.',
             'bible_verse': '"The Lord is compassionate and gracious, slow to anger, abounding in love." - Psalm 103:8'}
        ],
        'mental_health': [
            {'main_message': 'Your struggles are seen, beloved. You are never alone.',
             'explanation': 'In your darkest moments, remember that Love walks with you through every shadow.',
             'bible_verse': '"I am with you always." - Matthew 28:20'}
        ],
        'animal_care': [
            {'main_message': 'Every creature reflects the beauty of its Creator.',
             'explanation': 'When we care for animals and nature, we honor the One who made them all.',
             'bible_verse': '"The righteous care for the needs of their animals." - Proverbs 12:10'}
        ]
    }
    
    # Default message if theme not found
    default_message = {
        'main_message': 'Walk in love today, and watch how it changes everything.',
        'explanation': 'Each loving action, no matter how small, carries eternal significance.',
        'bible_verse': '"Whoever lives in love lives in God, and God in them." - 1 John 4:16'
    }
    
    # Get messages for current theme or default
    messages = theme_messages.get(params['theme'], [default_message])
    tip_data = random.choice(messages)
    tip_data.update(params)
    tip_data['hashtags'] = f"#{params['theme'].title()} #JesusTeachings #Love #Compassion"
    
    # Check if this is a duplicate
    if is_duplicate_post(tip_data):
        # Try a different theme
        print("🔄 Fallback message is duplicate, trying different theme...")
        return generate_fallback_message()
    
    return tip_data

def create_gradient_background(width=1200, height=1200):
    """Create a beautiful gradient background when Pixabay fails"""
    # Peaceful color combinations
    color_pairs = [
        [('#87CEEB', '#98FB98'), ('#E6E6FA', '#FFFACD')],  # Sky blue + Pale green, Lavender + Lemon chiffon
        [('#FFE4E1', '#F0FFF0'), ('#B0E0E6', '#FFEFD5')],  # Misty rose + Honeydew, Powder blue + Papaya whip
        [('#F5F5DC', '#E0FFFF'), ('#FFF8DC', '#F0F8FF')],  # Beige + Azure, Cornsilk + Alice blue
        [('#FFDAB9', '#E6E6FA'), ('#F0FFF0', '#FFE4E1')],  # Peach puff + Lavender, Honeydew + Misty rose
    ]
    
    colors = random.choice(color_pairs)
    start_color, end_color = colors[0], colors[1]
    
    # Convert hex to RGB
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
    
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)
    
    # Create gradient
    background = Image.new('RGB', (width, height), start_rgb)
    draw = ImageDraw.Draw(background)
    
    for y in range(height):
        # Calculate gradient color
        ratio = y / height
        r = int(start_rgb[0] * (1 - ratio) + end_rgb[0] * ratio)
        g = int(start_rgb[1] * (1 - ratio) + end_rgb[1] * ratio)
        b = int(start_rgb[2] * (1 - ratio) + end_rgb[2] * ratio)
        
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    # Add some gentle texture
    for _ in range(1000):
        x = random.randint(0, width-1)
        y = random.randint(0, height-1)
        brightness = random.randint(-10, 10)
        pixel = background.getpixel((x, y))
        new_pixel = (
            max(0, min(255, pixel[0] + brightness)),
            max(0, min(255, pixel[1] + brightness)),
            max(0, min(255, pixel[2] + brightness))
        )
        draw.point((x, y), fill=new_pixel)
    
    # Apply slight blur for softness
    background = background.filter(ImageFilter.GaussianBlur(1))
    
    return background

def get_pixabay_image():
    """Get a random peaceful or inspiring image from Pixabay API"""
    try:
        api_key = os.environ.get("PIXABAY_KEY")
        if not api_key:
            print("❌ PIXABAY_KEY not found in environment variables")
            return None
            
        categories = ["nature", "peace", "sky", "flowers", "sunset", "sunrise", "landscape", "light", "hope", "serene"]
        category = random.choice(categories)
        
        print(f"🌄 Searching Pixabay for: {category}")
        
        url = "https://pixabay.com/api/"
        params = {
            "key": api_key,
            "q": category,
            "image_type": "photo",
            "orientation": "horizontal",
            "per_page": 20,
            "safesearch": "true",
            "editors_choice": "true"
        }
        
        response = requests.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if data['hits']:
                # Select a random image from the results
                image_data = random.choice(data['hits'])
                image_url = image_data["largeImageURL"]
                
                print(f"✅ Found Pixabay image: {image_url}")
                
                # Download the image
                img_response = requests.get(image_url, timeout=15)
                return BytesIO(img_response.content)
            else:
                print(f"❌ No images found for category: {category}")
                return None
        else:
            print(f"❌ Pixabay API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Error fetching image from Pixabay: {e}")
        return None

def create_inspirational_image(tip_data):
    """Create inspirational image with varied layouts and styles"""
    width, height = 1200, 1200
    
    # Try to get a Pixabay image first
    image_bytes = get_pixabay_image()
    
    if image_bytes:
        try:
            # Open and process the Pixabay image
            background = Image.open(image_bytes)
            background = background.resize((width, height), Image.LANCZOS)
            
            # Apply a slight darkening filter for better text readability
            enhancer = ImageEnhance.Brightness(background)
            background = enhancer.enhance(0.7)  # Darken slightly
            
            print("✅ Using Pixabay background image")
            
        except Exception as e:
            print(f"❌ Error processing Pixabay image: {e}")
            # Create gradient background instead
            background = create_gradient_background(width, height)
            print("✅ Created beautiful gradient background")
    else:
        # Create gradient background when Pixabay fails
        background = create_gradient_background(width, height)
        print("✅ Created beautiful gradient background")
    
    # Create drawing context
    draw = ImageDraw.Draw(background)
    
    # Try to load fonts
    try:
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        title_font = ImageFont.truetype(font_path, 64)
        verse_font = ImageFont.truetype(font_path, 36)
    except (IOError, OSError):
        try:
            title_font = ImageFont.truetype("arial.ttf", 64)
            verse_font = ImageFont.truetype("arial.ttf", 36)
        except (IOError, OSError):
            title_font = ImageFont.load_default()
            verse_font = ImageFont.load_default()
    
    # Choose random layout style
    layout_style = random.choice(['centered', 'top_focus', 'with_verse'])
    
    # Generate random background color for text box - DIFFERENT EACH TIME
    random_bg_color = (
        random.randint(0, 255),
        random.randint(0, 255), 
        random.randint(0, 255),
        180  # Alpha value for transparency
    )
    
    if layout_style == 'centered':
        # Centered main message only
        wrapped_message = textwrap.fill(tip_data['main_message'], width=25)
        bbox = draw.textbbox((0, 0), wrapped_message, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Semi-transparent background with RANDOM COLOR
        padding = 40
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + text_height + padding
        ], fill=random_bg_color)
        
        draw.text((x, y), wrapped_message, fill=(255, 255, 255), font=title_font, align='center')
        
    elif layout_style == 'top_focus':
        # Main message at top with more space
        wrapped_message = textwrap.fill(tip_data['main_message'], width=22)
        bbox = draw.textbbox((0, 0), wrapped_message, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height // 4
        
        # Semi-transparent background with RANDOM COLOR
        padding = 40
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + bbox[3] - bbox[1] + padding
        ], fill=random_bg_color)
        
        draw.text((x, y), wrapped_message, fill=(255, 255, 255), font=title_font, align='center')
        
    else:  # with_verse
        # Main message with Bible verse below
        wrapped_message = textwrap.fill(tip_data['main_message'], width=22)
        wrapped_verse = textwrap.fill(tip_data.get('bible_verse', 'God is love.'), width=30)
        
        # Calculate positions
        message_bbox = draw.textbbox((0, 0), wrapped_message, font=title_font)
        verse_bbox = draw.textbbox((0, 0), wrapped_verse, font=verse_font)
        
        message_width = message_bbox[2] - message_bbox[0]
        verse_width = verse_bbox[2] - verse_bbox[0]
        
        message_x = (width - message_width) // 2
        verse_x = (width - verse_width) // 2
        
        total_height = (message_bbox[3] - message_bbox[1]) + (verse_bbox[3] - verse_bbox[1]) + 60
        start_y = (height - total_height) // 2
        
        # Draw message with RANDOM COLOR
        message_padding = 30
        draw.rectangle([
            message_x - message_padding, start_y - message_padding,
            message_x + message_width + message_padding, start_y + (message_bbox[3] - message_bbox[1]) + message_padding
        ], fill=random_bg_color)
        
        draw.text((message_x, start_y), wrapped_message, fill=(255, 255, 255), font=title_font, align='center')
        
        # Draw verse with slightly different random color
        verse_bg_color = (
            (random_bg_color[0] + 30) % 255,
            (random_bg_color[1] + 30) % 255,
            (random_bg_color[2] + 30) % 255,
            150
        )
        verse_y = start_y + (message_bbox[3] - message_bbox[1]) + 40
        verse_padding = 20
        draw.rectangle([
            verse_x - verse_padding, verse_y - verse_padding,
            verse_x + verse_width + verse_padding, verse_y + (verse_bbox[3] - verse_bbox[1]) + verse_padding
        ], fill=verse_bg_color)
        
        draw.text((verse_x, verse_y), wrapped_verse, fill=(255, 255, 240), font=verse_font, align='center')
    
    # Convert to bytes
    output_buffer = BytesIO()
    background.save(output_buffer, format="JPEG", quality=95)
    return output_buffer.getvalue()

def create_facebook_caption(tip_data):
    """Create Facebook caption with varied formats and warm, personal tone"""
    
    # Different caption formats for variety
    caption_formats = [
        # Gentle teacher format
        """
My dear friend, {message}

{explanation}

{verse}

💖 How is Love speaking to your heart today? I'd be blessed to hear your thoughts.

{hashtags}
        """,
        
        # Compassionate guide format
        """
Beloved, a gentle reminder for your heart:

{message}

{explanation}

{verse}

✨ Where have you seen grace today? Share your light with us.

{hashtags}
        """,
        
        # Wise mentor format
        """
Walking in love today means:

{message}

{explanation}

{verse}

🌱 What small act of kindness is calling you? You are loved.

{hashtags}
        """,
        
        # Gentle friend format
        """
For your heart today:

{message}

{explanation}

{verse}

🌟 Your presence makes this world more beautiful. Share your light.

{hashtags}
        """
    ]
    
    # Choose random CTA endings
    cta_endings = [
        "You are loved more than you know. 💫",
        "May peace fill your heart today. 🌿",
        "Your kindness matters more than you realize. ❤️",
        "The world needs exactly the love you have to give. 🌟",
        "Rest in the knowledge that you are enough, just as you are. 🕊️"
    ]
    
    format_template = random.choice(caption_formats)
    cta_ending = random.choice(cta_endings)
    
    caption = format_template.format(
        message=tip_data['main_message'],
        explanation=tip_data['explanation'],
        verse=tip_data.get('bible_verse', 'God is love.'),
        hashtags=tip_data['hashtags'] + " " + " ".join([
            '#Kindness', '#Jesus', '#Love', '#Compassion', '#Hope', 
            '#Faith', '#Inspiration', '#Peace', '#Grace', '#MentalHealth'
        ])
    )
    
    return caption.strip() + f"\n\n{cta_ending}"

def post_to_facebook(image_data, tip_data):
    """Post the image to Facebook Page with inspirational caption"""
    try:
        page_id = os.environ.get("FB_PAGE_ID")
        access_token = os.environ.get("FB_PAGE_TOKEN")
        
        if not page_id or not access_token:
            print("❌ Facebook credentials not found in environment variables")
            return False
        
        # Upload image to Facebook
        url = f"https://graph.facebook.com/v19.0/{page_id}/photos"
        
        # Create caption
        caption = create_facebook_caption(tip_data)
        
        files = {'source': ('kindness_post.jpg', image_data, 'image/jpeg')}
        data = {'message': caption, 'access_token': access_token}
        
        response = requests.post(url, files=files, data=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            # Save to posted messages history to prevent duplicates
            if save_posted_post(tip_data):
                print(f"✅ Successfully posted to Facebook! Post ID: {result.get('id')}")
            else:
                print(f"⚠️ Posted to Facebook but failed to save to history: {result.get('id')}")
            return True
        else:
            print(f"❌ Facebook API error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error posting to Facebook: {e}")
        return False

def main():
    """Main function to run the entire process"""
    print("🚀 Starting kindness inspiration post generation and posting process...")
    print(f"📁 History file location: {POST_HISTORY_FILE}")
    
    # Check environment variables
    required_env_vars = ["GEMINI_API_KEY", "FB_PAGE_ID", "FB_PAGE_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.environ.get(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        print("💡 Please add missing variables to your GitHub Secrets")
        return
    
    # Load existing history to check functionality
    posted_posts = load_posted_posts()
    print(f"📊 Existing posts in history: {len(posted_posts)}")
    
    # Generate kindness and inspiration message
    tip_data = generate_kindness_message()
    print(f"🎯 Theme: {tip_data.get('theme', 'general')}")
    print(f"🎨 Tone: {tip_data.get('tone', 'gentle_teacher')}")
    print(f"📐 Structure: {tip_data.get('structure', 'message_explanation_verse')}")
    print(f"💡 Main Message: {tip_data['main_message']}")
    print(f"📝 Explanation: {tip_data.get('explanation', '')}")
    if 'bible_verse' in tip_data:
        print(f"📖 Bible Verse: {tip_data['bible_verse']}")
    print(f"🏷️ Hashtags: {tip_data.get('hashtags', '')}")
    
    # Create image
    final_image = create_inspirational_image(tip_data)
    print("🎨 Inspirational image created")
    
    # Post to Facebook
    success = post_to_facebook(final_image, tip_data)
    
    if success:
        print("✅ Process completed successfully! The kindness message has been shared.")
    else:
        print("❌ Process completed with errors")

if __name__ == "__main__":
    main()