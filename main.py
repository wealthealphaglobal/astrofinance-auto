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
    res = requests.post(url)
    data = res.json()
    return data.get("description","")

def get_bitcoin_price():
    try:
        price = requests.get("https://api.coindesk.com/v1/bpi/currentprice/USD.json").json()
        return float(price["bpi"]["USD"]["rate_float"])
    except:
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
    tts = gTTS(script)
    audio_file = f"{UPLOAD_FOLDER}/{sign}.mp3"
    tts.save(audio_file)
    clip = VideoFileClip(BACKGROUND_FILE).subclip(0,15)
    audio = AudioFileClip(audio_file)
    txt = TextClip(f"{sign} — AstroFinance", fontsize=70, color='white', size=(1080,200)).set_duration(audio.duration)
    final = CompositeVideoClip([clip.set_audio(audio), txt.set_position(('center','bottom'))])
    output = f"{UPLOAD_FOLDER}/{sign}.mp4"
    final.write_videofile(output, fps=24, codec="libx264", audio_codec="aac", logger=None)
    return output

def main():
    btc = get_bitcoin_price()
    for sign in SIGN_LIST:
        try:
            text = make_script(sign, get_astrology(sign), btc)
            make_video(sign, text)
            print(f"✅ Created video for {sign}")
        except Exception as e:
            print(f"❌ Error with {sign}: {e}")

if __name__ == "__main__":
    main()
