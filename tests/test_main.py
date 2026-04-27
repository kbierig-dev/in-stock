import json
import urllib.error
import pytest

import main


@pytest.fixture
def env_setup(monkeypatch):
    """Fixture to set up necessary environment variables."""
    monkeypatch.setenv("URL", "https://example.com/add")
    monkeypatch.setenv("APP_ID", "123")
    monkeypatch.setenv("SUB_ID", "456")
    monkeypatch.setenv("PHONE_NUMBER", "+1234567890")


def test_success_with_sns(env_setup, mocker):
    """Test successful add to cart where the SNS message is successfully sent."""
    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_response = mocker.MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"success": True, "itemcount": 1}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    mock_boto3 = mocker.patch("main.boto3")
    mock_sns = mocker.MagicMock()
    mock_boto3.client.return_value = mock_sns

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 200
    assert "SUCCESS" in response["body"]
    assert "1" in response["body"]

    mock_sns.publish.assert_called_once_with(
        PhoneNumber="+1234567890",
        Message="SUCCESS! The item was added. Current cart item count: 1"
    )


def test_success_without_phone(monkeypatch, mocker):
    """Test successful add to cart when no phone number is provided (SNS skipped)."""
    monkeypatch.setenv("URL", "https://example.com/add")
    monkeypatch.setenv("APP_ID", "123")
    monkeypatch.setenv("SUB_ID", "456")
    monkeypatch.delenv("PHONE_NUMBER", raising=False)

    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_response = mocker.MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"success": True, "itemcount": 2}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    mock_boto3 = mocker.patch("main.boto3")
    mock_sns = mocker.MagicMock()
    mock_boto3.client.return_value = mock_sns

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 200
    mock_sns.publish.assert_not_called()


def test_sns_publish_error(env_setup, mocker):
    """Test successful add to cart, but SNS raises an exception."""
    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_response = mocker.MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"success": True, "itemcount": 1}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    mock_boto3 = mocker.patch("main.boto3")
    mock_sns = mocker.MagicMock()
    mock_sns.publish.side_effect = Exception("AWS SNS Failure")
    mock_boto3.client.return_value = mock_sns

    # Suppress the print output from the except block in the test output
    mocker.patch("builtins.print")

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 200
    assert "1" in response["body"]


def test_failure_response(env_setup, mocker):
    """Test when the site responds successfully but indicates the item was not added."""
    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_response = mocker.MagicMock()
    mock_response.getcode.return_value = 200
    mock_response.read.return_value = json.dumps({"success": False}).encode("utf-8")
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 400
    assert "FAILED to add item" in response["body"]


def test_invalid_json(env_setup, mocker):
    """Test handling of invalid JSON response from the site."""
    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_response = mocker.MagicMock()
    mock_response.getcode.return_value = 502
    mock_response.read.return_value = b"<html>Not JSON</html>"
    mock_urlopen.return_value.__enter__.return_value = mock_response

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 502
    assert "Response wasn't JSON" in response["body"]


def test_url_error(env_setup, mocker):
    """Test handling of a base URL/network error."""
    mock_urlopen = mocker.patch("main.urllib.request.urlopen")
    mock_urlopen.side_effect = urllib.error.URLError("Network unreachable")

    response = main.lambda_handler({}, {})

    assert response["statusCode"] == 500
    assert "An error occurred" in response["body"]
