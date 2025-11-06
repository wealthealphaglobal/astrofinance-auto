import os
from datetime import datetime
import textwrap
import yaml
import random
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

# Vibrant, eye-catching colors
VIBRANT_COLORS = [
    '#FFD700',  # Gold
    '#FF6B9D',  # Pink
    '#00E5FF',  # Cyan
    '#FF9500',  # Orange
    '#B388FF',  # Purple
    '#69F0AE',  # Mint Green
    '#FFE57F',  # Yellow
    '#FF80AB',  # Rose
    '#64FFDA',  # Turquoise
    '#FFAB40',  # Amber
    '#EA80FC',  # Lavender
    '#82E9DE',  # Aqua
]

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)

def create_heading(text, font_size, color, duration, screen_size):
    """Create BOLD, BIGGER heading with underline - NO background box."""
    # Main heading - BOLD and BIGGER
    heading = TextClip(
        text,
        fontsize=font_size + 20,  # Make it bigger
        color=color,
        font='Arial-Bold',  # Bold font
        stroke_color='black',
        stroke_width=5,  # Thicker stroke
        method='label'  # No background box
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    
    # Underline
    underline = TextClip(
        "━" * 20,
        fontsize=font_size // 2,
        color=color,
        stroke_color='black',
        stroke_width=3,
        method='label'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    
    return heading, underline

def create_text_clip(text, font_size, color, duration, screen_size):
    """Create text without background box."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=28))
    
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color=color,  # Use vibrant color
        stroke_color='black',
        stroke_width=3,
        method='label',  # NO background box
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_short(sign):
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Pick vibrant color
    sign_color = random.choice(VIBRANT_COLORS)
    print(f"  🎨 Color: {sign_color}")
    
    TARGET_DURATION = 45
    print(f"  ⏱️ Duration: {TARGET_DURATION}s")
    
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
    
    # Loop if needed
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background ready")
    
    # All clips
    all_clips = []
    current_time = 0
    
    # Position settings
    HEADING_Y = 300  # Heading stays here
    TEXT_Y = 700     # Text 5-6 lines down (400px lower)
    
    # 1. TITLE with Sign (5s)
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        sign_color,
        5,
        screen_size
    )
    title_heading = title_heading.set_position(('center', HEADING_Y)).set_start(current_time)
    title_underline = title_underline.set_position(('center', HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([title_heading, title_underline])
    
    # Date
    date_clip = TextClip(
        datetime.now().strftime("%d %b %Y"),
        fontsize=35,
        color='white',
        stroke_color='black',
        stroke_width=2,
        method='label'
    ).set_duration(5).set_position(('center', HEADING_Y + 150)).set_start(current_time).fadein(0.5).fadeout(0.5)
    all_clips.append(date_clip)
    current_time += 5
    
    # 2. HOROSCOPE (15s)
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        sign_color,
        15,
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    # Text in VIBRANT color, 5-6 lines down
    horo_text = create_text_clip(
        f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition.",
        TEXT_STYLE['content_font_size'] - 5,
        sign_color,  # VIBRANT COLOR for text
        15,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(horo_text)
    current_time += 15
    
    # 3. WEALTH (12s)
    wealth_heading, wealth_underline = create_heading(
        "💰 Wealth Guidance",
        TEXT_STYLE['tip_font_size'],
        sign_color,
        12,
        screen_size
    )
    wealth_heading = wealth_heading.set_position(('center', HEADING_Y)).set_start(current_time)
    wealth_underline = wealth_underline.set_position(('center', HEADING_Y + 90)).set_start(current_time)
    all_clips.extend([wealth_heading, wealth_underline])
    
    wealth_text = create_text_clip(
        "Do: Plan finances with Mercury's clarity. Strategic thinking favors you.\n\nDon't: Rush major investments. Patience brings returns.",
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,  # VIBRANT COLOR
        12,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(wealth_text)
    current_time += 12
    
    # 4. HEALTH (13s)
    health_heading, health_underline = create_heading(
        "🏥 Wellness Blessing",
        TEXT_STYLE['tip_font_size'],
        sign_color,
        13,
        screen_size
    )
    health_heading = health_heading.set_position(('center', HEADING_Y)).set_start(current_time)
    health_underline = health_underline.set_position(('center', HEADING_Y + 90)).set_start(current_time)
    all_clips.extend([health_heading, health_underline])
    
    health_text = create_text_clip(
        "The Moon stirs emotions. Drink water mindfully and practice deep breathing. Blessings for vitality.",
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,  # VIBRANT COLOR
        13,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(health_text)
    
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
    
    # Limit to 58s
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
    print("\n⚠️  TEST MODE: Generating only 1 short (Aries)\n")
    
    # TEST: Only generate Aries
    TEST_SIGN = "Aries"
    
    try:
        video = create_short(TEST_SIGN)
        print("\n"+"="*60)
        print(f"✅ TEST SUCCESSFUL!")
        print("="*60)
        print(f"📁 Video saved: {video}")
        print(f"📥 Download from: {VIDEO_CONFIG['output_folder']}/youtube_shorts/")
        print("\n💡 If this looks good, change TEST MODE to generate all 12 signs")
        print("💰 COST: $0.00")
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
