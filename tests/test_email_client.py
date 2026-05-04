import pytest
from unittest.mock import patch, MagicMock
from email_client import get_gmail_service


@patch("email_client.Credentials")
@patch("email_client.build")
def test_get_gmail_service_with_existing_token(mock_build, mock_credentials, tmp_path):
    # Setup a mock token file
    token_file = tmp_path / "token.json"
    token_file.write_text('{"token": "dummy"}')

    mock_creds_instance = MagicMock()
    mock_creds_instance.valid = True
    mock_credentials.from_authorized_user_file.return_value = mock_creds_instance

    service = get_gmail_service(token_path=str(token_file), creds_path="dummy.json")

    mock_build.assert_called_once_with("gmail", "v1", credentials=mock_creds_instance)
    assert service == mock_build.return_value
