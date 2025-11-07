#!/usr/bin/env python3
"""Upload a zodiac sign video to YouTube"""

import os
import sys
import argparse
import glob
from datetime import datetime
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Get YouTube credentials from environment
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID', '')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET', '')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN', '')


def get_latest_video(sign):
    """Find the most recently generated video for a sign"""
    pattern = f"videos/youtube_shorts/{sign}_*.mp4"
    videos = glob.glob(pattern)
    if not videos:
        return None
    return max(videos, key=os.path.getctime)


def upload_to_youtube(video_path, sign):
    """Upload video to YouTube Shorts"""
    if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN]):
        print(f"  ⚠️ YouTube credentials not configured - skipping upload")
        return None
    
    try:
        print(f"  📤 Uploading to YouTube...")
        
        # Create credentials
        credentials = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET
        )
        
        # Build YouTube API client
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Create video metadata
        today = datetime.now().strftime("%B %d, %Y")
        title = f"{sign} Daily Horoscope & Cosmic Guidance | {today} #Shorts"
        description = f"""🌟 {sign} Daily Horoscope for {today}

✨ Today's Cosmic Guidance:
- Daily Horoscope
- Wealth & Financial Tips
- Health & Wellness Blessings

🔔 Subscribe for daily cosmic guidance!
💬 Comment your zodiac sign below
👍 Like if this resonates with you

#{sign} #Horoscope #Astrology #DailyHoroscope #Zodiac #Shorts #VedicAstrology #CosmicGuidance #Spirituality

⚠️ For entertainment purposes only. Consult professionals for serious decisions."""
        
        tags = [
            "horoscope", "daily horoscope", "astrology", sign.lower(),
            "zodiac", "shorts", "vedic astrology", "cosmic guidance",
            "spiritual", "horoscope today", f"{sign.lower()} horoscope"
        ]
        
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags,
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',
                'madeForKids': False,
                'selfDeclaredMadeForKids': False
            }
        }
        
        # Upload video
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
        request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"    Upload progress: {int(status.progress() * 100)}%")
        
        video_id = response['id']
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        print(f"  ✅ Uploaded! Video ID: {video_id}")
        print(f"  🔗 URL: {video_url}")
        
        return video_url
        
    except Exception as e:
        print(f"  ❌ YouTube upload failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="Upload a zodiac sign video to YouTube")
    parser.add_argument('--sign', required=True, help='Zodiac sign')
    args = parser.parse_args()
    
    sign = args.sign
    
    print("="*60)
    print(f"📺 UPLOADING {sign.upper()} TO YOUTUBE")
    print("="*60)
    
    video_path = get_latest_video(sign)
    
    if not video_path:
        print(f"❌ No video found for {sign}")
        sys.exit(1)
    
    print(f"📁 Video: {video_path}")
    print(f"📊 Size: {os.path.getsize(video_path) / (1024*1024):.2f} MB")
    print("-"*60)
    
    youtube_url = upload_to_youtube(video_path, sign)
    
    if youtube_url:
        print("-"*60)
        print(f"✅ SUCCESS: Video uploaded to YouTube")
        print(f"🔗 {youtube_url}")
        print("="*60)
    else:
        print("-"*60)
        print(f"❌ FAILED: Upload unsuccessful")
        print("="*60)
        sys.exit(1)


if __name__ == "__main__":
    main()
