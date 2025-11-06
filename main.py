import os
from datetime import datetime
import textwrap
import yaml
import requests
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, ImageClip
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
                        {"role": "system", "content": "You are a warm Vedic astrologer."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
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
                    "parameters": {"max_new_tokens": 200, "temperature": 0.7}
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


def get_content_for_sign(sign):
    """Get horoscope, wealth, and health content"""
    print(f"    📝 Fetching content...")
    
    # Horoscope
    horo = fetch_ai_content(CONFIG['free_ai']['prompts']['horoscope'], sign)
    if not horo:
        horo = f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition."
    horo = horo.replace("**", "").replace("*", "").strip()
    
    # Wealth
    wealth = fetch_ai_content(CONFIG['free_ai']['prompts']['wealth'], sign)
    if not wealth:
        wealth = "Do: Plan finances with Mercury's clarity. Strategic thinking favors you.\n\nDon't: Rush major investments. Patience brings returns."
    wealth = wealth.replace("**", "").replace("*", "").strip()
    
    # Health
    health = fetch_ai_content(CONFIG['free_ai']['prompts']['health'], sign)
    if not health:
        health = "The Moon stirs emotions. Drink water mindfully and practice deep breathing. Blessings for vitality."
    health = health.replace("**", "").replace("*", "").strip()
    
    print(f"    ✅ Content ready")
    return {'horoscope': horo, 'wealth': wealth, 'health': health}


# ========================================
# YOUR ORIGINAL VIDEO FUNCTIONS
# ========================================

def create_heading(text, font_size, color, duration, screen_size, fade=True):
    """Create BOLD, BIGGER heading with underline - NO background box."""
    heading = TextClip(
        text,
        fontsize=font_size + 20,
        color="#F5F5F5",  # soft white
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
        heading = heading.fadein(0.5).fadeout(0.5)
        underline = underline.fadein(0.5).fadeout(0.5)
    
    return heading, underline


def create_text_clip(text, font_size, color, duration, screen_size):
    """Create wrapped text without background box."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=28))
    
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color="#F5F5F5",  # soft white
        method='label',
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip


def create_short(sign, content):
    """YOUR ORIGINAL FUNCTION with API content + subscribe screen"""
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    sign_color = "#F5F5F5"  # soft white for all text
    
    MAIN_DURATION = 45  # Your original duration
    SUBSCRIBE_DURATION = 10  # New subscribe screen
    TARGET_DURATION = MAIN_DURATION + SUBSCRIBE_DURATION  # 55 seconds total
    
    print(f"  ⏱️ Duration: {TARGET_DURATION}s (45s content + 10s subscribe)")
    
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
    
    # Loop background if needed (now for 55 seconds)
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background ready")
    
    # All clips
    all_clips = []
    current_time = 0
    
    # === POSITION SETTINGS (YOUR ORIGINAL) ===
    HEADING_Y = 100        # base heading position (requested)
    TEXT_Y = 910           # main text 7 rows down (~210px lower)
    
    # Adjustments to avoid overlay
    SIGN_Y = HEADING_Y + 60          # sign slightly down
    DATE_Y = SIGN_Y + 130            # date pushed further down to avoid overlap
    HORO_HEADING_Y = HEADING_Y - 60  # Daily Horoscope slightly up
    
    # === 1. TITLE (SIGN + DATE) — visible for main content only (45s) ===
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        sign_color,
        MAIN_DURATION,  # Only show for 45s
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
    ).set_duration(MAIN_DURATION).set_position(('center', DATE_Y))  # Only 45s
    all_clips.append(date_clip)
    
    # === 2. HOROSCOPE (15s) - NOW WITH REAL API CONTENT ===
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        sign_color,
        15,
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    horo_text = create_text_clip(
        content['horoscope'],  # REAL API CONTENT
        TEXT_STYLE['content_font_size'] - 5,
        sign_color,
        15,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(horo_text)
    current_time += 15
    
    # === 3. WEALTH TEXT ONLY (12s) - REAL API CONTENT ===
    wealth_text = create_text_clip(
        content['wealth'],  # REAL API CONTENT
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,
        12,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(wealth_text)
    current_time += 12
    
    # === 4. HEALTH TEXT ONLY (13s) - REAL API CONTENT ===
    health_text = create_text_clip(
        content['health'],  # REAL API CONTENT
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,
        13,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(health_text)
    current_time += 13  # Now at 45 seconds
    
    # === 5. SUBSCRIBE SCREEN (10s) - NEW ===
    if os.path.exists('sub.png'):
        print(f"  📺 Adding sub.png...")
        sub_img = ImageClip('sub.png').set_duration(SUBSCRIBE_DURATION)
        sub_img = sub_img.resize(height=screen_size[1])
        sub_img = sub_img.set_position('center').set_start(MAIN_DURATION).fadein(0.5)
        all_clips.append(sub_img)
    else:
        print(f"  ⚠️ sub.png not found - creating text screen")
        sub_text = TextClip(
            "🔔 LIKE • SHARE • SUBSCRIBE\n\nFor Daily Cosmic Guidance",
            fontsize=50,
            color="#FFD700",
            font='Arial-Bold',
            method='label',
            align='center'
        ).set_duration(SUBSCRIBE_DURATION).set_position('center').set_start(MAIN_DURATION).fadein(0.5)
        all_clips.append(sub_text)
    
    # === FINAL COMPOSITION ===
    final_video = CompositeVideoClip([bg_clip] + all_clips).set_duration(TARGET_DURATION)
    
    # Add OM Mantra background audio
    if os.path.exists(VIDEO_CONFIG['background_music']):
        print(f"  🎵 Adding OM Mantra...")
        music = AudioFileClip(VIDEO_CONFIG['background_music']).volumex(VIDEO_CONFIG['music_volume'])
        
        if music.duration < TARGET_DURATION:
            loops = int(TARGET_DURATION / music.duration) + 1
            music = music.loop(n=loops).subclip(0, TARGET_DURATION)
        else:
            music = music.subclip(0, TARGET_DURATION)
        
        final_video = final_video.set_audio(music)
    
    # Limit to 58s if needed
    if final_video.duration > 58:
        final_video = final_video.subclip(0, 58)
    
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
        # Fetch content from API
        content = get_content_for_sign(TEST_SIGN)
        
        # Create video
        video = create_short(TEST_SIGN, content)
        
        print("\n"+"="*60)
        print(f"✅ TEST SUCCESSFUL!")
        print("="*60)
        print(f"📁 Video: {video}")
        print(f"\n📝 Content used:")
        print(f"   Horo: {content['horoscope'][:50]}...")
        print(f"   Wealth: {content['wealth'][:50]}...")
        print(f"   Health: {content['health'][:50]}...")
        print("\n💡 If good, change to generate all 12 signs")
        print("💰 COST: $0.00")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
