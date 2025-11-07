import os
from datetime import datetime
import textwrap
import yaml
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from PIL import Image
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import time

# Patch for Pillow compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# Load config
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

VIDEO_CONFIG = CONFIG['video']
SHORTS_CONFIG = CONFIG['platforms']['youtube']['shorts']
TEXT_STYLE = CONFIG['text_style']
ZODIAC_SIGNS = CONFIG['zodiac_signs']

# Get API keys from environment
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID', '')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET', '')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN', '')

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)


# ========================================
# YOUTUBE UPLOAD FUNCTIONS
# ========================================

def upload_to_youtube(video_path, sign):
    """Upload video to YouTube Shorts"""
    if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN]):
        print(f"    ⚠️ YouTube credentials not configured - skipping upload")
        return None
    
    try:
        print(f"    📤 Uploading to YouTube...")
        
        # Create credentials
        credentials = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET
        )
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Create video metadata
        today = datetime.now().strftime("%B %d, %Y")
        title = f"{sign} Daily Horoscope & Cosmic Guidance | {today} #Shorts"
        description = f"""🌟 {sign} Daily Horoscope for {today}

✨ Today's Cosmic Guidance:
- Daily Horoscope
- Wealth & Financial Tips
- Health & Wellness Blessings

🔔 Subscribe for daily cosmic guidance!
💬 Comment your zodiac sign below
👍 Like if this resonates with you

#{sign} #Horoscope #Astrology #DailyHoroscope #Zodiac #Shorts #VedicAstrology #CosmicGuidance #Spirituality

⚠️ For entertainment purposes only. Consult professionals for serious decisions."""
        
        tags = [
            "horoscope", "daily horoscope", "astrology", sign.lower(),
            "zodiac", "shorts", "vedic astrology", "cosmic guidance",
            "spiritual", "horoscope today", f"{sign.lower()} horoscope"
        ]
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',  # or 'unlisted' for testing
                'madeForKids': False,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload video
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"      Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"    ✅ Uploaded! Video ID: {video_id}")
        print(f"    🔗 URL: {video_url}")
        
        return video_url
        
    except Exception as e:
        print(f"    ❌ YouTube upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None


# ========================================
# API FETCHING FUNCTIONS
# ========================================

def fetch_ai_content(prompt, sign):
    """Fetch content from Groq or HuggingFace"""
    formatted_prompt = prompt.format(sign=sign)
    
    if GROQ_API_KEY:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a warm Vedic astrologer. Keep responses concise and natural."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except:
            pass
    
    if HUGGINGFACE_API_KEY:
        try:
            response = requests.post(
                "https://router.huggingface.co/hf-inference/models/deepseek-ai/DeepSeek-V3",
                headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": formatted_prompt,
                    "parameters": {"max_new_tokens": 150, "temperature": 0.7}
                },
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
        except:
            pass
    
    return None


def clean_and_summarize(text):
    """Clean AI response and make it concise"""
    text = text.replace("**", "").replace("*", "").replace("#", "").strip()
    
    prefixes = ["Here is", "Here's", "Today's", "For today", "Namaste"]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            if text.startswith(":") or text.startswith(","):
                text = text[1:].strip()
    
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) > 4:
        sentences = sentences[:4]
    
    result = ". ".join(sentences)
    if result and result[-1] not in ".!?":
        result += "."
    
    return result


def get_content_for_sign(sign):
    """Get horoscope, wealth, and health content"""
    print(f"  📝 Fetching content...")
    
    horo = fetch_ai_content(CONFIG['free_ai']['prompts']['horoscope'], sign)
    if not horo:
        horo = f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition."
    horo = clean_and_summarize(horo)
    
    wealth = fetch_ai_content(CONFIG['free_ai']['prompts']['wealth'], sign)
    if not wealth:
        wealth = "Do: Plan finances with Mercury's clarity. Don't: Rush major investments today."
    wealth = clean_and_summarize(wealth)
    
    health = fetch_ai_content(CONFIG['free_ai']['prompts']['health'], sign)
    if not health:
        health = "The Moon stirs emotions today. Drink water mindfully and practice deep breathing for balance."
    health = clean_and_summarize(health)
    
    print(f"  ✅ Content ready")
    return {'horoscope': horo, 'wealth': wealth, 'health': health}


# ========================================
# VIDEO CREATION FUNCTIONS
# ========================================

def create_heading(text, font_size, color, duration, screen_size, fade=True):
    """Create heading with underline"""
    heading = TextClip(
        text,
        fontsize=font_size + 20,
        color="#F5F5F5",
        font='Arial-Bold',
        method='label'
    ).set_duration(duration)
    
    underline = TextClip(
        "━" * 20,
        fontsize=font_size // 2,
        color="#F5F5F5",
        method='label'
    ).set_duration(duration)
    
    if fade:
        heading = heading.fadein(0.8).fadeout(0.8)
        underline = underline.fadein(0.8).fadeout(0.8)
    
    return heading, underline


