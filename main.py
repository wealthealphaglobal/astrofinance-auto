import os
from datetime import datetime
import textwrap
import yaml
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip
from PIL import Image

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

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)


# ========================================
# API FETCHING FUNCTIONS
# ========================================

def fetch_ai_content(prompt, sign):
    """Fetch content from Groq or HuggingFace"""
    formatted_prompt = prompt.format(sign=sign)
    
    # Try Groq first
    if GROQ_API_KEY:
        try:
            print(f"      🤖 Groq AI...")
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
    
    # Try HuggingFace
    if HUGGINGFACE_API_KEY:
        try:
            print(f"      🤖 HuggingFace...")
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
    """Clean AI response and make it more concise/natural"""
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
    print(f"    📝 Fetching content...")
    
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
    
    print(f"    ✅ Content ready")
    return {'horoscope': horo, 'wealth': wealth, 'health': health}


# ========================================
# VIDEO CREATION FUNCTIONS
# ========================================

def create_heading(text, font_size, color, duration, screen_size, fade=True):
    """Create BOLD, BIGGER heading with underline"""
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
        heading = heading.fadein(0.8).fadeout(0.8)  # Slower fade
        underline = underline.fadein(0.8).fadeout(0.8)
    
    return heading, underline


def create_text_chunks(text, font_size, screen_size, total_duration):
    """Split text into chunks of 8-9 lines with SLOWER fade transitions"""
    # Wrap text to fit screen - using 35 chars per line for more text
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped_lines.extend(textwrap.wrap(line, width=35))
    
    # Force minimum lines if content is short
    if len(wrapped_lines) < 8:
        # If too short, just show all at once
        chunks = ["\n".join(wrapped_lines)]
    else:
        # Split into chunks of 8-9 lines
        LINES_PER_CHUNK = 9
        chunks = []
        
        for i in range(0, len(wrapped_lines), LINES_PER_CHUNK):
            chunk_lines = wrapped_lines[i:i + LINES_PER_CHUNK]
            chunk_text = "\n".join(chunk_lines)
            chunks.append(chunk_text)
    
    print(f"      📄 Split into {len(chunks)} chunk(s)")
    
    # Calculate duration per chunk with slower transitions
    chunk_duration = total_duration / len(chunks) if len(chunks) > 0 else total_duration
    
    # Create clips for each chunk
    text_clips = []
    current_time = 0
    
    for i, chunk in enumerate(chunks):
        print(f"      Chunk {i+1}: {len(chunk.split(chr(10)))} lines")
        
        clip = TextClip(
            chunk,
            fontsize=font_size,
            color="#F5F5F5",
            method='label',
            align='center'
        ).set_duration(chunk_duration).set_start(current_time)
        
        # Slower fade: 1 second in, 1 second out
        clip = clip.fadein(1.0).fadeout(1.0)
        
        text_clips.append(clip)
        current_time += chunk_duration
    
    return text_clips


def create_short(sign, content):
    """Create short with proper timing: 54s content + 5s subscribe = 59s total"""
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    sign_color = "#F5F5F5"
    
    # NEW TIMING: 54 seconds content + 5 seconds subscribe = 59 total
    MAIN_DURATION = 54  # Extended from 45
    SUBSCRIBE_DURATION = 5  # Reduced from 10
    TARGET_DURATION = MAIN_DURATION + SUBSCRIBE_DURATION  # 59 seconds
    
    print(f"  ⏱️ Duration: {TARGET_DURATION}s ({MAIN_DURATION}s content + {SUBSCRIBE_DURATION}s subscribe)")
    
    # Load background
    bg_original = VideoFileClip(VIDEO_CONFIG['background_video'])
    
    # Crop to vertical
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
    
    # Loop background
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background ready")
    
    all_clips = []
    current_time = 0
    
    # Position settings
    HEADING_Y = 100
    TEXT_Y = 910
    SIGN_Y = HEADING_Y + 60
    DATE_Y = SIGN_Y + 130
    HORO_HEADING_Y = HEADING_Y - 60
    
    # 1. TITLE (SIGN + DATE) — visible for 54s
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        sign_color,
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
    
    # 2. HOROSCOPE (20s) - More time, chunked with SLOW fade
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        sign_color,
        20,  # Extended from 15
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    print(f"    Creating horoscope chunks...")
    horo_chunks = create_text_chunks(content['horoscope'], TEXT_STYLE['content_font_size'] - 5, screen_size, 20)
    for chunk in horo_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += 20
    
    # 3. WEALTH (17s) - Extended, chunked with SLOW fade
    print(f"    Creating wealth chunks...")
    wealth_chunks = create_text_chunks(content['wealth'], TEXT_STYLE['tip_font_size'] - 5, screen_size, 17)
    for chunk in wealth_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += 17
    
    # 4. HEALTH (17s) - Extended, chunked with SLOW fade
    print(f"    Creating health chunks...")
    health_chunks = create_text_chunks(content['health'], TEXT_STYLE['tip_font_size'] - 5, screen_size, 17)
    for chunk in health_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += 17  # Now at 54 seconds
    
    # 5. SUBSCRIBE SCREEN (5s) - Shorter, last 5 seconds
    print(f"  📺 Adding subscribe (5s)...")
    sub_text = TextClip(
        "🔔 SUBSCRIBE\n\nLIKE • SHARE • COMMENT",
        fontsize=60,
        color="#FFD700",
        font='Arial-Bold',
        method='label',
        align='center'
    ).set_duration(SUBSCRIBE_DURATION).set_position('center').set_start(MAIN_DURATION).fadein(0.5)
    all_clips.append(sub_text)
    
    # Composite
    final_video = CompositeVideoClip([bg_clip] + all_clips).set_duration(TARGET_DURATION)
    
    # Add OM Mantra
    if os.path.exists(VIDEO_CONFIG['background_music']):
        print(f"  🎵 Adding OM Mantra...")
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
    
    print(f"  ✅ Done! ({final_video.duration:.1f}s)")
    
    # Cleanup
    bg_original.close()
    bg_clip.close()
    final_video.close()
    
    return output_file


def main():
    print("="*60)
    print("🌟 ASTROFINANCE DAILY - TEST MODE")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    print("="*60)
    
    if GROQ_API_KEY:
        print("🤖 API: Groq ✅")
    elif HUGGINGFACE_API_KEY:
        print("🤖 API: HuggingFace ✅")
    else:
        print("⚠️ No API key - using fallback")
    
    print("\n⚠️  TEST MODE: Generating only 1 short (Aries)\n")
    
    TEST_SIGN = "Aries"
    
    try:
        content = get_content_for_sign(TEST_SIGN)
        video = create_short(TEST_SIGN, content)
        
        print("\n"+"="*60)
        print(f"✅ TEST SUCCESSFUL!")
        print("="*60)
        print(f"📁 Video: {video}")
        print(f"\n📝 Content used:")
        print(f"   Horo: {content['horoscope']}")
        print(f"   Wealth: {content['wealth']}")
        print(f"   Health: {content['health']}")
        print("\n💡 If good, change to generate all 12 signs")
        print("💰 COST: $0.00")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
