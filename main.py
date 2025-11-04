import os
from datetime import datetime
import textwrap
import yaml
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, concatenate_videoclips

# Load config
with open("config.yml", "r") as f:
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
        size=(screen_size[0] - 100, None),  # Leave some padding
    ).set_duration(duration).fadein(0.5).fadeout(0.5)
    return txt_clip

def create_short(sign):
    print(f"⏳ Starting {sign} short...")

    screen_size = SHORTS_CONFIG['resolution']

    # Load and resize background video
    bg_clip = VideoFileClip(VIDEO_CONFIG['background_video']).resize(height=screen_size[1])

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

    # Generate content (here you would normally call AI API)
    horoscope_text = PROMPTS['horoscope'].replace("{sign}", sign)
    wealth_text = PROMPTS['wealth'].replace("{sign}", sign)
    health_text = PROMPTS['health'].replace("{sign}", sign)

    # Split content into paragraphs/sentences
    clips = [title_clip]
    for text_block, font_size in [
        (horoscope_text, TEXT_STYLE['content_font_size']),
        (wealth_text, TEXT_STYLE['tip_font_size']),
        (health_text, TEXT_STYLE['tip_font_size'])
    ]:
        for paragraph in text_block.strip().split("\n"):
            if paragraph.strip():
                paragraph_clip = create_text_clip(
                    paragraph.strip(),
                    font_size=font_size,
                    color='white',
                    shadow_color='black',
                    duration=3,
                    screen_size=screen_size
                )
                clips.append(paragraph_clip)

    # Composite clips on top of background
    final_clips = [
        CompositeVideoClip([bg_clip.set_duration(clip.duration), clip.set_position('center')])
        .set_duration(clip.duration)
        for clip in clips
    ]

    final_video = concatenate_videoclips(final_clips, method="compose")

    output_file = os.path.join(VIDEO_CONFIG['output_folder'], f"{sign}_short.mp4")
    final_video.write_videofile(output_file, fps=SHORTS_CONFIG['fps'])
    print(f"✅ Completed {sign} short!")

def main():
    print("🎬 Starting FREE content generation...\n")
    for sign in ZODIAC_SIGNS:
        create_short(sign)
    print("\n🎉 All shorts completed!")

if __name__ == "__main__":
    main()
