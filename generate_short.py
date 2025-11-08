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
os.makedirs(os.path.join(VIDEO_CONFIG['output_folder'], 'instagram_reels'), exist_ok=True)
os.makedirs(VIDEO_CONFIG['temp_folder'], exist_ok=True)


def get_day_of_week_background():
    """Get background video for current day of week"""
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    today_index = datetime.now().weekday()
    day_name = days[today_index]
    
    bg_filename = f"{day_name}_bg.mp4"
    
    print(f"  🔍 Looking for {day_name}'s background: {bg_filename}")
    
    if os.path.exists(bg_filename):
        size_mb = os.path.getsize(bg_filename) / (1024 * 1024)
        print(f"  ✅ Found {day_name} background: {bg_filename} ({size_mb:.2f} MB)")
        return bg_filename
    
    print(f"  ⚠️ {day_name}_bg.mp4 not found, trying fallback...")
    
    # Fallback to default background
    default_bg = VIDEO_CONFIG['background_video']
    if os.path.exists(default_bg):
        size_mb = os.path.getsize(default_bg) / (1024 * 1024)
        print(f"  ✅ Using default background: {default_bg} ({size_mb:.2f} MB)")
        return default_bg
    
    print(f"  ❌ No background found! Checked:")
    print(f"     • {bg_filename}")
    print(f"     • {default_bg}")
    return None


def fetch_ai_content(prompt, sign):
    """Fetch content from Groq or HuggingFace"""
    formatted_prompt = prompt.format(sign=sign, date=datetime.now().strftime("%B %d, %Y"))
    
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
                        {"role": "system", "content": "You are a traditional Indian astrologer speaking in a warm, devotional tone. Provide only the final narration script, no explanations."},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 300
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
                    "parameters": {"max_new_tokens": 300, "temperature": 0.8}
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


def simplify_to_simple_english(text):
    """Convert complex text to simple, clear English while keeping insight"""
    if not text:
        return ""
    
    # Remove markdown and extra formatting
    text = text.replace("**", "").replace("*", "").replace("#", "").strip()
    
    # Replace complex words with simple ones
    replacements = {
        "planetary alignment": "stars aligning",
        "celestial bodies": "planets",
        "auspicious": "good",
        "inauspicious": "challenging",
        "propitious": "favorable",
        "forthcoming": "coming",
        "endeavor": "try",
        "facilitate": "help",
        "manifest": "happen",
        "abundant": "lots of",
        "prosperity": "success",
        "adversity": "challenges",
        "fortuitous": "lucky",
        "serendipity": "good timing",
        "contemplation": "thinking",
        "meditation": "stillness",
        "introspection": "looking within",
        "intuition": "inner feeling",
        "synchronicity": "things lining up",
        "oscillate": "move",
        "fluctuation": "ups and downs",
        "momentum": "energy",
        "trajectory": "path",
        "leverage": "use",
        "capitalize": "take advantage",
        "precipitate": "cause",
        "endeavors": "efforts",
        "optimism": "hope",
        "vigilance": "awareness",
        "prudence": "caution",
        "articulate": "express",
        "initiate": "start",
        "culminate": "end",
        "decipher": "understand",
        "illuminate": "show",
        "nurture": "support",
        "cultivate": "build",
        "mitigate": "reduce",
        "augment": "increase",
        "ameliorate": "improve",
    }
    
    for complex_word, simple_word in replacements.items():
        text = text.replace(complex_word, simple_word)
        text = text.replace(complex_word.capitalize(), simple_word.capitalize())
    
    # Remove common prefixes
    prefixes = ["Here is", "Here's", "Today's", "For today", "Namaste", "Based on", "According to"]
    for prefix in prefixes:
        if text.lower().startswith(prefix.lower()):
            text = text[len(prefix):].strip()
            if text and text[0] in ":,- ":
                text = text[1:].strip()
    
    # Clean up punctuation
    text = text.strip()
    if not text:
        return ""
    
    return text


