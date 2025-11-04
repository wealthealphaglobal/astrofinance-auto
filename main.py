#!/usr/bin/env python3
"""
AstroFinance Daily - FREE Automated Content Creator
100% FREE - Vedic Astrology Style
"""

import os
import sys
import yaml
import requests
import json
from datetime import datetime
from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeVideoClip, 
                            ImageClip, concatenate_videoclips, concatenate_audioclips)
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import re

# Load configuration
print("📋 Loading configuration...")
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create folders
os.makedirs(config['video']['output_folder'], exist_ok=True)
os.makedirs(config['video']['temp_folder'], exist_ok=True)

# Get API keys
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# ========================================
# FREE AI
# ========================================

def get_free_ai_content(prompt, sign):
    """Fetch from DeepSeek/Groq"""
    formatted_prompt = prompt.format(sign=sign)
    
    # Try Groq (most reliable)
    if GROQ_API_KEY:
        try:
            print(f"  🤖 Using Groq AI...")
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
        except:
            pass
    
    # Try HuggingFace
    if HUGGINGFACE_API_KEY:
        try:
            print(f"  🤖 Using HuggingFace...")
            response = requests.post(
                config['free_ai']['api_url'],
                headers={"Authorization": f"Bearer {HUGGINGFACE_API_KEY}"},
                json={
                    "inputs": formatted_prompt,
                    "parameters": {"max_new_tokens": 200, "temperature": 0.7}
                },
                timeout=15
            )
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
        except:
            pass
    
    print(f"  💫 Using fallback")
    return None

