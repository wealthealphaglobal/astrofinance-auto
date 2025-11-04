import os
import datetime
import yaml
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips, AudioFileClip
from time import sleep
import random

# ===============================
# Load config
# ===============================
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

VIDEO_CONFIG = config['video']
TEXT_STYLE = config['text_style']
ZODIAC_SIGNS = config['zodiac_signs']
FREE_AI = config['free_ai']
BRANDING = config['branding']

# Colors for each section
SECTION_COLORS = {
    'horoscope': (255, 215, 0),  # Gold
    'wealth': (0, 255, 0),       # Green
    'health': (30, 144, 255)     # Blue
}

# ===============================
# Dummy content generator (replace with HuggingFace/AI calls)
# ===============================
def generate_content(sign):
    """Simulate AI-generated horoscope, wealth, health content"""
    horoscope = [
        f"{sign} today is full of cosmic energy.",
        "Focus on personal growth and self-awareness.",
        "Opportunities in relationships and career are present.",
        "Trust your intuition and take bold steps."
    ]
    wealth = [
        "Track your expenses carefully today.",
        "Look for small investment opportunities.",
        "Avoid impulsive spending decisions."
    ]
    health = [
        "Meditate for at least 10 minutes today.",
        "Drink plenty of water and eat fresh fruits.",
        "Take a short walk to refresh your mind."
    ]
    return horoscope, wealth, health

# ===============================
# Helper function: create animated text clip
# ===============================
def create_text_clip(text, font_size, color, duration, screen_size):
    """Create a TextClip with fade-in/out effect"""
    txt_clip = TextClip(
        txt=text,
        fontsize=font_size,
        color=color,
        font='Arial-Bold',
        stroke_color=TEXT_STYLE['shadow_color'],
        stroke_width=2,
        method='caption',
        size=(int(screen_size[0]*0.8), None)  # 80% width
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip.set_position(('center', 'center'))

# ===============================
# Create a short video for one zodiac sign
# ===============================
def create_short(sign):
    print(f"▶️ Processing {sign}...")

    # 1. Load background video
    bg_clip = VideoFileClip(VIDEO_CONFIG['background_video']).subclip(0, VIDEO_CONFIG['shorts_duration'])
    screen_size = bg_clip.size

    # 2. Load background music
    if VIDEO_CONFIG['background_music']:
        audio_clip = AudioFileClip(VIDEO_CONFIG['background_music']).volumex(VIDEO_CONFIG['music_volume'])
        bg_clip = bg_clip.set_audio(audio_clip)

    # 3. Generate content
    horoscope, wealth, health = generate_content(sign)
    all_sections = [
        ('horoscope', horoscope),
        ('wealth', wealth),
        ('health', health)
    ]

    clips = []

    # Add title and date
    date_str = datetime.datetime.now().strftime("%B %d, %Y")
    title_clip = create_text_clip(
        text=f"{BRANDING['channel_name']}\n{sign} | {date_str}",
        font_size=TEXT_STYLE['title_font_size'],
        color=(255, 255, 255),
        duration=3,
        screen_size=screen_size
    )
    clips.append(title_clip)

    # Loop through sections
    for section_name, sentences in all_sections:
        color = SECTION_COLORS[section_name]
        for sentence in sentences:
            txt_clip = create_text_clip(
                text=sentence,
                font_size=TEXT_STYLE['content_font_size'],
                color=color,
                duration=3,  # each sentence 3 seconds
                screen_size=screen_size
            )
            clips.append(txt_clip)

    # Branding / outro
    outro_clip = create_text_clip(
        text=f"{BRANDING['watermark_text']}",
        font_size=TEXT_STYLE['tip_font_size'],
        color=(255, 255, 255),
        duration=3,
        screen_size=screen_size
    )
    clips.append(outro_clip)

    # Composite each clip over background
    final_clips = [CompositeVideoClip([bg_clip, clip]) for clip in clips]

    # Concatenate
    final_video = concatenate_videoclips(final_clips)

    # Save
    output_path = os.path.join(VIDEO_CONFIG['output_folder'], f"{sign}_short.mp4")
    os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
    final_video.write_videofile(output_path, fps=VIDEO_CONFIG['shorts']['fps'], codec='libx264', audio_codec='aac')

    print(f"✅ {sign} completed!")

# ===============================
# Main loop
# ===============================
def main():
    for sign in ZODIAC_SIGNS:
        create_short(sign)
        sleep(1)  # tiny pause

if __name__ == "__main__":
    main()