def create_text_chunks(text, font_size, screen_size, total_duration):
    """Split text into smart chunks"""
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped_lines.extend(textwrap.wrap(line, width=35))
    
    total_lines = len(wrapped_lines)
    
    if total_lines <= 8:
        chunks = ["\n".join(wrapped_lines)]
    elif total_lines <= 16:
        mid = len(wrapped_lines) // 2
        chunks = ["\n".join(wrapped_lines[:mid]), "\n".join(wrapped_lines[mid:])]
    else:
        LINES_PER_CHUNK = 9
        chunks = []
        for i in range(0, len(wrapped_lines), LINES_PER_CHUNK):
            chunk_lines = wrapped_lines[i:i + LINES_PER_CHUNK]
            chunks.append("\n".join(chunk_lines))
    
    text_clips = []
    
    if len(chunks) == 1:
        clip = TextClip(
            chunks[0],
            fontsize=font_size,
            color="#F5F5F5",
            method='label',
            align='center'
        ).set_duration(total_duration).set_start(0).fadein(0.8).fadeout(0.8)
        text_clips.append(clip)
    else:
        chunk_line_counts = [len(chunk.split('\n')) for chunk in chunks]
        total_lines_all = sum(chunk_line_counts)
        
        current_time = 0
        for i, chunk in enumerate(chunks):
            lines_in_chunk = chunk_line_counts[i]
            chunk_duration = max(3.0, (lines_in_chunk / total_lines_all) * total_duration)
            
            clip = TextClip(
                chunk,
                fontsize=font_size,
                color="#F5F5F5",
                method='label',
                align='center'
            ).set_duration(chunk_duration).set_start(current_time).fadein(0.8).fadeout(0.8)
            
            text_clips.append(clip)
            current_time += chunk_duration
    
    return text_clips


