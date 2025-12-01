"""
Unit tests for EmailService.
"""
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from app.services.email_service import send_verification_email, send_password_reset_email


class TestEmailService:
    """Test cases for EmailService."""

    @patch('app.services.email_service.FastMail')
    def test_send_verification_email_success(self, mock_fastmail):
        """Test successfully sending verification email."""
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_verification_email(
            "user@example.com",
            "John Doe",
            "verification_token_123"
        ))

        assert result is True
        mock_fm_instance.send_message.assert_called_once()

    @patch('app.services.email_service.FastMail')
    def test_send_verification_email_connection_error(self, mock_fastmail):
        """Test sending verification email with connection error."""
        from fastapi_mail.errors import ConnectionErrors
        mock_fm_instance = AsyncMock()
        mock_fm_instance.send_message.side_effect = ConnectionErrors("Connection failed")
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_verification_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        assert result is False

    @patch('app.services.email_service.FastMail')
    def test_send_verification_email_unexpected_error(self, mock_fastmail):
        """Test sending verification email with unexpected error."""
        mock_fm_instance = AsyncMock()
        mock_fm_instance.send_message.side_effect = Exception("Unexpected error")
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_verification_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        assert result is False

    @patch('app.services.email_service.FastMail')
    def test_send_password_reset_email_success(self, mock_fastmail):
        """Test successfully sending password reset email."""
        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_password_reset_email(
            "user@example.com",
            "John Doe",
            "reset_token_123"
        ))

        assert result is True
        mock_fm_instance.send_message.assert_called_once()

    @patch('app.services.email_service.FastMail')
    def test_send_password_reset_email_connection_error(self, mock_fastmail):
        """Test sending password reset email with connection error."""
        from fastapi_mail.errors import ConnectionErrors
        mock_fm_instance = AsyncMock()
        mock_fm_instance.send_message.side_effect = ConnectionErrors("Connection failed")
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_password_reset_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        assert result is False

    @patch('app.services.email_service.FastMail')
    def test_send_password_reset_email_unexpected_error(self, mock_fastmail):
        """Test sending password reset email with unexpected error."""
        mock_fm_instance = AsyncMock()
        mock_fm_instance.send_message.side_effect = Exception("Unexpected error")
        mock_fastmail.return_value = mock_fm_instance

        result = asyncio.run(send_password_reset_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        assert result is False

    @patch('app.services.email_service.jinja_env')
    @patch('app.services.email_service.FastMail')
    def test_verification_email_uses_template(self, mock_fastmail, mock_jinja_env):
        """Test that verification email uses Jinja2 template."""
        mock_template = Mock()
        mock_template.render.return_value = "<html>Email content</html>"
        mock_jinja_env.get_template.return_value = mock_template

        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance

        asyncio.run(send_verification_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        mock_jinja_env.get_template.assert_called_once_with('verification_email.html')
        mock_template.render.assert_called_once()

    @patch('app.services.email_service.jinja_env')
    @patch('app.services.email_service.FastMail')
    def test_password_reset_email_uses_template(self, mock_fastmail, mock_jinja_env):
        """Test that password reset email uses Jinja2 template."""
        mock_template = Mock()
        mock_template.render.return_value = "<html>Reset content</html>"
        mock_jinja_env.get_template.return_value = mock_template

        mock_fm_instance = AsyncMock()
        mock_fastmail.return_value = mock_fm_instance

        asyncio.run(send_password_reset_email(
            "user@example.com",
            "John Doe",
            "token123"
        ))

        mock_jinja_env.get_template.assert_called_once_with('password_reset_email.html')
        mock_template.render.assert_called_once()

