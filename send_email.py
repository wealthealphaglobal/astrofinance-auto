#!/usr/bin/env python3
"""
Send email notifications using Resend API
Usage: python send_email.py --status success --generated Aries,Taurus --uploaded Aries:url,Taurus:url --failed Gemini
"""

import os
import sys
import argparse
import requests
from datetime import datetime

# Get Resend API key from environment
RESEND_API_KEY = os.getenv('RESEND_API_KEY', '')
EMAIL_TO = os.getenv('EMAIL_TO', 'wealthealphaglobal@gmail.com')  # Can be multiple addresses now
EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreply@astrofinance.com')  # Your verified domain

def send_email_resend(status, generated_signs, uploaded_signs, failed_signs):
    """Send email notification using Resend API"""
    
    if not RESEND_API_KEY:
        print("❌ Missing RESEND_API_KEY in environment variables")
        print("   Set it in GitHub Secrets as RESEND_API_KEY")
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
                .footer a {{ color: #3498db; text-decoration: none; }}
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
        
        # Parse multiple recipients (comma-separated)
        recipients = [email.strip() for email in EMAIL_TO.split(',') if email.strip()]
        
        # Prepare Resend API request
        print(f"📧 Sending emails via Resend...")
        print(f"   Recipients: {', '.join(recipients)}")
        
        headers = {
            "Authorization": f"Bearer {RESEND_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Send to each recipient (Resend free tier limitation)
        all_success = True
        for recipient in recipients:
            payload = {
                "from": EMAIL_FROM,
                "to": recipient,
                "subject": subject,
                "html": html_body,
                "reply_to": EMAIL_FROM
            }
            
            try:
                response = requests.post(
                    "https://api.resend.com/emails",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.status_code in [200, 201]:
                    result = response.json()
                    email_id = result.get('id', 'unknown')
                    print(f"   ✅ Sent to {recipient} (ID: {email_id})")
                else:
                    print(f"   ❌ Failed to send to {recipient}: {response.status_code}")
                    print(f"      {response.text}")
                    all_success = False
            except Exception as e:
                print(f"   ❌ Error sending to {recipient}: {e}")
                all_success = False
        
        return all_success
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send AstroFinance email report via Resend")
    parser.add_argument('--status', required=True, choices=['success', 'failure'], help='Report status')
    parser.add_argument('--generated', default='', help='Comma-separated list of generated signs')
    parser.add_argument('--uploaded', default='', help='Comma-separated list of uploaded signs (sign:url,sign:url)')
    parser.add_argument('--failed', default='', help='Comma-separated list of failed signs')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📧 ASTROFINANCE EMAIL NOTIFICATION")
    print("="*60)
    print(f"Status: {args.status.upper()}")
    print(f"Generated: {args.generated or 'None'}")
    print(f"Uploaded: {args.uploaded or 'None'}")
    print(f"Failed: {args.failed or 'None'}")
    print("-"*60)
    
    success = send_email_resend(args.status, args.generated, args.uploaded, args.failed)
    
    print("="*60)
    sys.exit(0 if success else 1)
