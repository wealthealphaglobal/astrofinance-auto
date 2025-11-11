#!/usr/bin/env python3
"""
Send email notifications using Resend API
Usage: python send_email.py --status success --generated Aries,Taurus --uploaded Aries,Taurus
"""

import os
import sys
import argparse
import requests
from datetime import datetime

def send_email(status, generated_signs, uploaded_signs, failed_signs):
    """Send email using Resend API"""
    
    # Get Resend API key from environment
    resend_api_key = os.getenv('RESEND_API_KEY', '')
    
    # Hardcoded emails - use delivered@resend.dev for testing
    email_from = "delivered@resend.dev"
    email_to = "tumu.mtm@gmail.com"
    
    if not resend_api_key:
        print("⚠️ Missing RESEND_API_KEY in GitHub Secrets")
        return False
    
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
        else:
            subject = f"⚠️ AstroFinance Daily Report - {timestamp}"
            color = "#e74c3c"
        
        # Build HTML email
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; }}
                .container {{ background-color: white; padding: 20px; border-radius: 10px; border-left: 5px solid {color}; }}
                .header {{ color: {color}; font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .date {{ color: #666; font-size: 12px; margin-bottom: 20px; }}
                .section {{ margin: 20px 0; }}
                .section-title {{ background-color: #f9f9f9; padding: 10px; font-weight: bold; border-left: 3px solid {color}; }}
                .sign-list {{ margin-left: 20px; margin-top: 10px; }}
                .sign {{ padding: 5px 0; }}
                .success {{ color: #27ae60; }}
                .failed {{ color: #e74c3c; }}
                .link {{ color: #3498db; text-decoration: none; }}
                .footer {{ color: #999; font-size: 12px; margin-top: 30px; border-top: 1px solid #ddd; padding-top: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">{'✅ SUCCESS' if status == 'success' else '⚠️ FAILURE'}</div>
                <div class="date">AstroFinance Daily Report</div>
                <div class="date">{datetime.now().strftime('%B %d, %Y at %I:%M %p UTC')}</div>
                
                <div class="section">
                    <div class="section-title">🎬 GENERATION</div>
                    <div class="sign-list">
                        <div class="sign">✅ Generated: {len(generated)}/12</div>
                        {chr(10).join(f'<div class="sign success">  ✅ {s}</div>' for s in sorted(generated)) if generated else '<div class="sign">  None</div>'}
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📤 UPLOAD TO YOUTUBE</div>
                    <div class="sign-list">
                        <div class="sign">✅ Uploaded: {len(uploaded_with_urls)}/12</div>
                        {chr(10).join(f'<div class="sign success">  ✅ <a href="{uploaded_with_urls.get(s, "#")}" class="link">{s}</a></div>' for s in sorted(uploaded_with_urls.keys())) if uploaded_with_urls else '<div class="sign">  None</div>'}
                    </div>
                </div>
        """
        
        if failed:
            html_body += f"""
                <div class="section">
                    <div class="section-title">❌ FAILED</div>
                    <div class="sign-list">
                        {chr(10).join(f'<div class="sign failed">  ❌ {s}</div>' for s in sorted(failed))}
                    </div>
                </div>
            """
        
        html_body += f"""
                <div class="footer">
                    <p>Automated daily report from AstroFinance</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send via Resend API
        url = "https://api.resend.com/emails"
        headers = {
            "Authorization": f"Bearer {resend_api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "from": email_from,
            "to": email_to,
            "subject": subject,
            "html": html_body
        }
        
        print(f"📧 Sending email to {email_to}...")
        print(f"   From: {email_from}")
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code in [200, 201]:
            print(f"✅ Email sent successfully!")
            return True
        else:
            print(f"❌ Email failed: {response.status_code}")
            print(f"   {response.text}")
            return False
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send AstroFinance email report")
    parser.add_argument('--status', required=True, choices=['success', 'failure'], help='Report status')
    parser.add_argument('--generated', default='', help='Comma-separated list of generated signs')
    parser.add_argument('--uploaded', default='', help='Comma-separated list of uploaded signs (sign:url,sign:url)')
    parser.add_argument('--failed', default='', help='Comma-separated list of failed signs')
    
    args = parser.parse_args()
    
    success = send_email(args.status, args.generated, args.uploaded, args.failed)
    sys.exit(0 if success else 1)
