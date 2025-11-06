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
        except Exception as e:
            print(f"      ⚠️ Groq failed: {e}")
    
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
        except Exception as e:
            print(f"      ⚠️ HuggingFace failed: {e}")
    
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
        heading = heading.fadein(0.8).fadeout(0.8)
        underline = underline.fadein(0.8).fadeout(0.8)
    
    return heading, underline


def create_text_chunks(text, font_size, screen_size, total_duration):
    """Split text intelligently based on content length with adaptive timing"""
    # Wrap text to fit screen
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped_lines.extend(textwrap.wrap(line, width=35))
    
    total_lines = len(wrapped_lines)
    print(f"      📄 Total lines: {total_lines}")
    
    # Determine optimal lines per chunk based on content length
    if total_lines <= 8:
        # Short content - show all at once
        chunks = ["\n".join(wrapped_lines)]
        print(f"      ✓ Short content: 1 chunk with {total_lines} lines")
    elif total_lines <= 16:
        # Medium content - split in half (8 lines each)
        mid = len(wrapped_lines) // 2
        chunks = [
            "\n".join(wrapped_lines[:mid]),
            "\n".join(wrapped_lines[mid:])
        ]
        print(f"      ✓ Medium content: 2 chunks ({mid} + {len(wrapped_lines)-mid} lines)")
    else:
        # Long content - split into 9-line chunks
        LINES_PER_CHUNK = 9
        chunks = []
        for i in range(0, len(wrapped_lines), LINES_PER_CHUNK):
            chunk_lines = wrapped_lines[i:i + LINES_PER_CHUNK]
            chunks.append("\n".join(chunk_lines))
        print(f"      ✓ Long content: {len(chunks)} chunks (~9 lines each)")
    
    # Calculate duration per chunk - give more time to chunks with more lines
    text_clips = []
    
    if len(chunks) == 1:
        # Single chunk - use full duration
        clip = TextClip(
            chunks[0],
            fontsize=font_size,
            color="#F5F5F5",
            method='label',
            align='center'
        ).set_duration(total_duration).set_start(0).fadein(0.8).fadeout(0.8)
        text_clips.append(clip)
    else:
        # Multiple chunks - distribute time proportionally
        chunk_line_counts = [len(chunk.split('\n')) for chunk in chunks]
        total_lines_all = sum(chunk_line_counts)
        
        current_time = 0
        for i, chunk in enumerate(chunks):
            # Allocate time based on line count proportion
            lines_in_chunk = chunk_line_counts[i]
            chunk_duration = (lines_in_chunk / total_lines_all) * total_duration
            
            # Minimum 3 seconds per chunk for readability
            chunk_duration = max(3.0, chunk_duration)
            
            clip = TextClip(
                chunk,
                fontsize=font_size,
                color="#F5F5F5",
                method='label',
                align='center'
            ).set_duration(chunk_duration).set_start(current_time).fadein(0.8).fadeout(0.8)
            
            text_clips.append(clip)
            print(f"      Chunk {i+1}: {lines_in_chunk} lines = {chunk_duration:.1f}s")
            current_time += chunk_duration
    
    return text_clips


def create_short(sign, content):
    """Create short with ADAPTIVE timing based on content length"""
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    sign_color = "#F5F5F5"
    
    # Calculate content lengths
    horo_length = len(content['horoscope'])
    wealth_length = len(content['wealth'])
    health_length = len(content['health'])
    total_content_length = horo_length + wealth_length + health_length
    
    print(f"  📊 Content lengths: Horo={horo_length}, Wealth={wealth_length}, Health={health_length}")
    
    # Available time for content (59 - 5 for subscribe)
    AVAILABLE_TIME = 54
    SUBSCRIBE_DURATION = 5
    TARGET_DURATION = 59
    
    # Distribute time proportionally based on content length
    horo_time = max(15, int((horo_length / total_content_length) * AVAILABLE_TIME))
    wealth_time = max(12, int((wealth_length / total_content_length) * AVAILABLE_TIME))
    health_time = AVAILABLE_TIME - horo_time - wealth_time  # Remainder
    
    # Ensure minimum times
    health_time = max(12, health_time)
    
    print(f"  ⏱️ Timing: Horo={horo_time}s, Wealth={wealth_time}s, Health={health_time}s, Subscribe={SUBSCRIBE_DURATION}s")
    print(f"  ⏱️ Total: {horo_time + wealth_time + health_time + SUBSCRIBE_DURATION}s")
    
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
    MAIN_DURATION = horo_time + wealth_time + health_time
    
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
    
    # 1. TITLE (SIGN + DATE)
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
    
    # 2. HOROSCOPE (adaptive timing)
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        sign_color,
        horo_time,
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    print(f"    Creating horoscope chunks...")
    horo_chunks = create_text_chunks(content['horoscope'], TEXT_STYLE['content_font_size'] - 5, screen_size, horo_time)
    for chunk in horo_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += horo_time
    
    # 3. WEALTH (adaptive timing)
    print(f"    Creating wealth chunks...")
    wealth_chunks = create_text_chunks(content['wealth'], TEXT_STYLE['tip_font_size'] - 5, screen_size, wealth_time)
    for chunk in wealth_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += wealth_time
    
    # 4. HEALTH (adaptive timing)
    print(f"    Creating health chunks...")
    health_chunks = create_text_chunks(content['health'], TEXT_STYLE['tip_font_size'] - 5, screen_size, health_time)
    for chunk in health_chunks:
        chunk = chunk.set_position(('center', TEXT_Y))
        chunk_with_offset = chunk.set_start(current_time + chunk.start)
        all_clips.append(chunk_with_offset)
    current_time += health_time
    
    # 5. SUBSCRIBE SCREEN (5s)
    print(f"  📺 Adding subscribe (5s)...")
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
        print("\n💡 If good, change TEST_SIGN to loop through all signs:")
        print("   for sign in ZODIAC_SIGNS:")
        print("       content = get_content_for_sign(sign)")
        print("       create_short(sign, content)")
        print("\n💰 COST: $0.00")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