def clean_and_summarize(text):
    """Clean AI response - keep insight, use simple English, format for video"""
    if not text:
        return ""
    
    # Step 1: Simplify to basic English
    text = simplify_to_simple_english(text)
    
    # Step 2: Split into sentences
    sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip() and len(s.strip()) > 5]
    
    # Step 3: Keep 4-6 sentences for good insight (not too short, not too long)
    if len(sentences) > 6:
        sentences = sentences[:6]
    elif len(sentences) < 2:
        # If very short, at least add some context
        sentences = sentences
    
    # Step 4: Filter out very long sentences (>20 words) - break them up
    cleaned_sentences = []
    for sent in sentences:
        words = sent.split()
        
        # If too long, try to break at logical point
        if len(words) > 20:
            # Find middle point
            mid = len(words) // 2
            # Look for best breaking point (comma, "and", "or")
            first_half = " ".join(words[:mid])
            second_half = " ".join(words[mid:])
            
            cleaned_sentences.append(first_half)
            if second_half.strip():
                cleaned_sentences.append(second_half)
        else:
            cleaned_sentences.append(sent)
    
    # Step 5: Join sentences
    result = ". ".join(cleaned_sentences)
    if result and result[-1] not in ".!?":
        result += "."
    
    # Step 6: Format for video display - intelligent line breaking
    # Max 50-60 chars per line for readability on video
    words = result.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        line_text = " ".join(current_line)
        
        # Break line if it gets too long or at sentence end
        if len(line_text) > 55 or word.endswith("."):
            lines.append(" ".join(current_line))
            current_line = []
    
    if current_line:
        lines.append(" ".join(current_line))
    
    result = "\n".join(lines)
    
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
    
    # Get Australian date for video display
    aus_datetime = get_australian_datetime()
    aus_date_display = aus_datetime.strftime("%d %b %Y")
    
    # TIMING ADJUSTED FOR READABILITY:
    # - Horoscope: 16 seconds (was 15)
    # - Wealth: 12 seconds (was 12)
    # - Health: 12 seconds (was 12)
    # - Subscribe: 5 seconds (was 5)
    # Total: 45 seconds + 14 seconds padding = 59 seconds
    
    AVAILABLE_TIME = 45
    HOROSCOPE_TIME = 16  # Increased from 15
    WEALTH_TIME = 12
    HEALTH_TIME = 12
    SUBSCRIBE_DURATION = 5
    TARGET_DURATION = 59
    
    # Calculate actual times based on content length
    horo_length = len(content['horoscope'])
    wealth_length = len(content['wealth'])
    health_length = len(content['health'])
    total_content_length = horo_length + wealth_length + health_length
    
    if total_content_length > 0:
        horo_time = max(16, int((horo_length / total_content_length) * AVAILABLE_TIME))
        wealth_time = max(12, int((wealth_length / total_content_length) * AVAILABLE_TIME))
        health_time = max(12, AVAILABLE_TIME - horo_time - wealth_time)
    else:
        horo_time = HOROSCOPE_TIME
        wealth_time = WEALTH_TIME
        health_time = HEALTH_TIME
    
    # Get day-of-week background
    bg_video_path = get_day_of_week_background()
    if not bg_video_path:
        print(f"  ❌ No background video available")
        return None
    
    # Load and crop background
    bg_original = VideoFileClip(bg_video_path)
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
    
    # Title (increased by 1)
    title_heading, title_underline = create_heading(
        f"✨ {sign} ✨",
        TEXT_STYLE['title_font_size'] + 1,  # +1
        MAIN_DURATION,
        fade=False
    )
    title_heading = title_heading.set_position(('center', SIGN_Y))
    title_underline = title_underline.set_position(('center', SIGN_Y + 100))
    all_clips.extend([title_heading, title_underline])
    
    date_clip = TextClip(
        aus_date_display,  # Use Australian date
        fontsize=36,  # Increased from 35 (by 1)
        color="#F5F5F5",
        method='label'
    ).set_duration(MAIN_DURATION).set_position(('center', DATE_Y))
    all_clips.append(date_clip)
    
    # Horoscope (increased by 1)
    horo_heading, horo_underline = create_heading(
        "🌙 Daily Horoscope",
        TEXT_STYLE['content_font_size'] + 1,  # +1
        horo_time
    )
    horo_heading = horo_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    horo_underline = horo_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([horo_heading, horo_underline])
    
    horo_chunks = create_text_chunks(content['horoscope'], TEXT_STYLE['content_font_size'] - 4, horo_time)  # -4 to keep proportional
    for chunk in horo_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += horo_time
    
    # Wealth (increased by 1)
    wealth_heading, wealth_underline = create_heading(
        "💰 Wealth Tips",
        TEXT_STYLE['content_font_size'] + 1,  # +1
        wealth_time
    )
    wealth_heading = wealth_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    wealth_underline = wealth_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([wealth_heading, wealth_underline])
    
    wealth_chunks = create_text_chunks(content['wealth'], TEXT_STYLE['tip_font_size'] - 4, wealth_time)  # -4 to keep proportional
    for chunk in wealth_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += wealth_time
    
    # Health (increased by 1)
    health_heading, health_underline = create_heading(
        "🏥 Health Tips",
        TEXT_STYLE['content_font_size'] + 1,  # +1
        health_time
    )
    health_heading = health_heading.set_position(('center', HORO_HEADING_Y)).set_start(current_time)
    health_underline = health_underline.set_position(('center', HORO_HEADING_Y + 100)).set_start(current_time)
    all_clips.extend([health_heading, health_underline])
    
    health_chunks = create_text_chunks(content['health'], TEXT_STYLE['tip_font_size'] - 4, health_time)  # -4 to keep proportional
    for chunk in health_chunks:
        all_clips.append(chunk.set_position(('center', TEXT_Y)).set_start(current_time + chunk.start))
    current_time += health_time
    
    # Subscribe (increased by 1)
    sub_text = TextClip(
        "🔔 SUBSCRIBE\n\nLIKE • SHARE • COMMENT",
        fontsize=61,  # Increased from 60 (by 1)
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
    
    # Also save to Instagram Reels folder (same video)
    insta_output = os.path.join(
        VIDEO_CONFIG['output_folder'],
        'instagram_reels',
        f"{sign}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4"
    )
    
    try:
        import shutil
        shutil.copy(output_file, insta_output)
        print(f"  ✅ Copied to Instagram Reels: {insta_output}")
    except Exception as e:
        print(f"  ⚠️ Could not copy to Instagram Reels: {e}")
    
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
