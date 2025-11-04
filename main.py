import os
from datetime import datetime
import textwrap
import yaml
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips
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

# Ensure output folder exists
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)

def create_text_clip(text, font_size, color, shadow_color, duration, screen_size):
    """Create a stylized TextClip with word wrap and background."""
    wrapped_text = "\n".join(textwrap.wrap(text, width=30))
    txt_clip = TextClip(
        wrapped_text,
        fontsize=font_size,
        color=color,
        stroke_color=shadow_color,
        stroke_width=2,
        method='caption',
        size=(screen_size[0] - 100, None),
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_short(sign):
    print(f"⏳ Starting {sign} short...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Load background video - DON'T resize, use crop instead
    bg_clip = VideoFileClip(VIDEO_CONFIG['background_video'])
    
    # Calculate crop to fit vertical format
    target_w, target_h = screen_size
    bg_w, bg_h = bg_clip.size
    
    # Scale to fit height
    scale = target_h / bg_h
    new_w = int(bg_w * scale)
    
    if new_w >= target_w:
        # Wide enough - crop width
        bg_clip = bg_clip.resize(height=target_h)
        x_center = bg_clip.w / 2
        x1 = int(x_center - target_w / 2)
        bg_clip = bg_clip.crop(x1=x1, width=target_w)
    else:
        # Too narrow - scale by width instead
        bg_clip = bg_clip.resize(width=target_w)
        if bg_clip.h > target_h:
            y_center = bg_clip.h / 2
            y1 = int(y_center - target_h / 2)
            bg_clip = bg_clip.crop(y1=y1, height=target_h)
    
    print(f"  ✅ Background: {bg_clip.size}")
    
    # Title with date
    today = datetime.now().strftime("%d %b %Y")
    title_text = f"{sign} Daily Horoscope\n{today}"
    title_clip = create_text_clip(
        title_text,
        font_size=TEXT_STYLE['title_font_size'],
        color='white',
        shadow_color='black',
        duration=3,
        screen_size=screen_size
    )
    
    # Generate content (use fallback for now, add AI later)
    horoscope_text = f"Today brings positive energy for {sign}. Trust your intuition and embrace opportunities."
    wealth_text = f"Do: Plan your finances carefully. Don't: Rush into investments today."
    health_text = f"Take time for deep breathing. Stay hydrated. Blessings for balance."
    
    # Create content clips
    clips = [title_clip]
    
    for text_block, font_size in [
        (horoscope_text, TEXT_STYLE['content_font_size']),
        (wealth_text, TEXT_STYLE['tip_font_size']),
        (health_text, TEXT_STYLE['tip_font_size'])
    ]:
        if text_block.strip():
            clip = create_text_clip(
                text_block.strip(),
                font_size=font_size,
                color='white',
                shadow_color='black',
                duration=4,
                screen_size=screen_size
            )
            clips.append(clip)
    
    # Composite clips on background
    final_clips = []
    for clip in clips:
        composite = CompositeVideoClip([
            bg_clip.subclip(0, clip.duration),
            clip.set_position('center')
        ]).set_duration(clip.duration)
        final_clips.append(composite)
    
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Limit to 58 seconds
    if final_video.duration > 58:
        final_video = final_video.subclip(0, 58)
    
    output_file = os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts', f"{sign}_short.mp4")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    final_video.write_videofile(
        output_file, 
        fps=SHORTS_CONFIG['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='fast',
        logger=None
    )
    
    print(f"✅ Completed {sign} short!")
    
    # Cleanup
    bg_clip.close()
    final_video.close()

def main():
    print("🎬 Starting FREE content generation...\n")
    for sign in ZODIAC_SIGNS:
        create_short(sign)
    print("\n🎉 All shorts completed!")

if __name__ == "__main__":
    main()
