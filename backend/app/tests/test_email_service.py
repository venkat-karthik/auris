import pytest
from unittest.mock import patch, MagicMock
from app.services.email_service import send_verification_email
from app.core import config

@pytest.mark.anyio
@patch("app.services.email_service.logger")
async def test_send_verification_email_no_host(mock_logger):
    # Temporarily clear SMTP_HOST
    with patch.object(config, "SMTP_HOST", ""):
        res = await send_verification_email("user@example.com", "123456")
        assert res is False
        mock_logger.warning.assert_called_once()
        assert "SMTP_HOST is not configured" in mock_logger.warning.call_args[0][0]


@pytest.mark.anyio
@patch("smtplib.SMTP")
async def test_send_verification_email_smtp_success(mock_smtp):
    mock_server = MagicMock()
    mock_smtp.return_value = mock_server

    with patch.object(config, "SMTP_HOST", "smtp.example.com"), \
         patch.object(config, "SMTP_PORT", 587), \
         patch.object(config, "SMTP_USER", "user"), \
         patch.object(config, "SMTP_PASSWORD", "pass"):
        
        res = await send_verification_email("user@example.com", "123456")
        assert res is True
        mock_smtp.assert_called_once_with("smtp.example.com", 587, timeout=10)
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("user", "pass")
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()
