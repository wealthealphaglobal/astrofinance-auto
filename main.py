import os
from datetime import datetime
import textwrap
import yaml
import random
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, concatenate_audioclips
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
PROMPTS = CONFIG['free_ai']['prompts']

# Mystical color palette
MYSTICAL_COLORS = [
    '#E6C27A',  # Soft Gold
    '#F1D18A',  # Pale Amber
    '#DDE1E4',  # Silver
    '#F4F4F4',  # Cool White
    '#B8A1E0',  # Lavender
    '#A597E8',  # Soft Violet
    '#9CC9E3',  # Misty Blue
    '#AEEAF5',  # Cyan Glow
    '#FFF9E3',  # Warm White
]

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)

def create_text_clip(text, font_size, color, shadow_color, duration, screen_size):
    """Create a stylized TextClip with word wrap."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=25))
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color=color,
        stroke_color=shadow_color,
        stroke_width=3,
        method='caption',
        size=(screen_size[0] - 120, None),
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_short(sign):
    print(f"⏳ Starting {sign} short...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Pick random mystical color for this sign
    sign_color = random.choice(MYSTICAL_COLORS)
    print(f"  🎨 Color: {sign_color}")
    
    # Load background video
    bg_clip = VideoFileClip(VIDEO_CONFIG['background_video'])
    
    # Calculate crop to fit vertical format
    target_w, target_h = screen_size
    bg_w, bg_h = bg_clip.size
    
    # Scale to fit height
    scale = target_h / bg_h
    new_w = int(bg_w * scale)
    
    if new_w >= target_w:
        bg_clip = bg_clip.resize(height=target_h)
        x_center = bg_clip.w / 2
        x1 = int(x_center - target_w / 2)
        bg_clip = bg_clip.crop(x1=x1, width=target_w)
    else:
        bg_clip = bg_clip.resize(width=target_w)
        if bg_clip.h > target_h:
            y_center = bg_clip.h / 2
            y1 = int(y_center - target_h / 2)
            bg_clip = bg_clip.crop(y1=y1, height=target_h)
    
    print(f"  ✅ Background: {bg_clip.size}")
    
    # Content (use prompts or fallback)
    today = datetime.now().strftime("%d %b %Y")
    title_text = f"✨ {sign} ✨\n{today}"
    
    horoscope_text = f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition and embrace the cosmic flow. Your inner wisdom guides you perfectly."
    
    wealth_text = f"💰 Wealth Guidance\n\nDo: Plan your finances with Mercury's clarity. Strategic thinking favors you now.\n\nDon't: Rush major investments today. Patience brings better returns."
    
    health_text = f"🏥 Wellness Blessing\n\nThe Moon stirs emotions today. Drink water mindfully and practice 5 minutes of deep breathing. Your body seeks balance. Blessings for vitality and peace."
    
    # Create clips with longer durations
    clips = []
    
    # Title - 5 seconds
    title_clip = create_text_clip(
        title_text,
        font_size=TEXT_STYLE['title_font_size'],
        color=sign_color,
        shadow_color='black',
        duration=5,
        screen_size=screen_size
    ).set_position(('center', 'center'))
    clips.append(title_clip)
    
    # Horoscope - 15 seconds
    horoscope_clip = create_text_clip(
        horoscope_text,
        font_size=TEXT_STYLE['content_font_size'],
        color=sign_color,
        shadow_color='black',
        duration=15,
        screen_size=screen_size
    ).set_position(('center', screen_size[1] - 800))  # 5 lines lower
    clips.append(horoscope_clip)
    
    # Wealth - 12 seconds
    wealth_clip = create_text_clip(
        wealth_text,
        font_size=TEXT_STYLE['tip_font_size'],
        color=sign_color,
        shadow_color='black',
        duration=12,
        screen_size=screen_size
    ).set_position(('center', screen_size[1] - 800))
    clips.append(wealth_clip)
    
    # Health - 13 seconds
    health_clip = create_text_clip(
        health_text,
        font_size=TEXT_STYLE['tip_font_size'],
        color=sign_color,
        shadow_color='black',
        duration=13,
        screen_size=screen_size
    ).set_position(('center', screen_size[1] - 800))
    clips.append(health_clip)
    
    # Composite clips on background
    total_duration = sum(c.duration for c in clips)
    print(f"  ⏱️ Total duration: {total_duration:.1f}s")
    
    # Loop background if needed
    if bg_clip.duration < total_duration:
        loops = int(total_duration / bg_clip.duration) + 1
        bg_clip = concatenate_videoclips([bg_clip] * loops)
    bg_clip = bg_clip.subclip(0, total_duration)
    
    # Create composite
    final_clips = []
    current_time = 0
    
    for clip in clips:
        composite = CompositeVideoClip([
            bg_clip.subclip(current_time, current_time + clip.duration),
            clip
        ]).set_duration(clip.duration)
        final_clips.append(composite)
        current_time += clip.duration
    
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Add OM Mantra background music
    if os.path.exists(VIDEO_CONFIG['background_music']):
        print(f"  🎵 Adding OM Mantra...")
        music = AudioFileClip(VIDEO_CONFIG['background_music'])
        music = music.volumex(VIDEO_CONFIG['music_volume'])
        
        if music.duration < final_video.duration:
            loops = int(final_video.duration / music.duration) + 1
            music = concatenate_audioclips([music] * loops)
        
        music = music.subclip(0, final_video.duration)
        final_video = final_video.set_audio(music)
    
    # Ensure under 58 seconds for YouTube Shorts
    if final_video.duration > 58:
        final_video = final_video.subclip(0, 58)
        print(f"  ⚠️ Trimmed to 58s for Shorts compliance")
    
    output_file = os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts', f"{sign}_{datetime.now().strftime('%Y%m%d')}.mp4")
    
    final_video.write_videofile(
        output_file, 
        fps=SHORTS_CONFIG['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='fast',
        threads=4,
        logger=None
    )
    
    print(f"✅ Completed {sign} short! ({final_video.duration:.1f}s)")
    
    # Cleanup
    bg_clip.close()
    final_video.close()

def main():
    print("="*60)
    print("🌟 ASTROFINANCE DAILY - VEDIC SHORTS")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}\n")
    
    for sign in ZODIAC_SIGNS:
        create_short(sign)
    
    print("\n"+"="*60)
    print("✅ All 12 shorts completed!")
    print("="*60)
    print(f"📁 {VIDEO_CONFIG['output_folder']}/youtube_shorts/")
    print("💰 COST: $0.00")

if __name__ == "__main__":
    main()
