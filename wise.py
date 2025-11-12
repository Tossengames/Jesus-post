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

# File to store posted tips for duplication check - using absolute path
POST_HISTORY_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "posted_kindness_posts.json")

def load_posted_tips():
    """Load history of posted messages to avoid duplicates"""
    try:
        print(f"Looking for history file at: {POST_HISTORY_FILE}")
        if os.path.exists(POST_HISTORY_FILE):
            with open(POST_HISTORY_FILE, 'r') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
                else:
                    return []
        return []
    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error loading history file: {e}")
        return []

def save_posted_tip(tip_data):
    """Save a posted message to history"""
    try:
        posted_tips = load_posted_tips()
        
        # Create a unique hash of the main message to identify duplicates
        tip_hash = hashlib.md5(tip_data['main_message'].encode()).hexdigest()
        
        # Add to history if not already there
        if tip_hash not in posted_tips:
            posted_tips.append(tip_hash)
            # Ensure directory exists
            os.makedirs(os.path.dirname(POST_HISTORY_FILE), exist_ok=True)
            with open(POST_HISTORY_FILE, 'w') as f:
                json.dump(posted_tips, f)
            print(f"✅ Saved message to history: {tip_data['main_message'][:50]}...")
            return True
        else:
            print(f"❌ Message already exists in history: {tip_data['main_message'][:50]}...")
            return False
    except Exception as e:
        print(f"❌ Error saving to history: {e}")
        return False

def is_duplicate_tip(tip_data):
    """Check if a message has already been posted"""
    try:
        posted_tips = load_posted_tips()
        tip_hash = hashlib.md5(tip_data['main_message'].encode()).hexdigest()
        is_dup = tip_hash in posted_tips
        if is_dup:
            print(f"❌ Duplicate detected: {tip_data['main_message'][:50]}...")
        else:
            print(f"✅ New message: {tip_data['main_message'][:50]}...")
        return is_dup
    except Exception as e:
        print(f"❌ Error checking duplicate: {e}")
        return False

