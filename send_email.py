#!/usr/bin/env python3
"""
Send email notifications using Gmail API
Uses same Google OAuth credentials as YouTube API
"""

import os
import sys
import argparse
import base64
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Get Google credentials from environment (same as YouTube)
YOUTUBE_CLIENT_ID = os.getenv('YOUTUBE_CLIENT_ID', '')
YOUTUBE_CLIENT_SECRET = os.getenv('YOUTUBE_CLIENT_SECRET', '')
YOUTUBE_REFRESH_TOKEN = os.getenv('YOUTUBE_REFRESH_TOKEN', '')

# Email recipients
PRIMARY_EMAIL = os.getenv('EMAIL_TO', 'wealthealphaglobal@gmail.com')
SECONDARY_EMAILS = os.getenv('SECONDARY_EMAILS', '')  # Comma-separated, optional

def send_email_gmail_api(to_address, subject, html_body):
    """Send email using Gmail API"""
    
    if not all([YOUTUBE_CLIENT_ID, YOUTUBE_CLIENT_SECRET, YOUTUBE_REFRESH_TOKEN]):
        print(f"   ❌ Missing Google OAuth credentials")
        return False
    
    try:
        # Create credentials using same YouTube tokens
        credentials = Credentials(
            token=None,
            refresh_token=YOUTUBE_REFRESH_TOKEN,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET,
            scopes=['https://www.googleapis.com/auth/gmail.send']
        )
        
        # Refresh token to get valid access token
        credentials.refresh(Request())
        
        # Build Gmail API client
        gmail = build('gmail', 'v1', credentials=credentials)
        
        # Create email message
        msg = MIMEMultipart('alternative')
        msg['To'] = to_address
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        # Encode message
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        
        # Send via Gmail API
        send_message = {
            'raw': raw_message
        }
        
        result = gmail.users().messages().send(userId='me', body=send_message).execute()
        
        print(f"   ✅ Sent to {to_address} (Message ID: {result['id']})")
        return True
        
    except Exception as e:
        print(f"   ❌ Gmail API error for {to_address}: {e}")
        import traceback
        traceback.print_exc()
        return False


