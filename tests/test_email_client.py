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