def create_short(sign, content):
    """Create video short"""
    print(f"  🎬 Creating video...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Calculate adaptive timing
    horo_length = len(content['horoscope'])
    wealth_length = len(content['wealth'])
    health_length = len(content['health'])
    total_content_length = horo_length + wealth_length + health_length
    
    AVAILABLE_TIME = 54
    SUBSCRIBE_DURATION = 5
    TARGET_DURATION = 59
    
    horo_time = max(15, int((horo_length / total_content_length) * AVAILABLE_TIME))
    wealth_time = max(12, int((wealth_length / total_content_length) * AVAILABLE_TIME))
    health_time = max(12, AVAILABLE_TIME - horo_time - wealth_time)
    
    # Load and crop background
    bg_original = VideoFileClip(VIDEO_CONFIG['background_video'])
    target_w, target_h = screen_size
    bg_w, bg_h = bg_original.size
    
    scale = target_h / bg_h
    new_w = int(bg_w * scale)
    
    if new_w >= target_w:
        bg_original = bg_original.resize(height=target_h)
        x_center = bg_original.w / 2
        x1 = int(x_center - target_w / 2)
        bg_original = bg_original.crop(x1=x1, width=target_w)
    else:
        bg_original = bg_original.resize(width=target_w)
        if bg_original.h > target_h:
            y_center = bg_original.h / 2
            y1 = int(y_center - target_h / 2)
            bg_original = bg_original.crop(y1=y1, height=target_h)
    
    MAIN_DURATION = horo_time + wealth_time + health_time
    
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    all_clips = []
    current_time = 0
    
    HEADING_Y = 100
    TEXT_Y = 910
    SIGN_Y = HEADING_Y + 60
    DATE_Y = SIGN_Y + 130
    HORO_HEADING_Y = HEADING_Y - 60
    
    # Title
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        "#F5F5F5",
        MAIN_DURATION,
        screen_size,
        fade=False
    )
    title_heading = title_heading.set_position(('center', SIGN_Y))
    title_underline = title_underline.set_position(('center', SIGN_Y + 100))
    all_clips.extend([title_heading, title_underline])
    
    date_clip = TextClip(
        datetime.now().strftime("%d %b %Y"),
        fontsize=35,
        color="#F5F5F5",
        method='label'
    ).set_duration(MAIN_DURATION).set_position(('center', DATE_Y))
    all_clips.append(date_clip)
    
    # Horoscope
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        "#F5F5F5",
        horo_time,
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    horo_chunks = create_text_chunks(content['horoscope'], TEXT_STYLE['content_font_size'] - 5, screen_size, horo_time)
    for chunk in horo_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += horo_time
    
    # Wealth
    wealth_chunks = create_text_chunks(content['wealth'], TEXT_STYLE['tip_font_size'] - 5, screen_size, wealth_time)
    for chunk in wealth_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += wealth_time
    
    # Health
    health_chunks = create_text_chunks(content['health'], TEXT_STYLE['tip_font_size'] - 5, screen_size, health_time)
    for chunk in health_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += health_time
    
    # Subscribe
    sub_text = TextClip(
        "🔔 SUBSCRIBE\n\nLIKE • SHARE • COMMENT",
        fontsize=60,
        color="#FFD700",
        font='Arial-Bold',
        method='label',
        align='center'
    ).set_duration(SUBSCRIBE_DURATION).set_position('center').set_start(current_time).fadein(0.5)
    all_clips.append(sub_text)
    
    # Composite
    final_video = CompositeVideoClip([bg_clip] + all_clips).set_duration(TARGET_DURATION)
    
    # Add music
    if os.path.exists(VIDEO_CONFIG['background_music']):
        music = AudioFileClip(VIDEO_CONFIG['background_music']).volumex(VIDEO_CONFIG['music_volume'])
        if music.duration < TARGET_DURATION:
            loops = int(TARGET_DURATION / music.duration) + 1
            music = music.loop(n=loops).subclip(0, TARGET_DURATION)
        else:
            music = music.subclip(0, TARGET_DURATION)
        final_video = final_video.set_audio(music)
    
    output_file = os.path.join(
        VIDEO_CONFIG['output_folder'], 
        'youtube_shorts', 
        f"{sign}_{datetime.now().strftime('%Y%m%d')}.mp4"
    )
    
    final_video.write_videofile(
        output_file, 
        fps=SHORTS_CONFIG['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None
    )
    
    print(f"  ✅ Video created")
    
    # Cleanup
    bg_original.close()
    bg_clip.close()
    final_video.close()
    
    return output_file


# ========================================
# MAIN - ONE AT A TIME
# ========================================

def main():
    print("="*60)
    print("🌟 ASTROFINANCE DAILY - GENERATE → UPLOAD → DELETE")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    print("="*60)
    
    # Check credentials
    if GROQ_API_KEY:
        print("🤖 AI: Groq ✅")
    elif HUGGINGFACE_API_KEY:
        print("🤖 AI: HuggingFace ✅")
    else:
        print("⚠️ No AI key - using fallback")
    
    if all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN]):
        print("📺 YouTube: Configured ✅")
        auto_upload = True
    else:
        print("⚠️ YouTube: Not configured - videos will be saved locally")
        auto_upload = False
    
    print("\n🔄 Processing one sign at a time...")
    print("="*60)
    
    results = []
    
    for i, sign in enumerate(ZODIAC_SIGNS, 1):
        print(f"\n[{i}/12] 🔮 {sign}")
        print("-" * 40)
        
        try:
            # Step 1: Generate content
            content = get_content_for_sign(sign)
            
            # Step 2: Create video
            video_path = create_short(sign, content)
            
            # Step 3: Upload to YouTube (if configured)
            youtube_url = None
            if auto_upload:
                youtube_url = upload_to_youtube(video_path, sign)
                
                # Wait 30 seconds between uploads to avoid rate limits
                if youtube_url and i < len(ZODIAC_SIGNS):
                    print(f"    ⏳ Waiting 30s before next upload...")
                    time.sleep(30)
            
            # Step 4: Delete video file to save space
            try:
                os.remove(video_path)
                print(f"  🗑️ Local file deleted")
            except:
                print(f"  ⚠️ Could not delete local file")
            
            # Track results
            results.append({
                'sign': sign,
                'success': True,
                'youtube_url': youtube_url
            })
            
            print(f"  ✅ {sign} complete!")
            
        except Exception as e:
            print(f"  ❌ {sign} failed: {e}")
            results.append({
                'sign': sign,
                'success': False,
                'error': str(e)
            })
    
    # Summary
    print("\n" + "="*60)
    print("📊 FINAL SUMMARY")
    print("="*60)
    
    successful = [r for r in results if r['success']]
    failed = [r for r in results if not r['success']]
    
    print(f"✅ Successful: {len(successful)}/12")
    for r in successful:
        if r.get('youtube_url'):
            print(f"   • {r['sign']}: {r['youtube_url']}")
        else:
            print(f"   • {r['sign']}: Video created locally")
    
    if failed:
        print(f"\n❌ Failed: {len(failed)}/12")
        for r in failed:
            print(f"   • {r['sign']}: {r.get('error', 'Unknown error')}")
    
    print("\n💰 COST: $0.00")
    print("="*60)


if __name__ == "__main__":
    main()
