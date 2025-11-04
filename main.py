import os
import sys
import time
import random
import textwrap
import yaml
from datetime import datetime
from moviepy.editor import (
    VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip,
    concatenate_videoclips, concatenate_audioclips
)
from PIL import Image

# --------------------------
# 🧩 Fix Pillow compatibility
# --------------------------
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# --------------------------
# 📜 Load config safely
# --------------------------
CONFIG_FILE = "config.yaml"
if not os.path.exists(CONFIG_FILE):
    print("❌ config.yaml not found! Please place it next to main.py.")
    sys.exit(1)

with open(CONFIG_FILE, "r") as f:
    CONFIG = yaml.safe_load(f)

VIDEO_CONFIG = CONFIG['video']
SHORTS_CONFIG = CONFIG['platforms']['youtube']['shorts']
TEXT_STYLE = CONFIG['text_style']
ZODIAC_SIGNS = CONFIG['zodiac_signs']

# --------------------------
# 🎨 Visual Palette
# --------------------------
MYSTICAL_COLORS = [
    '#E6C27A', '#F1D18A', '#DDE1E4', '#F4F4F4',
    '#B8A1E0', '#A597E8', '#9CC9E3', '#AEEAF5', '#FFF9E3'
]

# --------------------------
# 📁 Ensure folders exist
# --------------------------
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
shorts_folder = os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts')
os.makedirs(shorts_folder, exist_ok=True)

# --------------------------
# 🧠 Helper: Text styling
# --------------------------
def create_text_clip(text, font_size, color, shadow_color, duration, screen_size):
    """Create a stylized text clip with nice wrapping."""
    wrapped = "\n".join(textwrap.wrap(text, width=28))
    return (
        TextClip(
            wrapped,
            fontsize=font_size,
            color=color,
            stroke_color=shadow_color,
            stroke_width=3,
            method="caption",
            size=(screen_size[0] - 120, None),
            align="center",
        )
        .set_duration(duration)
        .fadein(0.4)
        .fadeout(0.4)
        .set_position("center")
    )

# --------------------------
# 🌟 Core short generator
# --------------------------
def create_short(sign, test_mode=False):
    start_time = time.time()
    print(f"\n🔮 [{sign}] — starting...")
    sys.stdout.flush()  # for GitHub Action live log

    screen_size = SHORTS_CONFIG["resolution"]
    sign_color = random.choice(MYSTICAL_COLORS)

    # 🎬 Load background
    bg_clip = VideoFileClip(VIDEO_CONFIG["background_video"]).resize(height=720)
    target_w, target_h = screen_size
    scale = target_h / bg_clip.h
    new_w = int(bg_clip.w * scale)
    if new_w > target_w:
        x1 = int((new_w - target_w) / 2)
        bg_clip = bg_clip.resize(height=target_h).crop(x1=x1, width=target_w)
    else:
        bg_clip = bg_clip.resize(width=target_w)

    today = datetime.now().strftime("%d %b %Y")
    # ✨ Horoscope text (editable or AI-generated later)
    title_text = f"✨ {sign} ✨\n{today}"
    horoscope_text = f"{sign}, cosmic energy aligns your path today. Stay calm and trust the universe’s timing."
    wealth_text = f"💰 Wealth Tip\nDo: Think long-term.\nDon’t: Spend impulsively."
    health_text = f"🏥 Health Tip\nDo: Breathe deeply & stay hydrated.\nDon’t: Skip your rest."

    # 🎞️ Create text clips in order
    clips = [
        create_text_clip(title_text, TEXT_STYLE["title_font_size"], sign_color, "black", 5, screen_size),
        create_text_clip(horoscope_text, TEXT_STYLE["content_font_size"], sign_color, "black", 15, screen_size),
        create_text_clip(wealth_text, TEXT_STYLE["tip_font_size"], sign_color, "black", 10, screen_size),
        create_text_clip(health_text, TEXT_STYLE["tip_font_size"], sign_color, "black", 10, screen_size),
    ]

    total_duration = sum(c.duration for c in clips)
    print(f"⏱️ Duration planned: {total_duration:.1f}s")

    # Loop background if too short
    if bg_clip.duration < total_duration:
        loops = int(total_duration / bg_clip.duration) + 1
        bg_clip = concatenate_videoclips([bg_clip] * loops)
    bg_clip = bg_clip.subclip(0, total_duration)

    # Compose sequentially
    timeline, current = [], 0
    for clip in clips:
        segment = CompositeVideoClip(
            [bg_clip.subclip(current, current + clip.duration), clip]
        ).set_duration(clip.duration)
        timeline.append(segment)
        current += clip.duration

    final = concatenate_videoclips(timeline, method="compose")

    # 🎵 Add background mantra
    if os.path.exists(VIDEO_CONFIG["background_music"]):
        music = AudioFileClip(VIDEO_CONFIG["background_music"]).volumex(VIDEO_CONFIG["music_volume"])
        if music.duration < final.duration:
            loops = int(final.duration / music.duration) + 1
            music = concatenate_audioclips([music] * loops)
        final = final.set_audio(music.subclip(0, final.duration))

    # Trim for YouTube Shorts
    if final.duration > 58:
        final = final.subclip(0, 58)
        print("⚠️ Trimmed to 58 seconds for Shorts compliance")

    # 🧾 Save output
    filename = f"{sign}_{datetime.now():%Y%m%d}.mp4"
    output_path = os.path.join(shorts_folder, filename)
    print(f"🎥 Rendering {filename} ...")

    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2,
        logger=None,
    )

    elapsed = time.time() - start_time
    print(f"✅ [{sign}] — completed in {elapsed:.1f}s")
    sys.stdout.flush()

    bg_clip.close()
    final.close()

    if test_mode:
        print("🧪 Test mode: stopping after first sign.")
        return False  # stop after first sign
    return True  # continue

# --------------------------
# 🪐 Main Execution
# --------------------------
def main():
    print("🎬 Starting AstroFinance Shorts Generator")
    print(f"📅 {datetime.now():%B %d, %Y}")
    print("=" * 60)

    for i, sign in enumerate(ZODIAC_SIGNS, start=1):
        cont = create_short(sign, test_mode=True)  # Change to False for full batch
        if not cont:
            break
        print(f"🔁 Progress: {i}/{len(ZODIAC_SIGNS)} done\n")

    print("------------------------------------------------------------")
    print("✨ All completed successfully (test mode).")
    print(f"📁 Saved in: {shorts_folder}")
    print("=" * 60)

# --------------------------
# 🚀 Run
# --------------------------
if __name__ == "__main__":
    # Make stdout unbuffered (real-time logs in GitHub Actions)
    sys.stdout.reconfigure(line_buffering=True)
    main()
