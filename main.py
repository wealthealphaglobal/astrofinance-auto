import os
from datetime import datetime
import textwrap
import yaml
import random
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip, concatenate_audioclips
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

# Mystical color palette
MYSTICAL_COLORS = [
    '#E6C27A', '#F1D18A', '#DDE1E4', '#F4F4F4',
    '#B8A1E0', '#A597E8', '#9CC9E3', '#AEEAF5', '#FFF9E3'
]

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)

def create_text_clip(text, font_size, color, duration, screen_size):
    """Create a stylized TextClip with word wrap."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=25))
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color=color,
        stroke_color='black',
        stroke_width=3,
        method='caption',
        size=(screen_size[0] - 120, None),
        align='center'
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_short(sign):
    print(f"\n🔮 [{sign}] — starting...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Pick random mystical color
    sign_color = random.choice(MYSTICAL_COLORS)
    print(f"  🎨 Color: {sign_color}")
    
    # Target duration: 40-45 seconds
    TARGET_DURATION = 45
    print(f"  ⏱️ Duration planned: {TARGET_DURATION}s")
    
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
    
    # Use loop parameter instead of concatenate
    if bg_original.duration < TARGET_DURATION:
        loops_needed = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops_needed).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    print(f"  ✅ Background: {bg_clip.size} for {TARGET_DURATION}s")
    
    # Content
    today = datetime.now().strftime("%d %b %Y")
    
    sections = [
        (f"✨ {sign} ✨\n{today}", TEXT_STYLE['title_font_size'], 5),
        (f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition and embrace the cosmic flow.", TEXT_STYLE['content_font_size'], 15),
        (f"💰 Wealth Guidance\n\nDo: Plan finances with Mercury's clarity. Strategic thinking favors you.\n\nDon't: Rush major investments. Patience brings better returns.", TEXT_STYLE['tip_font_size'], 12),
        (f"🏥 Wellness Blessing\n\nThe Moon stirs emotions. Drink water mindfully and practice deep breathing. Blessings for vitality and peace.", TEXT_STYLE['tip_font_size'], 13)
    ]
    
    # Create text overlays
    text_clips = []
    for text, font_size, duration in sections:
        clip = create_text_clip(text, font_size, sign_color, duration, screen_size)
        # Position lower (5 lines = ~250px lower)
        clip = clip.set_position(('center', screen_size[1] - 900))
        clip = clip.set_start(sum([s[2] for s in sections[:sections.index((text, font_size, duration))]]))
        text_clips.append(clip)
    
    # Composite: background + all text overlays at once
    final_video = CompositeVideoClip([bg_clip] + text_clips).set_duration(TARGET_DURATION)
    
    # Add OM Mantra music
    if os.path.exists(VIDEO_CONFIG['background_music']):
        print(f"  🎵 Adding OM Mantra...")
        music = AudioFileClip(VIDEO_CONFIG['background_music'])
        music = music.volumex(VIDEO_CONFIG['music_volume'])
        
        if music.duration < TARGET_DURATION:
            # Loop music
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
            print(f"  ❌ Error: {e}")
    
    print("\n"+"="*60)
    print(f"✅ Completed {len(created)}/12 shorts!")
    print("="*60)
    print(f"📁 {VIDEO_CONFIG['output_folder']}/youtube_shorts/")
    print("💰 COST: $0.00")

if __name__ == "__main__":
    main()
