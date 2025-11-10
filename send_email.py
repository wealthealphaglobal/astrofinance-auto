#!/usr/bin/env python3
"""
Send email notifications for AstroFinance daily reports
Usage: python send_email.py --status success --generated Aries,Taurus --uploaded Aries,Taurus
"""

import os
import sys
import argparse
import smtplib
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(status, generated_signs, uploaded_signs, failed_signs, youtube_urls):
    """Send email notification"""
    
    # Get email config from environment
    email_from = os.getenv('EMAIL_FROM', '')
    email_password = os.getenv('EMAIL_PASSWORD', '')
    email_to = os.getenv('EMAIL_TO', '')
    smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
    smtp_port = int(os.getenv('SMTP_PORT', '587'))
    
    if not all([email_from, email_password, email_to]):
        print("⚠️ Email credentials not configured")
        return False
    
    try:
        # Parse inputs
        generated = generated_signs.split(',') if generated_signs else []
        uploaded = uploaded_signs.split(',') if uploaded_signs else []
        failed = failed_signs.split(',') if failed_signs else []
        urls = dict(item.split(':') for item in youtube_urls.split(',')) if youtube_urls else {}
        
        # Build email subject
        timestamp = datetime.now().strftime("%B %d, %Y")
        
        if status == 'success':
            subject = f"✅ AstroFinance Daily Report - {timestamp}"
            color = "#27ae60"  # Green
        else:
            subject = f"⚠️ AstroFinance Daily Report - {timestamp}"
            color = "#e74c3c"  # Red
        
        # Build email body
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
                        {chr(10).join(f'<div class="sign success">  ✅ {s}</div>' for s in sorted(generated)) if generated else ''}
                    </div>
                </div>
                
                <div class="section">
                    <div class="section-title">📤 UPLOAD</div>
                    <div class="sign-list">
                        <div class="sign">✅ Uploaded: {len(uploaded)}/12</div>
                        {chr(10).join(f'<div class="sign success">  ✅ <a href="{urls.get(s, "#")}" class="link">{s}</a></div>' for s in sorted(uploaded)) if uploaded else ''}
                    </div>
                </div>
        """
        
        if failed:
            html_body += f"""
                <div class="section">
                    <div class="section-title">❌ FAILED</div>
                    <div class="sign-list">
                        {chr(10).join(f'<div class="sign failed">  ❌ {s}</div>' for s in sorted(failed)) if failed else ''}
                    </div>
                </div>
            """
        
        html_body += f"""
                <div class="footer">
                    <p>Automated report from AstroFinance</p>
                    <p>Workflow: <a href="https://github.com/${{GITHUB_REPOSITORY}}/actions/runs/${{GITHUB_RUN_ID}}" class="link">View on GitHub</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Send email
        msg = MIMEMultipart()
        msg['From'] = email_from
        msg['To'] = email_to
        msg['Subject'] = subject
        msg.attach(MIMEText(html_body, 'html'))
        
        print(f"📧 Sending email to {email_to}...")
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(email_from, email_password)
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send AstroFinance email report")
    parser.add_argument('--status', required=True, choices=['success', 'failure'], help='Report status')
    parser.add_argument('--generated', default='', help='Comma-separated list of generated signs')
    parser.add_argument('--uploaded', default='', help='Comma-separated list of uploaded signs with URLs (sign:url,sign:url)')
    parser.add_argument('--failed', default='', help='Comma-separated list of failed signs')
    
    args = parser.parse_args()
    
    success = send_email(args.status, args.generated, args.uploaded, args.failed, args.uploaded)
    sys.exit(0 if success else 1)