def generate_kindness_message():
    """Generate an inspirational message about kindness and Jesus's teachings using Gemini"""
    max_retries = 3
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            # Initialize client based on available SDK
            if SDK_TYPE == "new":
                client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
            else:
                genai.configure(api_key=os.environ["GEMINI_API_KEY"])
            
            # Different prompt styles for variety
            prompt_styles = [
                """
                You are a wise, gentle teacher sharing Jesus's way of love and kindness. 
                Speak with warmth and compassion as if guiding a dear friend.
                
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [A heartfelt message about kindness, love, or compassion - under 15 words]
                EXPLANATION: [1-2 sentences in a warm, mentoring tone explaining why this matters]
                BIBLE_VERSE: [A relevant Bible verse that supports the message]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                """
                You are a compassionate guide sharing practical ways to live out Jesus's teachings.
                Your tone should be encouraging, personal, and full of grace.
                
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [An encouraging message about love in action - under 15 words]
                EXPLANATION: [1-2 sentences that feel like gentle wisdom from a trusted friend]
                BIBLE_VERSE: [A relevant Bible verse that supports the message]
                HASHTAGS: [3-4 relevant hashtags]
                """,
                """
                You are a kind soul sharing the gentle way of Jesus with the world.
                Speak with the warmth of someone who has found peace in serving others.
                
                Create ONE inspirational post with these components:
                MAIN_MESSAGE: [A peaceful message about compassion or healing - under 15 words]
                EXPLANATION: [1-2 sentences that feel like quiet wisdom shared over tea]
                BIBLE_VERSE: [A relevant Bible verse that supports the message]
                HASHTAGS: [3-4 relevant hashtags]
                """
            ]
            
            prompt = random.choice(prompt_styles)
            
            # Generate content based on available SDK
            if SDK_TYPE == "new":
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt,
                )
                response_text = response.text
            else:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                response_text = response.text
            
            response_text = response_text.strip()
            print(f"Gemini response:\n{response_text}")
            
            # Parse the response
            tip_data = {}
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
                if is_duplicate_tip(tip_data):
                    print(f"🔄 Generated message is a duplicate, trying again... (Attempt {retry_count + 1}/{max_retries})")
                    retry_count += 1
                    continue
                
                return tip_data
            else:
                raise Exception("Invalid response format from Gemini")
            
        except Exception as e:
            print(f"❌ Error generating kindness message: {e}")
            retry_count += 1
            if retry_count >= max_retries:
                break
            time.sleep(2)  # Wait before retrying
    
    # Fallback kindness messages with varied tones
    print("🔄 Using fallback messages after Gemini failures...")
    fallback_messages = [
        {
            'main_message': 'Love your neighbor as yourself, starting with small acts of kindness.',
            'explanation': 'My friend, even the smallest acts of love can ripple out and transform entire communities.',
            'bible_verse': '"Love your neighbor as yourself." - Mark 12:31',
            'hashtags': '#Kindness #JesusTeachings #Love #Compassion'
        },
        {
            'main_message': 'Be gentle with yourself and others on this journey.',
            'explanation': 'We are all learning and growing. Grace meets us exactly where we are.',
            'bible_verse': '"Come to me, all you who are weary and burdened, and I will give you rest." - Matthew 11:28',
            'hashtags': '#Grace #MentalHealth #Compassion #Peace'
        },
        {
            'main_message': 'Forgiveness is a gift you give your own heart.',
            'explanation': 'When we release others from our judgments, we free ourselves to receive peace.',
            'bible_verse': '"Forgive as the Lord forgave you." - Colossians 3:13',
            'hashtags': '#Forgiveness #Peace #Healing #Grace'
        },
        {
            'main_message': 'Every creature reflects the beauty of its Creator.',
            'explanation': 'When we care for animals and nature, we honor the One who made them all.',
            'bible_verse': '"The righteous care for the needs of their animals." - Proverbs 12:10',
            'hashtags': '#AnimalKindness #CreationCare #Compassion #Stewardship'
        },
        {
            'main_message': 'Your struggles are seen, beloved. You are never alone.',
            'explanation': 'In your darkest moments, remember that Love walks with you through every shadow.',
            'bible_verse': '"I am with you always." - Matthew 28:20',
            'hashtags': '#MentalHealth #Hope #YouAreNotAlone #Peace'
        },
        {
            'main_message': 'Serve others with the joy of a grateful heart.',
            'explanation': 'True service flows not from obligation, but from the overflow of love we have received.',
            'bible_verse': '"Serve wholeheartedly, as if you were serving the Lord." - Ephesians 6:7',
            'hashtags': '#Service #Joy #LoveInAction #Community'
        },
        {
            'main_message': 'Speak life, hope, and healing with your words.',
            'explanation': 'Our words can be gentle rain on parched soil or warm light in dark places.',
            'bible_verse': '"Let your conversation be always full of grace." - Colossians 4:6',
            'hashtags': '#Encouragement #KindWords #Love #Hope'
        },
        {
            'main_message': 'Rest in the peace that surpasses all understanding.',
            'explanation': 'When worries come, breathe deeply and trust that you are held in loving hands.',
            'bible_verse': '"Do not be anxious about anything." - Philippians 4:6',
            'hashtags': '#Peace #Trust #LetGo #Faith'
        }
    ]
    
    # Filter out duplicates from fallback messages
    non_duplicate_messages = [
        t for t in fallback_messages 
        if not is_duplicate_tip(t)
    ]
    
    if non_duplicate_messages:
        return random.choice(non_duplicate_messages)
    else:
        # If all fallbacks are duplicates, return a random one anyway
        print("⚠️ All fallback messages are duplicates, using random one")
        return random.choice(fallback_messages)

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
    
    if layout_style == 'centered':
        # Centered main message only
        wrapped_message = textwrap.fill(tip_data['main_message'], width=25)
        bbox = draw.textbbox((0, 0), wrapped_message, font=title_font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Semi-transparent background
        padding = 40
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + text_height + padding
        ], fill=(0, 0, 0, 128))
        
        draw.text((x, y), wrapped_message, fill=(255, 255, 255), font=title_font, align='center')
        
    elif layout_style == 'top_focus':
        # Main message at top with more space
        wrapped_message = textwrap.fill(tip_data['main_message'], width=22)
        bbox = draw.textbbox((0, 0), wrapped_message, font=title_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = height // 4
        
        # Semi-transparent background
        padding = 40
        draw.rectangle([
            x - padding, y - padding,
            x + text_width + padding, y + bbox[3] - bbox[1] + padding
        ], fill=(0, 0, 0, 150))
        
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
        
        # Draw message
        message_padding = 30
        draw.rectangle([
            message_x - message_padding, start_y - message_padding,
            message_x + message_width + message_padding, start_y + (message_bbox[3] - message_bbox[1]) + message_padding
        ], fill=(0, 0, 0, 150))
        
        draw.text((message_x, start_y), wrapped_message, fill=(255, 255, 255), font=title_font, align='center')
        
        # Draw verse
        verse_y = start_y + (message_bbox[3] - message_bbox[1]) + 40
        verse_padding = 20
        draw.rectangle([
            verse_x - verse_padding, verse_y - verse_padding,
            verse_x + verse_width + verse_padding, verse_y + (verse_bbox[3] - verse_bbox[1]) + verse_padding
        ], fill=(0, 0, 0, 120))
        
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
            if save_posted_tip(tip_data):
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
    posted_tips = load_posted_tips()
    print(f"📊 Existing posts in history: {len(posted_tips)}")
    
    # Generate kindness and inspiration message
    tip_data = generate_kindness_message()
    print(f"💡 Main Message: {tip_data['main_message']}")
    print(f"📝 Explanation: {tip_data['explanation']}")
    if 'bible_verse' in tip_data:
        print(f"📖 Bible Verse: {tip_data['bible_verse']}")
    print(f"🏷️ Hashtags: {tip_data['hashtags']}")
    
    # Create image with main message text only
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