import pytest
from unittest.mock import patch, MagicMock
from email_client import get_gmail_service

@patch("email_client.Credentials")
@patch("email_client.build")
def test_get_gmail_service_with_existing_token(mock_build, mock_credentials, tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "dummy"}')

    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials.from_authorized_user_file.return_value = mock_creds_instance

    service = get_gmail_service(token_path=str(token_file), creds_path="dummy.json")

    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds_instance)
    assert service == mock_build.return_value

@patch("email_client.Credentials")
@patch("email_client.build")
@patch("email_client.Request")
def test_get_gmail_service_refresh_token(mock_request, mock_build, mock_credentials, tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "expired"}')

    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = False
    mock_creds_instance.expired = True
    mock_creds_instance.refresh_token = "some_refresh_token"
    mock_creds_instance.to_json.return_value = '{"token": "refreshed"}'
    
    mock_credentials.from_authorized_user_file.return_value = mock_creds_instance

    service = get_gmail_service(token_path=str(token_file), creds_path="dummy.json")

    mock_creds_instance.refresh.assert_called_once_with(mock_request.return_value)
    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds_instance)
    assert service == mock_build.return_value
    assert token_file.read_text() == '{"token": "refreshed"}'

@patch("email_client.InstalledAppFlow")
@patch("email_client.build")
def test_get_gmail_service_missing_token(mock_build, mock_flow_class, tmp_path):
    token_file = tmp_path / "token.json"
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("{}")
    
    mock_flow_instance = MagicMock()
    mock_creds_instance = MagicMock()
    mock_creds_instance.to_json.return_value = '{"token": "new"}'
    mock_flow_instance.run_local_server.return_value = mock_creds_instance
    mock_flow_class.from_client_secrets_file.return_value = mock_flow_instance

    service = get_gmail_service(token_path=str(token_file), creds_path=str(creds_file))

    mock_flow_class.from_client_secrets_file.assert_called_once()
    mock_flow_instance.run_local_server.assert_called_once_with(port=0)
    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds_instance)
    assert service == mock_build.return_value
    assert token_file.read_text() == '{"token": "new"}'

@patch("email_client.Credentials")
@patch("email_client.InstalledAppFlow")
@patch("email_client.build")
def test_get_gmail_service_corrupted_token(mock_build, mock_flow_class, mock_credentials, tmp_path):
    token_file = tmp_path / "token.json"
    token_file.write_text("invalid json")
    
    creds_file = tmp_path / "credentials.json"
    creds_file.write_text("{}")

    mock_credentials.from_authorized_user_file.side_effect = ValueError("Invalid JSON")
    
    mock_flow_instance = MagicMock()
    mock_creds_instance = MagicMock()
    mock_creds_instance.to_json.return_value = '{"token": "new_from_corrupted"}'
    mock_flow_instance.run_local_server.return_value = mock_creds_instance
    mock_flow_class.from_client_secrets_file.return_value = mock_flow_instance

    service = get_gmail_service(token_path=str(token_file), creds_path=str(creds_file))

    mock_flow_class.from_client_secrets_file.assert_called_once()
    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds_instance)
    assert service == mock_build.return_value
    assert token_file.read_text() == '{"token": "new_from_corrupted"}'

def test_get_gmail_service_missing_credentials(tmp_path):
    token_file = tmp_path / "token.json"
    creds_file = tmp_path / "credentials.json"
    
    with pytest.raises(FileNotFoundError, match=f"Missing {creds_file}"):
        get_gmail_service(token_path=str(token_file), creds_path=str(creds_file))
import base64
from email_client import fetch_latest_astroph_email

def test_fetch_latest_astroph_email():
    mock_service = MagicMock()
    mock_messages = MagicMock()
    mock_service.users().messages().list.return_value = mock_messages
    mock_messages.execute.return_value = {'messages': [{'id': '123'}]}
    
    mock_message_get = MagicMock()
    mock_service.users().messages().get.return_value = mock_message_get
    
    # Mocking base64 encoded payload "Subject: astro-ph daily\n\nHello World"
    dummy_body = base64.urlsafe_b64encode(b"Hello World").decode('utf-8')
    mock_message_get.execute.return_value = {
        'payload': {
            'parts': [{'mimeType': 'text/plain', 'body': {'data': dummy_body}}]
        }
    }
    
    email_text = fetch_latest_astroph_email(mock_service, mark_read=False)
    
    mock_service.users().messages().list.assert_called_once()
    mock_service.users().messages().get.assert_called_once_with(userId='me', id='123', format='full')
    assert email_text == "Hello World"

def test_fetch_latest_astroph_email_no_messages():
    mock_service = MagicMock()
    mock_messages = MagicMock()
    mock_service.users().messages().list.return_value = mock_messages
    mock_messages.execute.return_value = {} # No messages
    
    email_text = fetch_latest_astroph_email(mock_service)
    assert email_text is None

from email_client import send_email

def test_send_email():
    mock_service = MagicMock()
    mock_messages = MagicMock()
    mock_service.users().messages().send.return_value = mock_messages
    mock_messages.execute.return_value = {'id': 'sent_id'}
    
    result = send_email(mock_service, "me@example.com", "Test Subject", "Test Body")
    
    mock_service.users().messages().send.assert_called_once()
    assert result == {'id': 'sent_id'}
