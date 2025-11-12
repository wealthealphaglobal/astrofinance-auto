#!/usr/bin/env python3
"""
Send email notifications using system mail command
Works on GitHub Actions Ubuntu runners
"""

import os
import sys
import argparse
import subprocess
from datetime import datetime

# Get environment variables
RECIPIENTS = os.getenv('EMAIL_TO', 'wealthealphaglobal@gmail.com')
SENDER_NAME = "AstroFinance Bot"

def send_email_system(status, generated_signs, uploaded_signs, failed_signs):
    """Send email using system mail command"""
    
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
        
        # Parse recipients (comma-separated)
        recipients_list = [e.strip() for e in RECIPIENTS.split(',') if e.strip()]
        
        print(f"📧 Sending emails via system mail command...")
        print(f"   Recipients: {', '.join(recipients_list)}")
        
        # Create temporary email file
        email_file = '/tmp/astrofinance_email.txt'
        with open(email_file, 'w') as f:
            f.write(f"From: {SENDER_NAME} <root@localhost>\n")
            f.write(f"To: {', '.join(recipients_list)}\n")
            f.write(f"Subject: {subject}\n")
            f.write("Content-Type: text/html; charset=UTF-8\n")
            f.write(f"MIME-Version: 1.0\n\n")
            f.write(html_body)
        
        # Send email using sendmail
        for recipient in recipients_list:
            try:
                # Use sendmail to send email
                with open(email_file, 'r') as f:
                    result = subprocess.run(
                        ['sendmail', recipient],
                        stdin=f,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                
                if result.returncode == 0:
                    print(f"   ✅ Email sent to {recipient}")
                else:
                    print(f"   ⚠️ Sendmail returned code {result.returncode}")
                    if result.stderr:
                        print(f"      Error: {result.stderr}")
            except FileNotFoundError:
                print(f"   ⚠️ Sendmail not found, trying mail command...")
                try:
                    result = subprocess.run(
                        f'mail -s "{subject}" -a "Content-Type: text/html" {recipient}',
                        input=html_body,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    if result.returncode == 0:
                        print(f"   ✅ Email sent to {recipient} (via mail)")
                    else:
                        print(f"   ⚠️ Mail command failed for {recipient}")
                except Exception as e:
                    print(f"   ❌ Error sending to {recipient}: {e}")
            except Exception as e:
                print(f"   ❌ Error sending to {recipient}: {e}")
        
        # Cleanup
        try:
            os.remove(email_file)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send AstroFinance email report via system mail")
    parser.add_argument('--status', required=True, choices=['success', 'failure'], help='Report status')
    parser.add_argument('--generated', default='', help='Comma-separated list of generated signs')
    parser.add_argument('--uploaded', default='', help='Comma-separated list of uploaded signs (sign:url,sign:url)')
    parser.add_argument('--failed', default='', help='Comma-separated list of failed signs')
    
    args = parser.parse_args()
    
    print("="*60)
    print("📧 ASTROFINANCE EMAIL NOTIFICATION (System Mail)")
    print("="*60)
    print(f"Status: {args.status.upper()}")
    print(f"Generated: {args.generated or 'None'}")
    print(f"Uploaded: {args.uploaded or 'None'}")
    print(f"Failed: {args.failed or 'None'}")
    print("-"*60)
    
    success = send_email_system(args.status, args.generated, args.uploaded, args.failed)
    
    print("="*60)
    sys.exit(0 if success else 1)
