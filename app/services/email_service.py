from pathlib import Path
from datetime import datetime
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
from jinja2 import Environment, FileSystemLoader

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

template_dir = Path(__file__).parent / 'templates'
jinja_env = Environment(loader=FileSystemLoader(str(template_dir)))


async def send_verification_email(
    email: EmailStr,
    username: str,
    verification_token: str
) -> bool:
    verification_url = f"{settings.backend_url}/auth/verify-email/{verification_token}"

    template = jinja_env.get_template('verification_email.html')
    html_content = template.render(
        username=username,
        verification_url=verification_url
    )

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


async def send_password_reset_email(
    email: EmailStr,
    username: str,
    reset_token: str
) -> bool:
    reset_url = f"{settings.backend_url}/auth/reset-password/{reset_token}"

    template = jinja_env.get_template('password_reset_email.html')
    html_content = template.render(
        username=username,
        reset_url=reset_url,
        timestamp=datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    )

    try:
        message = MessageSchema(
            subject="Password Reset Request - Contacts API",
            recipients=[email],
            body=html_content,
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message)
        print(f"✓ Password reset email sent to {email}")
        print(f"✓ Reset URL: {reset_url}")
        print(f"✓ Reset Token: {reset_token}")
        return True
    except ConnectionErrors as e:
        print(f"✗ Error sending password reset email to {email}: {e}")
        print(f"✓ Reset URL (use this for testing): {reset_url}")
        print(f"✓ Reset Token (use this for testing): {reset_token}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error sending password reset email: {e}")
        print(f"✓ Reset URL (use this for testing): {reset_url}")
        print(f"✓ Reset Token (use this for testing): {reset_token}")
        return False
