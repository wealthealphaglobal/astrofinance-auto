#!/usr/bin/env python3
"""
AstroFinance Daily - FREE Automated Content Creator
Optimized Vedic Astrology Style - YouTube Shorts Generator
"""

import os
import sys
import yaml
import requests
import json
from datetime import datetime
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip,
    ImageClip, concatenate_videoclips, concatenate_audioclips, ColorClip
)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

# 🩹 Pillow >=10 fix
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

# ========================================
# CONFIG LOADING
# ========================================
print("📋 Loading configuration...")
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

os.makedirs(config['video']['output_folder'], exist_ok=True)
os.makedirs(config['video']['temp_folder'], exist_ok=True)

HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# ========================================
# AI CONTENT
# ========================================
def get_free_ai_content(prompt, sign):
    """Fetch horoscope text from Groq or HuggingFace"""
    formatted_prompt = prompt.format(sign=sign)

    # Groq
    if GROQ_API_KEY:
        try:
            response = requests.post(
                config['free_ai']['groq_api_url'],
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": config['free_ai']['groq_model'],
                    "messages": [
                        {"role": "system", "content": "You are a warm Vedic astrologer."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 200
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except Exception:
            pass

    # HuggingFace
    if HUGGINGFACE_API_KEY:
        try:
            response = requests.post(
                config['free_ai']['api_url'],
                headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                json={"inputs": formatted_prompt, "parameters": {"max_new_tokens": 200, "temperature": 0.7}},
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
        except Exception:
            pass

    print("  💫 Using fallback")
    return None


def clean_text(text):
    """Remove unwanted chars or markdown"""
    if not text:
        return ""
    text = re.sub(r'\*\*|__|<.*?>|\[.*?\]|\{.*?\}|#{1,6}\s', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(Here is|Today\'s horoscope:|Horoscope:)\s*', '', text, flags=re.IGNORECASE)
    if text and text[-1] not in '.!?':
        text += '.'
    return text


# ========================================
# FALLBACK DATA
# ========================================
FALLBACK = {
    'Aries': "Today brings opportunities for bold action. Your leadership shines bright.",
    'Taurus': "Financial stability grows. Stay patient and practical in all matters.",
    'Gemini': "Communication opens new doors. Stay curious and adaptable.",
    'Cancer': "Emotional balance guides you. Nurture close bonds today.",
    'Leo': "Your confidence draws attention. Step into the spotlight fearlessly.",
    'Virgo': "Focus and detail bring success. Stay organized and kind to yourself.",
    'Libra': "Harmony is your power. Connect with people and share your light.",
    'Scorpio': "Deep emotions lead to transformation. Trust the process fully.",
    'Sagittarius': "Adventure inspires you. Expand your vision with optimism.",
    'Capricorn': "Steady progress wins. Discipline brings lasting rewards.",
    'Aquarius': "Innovation flows. Share your ideas and inspire others.",
    'Pisces': "Let intuition lead you. Compassion attracts blessings."
}

FALLBACK_WEALTH = {
    'Aries': "Do: Take smart risks. Don't: Rush investments.",
    'Taurus': "Do: Build savings. Don't: Chase quick profits.",
    'Gemini': "Do: Diversify. Don't: Overspend.",
    'Cancer': "Do: Invest in security. Don't: Mix money with emotion.",
    'Leo': "Do: Invest in skills. Don't: Overshow success.",
    'Virgo': "Do: Research before investing. Don't: Act impulsively.",
    'Libra': "Do: Balance risk and safety. Don't: Delay key choices.",
    'Scorpio': "Do: Plan with insight. Don't: React emotionally.",
    'Sagittarius': "Do: Think global. Don't: Ignore fine print.",
    'Capricorn': "Do: Stick to structure. Don't: Cut corners.",
    'Aquarius': "Do: Innovate wisely. Don't: Forget basics.",
    'Pisces': "Do: Trust but verify. Don't: Ignore facts."
}

FALLBACK_HEALTH = {
    'Aries': "Channel energy through exercise. Breathe deeply and stay hydrated.",
    'Taurus': "Stretch and move gently. Nature helps ground your body.",
    'Gemini': "Calm the mind with meditation. Keep routines flexible.",
    'Cancer': "Eat light and balanced. Stay near water for calm energy.",
    'Leo': "Protect your heart energy. Rest restores your glow.",
    'Virgo': "Mind your digestion. Rest your thoughts too.",
    'Libra': "Balance rest and motion. Hydrate and smile often.",
    'Scorpio': "Release tension with workouts. Stay mindful of emotions.",
    'Sagittarius': "Stretch hips and legs. Outdoor activity refreshes you.",
    'Capricorn': "Mind your bones and joints. Gentle movement heals.",
    'Aquarius': "Improve circulation. Try creative exercises.",
    'Pisces': "Move with water energy. Soft yoga restores peace."
}


# ========================================
# TEXT IMAGE CREATOR
# ========================================
def create_text_image_styled(text, width, height, fontsize, color):
    """Create vibrant text overlay"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 160))
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()

    # Word wrap
    words = text.split()
    lines, current = [], []
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] < width - 100:
            current.append(word)
        else:
            lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))

    y = (height - len(lines) * (fontsize + 10)) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        # shadow
        draw.text((x + 3, y + 3), line, font=font, fill=(0, 0, 0, 255))
        draw.text((x, y), line, font=font, fill=color + (255,))
        y += fontsize + 10

    return np.array(img)


# ========================================
# CONTENT GENERATION
# ========================================
def generate_content(sign):
    print(f"\n✨ {sign}...")
    h_raw = get_free_ai_content(config['free_ai']['prompts']['horoscope'], sign)
    w_raw = get_free_ai_content(config['free_ai']['prompts']['wealth'], sign)
    he_raw = get_free_ai_content(config['free_ai']['prompts']['health'], sign)

    horoscope = clean_text(h_raw) or FALLBACK[sign]
    wealth = clean_text(w_raw) or FALLBACK_WEALTH[sign]
    health = clean_text(he_raw) or FALLBACK_HEALTH[sign]

    return {'horoscope': horoscope, 'wealth': wealth, 'health': health}


# ========================================
# VIDEO CREATION
# ========================================
def create_shorts(all_content):
    print("\n📱 Creating YouTube Shorts...")
    folder = f"{config['video']['output_folder']}/youtube_shorts"
    os.makedirs(folder, exist_ok=True)

    bg_video_path = config['video']['background_video']
    bg_music_path = config['video']['background_music']
    videos = []
    target_w, target_h = 720, 1280

    for sign in config['zodiac_signs']:
        content = all_content[sign]
        print(f"\n🎬 {sign}...")

        # Create sections
        sections = [
            ("🌟 Horoscope", content['horoscope'], (255, 215, 0)),
            ("💰 Wealth", content['wealth'], (50, 205, 50)),
            ("🌿 Health", content['health'], (135, 206, 250))
        ]

        clips = []
        bg = VideoFileClip(bg_video_path).resize(height=target_h)

        total_text = " ".join([s[1] for s in sections])
        total_duration = min(max(25, len(total_text.split()) / 2.5), 50)
        if bg.duration < total_duration:
            loops = int(total_duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * loops)
        bg = bg.subclip(0, total_duration)

        for title, text, color in sections:
            clip_text = f"{title}\n\n{text}"
            img = create_text_image_styled(clip_text, target_w, target_h, 42, color)
            txt_clip = ImageClip(img).set_duration(total_duration / 3).set_opacity(0.9)
            clips.append(txt_clip)

        slides = concatenate_videoclips(clips, method="compose")
        video = CompositeVideoClip([bg.set_duration(slides.duration), slides])

        # Add background music
        if os.path.exists(bg_music_path):
            music = AudioFileClip(bg_music_path).volumex(config['video']['music_volume'])
            if music.duration < video.duration:
                loops = int(video.duration / music.duration) + 1
                music = concatenate_audioclips([music] * loops)
            music = music.subclip(0, video.duration)
            video = video.set_audio(music)

        # Watermark
        wm_img = create_text_image_styled(config['branding']['watermark_text'], 250, 60, 25, (255, 255, 255))
        watermark = ImageClip(wm_img).set_duration(video.duration).set_position(('right', 'top')).set_opacity(0.6)
        final_video = CompositeVideoClip([video, watermark])

        output = f"{folder}/{sign}_{datetime.now().strftime('%Y%m%d')}.mp4"
        final_video.write_videofile(
            output,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            threads=4,
            logger=None
        )

        videos.append(output)
        print(f"  ✅ Done")

        bg.close()
        final_video.close()

    print(f"\n✅ {len(videos)} Shorts created successfully!")
    return videos


# ========================================
# MAIN
# ========================================
def main():
    print("=" * 60)
    print("🌟 ASTROFINANCE DAILY - FREE")
    print("=" * 60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")

    if GROQ_API_KEY:
        print("🤖 AI: Groq ✅")
    elif HUGGINGFACE_API_KEY:
        print("🤖 AI: HuggingFace ✅")
    else:
        print("⚠️ No AI - using fallback")

    print("\n🎭 Generating content...")
    all_content = {sign: generate_content(sign) for sign in config['zodiac_signs']}

    shorts = create_shorts(all_content)

    metadata = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'shorts': shorts,
        'content': all_content
    }
    with open(f"{config['video']['output_folder']}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)

    print("\n" + "=" * 60)
    print("✅ ALL DONE!")
    print("=" * 60)
    print(f"📁 Output folder: {config['video']['output_folder']}/youtube_shorts/")
    for i, s in enumerate(shorts, 1):
        print(f"   {i}. {os.path.basename(s)}")
    print("\n🚀 Ready to upload! 💰 COST: $0.00")


if __name__ == "__main__":
    main()
