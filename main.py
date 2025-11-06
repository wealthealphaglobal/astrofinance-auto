import os
from datetime import datetime
import textwrap
import yaml
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

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)


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


def create_short(sign):
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    sign_color = "#F5F5F5"  # soft white for all text
    
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
    
    # Loop background if needed
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background ready")
    
    # All clips
    all_clips = []
    current_time = 0
    
    # === POSITION SETTINGS ===
    HEADING_Y = 100        # base heading position (requested)
    TEXT_Y = 910           # main text 7 rows down (~210px lower)
    
    # Adjustments to avoid overlay
    SIGN_Y = HEADING_Y + 60          # sign slightly down
    DATE_Y = SIGN_Y + 130            # date pushed further down to avoid overlap
    HORO_HEADING_Y = HEADING_Y - 60  # Daily Horoscope slightly up
    
    # === 1. TITLE (SIGN + DATE) — visible entire video ===
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        sign_color,
        TARGET_DURATION,
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
    ).set_duration(TARGET_DURATION).set_position(('center', DATE_Y))
    all_clips.append(date_clip)
    
    # === 2. HOROSCOPE (15s) ===
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
        f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition.",
        TEXT_STYLE['content_font_size'] - 5,
        sign_color,
        15,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(horo_text)
    current_time += 15
    
    # === 3. WEALTH TEXT ONLY (12s) ===
    wealth_text = create_text_clip(
        "Do: Plan finances with Mercury's clarity. Strategic thinking favors you.\n\nDon't: Rush major investments. Patience brings returns.",
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,
        12,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(wealth_text)
    current_time += 12
    
    # === 4. HEALTH TEXT ONLY (13s) ===
    health_text = create_text_clip(
        "The Moon stirs emotions. Drink water mindfully and practice deep breathing. Blessings for vitality.",
        TEXT_STYLE['tip_font_size'] - 5,
        sign_color,
        13,
        screen_size
    ).set_position(('center', TEXT_Y)).set_start(current_time)
    all_clips.append(health_text)
    
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
    print("\n⚠️  TEST MODE: Generating only 1 short (Aries)\n")
    
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
