from typing import List
from pathlib import Path
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.mail_username,
    MAIL_PASSWORD=settings.mail_password,
    MAIL_FROM=settings.mail_from,
    MAIL_PORT=settings.mail_port,
    MAIL_SERVER=settings.mail_server,
    MAIL_FROM_NAME=settings.mail_from_name,
    MAIL_STARTTLS=settings.mail_starttls,
    MAIL_SSL_TLS=settings.mail_ssl_tls,
    USE_CREDENTIALS=settings.mail_use_credentials,
    VALIDATE_CERTS=settings.mail_validate_certs,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_verification_email(
    email: EmailStr,
    username: str,
    verification_token: str
) -> bool:
    verification_url = f"{settings.backend_url}/auth/verify-email/{verification_token}"

    html_content = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .container {{
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 5px 5px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 5px 5px;
                }}
                .button {{
                    display: inline-block;
                    padding: 12px 30px;
                    margin: 20px 0;
                    background-color: #4CAF50;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                    font-weight: bold;
                }}
                .footer {{
                    margin-top: 20px;
                    padding-top: 20px;
                    border-top: 1px solid #ddd;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Welcome to Contacts API!</h1>
                </div>
                <div class="content">
                    <h2>Hello {username}!</h2>
                    <p>Thank you for registering with Contacts API. To complete your registration and activate your account, please verify your email address.</p>
                    <p>Click the button below to verify your email:</p>
                    <center>
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </center>
                    <p>Or copy and paste this link into your browser:</p>
                    <p style="word-break: break-all; color: #666;">{verification_url}</p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account, you can safely ignore this email.</p>
                </div>
                <div class="footer">
                    <p>Best regards,<br>Contacts API Team</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
    </html>
    """

    try:
        message = MessageSchema(
            subject="Verify your email address - Contacts API",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"✓ Verification email sent to {email}")
        print(f"✓ Verification URL: {verification_url}")
        return True
    except ConnectionErrors as e:
        print(f"✗ Error sending email to {email}: {e}")
        print(f"✓ Verification URL (use this for testing): {verification_url}")
        # Don't fail registration if email fails
        return False
    except Exception as e:
        print(f"✗ Unexpected error sending email: {e}")
        print(f"✓ Verification URL (use this for testing): {verification_url}")
        return False

