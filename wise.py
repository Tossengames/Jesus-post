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

# ... (Keep the existing image creation functions: create_gradient_background, get_pixabay_image, create_inspirational_image)
# ... (Keep the existing caption creation function: create_facebook_caption)
# ... (Keep the existing Facebook posting function: post_to_facebook)

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