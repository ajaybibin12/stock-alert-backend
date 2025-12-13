from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from app.core.config import settings


def send_alert_email(
    to_email: str,
    symbol: str,
    price: float,
    target: float,
):
    """
    Send stock alert email using SendGrid API
    (Render-safe, production-ready)
    """

    subject = f"🚨 Stock Alert Triggered: {symbol}"

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
            <p style="color:#d1d5db;margin:6px 0;">
              Target Price: <b style="color:#fbbf24">${target}</b>
            </p>
            <p style="color:#d1d5db;margin:6px 0;">
              Current Price: <b style="color:#34d399">${price}</b>
            </p>
          </div>

          <p style="color:#9ca3af;font-size:14px;">
            You are receiving this email because you created a stock alert.
          </p>

          <p style="color:#6b7280;font-size:12px;text-align:center;margin-top:30px;">
            © 2025 Stock Alerts Platform
          </p>

        </div>
      </body>
    </html>
    """

    message = Mail(
        from_email=settings.EMAIL_FROM,
        to_emails=to_email,
        subject=subject,
        html_content=html,
    )

    try:
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        sg.send(message)
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ SendGrid email failed: {e}")