def clean_text(text):
    """Clean AI response"""
    text = re.sub(r'\*\*|__|<.*?>|\[.*?\]|\{.*?\}|#{1,6}\s', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    text = re.sub(r'^(Here is|Here\'s|Today\'s horoscope:|Horoscope:)\s*', '', text, flags=re.IGNORECASE)
    if text and text[-1] not in '.!?':
        text += '.'
    return text

# ========================================
# FALLBACK CONTENT
# ========================================

FALLBACK = {
    'Aries': "Today brings opportunities for bold action. Your leadership shines. Trust your instincts.",
    'Taurus': "Financial stability is highlighted. Your practical approach yields results. Focus on long-term goals.",
    'Gemini': "Communication flows easily. Share your ideas. Mental agility helps you navigate challenges.",
    'Cancer': "Emotional intelligence guides you. Nurture relationships. Home brings comfort.",
    'Leo': "Confidence radiates today. Creative projects flourish. Leadership opportunities arise.",
    'Virgo': "Attention to detail serves you well. Organize and execute with precision.",
    'Libra': "Balance and harmony are within reach. Relationships benefit from your diplomatic approach.",
    'Scorpio': "Transformation is in the air. Deep insights emerge. Trust the process of change.",
    'Sagittarius': "Adventure calls today. Expand horizons through learning. Optimism attracts fortune.",
    'Capricorn': "Disciplined effort yields rewards. Your ambition creates solid foundations.",
    'Aquarius': "Innovation is your strength. Think outside the box. Community brings opportunities.",
    'Pisces': "Intuition flows freely. Artistic expression brings fulfillment. Compassion connects you."
}

FALLBACK_WEALTH = {
    'Aries': "Do: Take calculated risks. Don't: Rush into investments without research.",
    'Taurus': "Do: Build long-term savings. Don't: Fall for get-rich-quick schemes.",
    'Gemini': "Do: Diversify income streams. Don't: Spread yourself too thin financially.",
    'Cancer': "Do: Invest in security. Don't: Make emotional financial decisions.",
    'Leo': "Do: Invest in your skills. Don't: Overspend to impress others.",
    'Virgo': "Do: Research thoroughly. Don't: Rush financial decisions.",
    'Libra': "Do: Balance growth and stability. Don't: Avoid necessary financial choices.",
    'Scorpio': "Do: Plan strategically. Don't: Let emotions drive money decisions.",
    'Sagittarius': "Do: Think globally. Don't: Ignore due diligence.",
    'Capricorn': "Do: Stick to your plan. Don't: Chase quick profits.",
    'Aquarius': "Do: Think innovatively. Don't: Neglect practical basics.",
    'Pisces': "Do: Trust intuition but verify. Don't: Ignore financial facts."
}

FALLBACK_HEALTH = {
    'Aries': "Channel energy through exercise. Protect your head. Breathe deeply. Blessings for vitality.",
    'Taurus': "Try gentle yoga for neck health. Enjoy good food mindfully. Nature grounds you.",
    'Gemini': "Calm your mind with meditation. Practice deep breathing. Vary your routine.",
    'Cancer': "Support digestion with mindful eating. Process emotions healthily. Water activities soothe.",
    'Leo': "Protect heart health with cardio. Practice good posture. Rest prevents burnout.",
    'Virgo': "Support digestion with probiotics. Practice self-compassion. Create flexible routines.",
    'Libra': "Drink plenty of water. Find balance in exercise. Partner workouts motivate.",
    'Scorpio': "Release intensity through vigorous exercise. Honor your body. Stay hydrated.",
    'Sagittarius': "Stretch to protect hips. Enjoy outdoor activities. Warm up properly.",
    'Capricorn': "Include calcium for bones. Maintain consistency. Schedule rest days.",
    'Aquarius': "Keep circulation healthy by moving. Try unique workouts. Group fitness inspires.",
    'Pisces': "Care for your feet. Water activities restore you. Try gentle yoga."
}

# ========================================
# CONTENT GENERATION
# ========================================

def generate_content(sign):
    """Generate all content for one sign"""
    print(f"\n✨ {sign}...")
    
    # Horoscope
    horoscope_raw = get_free_ai_content(config['free_ai']['prompts']['horoscope'], sign)
    horoscope = clean_text(horoscope_raw) if horoscope_raw else FALLBACK.get(sign, "The stars align favorably.")
    
    # Wealth
    wealth_raw = get_free_ai_content(config['free_ai']['prompts']['wealth'], sign)
    wealth = clean_text(wealth_raw) if wealth_raw else FALLBACK_WEALTH.get(sign, "Trust your financial wisdom.")
    
    # Health
    health_raw = get_free_ai_content(config['free_ai']['prompts']['health'], sign)
    health = clean_text(health_raw) if health_raw else FALLBACK_HEALTH.get(sign, "Balance your energy today.")
    
    return {'horoscope': horoscope, 'wealth': wealth, 'health': health}

# ========================================
# VIDEO CREATION
# ========================================

def create_text_image(text, width, height, fontsize):
    """Create text overlay"""
    img = Image.new('RGBA', (width, height), (0, 0, 0, 180))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    # Word wrap
    words = text.split()
    lines = []
    current = []
    
    for word in words:
        test = ' '.join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] < width - 80:
            current.append(word)
        else:
            if current:
                lines.append(' '.join(current))
            current = [word]
    if current:
        lines.append(' '.join(current))
    
    # Draw
    y = (height - len(lines) * (fontsize + 15)) // 2
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x+2, y+2), line, font=font, fill=(0,0,0,255))
        draw.text((x, y), line, font=font, fill=(255,255,255,255))
        y += fontsize + 15
    
    return np.array(img)

