import os
import datetime
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
import yaml
import time

# ==========================
# Load config
# ==========================
with open("config.yaml", "r") as f:
    CONFIG = yaml.safe_load(f)

VIDEO_CONFIG = CONFIG['video']
TEXT_STYLE = CONFIG['text_style']
ZODIAC_SIGNS = CONFIG['zodiac_signs']
FREE_AI = CONFIG['free_ai']
BRANDING = CONFIG['branding']

# ==========================
# Helper: RGB to HEX
# ==========================
def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % tuple(rgb)

# ==========================
# Helper: create text clip
# ==========================
def create_text_clip(text, font_size, duration, screen_size, color=None):
    txt_clip = TextClip(
        txt=text,
        fontsize=font_size,
        color=rgb_to_hex(color) if color else "#FFFFFF",
        font="DejaVu-Sans-Bold",
        stroke_color=rgb_to_hex(TEXT_STYLE['shadow_color']),
        stroke_width=2,
        method='caption',
        size=(int(screen_size[0]*0.8), None)
    ).set_duration(duration).set_position('center')
    return txt_clip

# ==========================
# Helper: generate content (stub)
# ==========================
def generate_content(sign):
    # Replace with actual API calls
    today = datetime.date.today().strftime("%d %b %Y")
    horoscope = f"{sign} Daily Horoscope: You will find clarity today. Cosmic energy is high."
    wealth = f"💰 Wealth Tips for {sign}:\n1. Save wisely\n2. Invest carefully\n3. Avoid impulsive spending"
    health = f"🏥 Health Tips for {sign}:\n1. Exercise daily\n2. Eat nutritious meals\n3. Meditate"
    return today, horoscope, wealth, health

# ==========================
# Create one short video per sign
# ==========================
def create_short(sign):
    print(f"⏳ Starting {sign} short...")
    youtube_shorts_config = VIDEO_CONFIG['platforms']['youtube']['shorts']
screen_size = youtube_shorts_config['resolution']
fps = youtube_shorts_config['fps']
duration = youtube_shorts_config['duration']

    bg_clip = VideoFileClip(VIDEO_CONFIG['background_video']).resize(height=screen_size[1])

    today, horoscope_text, wealth_text, health_text = generate_content(sign)

    clips = []

    # Title & Date
    title_clip = create_text_clip(f"{sign} Daily Forecast\n{today}", TEXT_STYLE['title_font_size'], 3, screen_size, TEXT_STYLE['font_color'])
    clips.append(title_clip)

    # Horoscope
    clips.append(create_text_clip(horoscope_text, TEXT_STYLE['content_font_size'], 5, screen_size, TEXT_STYLE['font_color']))

    # Wealth
    clips.append(create_text_clip(wealth_text, TEXT_STYLE['tip_font_size'], 5, screen_size, TEXT_STYLE['font_color']))

    # Health
    clips.append(create_text_clip(health_text, TEXT_STYLE['tip_font_size'], 5, screen_size, TEXT_STYLE['font_color']))

    final_clip = CompositeVideoClip([bg_clip.set_duration(sum(c.duration for c in clips))])
    final_clip = concatenate_videoclips(clips).set_audio(AudioFileClip(VIDEO_CONFIG['background_music']).volumex(VIDEO_CONFIG['music_volume']))

    output_path = os.path.join(VIDEO_CONFIG['output_folder'], f"{sign}_short.mp4")
    os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
    final_clip.write_videofile(output_path, fps=VIDEO_CONFIG['shorts']['fps'])
    print(f"✅ Completed {sign} short: {output_path}")

# ==========================
# Main
# ==========================
def main():
    for sign in ZODIAC_SIGNS:
        create_short(sign)

if __name__ == "__main__":
    main()
