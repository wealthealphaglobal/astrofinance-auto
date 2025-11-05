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

# Vibrant, eye-catching colors with good contrast
VIBRANT_COLORS = [
    '#FFD700',  # Gold - bright and royal
    '#FF6B9D',  # Pink - warm and inviting
    '#00E5FF',  # Cyan - bright and energetic
    '#FF9500',  # Orange - vibrant and warm
    '#B388FF',  # Purple - mystical and elegant
    '#69F0AE',  # Mint Green - fresh and calming
    '#FFE57F',  # Yellow - cheerful and bright
    '#FF80AB',  # Rose - soft but visible
    '#64FFDA',  # Turquoise - spiritual and bright
    '#FFAB40',  # Amber - warm and glowing
    '#EA80FC',  # Lavender - mystical and bright
    '#82E9DE',  # Aqua - serene and bright
]

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)

def create_text_clip(text, font_size, color, duration, screen_size, bold=False):
    """Create a stylized TextClip with word wrap and strong contrast."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=25))
    
    # Use larger stroke for better visibility
    stroke_width = 4 if bold else 3
    
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color=color,
        bg_color='rgba(0,0,0,0.7)',  # Semi-transparent black background
        stroke_color='black',
        stroke_width=stroke_width,
        method='caption',
        size=(screen_size[0] - 120, None),
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_heading_with_underline(text, font_size, color, duration, screen_size):
    """Create heading with underline effect using two clips."""
    # Main heading
    heading = TextClip(
        text,
        fontsize=font_size,
        color=color,
        bg_color='rgba(0,0,0,0.8)',
        stroke_color='black',
        stroke_width=4,
        method='caption',
        size=(screen_size[0] - 120, None),
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    
    # Underline (using dashes or special characters)
    underline_text = "━" * 15  # Unicode line character
    underline = TextClip(
        underline_text,
        fontsize=font_size // 2,
        color=color,
        stroke_color='black',
        stroke_width=2,
        method='caption',
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    
    return heading, underline

def create_short(sign):
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Pick vibrant color for this sign
    sign_color = random.choice(VIBRANT_COLORS)
    print(f"  🎨 Color: {sign_color}")
    
    # Target duration: 45 seconds
    TARGET_DURATION = 45
    print(f"  ⏱️ Duration: {TARGET_DURATION}s")
    
    # Load background video ONCE
    bg_original = VideoFileClip(VIDEO_CONFIG['background_video'])
    
    # Crop to vertical format
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
    
    # Loop background if needed
    if bg_original.duration < TARGET_DURATION:
        loops_needed = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops_needed).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background ready: {bg_clip.size}")
    
    # Content with timings
    today = datetime.now().strftime("%d %b %Y")
    
    all_clips = []
    current_time = 0
    
    # 1. TITLE with Sign (5s)
    title_heading, title_underline = create_heading_with_underline(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        sign_color,
        5,
        screen_size
    )
    title_heading = title_heading.set_position(('center', 400)).set_start(current_time)
    title_underline = title_underline.set_position(('center', 520)).set_start(current_time)
    all_clips.extend([title_heading, title_underline])
    
    # Date subtitle
    date_clip = TextClip(
        today,
        fontsize=40,
        color='white',
        stroke_color='black',
        stroke_width=2
    ).set_duration(5).set_position(('center', 580)).set_start(current_time).fadein(0.5).fadeout(0.5)
    all_clips.append(date_clip)
    current_time += 5
    
    # 2. HOROSCOPE (15s)
    horo_heading, horo_underline = create_heading_with_underline(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'] + 10,
        sign_color,
        15,
        screen_size
    )
    horo_heading = horo_heading.set_position(('center', 300)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', 400)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    horo_text = create_text_clip(
        f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition.",
        TEXT_STYLE['content_font_size'],
        'white',  # White text for body content
        15,
        screen_size
    ).set_position(('center', 500)).set_start(current_time)
    all_clips.append(horo_text)
    current_time += 15
    
    # 3. WEALTH (12s)
    wealth_heading, wealth_underline = create_heading_with_underline(
        "💰 Wealth Guidance",
        TEXT_STYLE['tip_font_size'] + 10,
        sign_color,
        12,
        screen_size
    )
    wealth_heading = wealth_heading.set_position(('center', 300)).set_start(current_time)
    wealth_underline = wealth_underline.set_position(('center', 390)).set_start(current_time)
    all_clips.extend([wealth_heading, wealth_underline])
    
    wealth_text = create_text_clip(
        "Do: Plan finances with Mercury's clarity. Strategic thinking favors you.\n\nDon't: Rush major investments. Patience brings better returns.",
        TEXT_STYLE['tip_font_size'],
        'white',
        12,
        screen_size
    ).set_position(('center', 500)).set_start(current_time)
    all_clips.append(wealth_text)
    current_time += 12
    
    # 4. HEALTH (13s)
    health_heading, health_underline = create_heading_with_underline(
        "🏥 Wellness Blessing",
        TEXT_STYLE['tip_font_size'] + 10,
        sign_color,
        13,
        screen_size
    )
    health_heading = health_heading.set_position(('center', 300)).set_start(current_time)
    health_underline = health_underline.set_position(('center', 390)).set_start(current_time)
    all_clips.extend([health_heading, health_underline])
    
    health_text = create_text_clip(
        "The Moon stirs emotions. Drink water mindfully and practice deep breathing. Blessings for vitality and peace.",
        TEXT_STYLE['tip_font_size'],
        'white',
        13,
        screen_size
    ).set_position(('center', 500)).set_start(current_time)
    all_clips.append(health_text)
    
    # Composite everything
    final_video = CompositeVideoClip([bg_clip] + all_clips).set_duration(TARGET_DURATION)
    
    # Add OM Mantra music
    if os.path.exists(VIDEO_CONFIG['background_music']):
        print(f"  🎵 Adding OM Mantra...")
        music = AudioFileClip(VIDEO_CONFIG['background_music'])
        music = music.volumex(VIDEO_CONFIG['music_volume'])
        
        if music.duration < TARGET_DURATION:
            loops = int(TARGET_DURATION / music.duration) + 1
            music = music.loop(n=loops).subclip(0, TARGET_DURATION)
        else:
            music = music.subclip(0, TARGET_DURATION)
        
        final_video = final_video.set_audio(music)
    
    # Ensure under 58 seconds
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
    
    print(f"  ✅ Completed! ({final_video.duration:.1f}s)")
    
    # Cleanup
    bg_original.close()
    bg_clip.close()
    final_video.close()
    
    return output_file

def main():
    print("="*60)
    print("🌟 ASTROFINANCE DAILY - VEDIC SHORTS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    print("="*60)
    
    created = []
    for sign in ZODIAC_SIGNS:
        try:
            video = create_short(sign)
            created.append(video)
        except Exception as e:
            print(f"  ❌ Error creating {sign}: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n"+"="*60)
    print(f"✅ Completed {len(created)}/12 shorts!")
    print("="*60)
    print(f"📁 {VIDEO_CONFIG['output_folder']}/youtube_shorts/")
    for video in created:
        print(f"   ✓ {os.path.basename(video)}")
    print("💰 COST: $0.00")

if __name__ == "__main__":
    main()
