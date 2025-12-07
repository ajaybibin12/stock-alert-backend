import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


def send_alert_email(to_email: str, symbol: str, price: float, target: float):
    EMAIL_HOST = os.getenv("EMAIL_HOST")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT"))
    EMAIL_USER = os.getenv("EMAIL_USER")
    EMAIL_PASS = os.getenv("EMAIL_PASS")

    subject = f"🚨 Stock Alert Triggered: {symbol}"

    # ✅ STYLISH HTML TEMPLATE
    html = f"""
    <html>
      <body style="background:#0f172a;font-family:Arial;padding:40px;">
        <div style="max-width:600px;margin:auto;background:#020617;border-radius:14px;padding:30px;border:1px solid #1e293b;">
          
          <h1 style="color:#34d399;text-align:center;">📈 Stock Alert Triggered</h1>

          <p style="color:#e5e7eb;font-size:16px;">
            Hi Trader,
          </p>

          <p style="color:#9ca3af;font-size:15px;">
            Your alert for the stock below has just been triggered:
          </p>

          <div style="background:#020617;padding:20px;border-radius:12px;border:1px solid #1f2937;margin:20px 0;">
            <h2 style="color:#60a5fa;margin:0;">{symbol}</h2>
            <p style="color:#d1d5db;margin:6px 0;">Target Price: <b style="color:#fbbf24">${target}</b></p>
            <p style="color:#d1d5db;margin:6px 0;">Current Price: <b style="color:#34d399">${price}</b></p>
          </div>

          <p style="color:#9ca3af;font-size:14px;">
            You are receiving this email because you created a stock alert in your dashboard.
          </p>

          <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:30px;">
            © 2025 Stock Alerts Platform
          </p>

        </div>
      </body>
    </html>
    """

    msg = MIMEMultipart()
    msg["From"] = EMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(html, "html"))

    server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    server.starttls()
    server.login(EMAIL_USER, EMAIL_PASS)
    server.sendmail(EMAIL_USER, to_email, msg.as_string())
    server.quit()