def create_shorts(all_content):
    """Create 12 shorts"""
    print("\n📱 Creating YouTube Shorts...")
    
    folder = f"{config['video']['output_folder']}/youtube_shorts"
    os.makedirs(folder, exist_ok=True)
    
    bg_video_path = config['video']['background_video']
    bg_music_path = config['video']['background_music']
    
    if not os.path.exists(bg_video_path):
        print(f"❌ {bg_video_path} not found!")
        return []
    
    videos = []
    
    for sign in config['zodiac_signs']:
        content = all_content[sign]
        print(f"\n  {sign}...")
        
        # Create text
        text = f"🌟 {sign} Daily 🌟\n\n✨ {content['horoscope']}\n\n💰 {content['wealth']}\n\n🏥 {content['health']}"
        
        # Duration
        words = len(text.split())
        duration = min(max(20, words / 2.5), 58)
        print(f"  ⏱️ {duration:.1f}s")
        
        # Load background
        bg = VideoFileClip(bg_video_path)
        
        # Loop if needed
        if bg.duration < duration:
            loops = int(duration / bg.duration) + 1
            bg = concatenate_videoclips([bg] * loops)
        bg = bg.subclip(0, duration)
        
        # Resize background to 1080x1920 (vertical)
        # Calculate aspect ratio crop
        target_w, target_h = 1080, 1920
        bg_w, bg_h = bg.size
        
        # Scale to fit height
        scale = target_h / bg_h
        new_w = int(bg_w * scale)
        new_h = target_h
        
        # Resize
        bg = bg.resize(height=new_h)
        
        # Center crop width if needed
        if bg.w > target_w:
            x_center = bg.w / 2
            x1 = int(x_center - target_w / 2)
            bg = bg.crop(x1=x1, width=target_w)
        elif bg.w < target_w:
            # Pad if too narrow (shouldn't happen with landscape source)
            from moviepy.editor import ColorClip
            pad = ColorClip(size=(target_w, target_h), color=(0,0,0), duration=duration)
            x_pos = (target_w - bg.w) // 2
            bg = CompositeVideoClip([pad, bg.set_position((x_pos, 0))])
        
        print(f"  ✅ Background: {bg.size}")
        
        # Text overlay
        text_img = create_text_image(text, 1080, 1920, 42)
        text_overlay = ImageClip(text_img).set_duration(duration).set_opacity(0.9)
        
        # Watermark
        wm_img = create_text_image(config['branding']['watermark_text'], 250, 60, 25)
        watermark = ImageClip(wm_img).set_duration(duration).set_position(('right','top')).set_opacity(0.6)
        
        # Composite
        video = CompositeVideoClip([bg, text_overlay, watermark])
        
        # Add music
        if os.path.exists(bg_music_path):
            music = AudioFileClip(bg_music_path).volumex(config['video']['music_volume'])
            if music.duration < duration:
                loops = int(duration / music.duration) + 1
                music = concatenate_audioclips([music] * loops)
            music = music.subclip(0, duration)
            video = video.set_audio(music)
        
        # Export
        output = f"{folder}/{sign}_{datetime.now().strftime('%Y%m%d')}.mp4"
        video.write_videofile(output, fps=30, codec='libx264', audio_codec='aac', preset='fast', threads=4, logger=None)
        
        videos.append(output)
        print(f"  ✅ Done")
        
        # Cleanup
        bg.close()
        video.close()
    
    print(f"\n✅ {len(videos)} shorts created")
    return videos

# ========================================
# MAIN
# ========================================

def main():
    print("="*60)
    print("🌟 ASTROFINANCE DAILY - FREE")
    print("="*60)
    print(f"📅 {datetime.now().strftime('%B %d, %Y')}")
    
    if GROQ_API_KEY:
        print("🤖 AI: Groq ✅")
    elif HUGGINGFACE_API_KEY:
        print("🤖 AI: HuggingFace ✅")
    else:
        print("⚠️ No AI - using fallback")
    
    # Generate content
    print("\n🎭 Generating content...")
    all_content = {}
    for sign in config['zodiac_signs']:
        all_content[sign] = generate_content(sign)
    
    # Create shorts
    shorts = create_shorts(all_content)
    
    # Save metadata
    metadata = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'shorts': shorts,
        'content': all_content
    }
    
    with open(f"{config['video']['output_folder']}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n"+"="*60)
    print("✅ ALL DONE!")
    print("="*60)
    print(f"📁 {config['video']['output_folder']}/youtube_shorts/")
    for i, s in enumerate(shorts, 1):
        print(f"   {i}. {os.path.basename(s)}")
    print("\n🚀 Ready to upload!")
    print("💰 COST: $0.00")

if __name__ == "__main__":
    main()