def send_email_gmail(status, generated_signs, uploaded_signs, failed_signs):
    """Send email to multiple recipients using Gmail API"""
    
    try:
        # Parse inputs
        generated = [s.strip() for s in generated_signs.split(',') if s.strip()]
        uploaded_with_urls = {}
        
        for item in uploaded_signs.split(','):
            if item.strip() and ':' in item:
                sign, url = item.split(':', 1)
                uploaded_with_urls[sign.strip()] = url.strip()
        
        failed = [s.strip() for s in failed_signs.split(',') if s.strip()]
        
        # Build subject
        timestamp = datetime.now().strftime("%B %d, %Y")
        if status == 'success':
            subject = f"✅ AstroFinance Daily Report - {timestamp}"
            color = "#27ae60"
            emoji = "✅"
        else:
            subject = f"⚠️ AstroFinance Daily Report - {timestamp}"
            color = "#e74c3c"
            emoji = "⚠️"
        
        # Build HTML email
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; margin: 0; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; border-left: 5px solid {color}; box-shadow: 0 4px 6px rgba(0,0,0,0.1); max-width: 600px; margin: 0 auto; }}
                .header {{ color: {color}; font-size: 28px; font-weight: bold; margin-bottom: 10px; }}
                .subheader {{ color: #666; font-size: 14px; margin-bottom: 20px; border-bottom: 2px solid #f0f0f0; padding-bottom: 15px; }}
                .section {{ margin: 25px 0; }}
                .section-title {{ background: linear-gradient(135deg, {color}20 0%, {color}10 100%); padding: 12px 15px; font-weight: bold; border-left: 4px solid {color}; font-size: 16px; margin-bottom: 15px; }}
                .sign-list {{ margin-left: 20px; }}
                .sign {{ padding: 8px 0; font-size: 15px; display: flex; align-items: center; }}
                .sign-icon {{ margin-right: 10px; font-size: 18px; }}
                .success {{ color: #27ae60; }}
                .failed {{ color: #e74c3c; }}
                .skipped {{ color: #f39c12; }}
                .link {{ color: #3498db; text-decoration: none; font-weight: 500; }}
                .link:hover {{ text-decoration: underline; }}
                .stats {{ display: flex; justify-content: space-around; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }}
                .stat-box {{ text-align: center; }}
                .stat-number {{ font-size: 24px; font-weight: bold; color: {color}; }}
                .stat-label {{ font-size: 12px; color: #666; margin-top: 5px; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 30px; border-top: 2px solid #f0f0f0; padding-top: 15px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">{emoji} {status.upper()}</div>
                <div class="subheader">AstroFinance Daily Report • {datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</div>
                
                <div class="stats">
                    <div class="stat-box">
                        <div class="stat-number">{len(generated)}</div>
                        <div class="stat-label">Generated</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(uploaded_with_urls)}</div>
                        <div class="stat-label">Uploaded</div>
                    </div>
                    <div class="stat-box">
                        <div class="stat-number">{len(failed)}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">🎬 GENERATION REPORT</div>
                    <div class="sign-list">
        """
        
        if generated:
            for s in sorted(generated):
                html_body += f'<div class="sign"><span class="sign-icon success">✅</span><span class="success">{s}</span></div>'
        else:
            html_body += '<div class="sign"><span class="sign-icon skipped">⏭️</span><span class="skipped">No videos generated</span></div>'
        
        html_body += """
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📤 YOUTUBE UPLOAD REPORT</div>
                    <div class="sign-list">
        """
        
        if uploaded_with_urls:
            for s in sorted(uploaded_with_urls.keys()):
                url = uploaded_with_urls[s]
                html_body += f'<div class="sign"><span class="sign-icon success">✅</span><span class="success"><a href="{url}" class="link">{s}</a></span></div>'
        else:
            html_body += '<div class="sign"><span class="sign-icon skipped">⏭️</span><span class="skipped">No videos uploaded</span></div>'
        
        html_body += """
                    </div>
                </div>
        """
        
        if failed:
            html_body += f"""
                <div class="section">
                    <div class="section-title">❌ FAILED ITEMS</div>
                    <div class="sign-list">
            """
            for s in sorted(failed):
                html_body += f'<div class="sign"><span class="sign-icon failed">❌</span><span class="failed">{s}</span></div>'
            
            html_body += """
                    </div>
                </div>
            """
        
        html_body += """
                <div class="footer">
                    <p>🌟 <strong>AstroFinance Daily</strong> - Automated Report</p>
                    <p style="margin-top: 10px; font-size: 11px;">This is an automated message. Please do not reply to this email.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        print(f"📧 Sending emails via Gmail API...")
        
        # Send to primary email
        print(f"   PRIMARY: {PRIMARY_EMAIL}")
        send_email_gmail_api(PRIMARY_EMAIL, subject, html_body)
        
        # Send to secondary emails if provided
        if SECONDARY_EMAILS:
            secondary_list = [e.strip() for e in SECONDARY_EMAILS.split(',') if e.strip()]
            for email in secondary_list:
                print(f"   SECONDARY: {email}")
                send_email_gmail_api(email, subject, html_body)
        
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send AstroFinance email report via Gmail API")
    parser.add_argument('--status', required=True, choices=['success', 'failure'], help='Report status')
    parser.add_argument('--generated', default='', help='Comma-separated list of generated signs')
    parser.add_argument('--uploaded', default='', help='Comma-separated list of uploaded signs (sign:url,sign:url)')
    parser.add_argument('--failed', default='', help='Comma-separated list of failed signs')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📧 ASTROFINANCE EMAIL NOTIFICATION (Gmail API)")
    print("="*60)
    print(f"Status: {args.status.upper()}")
    print(f"Generated: {args.generated or 'None'}")
    print(f"Uploaded: {args.uploaded or 'None'}")
    print(f"Failed: {args.failed or 'None'}")
    print("-"*60)
    
    success = send_email_gmail(args.status, args.generated, args.uploaded, args.failed)
    
    print("="*60)
    sys.exit(0 if success else 1)
