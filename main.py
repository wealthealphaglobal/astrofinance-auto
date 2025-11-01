import requests, os, random
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, TextClip, CompositeVideoClip

# --------- SETTINGS ---------
SIGN_LIST = ["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
BACKGROUND_FILE = "background.mp4"
UPLOAD_FOLDER = "videos"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# ----------------------------

def get_astrology(sign):
    # Free horoscope API
    url = f"https://aztro.sameerkumar.website/?sign={sign.lower()}&day=today"
    try:
        res = requests.post(url, timeout=10)
        data = res.json()
        return data.get("description","No horoscope available today.")
    except Exception as e:
        print(f"⚠️ Astrology API error for {sign}: {e}")
        return "The stars are aligning in your favor today."

def get_bitcoin_price():
    try:
        price = requests.get("https://api.coindesk.com/v1/bpi/currentprice/USD.json", timeout=10).json()
        return float(price["bpi"]["USD"]["rate_float"])
    except Exception as e:
        print(f"⚠️ Bitcoin API error: {e}")
        return None

def make_script(sign, horoscope, btc_price):
    finance_line = ""
    if btc_price:
        if btc_price > 65000:
            finance_line = "Bitcoin stays strong today. A stable day for patient investors."
        elif btc_price < 60000:
            finance_line = "Markets may look shaky. Trust your intuition before investing."
        else:
            finance_line = "Balanced market energy supports your goals."
    text = f"{sign}: {horoscope} {finance_line}"
    return text

def make_video(sign, script):
    print(f"🎬 Creating video for {sign}...")
    
    # Create audio from text
    tts = gTTS(script, lang='en', slow=False)
    audio_file = f"{UPLOAD_FOLDER}/{sign}.mp3"
    tts.save(audio_file)
    print(f"  ✓ Audio saved: {audio_file}")
    
    # Load audio and get duration
    audio = AudioFileClip(audio_file)
    audio_duration = audio.duration
    print(f"  ✓ Audio duration: {audio_duration:.2f}s")
    
    # Load background video and loop/trim to match audio
    bg_clip = VideoFileClip(BACKGROUND_FILE)
    
    # If audio is longer than video, loop the video
    if audio_duration > bg_clip.duration:
        num_loops = int(audio_duration / bg_clip.duration) + 1
        bg_clip = bg_clip.loop(n=num_loops)
    
    # Trim to match audio duration
    video_clip = bg_clip.subclip(0, audio_duration)
    print(f"  ✓ Video clip prepared: {audio_duration:.2f}s")
    
    # Create text overlay
    txt = TextClip(
        f"{sign} — AstroFinance", 
        fontsize=70, 
        color='white',
        font='Arial-Bold',  # Added font parameter
        size=(1080, None),
        method='caption'
    ).set_duration(audio_duration).set_position(('center', 'bottom'))
    print(f"  ✓ Text overlay created")
    
    # Combine video with audio
    video_with_audio = video_clip.set_audio(audio)
    
    # Composite everything together
    final = CompositeVideoClip([video_with_audio, txt])
    
    # Write output
    output = f"{UPLOAD_FOLDER}/{sign}.mp4"
    final.write_videofile(
        output, 
        fps=24, 
        codec="libx264", 
        audio_codec="aac",
        preset='ultrafast',  # Faster encoding
        threads=4,
        logger=None
    )
    
    # Clean up
    audio.close()
    bg_clip.close()
    video_clip.close()
    final.close()
    
    print(f"  ✓ Video saved: {output}")
    return output

def main():
    print("=" * 50)
    print("🌟 ASTROFINANCE VIDEO GENERATOR 🌟")
    print("=" * 50)
    
    # Check if background video exists
    if not os.path.exists(BACKGROUND_FILE):
        print(f"❌ ERROR: {BACKGROUND_FILE} not found!")
        print("   The workflow should create it. Check previous steps.")
        return
    
    print(f"✓ Background video found: {BACKGROUND_FILE}")
    
    # Get Bitcoin price once
    print("\n📊 Fetching Bitcoin price...")
    btc = get_bitcoin_price()
    if btc:
        print(f"✓ Bitcoin price: ${btc:,.2f}")
    else:
        print("⚠️ Could not fetch Bitcoin price, continuing without it")
    
    print(f"\n🎥 Creating videos for {len(SIGN_LIST)} zodiac signs...")
    print("-" * 50)
    
    success_count = 0
    fail_count = 0
    
    for sign in SIGN_LIST:
        try:
            horoscope = get_astrology(sign)
            script = make_script(sign, horoscope, btc)
            print(f"\n📝 Script for {sign}:")
            print(f"   {script[:100]}...")  # Print first 100 chars
            
            make_video(sign, script)
            print(f"✅ SUCCESS: {sign} video created")
            success_count += 1
            
        except Exception as e:
            print(f"❌ FAILED: {sign}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()  # Print full error for debugging
            fail_count += 1
    
    print("\n" + "=" * 50)
    print(f"✅ Successful: {success_count}/{len(SIGN_LIST)}")
    print(f"❌ Failed: {fail_count}/{len(SIGN_LIST)}")
    print("=" * 50)

if __name__ == "__main__":
    main()
