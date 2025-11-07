#!/usr/bin/env python3
"""Generate a single zodiac sign video short"""

import os
import sys
import argparse
import textwrap
from datetime import datetime
import yaml
import requests
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

# Get API keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')

# Ensure output folders exist
os.makedirs(VIDEO_CONFIG['output_folder'], exist_ok=True)
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'youtube_shorts'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)


def fetch_ai_content(prompt, sign):
    """Fetch content from Groq or HuggingFace"""
    formatted_prompt = prompt.format(sign=sign)
    
    if GROQ_API_KEY:
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.3-70b-versatile",
                    "messages": [
                        {"role": "system", "content": "You are a warm Vedic astrologer. Keep responses concise and natural."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 150
                },
                timeout=15
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
        except Exception as e:
            print(f"    ⚠️ Groq API error: {e}")
    
    if HUGGINGFACE_API_KEY:
        try:
            response = requests.post(
                "https://router.huggingface.co/hf-inference/models/deepseek-ai/DeepSeek-V3",
                headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": formatted_prompt,
                    "parameters": {"max_new_tokens": 150, "temperature": 0.7}
                },
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
        except Exception as e:
            print(f"    ⚠️ HuggingFace API error: {e}")
    
    return None


def clean_and_summarize(text):
    """Clean AI response and make it concise"""
    if not text:
        return ""
    
    text = text.replace("**", "").replace("*", "").replace("#", "").strip()
    
    prefixes = ["Here is", "Here's", "Today's", "For today", "Namaste"]
    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            if text.startswith(":") or text.startswith(","):
                text = text[1:].strip()
    
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
    if len(sentences) > 4:
        sentences = sentences[:4]
    
    result = ". ".join(sentences)
    if result and result[-1] not in ".!?":
        result += "."
    
    return result


def get_content_for_sign(sign):
    """Get horoscope, wealth, and health content"""
    print(f"  📝 Fetching content for {sign}...")
    
    horo = fetch_ai_content(CONFIG['free_ai']['prompts']['horoscope'], sign)
    if not horo:
        horo = f"Namaste {sign}! The stars shine bright for you today. Planetary energy brings opportunities in relationships and career. Trust your intuition."
    horo = clean_and_summarize(horo)
    
    wealth = fetch_ai_content(CONFIG['free_ai']['prompts']['wealth'], sign)
    if not wealth:
        wealth = "Do: Plan finances with Mercury's clarity. Don't: Rush major investments today."
    wealth = clean_and_summarize(wealth)
    
    health = fetch_ai_content(CONFIG['free_ai']['prompts']['health'], sign)
    if not health:
        health = "The Moon stirs emotions today. Drink water mindfully and practice deep breathing for balance."
    health = clean_and_summarize(health)
    
    print(f"  ✅ Content ready")
    return {'horoscope': horo, 'wealth': wealth, 'health': health}


def create_heading(text, font_size, duration, fade=True):
    """Create heading with underline"""
    heading = TextClip(
        text,
        fontsize=font_size + 20,
        color="#F5F5F5",
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
        heading = heading.fadein(0.8).fadeout(0.8)
        underline = underline.fadein(0.8).fadeout(0.8)
    
    return heading, underline


def create_text_chunks(text, font_size, total_duration):
    """Split text into smart chunks"""
    wrapped_lines = []
    for line in text.split('\n'):
        if line.strip():
            wrapped_lines.extend(textwrap.wrap(line, width=35))
    
    total_lines = len(wrapped_lines)
    
    if total_lines <= 8:
        chunks = ["\n".join(wrapped_lines)]
    elif total_lines <= 16:
        mid = len(wrapped_lines) // 2
        chunks = ["\n".join(wrapped_lines[:mid]), "\n".join(wrapped_lines[mid:])]
    else:
        LINES_PER_CHUNK = 9
        chunks = []
        for i in range(0, len(wrapped_lines), LINES_PER_CHUNK):
            chunk_lines = wrapped_lines[i:i + LINES_PER_CHUNK]
            chunks.append("\n".join(chunk_lines))
    
    text_clips = []
    
    if len(chunks) == 1:
        clip = TextClip(
            chunks[0],
            fontsize=font_size,
            color="#F5F5F5",
            method='label',
            align='center'
        ).set_duration(total_duration).set_start(0).fadein(0.8).fadeout(0.8)
        text_clips.append(clip)
    else:
        chunk_line_counts = [len(chunk.split('\n')) for chunk in chunks]
        total_lines_all = sum(chunk_line_counts)
        
        current_time = 0
        for i, chunk in enumerate(chunks):
            lines_in_chunk = chunk_line_counts[i]
            chunk_duration = max(3.0, (lines_in_chunk / total_lines_all) * total_duration)
            
            clip = TextClip(
                chunk,
                fontsize=font_size,
                color="#F5F5F5",
                method='label',
                align='center'
            ).set_duration(chunk_duration).set_start(current_time).fadein(0.8).fadeout(0.8)
            
            text_clips.append(clip)
            current_time += chunk_duration
    
    return text_clips


def create_short(sign, content):
    """Create video short"""
    print(f"  🎬 Creating video for {sign}...")
    screen_size = SHORTS_CONFIG['resolution']
    
    # Calculate timing
    horo_length = len(content['horoscope'])
    wealth_length = len(content['wealth'])
    health_length = len(content['health'])
    total_content_length = horo_length + wealth_length + health_length
    
    AVAILABLE_TIME = 54
    SUBSCRIBE_DURATION = 5
    TARGET_DURATION = 59
    
    horo_time = max(15, int((horo_length / total_content_length) * AVAILABLE_TIME))
    wealth_time = max(12, int((wealth_length / total_content_length) * AVAILABLE_TIME))
    health_time = max(12, AVAILABLE_TIME - horo_time - wealth_time)
    
    # Load and crop background
    bg_original = VideoFileClip(VIDEO_CONFIG['background_video'])
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
    
    MAIN_DURATION = horo_time + wealth_time + health_time
    
    if bg_original.duration < TARGET_DURATION:
        loops = int(TARGET_DURATION / bg_original.duration) + 1
        bg_clip = bg_original.loop(n=loops).subclip(0, TARGET_DURATION)
    else:
        bg_clip = bg_original.subclip(0, TARGET_DURATION)
    
    all_clips = []
    current_time = 0
    
    HEADING_Y = 100
    TEXT_Y = 910
    SIGN_Y = HEADING_Y + 60
    DATE_Y = SIGN_Y + 130
    HORO_HEADING_Y = HEADING_Y - 60
    
    # Title
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'],
        MAIN_DURATION,
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
    ).set_duration(MAIN_DURATION).set_position(('center', DATE_Y))
    all_clips.append(date_clip)
    
    # Horoscope
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'],
        horo_time
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    horo_chunks = create_text_chunks(content['horoscope'], TEXT_STYLE['content_font_size'] - 5, horo_time)
    for chunk in horo_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += horo_time
    
    # Wealth
    wealth_heading, wealth_underline = create_heading(
        "💰 Wealth Tips",
        TEXT_STYLE['content_font_size'],
        wealth_time
    )
    wealth_heading = wealth_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    wealth_underline = wealth_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([wealth_heading, wealth_underline])
    
    wealth_chunks = create_text_chunks(content['wealth'], TEXT_STYLE['tip_font_size'] - 5, wealth_time)
    for chunk in wealth_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += wealth_time
    
    # Health
    health_heading, health_underline = create_heading(
        "🏥 Health Tips",
        TEXT_STYLE['content_font_size'],
        health_time
    )
    health_heading = health_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    health_underline = health_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([health_heading, health_underline])
    
    health_chunks = create_text_chunks(content['health'], TEXT_STYLE['tip_font_size'] - 5, health_time)
    for chunk in health_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += health_time
    
    # Subscribe
    sub_text = TextClip(
        "🔔 SUBSCRIBE\n\nLIKE • SHARE • COMMENT",
        fontsize=60,
        color="#FFD700",
        font='Arial-Bold',
        method='label',
        align='center'
    ).set_duration(SUBSCRIBE_DURATION).set_position('center').set_start(current_time).fadein(0.5)
    all_clips.append(sub_text)
    
    # Composite
    final_video = CompositeVideoClip([bg_clip] + all_clips).set_duration(TARGET_DURATION)
    
    # Add music
    if os.path.exists(VIDEO_CONFIG['background_music']):
        music = AudioFileClip(VIDEO_CONFIG['background_music']).volumex(VIDEO_CONFIG['music_volume'])
        if music.duration < TARGET_DURATION:
            loops = int(TARGET_DURATION / music.duration) + 1
            music = music.loop(n=loops).subclip(0, TARGET_DURATION)
        else:
            music = music.subclip(0, TARGET_DURATION)
        final_video = final_video.set_audio(music)
    
    output_file = os.path.join(
        VIDEO_CONFIG['output_folder'],
        'youtube_shorts',
        f"{sign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )
    
    final_video.write_videofile(
        output_file,
        fps=SHORTS_CONFIG['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='ultrafast',
        threads=4,
        logger=None,
        verbose=False
    )
    
    print(f"  ✅ Video created: {output_file}")
    
    # Cleanup
    bg_original.close()
    bg_clip.close()
    final_video.close()
    
    return output_file


def main():
    parser = argparse.ArgumentParser(description="Generate a zodiac sign video short")
    parser.add_argument('--sign', required=True, help='Zodiac sign')
    args = parser.parse_args()
    
    sign = args.sign
    
    print("="*60)
    print(f"🌟 GENERATING VIDEO FOR {sign.upper()}")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    print("-"*60)
    
    try:
        content = get_content_for_sign(sign)
        video_path = create_short(sign, content)
        
        print("-"*60)
        print(f"✅ SUCCESS: Video generated at {video_path}")
        print("="*60)
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
