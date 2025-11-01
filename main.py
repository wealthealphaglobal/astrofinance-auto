#!/usr/bin/env python3
"""
AstroFinance Daily - Automated Content Creator
Generates daily horoscope videos with wealth & health tips for all platforms
"""

import os
import sys
import yaml
import requests
import json
from datetime import datetime
from gtts import gTTS
from moviepy.editor import (VideoFileClip, AudioFileClip, CompositeVideoClip, 
                            ImageClip, concatenate_videoclips, CompositeAudioClip)
from PIL import Image, ImageDraw, ImageFont
import numpy as np

# Load configuration
print("📋 Loading configuration...")
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

# Create necessary folders
os.makedirs(config['video']['output_folder'], exist_ok=True)
os.makedirs(config['video']['temp_folder'], exist_ok=True)

# Get API keys from environment variables (set by GitHub Actions)
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY', '')
GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')

# ========================================
# FREE AI INTEGRATION (HuggingFace or Groq)
# ========================================

def get_free_ai_content(prompt, sign, btc_price=None, market_trend=None):
    """Fetch content from FREE AI APIs (HuggingFace or Groq)"""
    
    # Format prompt with variables
    formatted_prompt = prompt.format(
        sign=sign,
        btc_price=btc_price or "N/A",
        market_trend=market_trend or "neutral"
    )
    
    # Try HuggingFace first (completely free!)
    if HUGGINGFACE_API_KEY:
        try:
            print(f"  🤖 Using HuggingFace AI (FREE)...")
            headers = {
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 300,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                config['free_ai']['api_url'],
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get('generated_text', '').strip()
            else:
                print(f"  ⚠️ HuggingFace error: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ HuggingFace failed: {e}")
    
    # Try Groq as backup (also free!)
    if GROQ_API_KEY:
        try:
            print(f"  🤖 Using Groq AI (FREE)...")
            headers = {
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": config['free_ai']['groq_model'],
                "messages": [
                    {"role": "system", "content": "You are an expert astrologer and financial advisor."},
                    {"role": "user", "content": formatted_prompt}
                ],
                "temperature": 0.7,
                "max_tokens": 300
            }
            
            response = requests.post(
                config['free_ai']['groq_api_url'],
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content'].strip()
            else:
                print(f"  ⚠️ Groq error: {response.status_code}")
        except Exception as e:
            print(f"  ⚠️ Groq failed: {e}")
    
    # No API keys available
    print(f"  ⚠️ No AI API keys configured. Using fallback content.")
    return None

# ========================================
# MARKET DATA
# ========================================

def get_bitcoin_price():
    """Fetch current Bitcoin price"""
    try:
        res = requests.get(config['apis']['bitcoin']['url'], timeout=10)
        return float(res.json()["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print(f"⚠️ Bitcoin API error: {e}")
        return None

def get_market_trend():
    """Fetch S&P 500 trend"""
    try:
        res = requests.get(config['apis']['stock_market']['url'], timeout=10)
        data = res.json()
        current = data['chart']['result'][0]['meta']['regularMarketPrice']
        previous = data['chart']['result'][0]['meta']['previousClose']
        change = ((current - previous) / previous) * 100
        return 'bullish' if change > 0 else 'bearish'
    except:
        return 'neutral'

# ========================================
# FALLBACK CONTENT (if ChatGPT unavailable)
# ========================================

FALLBACK_HOROSCOPES = {
    'Aries': "Today brings opportunities for bold action. Your natural leadership shines, attracting positive attention. Trust your instincts in both personal and professional matters.",
    'Taurus': "Financial stability is highlighted today. Your practical approach yields results. Focus on long-term goals and resist impulsive decisions.",
    'Gemini': "Communication flows easily today. Share your ideas and connect with others. Mental agility helps you navigate challenges with grace.",
    'Cancer': "Emotional intelligence guides you today. Nurture relationships and trust your intuition. Home and family bring comfort and joy.",
    'Leo': "Your confidence radiates today. Creative projects flourish under your passionate energy. Leadership opportunities arise naturally.",
    'Virgo': "Attention to detail serves you well today. Organize, plan, and execute with precision. Health and wellness deserve focus.",
    'Libra': "Balance and harmony are within reach today. Relationships benefit from your diplomatic approach. Beauty and art inspire you.",
    'Scorpio': "Transformation is in the air today. Deep insights emerge from introspection. Trust the process of change and renewal.",
    'Sagittarius': "Adventure calls today. Expand your horizons through learning and exploration. Optimism attracts fortunate circumstances.",
    'Capricorn': "Disciplined effort yields rewards today. Your ambition and structure create solid foundations. Professional recognition is possible.",
    'Aquarius': "Innovation and originality are your strengths today. Think outside the box. Community connections bring unexpected opportunities.",
    'Pisces': "Intuition and creativity flow freely today. Artistic expression brings fulfillment. Compassion connects you deeply with others."
}

def get_fallback_wealth_tips(sign):
    """Generate basic wealth tips"""
    return [
        f"{sign}, focus on long-term investment strategies today.",
        "Diversify your portfolio to manage risk effectively.",
        "Review your budget and identify areas for savings."
    ]

def get_fallback_health_tips(sign):
    """Generate basic health tips"""
    return [
        f"{sign}, prioritize 8 hours of quality sleep tonight.",
        "Stay hydrated with at least 8 glasses of water today.",
        "Take short breaks every hour to stretch and move."
    ]

# ========================================
# CONTENT GENERATION
# ========================================

def generate_daily_content(sign, btc_price, market_trend):
    """Generate all content for one zodiac sign using ChatGPT"""
    print(f"\n✨ Generating content for {sign}...")
    
    # Get horoscope
    horoscope = get_chatgpt_content(
        config['chatgpt']['prompts']['horoscope'],
        sign
    ) or FALLBACK_HOROSCOPES.get(sign, "The stars align favorably for you today.")
    
    # Get wealth tips
    wealth_tips_raw = get_chatgpt_content(
        config['chatgpt']['prompts']['wealth'],
        sign,
        btc_price,
        market_trend
    )
    
    if wealth_tips_raw:
        wealth_tips = [tip.strip('• -').strip() for tip in wealth_tips_raw.split('\n') if tip.strip()]
    else:
        wealth_tips = get_fallback_wealth_tips(sign)
    
    # Get health tips
    health_tips_raw = get_chatgpt_content(
        config['chatgpt']['prompts']['health'],
        sign
    )
    
    if health_tips_raw:
        health_tips = [tip.strip('• -').strip() for tip in health_tips_raw.split('\n') if tip.strip()]
    else:
        health_tips = get_fallback_health_tips(sign)
    
    return {
        'horoscope': horoscope,
        'wealth_tips': wealth_tips[:3],  # Limit to 3 tips
        'health_tips': health_tips[:3]   # Limit to 3 tips
    }

# ========================================
# VIDEO CREATION
# ========================================

def create_text_image(text, width, height, fontsize, wrap=True):
    """Create text overlay image"""
    # Create semi-transparent background
    img = Image.new('RGBA', (width, height), (0, 0, 0, config['text_style']['background_opacity']))
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", fontsize)
    except:
        font = ImageFont.load_default()
    
    if wrap:
        # Word wrap logic
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            bbox = draw.textbbox((0, 0), test_line, font=font)
            if bbox[2] - bbox[0] < width - 80:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw lines
        y_offset = (height - len(lines) * (fontsize + 15)) // 2
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            text_width = bbox[2] - bbox[0]
            x = (width - text_width) // 2
            
            # Draw shadow
            draw.text((x + 2, y_offset + 2), line, font=font, fill=tuple(config['text_style']['shadow_color']))
            # Draw text
            draw.text((x, y_offset), line, font=font, fill=tuple(config['text_style']['font_color']))
            y_offset += fontsize + 15
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw shadow
        draw.text((x + 2, y + 2), text, font=font, fill=tuple(config['text_style']['shadow_color']))
        # Draw text
        draw.text((x, y), text, font=font, fill=tuple(config['text_style']['font_color']))
    
    return np.array(img)

def text_to_speech(text, filename):
    """Convert text to speech"""
    tts = gTTS(text, lang='en', slow=False)
    tts.save(filename)
    return filename

def create_sign_segment(sign, content, resolution):
    """Create complete video segment for one zodiac sign"""
    width, height = resolution
    clips = []
    
    print(f"  🎬 Creating video for {sign}...")
    
    # 1. INTRO SCREEN
    intro_text = f"🌟 {sign} 🌟\nDaily Forecast"
    intro_speech = f"{sign}. Your daily cosmic guidance."
    intro_audio = text_to_speech(intro_speech, f"{config['video']['temp_folder']}/{sign}_intro.mp3")
    
    intro_audio_clip = AudioFileClip(intro_audio)
    intro_img = create_text_image(intro_text, width, height, config['text_style']['title_font_size'], False)
    intro_clip = ImageClip(intro_img).set_duration(intro_audio_clip.duration).set_audio(intro_audio_clip)
    clips.append(intro_clip)
    
    # 2. HOROSCOPE
    horoscope_text = f"✨ TODAY'S HOROSCOPE ✨\n\n{content['horoscope']}"
    horoscope_speech = f"Today's horoscope for {sign}. {content['horoscope']}"
    horoscope_audio = text_to_speech(horoscope_speech, f"{config['video']['temp_folder']}/{sign}_horoscope.mp3")
    
    horoscope_audio_clip = AudioFileClip(horoscope_audio)
    horoscope_img = create_text_image(horoscope_text, width, height, config['text_style']['content_font_size'])
    horoscope_clip = ImageClip(horoscope_img).set_duration(horoscope_audio_clip.duration).set_audio(horoscope_audio_clip)
    clips.append(horoscope_clip)
    
    # 3. WEALTH TIPS
    wealth_text = "💰 WEALTH GUIDANCE 💰\n\n" + "\n\n".join([f"• {tip}" for tip in content['wealth_tips']])
    wealth_speech = f"Wealth guidance for {sign}. " + " ".join(content['wealth_tips'])
    wealth_audio = text_to_speech(wealth_speech, f"{config['video']['temp_folder']}/{sign}_wealth.mp3")
    
    wealth_audio_clip = AudioFileClip(wealth_audio)
    wealth_img = create_text_image(wealth_text, width, height, config['text_style']['tip_font_size'])
    wealth_clip = ImageClip(wealth_img).set_duration(wealth_audio_clip.duration).set_audio(wealth_audio_clip)
    clips.append(wealth_clip)
    
    # 4. HEALTH TIPS
    health_text = "🏥 HEALTH GUIDANCE 🏥\n\n" + "\n\n".join([f"• {tip}" for tip in content['health_tips']])
    health_speech = f"Health guidance for {sign}. " + " ".join(content['health_tips'])
    health_audio = text_to_speech(health_speech, f"{config['video']['temp_folder']}/{sign}_health.mp3")
    
    health_audio_clip = AudioFileClip(health_audio)
    health_img = create_text_image(health_text, width, height, config['text_style']['tip_font_size'])
    health_clip = ImageClip(health_img).set_duration(health_audio_clip.duration).set_audio(health_audio_clip)
    clips.append(health_clip)
    
    # Concatenate all clips for this sign
    segment = concatenate_videoclips(clips, method="compose")
    
    print(f"  ✅ {sign} segment complete ({segment.duration:.1f}s)")
    return segment

def create_intro_outro(text, duration, resolution):
    """Create intro/outro screens"""
    width, height = resolution
    speech = text_to_speech(text, f"{config['video']['temp_folder']}/intro_outro.mp3")
    audio_clip = AudioFileClip(speech)
    
    img = create_text_image(text, width, height, config['text_style']['title_font_size'], False)
    clip = ImageClip(img).set_duration(min(duration, audio_clip.duration)).set_audio(audio_clip.subclip(0, min(duration, audio_clip.duration)))
    
    return clip

def create_youtube_long_video(all_segments):
    """Create 40-minute YouTube video"""
    print("\n📺 Creating YouTube long-form video...")
    
    resolution = config['platforms']['youtube']['long_form']['resolution']
    
    # Create intro
    intro_text = f"{config['branding']['channel_name']}\n{config['branding']['tagline']}\n\n{datetime.now().strftime('%B %d, %Y')}"
    intro_clip = create_intro_outro(intro_text, config['timing']['intro_duration'], resolution)
    
    # Create outro
    outro_text = "Thank you for watching!\n\n🔔 Subscribe for daily guidance\n👍 Like & Share\n💬 Comment your sign"
    outro_clip = create_intro_outro(outro_text, config['timing']['outro_duration'], resolution)
    
    # Combine all
    final_clips = [intro_clip] + all_segments + [outro_clip]
    final_video = concatenate_videoclips(final_clips, method="compose")
    
    # Add background music (OM Mantra)
    if os.path.exists(config['video']['background_music']):
        print("  🎵 Adding OM Mantra background music...")
        bg_music = AudioFileClip(config['video']['background_music'])
        bg_music = bg_music.volumex(config['video']['music_volume'])
        
        # Loop music to match video
        if bg_music.duration < final_video.duration:
            loops_needed = int(final_video.duration / bg_music.duration) + 1
            bg_music = concatenate_audioclips([bg_music] * loops_needed).subclip(0, final_video.duration)
        else:
            bg_music = bg_music.subclip(0, final_video.duration)
        
        # Mix audio
        final_audio = CompositeAudioClip([final_video.audio, bg_music])
        final_video = final_video.set_audio(final_audio)
    
    # Add watermark
    watermark_img = create_text_image(config['branding']['watermark_text'], 300, 80, 30, False)
    watermark = ImageClip(watermark_img).set_duration(final_video.duration)
    watermark = watermark.set_position(('right', 'top')).set_opacity(0.7)
    
    final_video = CompositeVideoClip([final_video, watermark])
    
    # Export
    output_path = f"{config['video']['output_folder']}/youtube/daily_horoscope_{datetime.now().strftime('%Y%m%d')}.mp4"
    print(f"  💾 Exporting to {output_path}...")
    
    final_video.write_videofile(
        output_path,
        fps=config['platforms']['youtube']['long_form']['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4
    )
    
    print(f"  ✅ YouTube video complete! Duration: {final_video.duration/60:.1f} minutes")
    return output_path

def create_shorts_reels(all_content):
    """Create short-form content for each platform"""
    print("\n📱 Creating short-form content...")
    
    outputs = {}
    
    for platform in ['youtube', 'instagram', 'tiktok']:
        if not config['platforms'][platform]['enabled']:
            continue
            
        print(f"\n  Creating {platform} shorts...")
        
        if platform == 'youtube':
            resolution = config['platforms']['youtube']['shorts']['resolution']
            max_duration = config['platforms']['youtube']['shorts']['duration']
        else:
            resolution = config['platforms'][platform]['resolution']
            max_duration = config['platforms'][platform]['duration']
        
        platform_videos = []
        
        # Create one short per zodiac sign
        for sign in config['zodiac_signs']:
            content = all_content[sign]
            
            # Condense to fit duration
            short_text = f"🌟 {sign} 🌟\n\n{content['horoscope'][:100]}...\n\n💰 {content['wealth_tips'][0][:50]}...\n\n🏥 {content['health_tips'][0][:50]}..."
            short_speech = f"{sign}. {content['horoscope'][:100]}. Wealth tip: {content['wealth_tips'][0][:50]}. Health tip: {content['health_tips'][0][:50]}."
            
            audio_file = text_to_speech(short_speech, f"{config['video']['temp_folder']}/{sign}_{platform}_short.mp3")
            audio_clip = AudioFileClip(audio_file)
            
            # Limit to max duration
            duration = min(audio_clip.duration, max_duration)
            audio_clip = audio_clip.subclip(0, duration)
            
            img = create_text_image(short_text, resolution[0], resolution[1], 45)
            video_clip = ImageClip(img).set_duration(duration).set_audio(audio_clip)
            
            output_path = f"{config['video']['output_folder']}/{platform}/{sign}_{datetime.now().strftime('%Y%m%d')}.mp4"
            video_clip.write_videofile(output_path, fps=30, codec='libx264', audio_codec='aac', preset='ultrafast')
            
            platform_videos.append(output_path)
        
        outputs[platform] = platform_videos
        print(f"  ✅ Created {len(platform_videos)} {platform} videos")
    
    return outputs

# ========================================
# MAIN EXECUTION
# ========================================

def main():
    print("=" * 60)
    print("🌟 ASTROFINANCE DAILY - CONTENT GENERATOR 🌟")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    print(f"🤖 Using ChatGPT: {bool(OPENAI_API_KEY)}")
    
    # Get market data
    print("\n📊 Fetching market data...")
    btc_price = get_bitcoin_price()
    market_trend = get_market_trend()
    
    if btc_price:
        print(f"  ₿ Bitcoin: ${btc_price:,.2f}")
    print(f"  📈 Market: {market_trend}")
    
    # Generate content for all signs
    print("\n🎭 Generating content for all zodiac signs...")
    all_content = {}
    all_segments = []
    
    for sign in config['zodiac_signs']:
        content = generate_daily_content(sign, btc_price, market_trend)
        all_content[sign] = content
        
        # Create video segment
        segment = create_sign_segment(
            sign,
            content,
            config['platforms']['youtube']['long_form']['resolution']
        )
        all_segments.append(segment)
    
    # Create YouTube long-form video
    youtube_video = create_youtube_long_video(all_segments)
    
    # Create short-form content
    shorts = create_shorts_reels(all_content)
    
    # Save metadata for uploading
    metadata = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'youtube_video': youtube_video,
        'shorts': shorts,
        'content': all_content
    }
    
    with open(f"{config['video']['output_folder']}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ ALL VIDEOS GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📁 Output folder: {config['video']['output_folder']}/")
    print(f"📺 YouTube video: {youtube_video}")
    print(f"📱 Shorts/Reels: {sum(len(v) for v in shorts.values())} files")
    print("\n🚀 Ready for upload!")

if __name__ == "__main__":
    main()
