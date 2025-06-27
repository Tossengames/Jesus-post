import os
import random
import requests
import json
import feedparser
import re
from html import unescape
from datetime import datetime

# === FALLBACK CONTENT ===
BIBLE_VERSES = [
    {"verse": "I am the way and the truth and the life. No one comes to the Father except through me.", "ref": "John 14:6"},
    {"verse": "Come to me, all who are weary and burdened, and I will give you rest.", "ref": "Matthew 11:28"},
    {"verse": "Peace I leave with you; my peace I give you. I do not give to you as the world gives.", "ref": "John 14:27"},
    {"verse": "I am the good shepherd. The good shepherd lays down his life for the sheep.", "ref": "John 10:11"},
    {"verse": "Blessed are the pure in heart, for they will see God.", "ref": "Matthew 5:8"},
    {"verse": "You are the light of the world. A town built on a hill cannot be hidden.", "ref": "Matthew 5:14"},
    {"verse": "Be still, and know that I am God.", "ref": "Psalm 46:10"},
    {"verse": "The Lord is my shepherd; I shall not want.", "ref": "Psalm 23:1"},
    {"verse": "For whoever wants to save their life will lose it, but whoever loses their life for me will find it.", "ref": "Matthew 16:25"}
]

JESUS_QUOTES = [
    "With man this is impossible, but with God all things are possible.",
    "Do not let your hearts be troubled. Trust in God; trust also in me.",
    "Love your enemies and pray for those who persecute you.",
    "Blessed are the peacemakers, for they shall be called children of God.",
    "For where two or three gather in my name, there am I with them.",
    "Let the little children come to me, and do not hinder them."
]

PRAYERS = [
    "Lord Jesus, help me to walk in Your peace today. Amen.",
    "Jesus, You are my light in darkness. I trust You completely.",
    "Thank You, Jesus, for always being near. I give You my heart again today.",
    "Heavenly Father, let me feel Jesus close today. Amen.",
    "Lord, help me to hear Your voice and follow You."
]

DECLARATIONS = [
    "Today I walk with Jesus. I am not alone.",
    "Jesus is my peace. I will not be shaken.",
    "He is my Shepherd — I have all I need.",
    "Jesus lives in me. His light shines through my life.",
    "I am forgiven, loved, and made new in Christ."
]

QUESTIONS = [
    "What is one thing you're trusting Jesus with today?",
    "What’s your favorite thing Jesus said?",
    "How has Jesus changed your life?",
    "When do you feel Jesus the closest?",
    "What is your favorite Psalm or Bible promise?"
]

IMAGE_KEYWORDS = ["Jesus", "peaceful nature", "cross", "sunrise", "Bible", "heavenly light"]

PIXABAY_API_KEY = os.getenv("PIXABAY_KEY")
FB_PAGE_TOKEN = os.getenv("FB_PAGE_TOKEN")
FB_PAGE_ID = os.getenv("FB_PAGE_ID")

RSS_FEEDS = [
    "https://www.biblegateway.com/usage/votd/rss/votd.rdf",
    "https://odb.org/feed/",
    "https://www.esv.org/votd/feed/"
]

# === UTILITIES ===

def load_json(file, default):
    if not os.path.exists(file):
        return default
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def clean_html(text):
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text.strip())

def fetch_image_url():
    keyword = random.choice(IMAGE_KEYWORDS)
    url = f"https://pixabay.com/api/?key={PIXABAY_API_KEY}&q={keyword}&image_type=photo&per_page=30&safesearch=true"
    res = requests.get(url).json()
    images = res.get("hits", [])
    return random.choice(images)["largeImageURL"] if images else None

def fetch_rss_post():
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                title = clean_html(entry.get("title", ""))
                summary = clean_html(entry.get("summary", ""))
                print("DEBUG RSS title:", title)
                print("DEBUG RSS summary:", summary)
                if title and summary and len(summary) > 30 and "verse of the day" not in summary.lower():
                    return f"📖 {title}\n\n{summary}"
        except Exception as e:
            print("❌ RSS error:", e)
    return None

def get_random_post():
    rss = fetch_rss_post()
    if rss:
        return rss

    choice = random.choice(["verse", "quote", "prayer", "declaration", "question"])
    if choice == "verse":
        v = random.choice(BIBLE_VERSES)
        return f"📖 \"{v['verse']}\"\n— {v['ref']}"
    elif choice == "quote":
        return f"📣 Jesus says: \"{random.choice(JESUS_QUOTES)}\""
    elif choice == "prayer":
        return f"🙏 {random.choice(PRAYERS)}"
    elif choice == "declaration":
        return f"🔊 {random.choice(DECLARATIONS)}"
    else:
        return f"🖊️ {random.choice(QUESTIONS)}"

def post_to_facebook(text, image_url):
    img_path = "temp.jpg"
    img_data = requests.get(image_url).content
    with open(img_path, "wb") as f:
        f.write(img_data)

    caption = f"{text}\n\n#Jesus #Faith #BibleVerse #ChristianQuotes"

    files = {'source': open(img_path, 'rb')}
    params = {'access_token': FB_PAGE_TOKEN, 'caption': caption}
    url = f"https://graph.facebook.com/{FB_PAGE_ID}/photos"
    res = requests.post(url, files=files, data=params)
    print("✅ Facebook response:", res.json())
    os.remove(img_path)

# === MAIN ===
if __name__ == "__main__":
    log = load_json("jesus_post_log.json", {"posts": []})
    image_url = fetch_image_url()
    if image_url:
        post_text = get_random_post()
        post_to_facebook(post_text, image_url)
        log["posts"].append({
            "time": datetime.utcnow().isoformat(),
            "text": post_text,
            "image_url": image_url
        })
        save_json("jesus_post_log.json", log)
    else:
        print("❌ No image found.")
