import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")

def dispatch_email(status_summary, activity_html):
    msg = MIMEMultipart('related')
    msg['From'] = SENDER_EMAIL
    msg['To'] = RECEIVER_EMAIL
    msg['Subject'] = "📊 Portfolio Activity & Analytics Report"
    
    # FIX: Format the string here, outside the f-string
    formatted_status = status_summary.replace('\n', '<br>')
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; background-color: #f9f9f9; padding: 20px;">
        <div style="max-width: 800px; margin: 0 auto; background: #fff; padding: 20px; border-radius: 8px; border: 1px solid #ddd;">
          <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">Mutual Fund Strategy Pulse</h2>
          
          <div style="background: #ecf0f1; padding: 15px; border-left: 4px solid #7f8c8d; margin-bottom: 20px;">
            <strong>Status Check:</strong><br>
            {formatted_status}
          </div>
          
          {activity_html}
          
          <h3 style="color: #2c3e50;">1. Portfolio Structure Visuals</h3>
          <img src="cid:holdings_chart" alt="Holdings Chart" style="max-width: 100%; border: 1px solid #eee; margin-bottom: 20px;">
          
          <h3 style="color: #2c3e50;">2. Multi-Fund Cross Analytics</h3>
          <img src="cid:analytics_chart" alt="Analytics Chart" style="max-width: 100%; border: 1px solid #eee;">
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(html_content, 'html'))
    
    for chart_file, cid in [("holdings_chart.png", "holdings_chart"), ("analytics_chart.png", "analytics_chart")]:
        if os.path.exists(chart_file):
            with open(chart_file, 'rb') as img:
                mime_img = MIMEImage(img.read())
                mime_img.add_header('Content-ID', f'<{cid}>')
                mime_img.add_header('Content-Disposition', 'inline', filename=chart_file)
                msg.attach(mime_img)
                
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email deployed successfully.")
    except Exception as e:
        print(f"Failed to transmit email: {e}")