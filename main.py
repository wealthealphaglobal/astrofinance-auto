#!/usr/bin/env python3
"""
AstroFinance Daily - FREE Automated Content Creator
Generates daily horoscope videos with wealth & health tips
100% FREE - No paid APIs needed!
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

def get_free_ai_content(prompt, sign):
    """Fetch content from FREE AI APIs (HuggingFace or Groq)"""
    
    # Format prompt with variables
    formatted_prompt = prompt.format(sign=sign)
    
    # Try HuggingFace first (completely free!)
    if HUGGINGFACE_API_KEY:
        try:
            print(f"  🤖 Using HuggingFace AI (FREE)...")
            headers = {
                "Authorization": f"Bearer {HUGGINGFACE_API_KEY}"
            }
            
            payload = {
                "inputs": formatted_prompt,
                "parameters": {
                    "max_new_tokens": 250,
                    "temperature": 0.7,
                    "top_p": 0.9,
                    "return_full_text": False
                }
            }
            
            response = requests.post(
                config['free_ai']['api_url'],
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    generated = result[0].get('generated_text', '')
                    if generated:
                        return generated.strip()
                print(f"  ⚠️ HuggingFace unexpected response format")
            else:
                print(f"  ⚠️ HuggingFace error {response.status_code}: {response.text[:100]}")
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
                "max_tokens": 250
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
                print(f"  ⚠️ Groq error {response.status_code}: {response.text[:100]}")
        except Exception as e:
            print(f"  ⚠️ Groq failed: {e}")
    
    # No API keys available
    print(f"  ⚠️ Using fallback content (no AI API available)")
    return None

# ========================================
# FALLBACK CONTENT (if AI unavailable)
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
    tips = {
        'Aries': [
            "Take calculated risks in your investments today.",
            "Your bold approach can lead to financial gains - trust your instincts.",
            "Consider starting that side project you've been thinking about."
        ],
        'Taurus': [
            "Focus on building long-term financial security.",
            "Review your savings strategy and look for better interest rates.",
            "Patient investing pays off - avoid get-rich-quick schemes."
        ],
        'Gemini': [
            "Diversify your income streams to maximize earnings.",
            "Network with financial experts to gain new insights.",
            "Stay informed but avoid information overload when making decisions."
        ],
        'Cancer': [
            "Real estate or family business investments look favorable.",
            "Trust your emotional intelligence when evaluating opportunities.",
            "Secure your financial future by planning for loved ones."
        ],
        'Leo': [
            "Invest in yourself - education and skills pay dividends.",
            "Your confidence attracts lucrative opportunities.",
            "Consider leadership roles or entrepreneurship for wealth building."
        ],
        'Virgo': [
            "Your analytical skills help identify undervalued assets.",
            "Create detailed budgets and stick to systematic saving plans.",
            "Research thoroughly before making any financial commitment."
        ],
        'Libra': [
            "Balance growth investments with stable income sources.",
            "Partner with financially savvy people for mutual benefit.",
            "Aesthetic businesses or beauty industry investments may prosper."
        ],
        'Scorpio': [
            "Deep research uncovers hidden investment opportunities.",
            "Your intensity serves long-term wealth accumulation.",
            "Transform your financial situation through strategic planning."
        ],
        'Sagittarius': [
            "International markets or foreign investments look promising.",
            "Expand your financial horizons through education and travel.",
            "Optimism is good, but due diligence is essential."
        ],
        'Capricorn': [
            "Your disciplined approach builds substantial wealth over time.",
            "Focus on traditional, proven investment strategies.",
            "Professional advancement leads to increased earning potential."
        ],
        'Aquarius': [
            "Innovative technologies and emerging markets offer opportunities.",
            "Think unconventionally about income generation.",
            "Community-based or socially responsible investments align with your values."
        ],
        'Pisces': [
            "Trust your intuition but verify with financial facts.",
            "Creative pursuits can become profitable ventures.",
            "Compassionate businesses or healing industries may reward you."
        ]
    }
    return tips.get(sign, [
        "Focus on building emergency savings today.",
        "Review your spending habits and identify areas to cut costs.",
        "Consider consulting a financial advisor for personalized guidance."
    ])

def get_fallback_health_tips(sign):
    """Generate basic health tips"""
    tips = {
        'Aries': [
            "Channel high energy with cardio or competitive sports.",
            "Watch stress levels - practice breathing exercises.",
            "Protect your head and take breaks from screen time."
        ],
        'Taurus': [
            "Try gentle yoga or stretching for neck and throat health.",
            "Enjoy good food but maintain balanced portions.",
            "Spend time in nature to ground yourself."
        ],
        'Gemini': [
            "Calm your active mind with meditation or journaling.",
            "Practice deep breathing exercises for lung health.",
            "Vary your workout routine to stay engaged."
        ],
        'Cancer': [
            "Support digestive health with mindful eating habits.",
            "Process emotions healthily - talk to someone you trust.",
            "Swimming or water activities soothe your soul."
        ],
        'Leo': [
            "Protect heart health with cardio exercise.",
            "Practice good posture to support your spine.",
            "Rest is productive - avoid burnout."
        ],
        'Virgo': [
            "Support digestive health with probiotics and fiber.",
            "Practice self-compassion to reduce stress.",
            "Create healthy routines with built-in flexibility."
        ],
        'Libra': [
            "Drink plenty of water for kidney health.",
            "Find balance in exercise - not too much or too little.",
            "Partner workouts keep you motivated."
        ],
        'Scorpio': [
            "Release intensity through boxing or vigorous exercise.",
            "Honor your body's need for transformation and rest.",
            "Stay hydrated and support elimination processes."
        ],
        'Sagittarius': [
            "Stretch regularly to protect hips and thighs.",
            "Enjoy outdoor activities and hiking.",
            "Warm up properly before physical activities."
        ],
        'Capricorn': [
            "Include calcium and vitamin D for bone health.",
            "Your discipline serves fitness - maintain consistency.",
            "Schedule rest days for muscle recovery."
        ],
        'Aquarius': [
            "Keep circulation healthy by moving throughout the day.",
            "Try unique workouts that interest you.",
            "Group fitness classes match your social nature."
        ],
        'Pisces': [
            "Care for your feet with comfortable, supportive shoes.",
            "Water activities and swimming restore you.",
            "Try gentle exercise like tai chi or yoga."
        ]
    }
    return tips.get(sign, [
        "Aim for 8 hours of quality sleep tonight.",
        "Stay hydrated with at least 8 glasses of water.",
        "Take short breaks to stretch and move."
    ])

# ========================================
# CONTENT GENERATION
# ========================================

def generate_daily_content(sign):
    """Generate all content for one zodiac sign using FREE AI"""
    print(f"\n✨ Generating content for {sign}...")
    
    # Get horoscope
    horoscope = get_free_ai_content(
        config['free_ai']['prompts']['horoscope'],
        sign
    ) or FALLBACK_HOROSCOPES.get(sign, "The stars align favorably for you today.")
    
    # Get wealth tips
    wealth_tips_raw = get_free_ai_content(
        config['free_ai']['prompts']['wealth'],
        sign
    )
    
    if wealth_tips_raw:
        wealth_tips = [tip.strip('• -*').strip() for tip in wealth_tips_raw.split('\n') if tip.strip() and len(tip.strip()) > 10]
    else:
        wealth_tips = get_fallback_wealth_tips(sign)
    
    # Get health tips
    health_tips_raw = get_free_ai_content(
        config['free_ai']['prompts']['health'],
        sign
    )
    
    if health_tips_raw:
        health_tips = [tip.strip('• -*').strip() for tip in health_tips_raw.split('\n') if tip.strip() and len(tip.strip()) > 10]
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
            draw.text((x + 2, y_offset + 2), line, font=font, fill=(0, 0, 0, 255))
            # Draw text
            draw.text((x, y_offset), line, font=font, fill=tuple(config['text_style']['font_color'] + [255]))
            y_offset += fontsize + 15
    else:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        # Draw shadow
        draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 255))
        # Draw text
        draw.text((x, y), text, font=font, fill=tuple(config['text_style']['font_color'] + [255]))
    
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
    output_folder = f"{config['video']['output_folder']}/youtube"
    os.makedirs(output_folder, exist_ok=True)
    output_path = f"{output_folder}/daily_horoscope_{datetime.now().strftime('%Y%m%d')}.mp4"
    print(f"  💾 Exporting to {output_path}...")
    
    final_video.write_videofile(
        output_path,
        fps=config['platforms']['youtube']['long_form']['fps'],
        codec='libx264',
        audio_codec='aac',
        preset='medium',
        threads=4,
        logger=None
    )
    
    print(f"  ✅ YouTube video complete! Duration: {final_video.duration/60:.1f} minutes")
    return output_path

def create_youtube_shorts(all_content):
    """Create 12 YouTube Shorts (one per zodiac sign, under 59 seconds)"""
    print("\n📱 Creating 12 YouTube Shorts (under 59 seconds each)...")
    
    shorts_folder = f"{config['video']['output_folder']}/youtube_shorts"
    os.makedirs(shorts_folder, exist_ok=True)
    
    short_videos = []
    resolution = config['platforms']['youtube']['shorts']['resolution']
    
    for sign in config['zodiac_signs']:
        content = all_content[sign]
        
        print(f"\n  Creating short for {sign}...")
        
        # Condense content to fit in 59 seconds
        short_horoscope = content['horoscope'][:120]
        short_wealth = content['wealth_tips'][0][:80] if content['wealth_tips'] else "Stay financially wise today."
        short_health = content['health_tips'][0][:80] if content['health_tips'] else "Take care of your health."
        
        # Create condensed text
        short_text = f"🌟 {sign} 🌟\n\n✨ {short_horoscope}\n\n💰 {short_wealth}\n\n🏥 {short_health}"
        
        # Create speech (keep it brief!)
        short_speech = f"{sign}. {short_horoscope}. Wealth tip: {short_wealth}. Health tip: {short_health}."
        
        # Generate audio
        audio_file = f"{config['video']['temp_folder']}/{sign}_short.mp3"
        text_to_speech(short_speech, audio_file)
        audio_clip = AudioFileClip(audio_file)
        
        # CRITICAL: Limit to 58 seconds to be safe
        max_duration = 58
        if audio_clip.duration > max_duration:
            audio_clip = audio_clip.subclip(0, max_duration)
        
        duration = audio_clip.duration
        
        # Create text image
        img = create_text_image(short_text, resolution[0], resolution[1], 45)
        video_clip = ImageClip(img).set_duration(duration).set_audio(audio_clip)
        
        # Add watermark
        watermark_img = create_text_image(config['branding']['watermark_text'], 250, 60, 25, False)
        watermark = ImageClip(watermark_img).set_duration(duration).set_position(('right', 'top')).set_opacity(0.7)
        
        final_clip = CompositeVideoClip([video_clip, watermark])
        
        # Export
        output_path = f"{shorts_folder}/{sign}_{datetime.now().strftime('%Y%m%d')}.mp4"
        final_clip.write_videofile(
            output_path,
            fps=config['platforms']['youtube']['shorts']['fps'],
            codec='libx264',
            audio_codec='aac',
            preset='ultrafast',
            logger=None
        )
        
        short_videos.append(output_path)
        print(f"  ✅ {sign} short created ({duration:.1f}s) - {output_path}")
        
        # Cleanup
        audio_clip.close()
        video_clip.close()
        final_clip.close()
        try:
            os.remove(audio_file)
        except:
            pass
    
    print(f"\n✅ Created {len(short_videos)} YouTube Shorts")
    return short_videos

# ========================================
# MAIN EXECUTION
# ========================================

def main():
    print("=" * 60)
    print("🌟 ASTROFINANCE DAILY - FREE CONTENT GENERATOR 🌟")
    print("=" * 60)
    print(f"📅 Date: {datetime.now().strftime('%B %d, %Y')}")
    
    # Check which AI provider is available
    if HUGGINGFACE_API_KEY:
        print(f"🤖 Using FREE AI: HuggingFace ✅")
    elif GROQ_API_KEY:
        print(f"🤖 Using FREE AI: Groq ✅")
    else:
        print(f"⚠️ No AI API configured - using fallback content")
    
    # Generate content for all signs
    print("\n🎭 Generating content for all zodiac signs...")
    all_content = {}
    all_segments = []
    
    for sign in config['zodiac_signs']:
        content = generate_daily_content(sign)
        all_content[sign] = content
        
        # Create video segment
        segment = create_sign_segment(
            sign,
            content,
            config['platforms']['youtube']['long_form']['resolution']
        )
        all_segments.append(segment)
    
    # Create 1 BIG YouTube video (all signs)
    print("\n" + "=" * 60)
    print("📺 CREATING YOUTUBE VIDEOS")
    print("=" * 60)
    youtube_long_video = create_youtube_long_video(all_segments)
    
    # Create 12 YouTube Shorts (one per sign, under 59 seconds)
    youtube_shorts = create_youtube_shorts(all_content)
    
    # Save metadata
    metadata = {
        'date': datetime.now().strftime('%Y-%m-%d'),
        'youtube_long_video': youtube_long_video,
        'youtube_shorts': youtube_shorts,
        'content': all_content
    }
    
    with open(f"{config['video']['output_folder']}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 60)
    print("✅ ALL VIDEOS GENERATED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📁 Output folder: {config['video']['output_folder']}/")
    print(f"\n📺 YOUTUBE LONG VIDEO (40 mins):")
    print(f"   {youtube_long_video}")
    print(f"\n📱 YOUTUBE SHORTS (12 videos, <59 sec each):")
    for i, short in enumerate(youtube_shorts, 1):
        print(f"   {i}. {os.path.basename(short)}")
    print("\n🚀 Ready for upload!")
    print("💰 TOTAL COST: $0.00 (100% FREE!)")

if __name__ == "__main__":
    main()
