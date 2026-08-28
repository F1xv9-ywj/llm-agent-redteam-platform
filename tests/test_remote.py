import json
import os
import urllib.error
from unittest.mock import MagicMock, patch

import pytest

from redsentinel.cases import get_case
from redsentinel.redaction import redact
from redsentinel.targets import OpenAICompatibleTarget, PinnedHTTPConnection, PinnedHTTPSConnection, validate_remote_url

PUBLIC_DNS = [(2, 1, 6, "", ("93.184.216.34", 0))]


def test_redaction():
    assert "secret" not in redact("Authorization: Bearer secret").lower()
    assert "sk-abcdefgh" not in redact("error sk-abcdefgh")


def test_remote_url_safety():
    with pytest.raises(ValueError):
        validate_remote_url("file:///tmp/x", {"example.com"})
    with pytest.raises(ValueError):
        validate_remote_url("http://127.0.0.1:8000", {"127.0.0.1"})
    with pytest.raises(ValueError):
        validate_remote_url("https://evil.example", {"api.example.com"})
    with patch("socket.getaddrinfo", return_value=PUBLIC_DNS):
        assert validate_remote_url("https://api.example.com/v1", {"api.example.com"}).startswith("https://")


def test_domain_resolution_rejects_any_non_global_address():
    mixed_dns = PUBLIC_DNS + [(2, 1, 6, "", ("10.0.0.8", 0))]
    with patch("socket.getaddrinfo", return_value=mixed_dns), pytest.raises(ValueError, match="globally routable"):
        validate_remote_url("https://api.example.com/v1", {"api.example.com"})


def test_dns_resolution_failure_is_rejected():
    with patch("socket.getaddrinfo", side_effect=OSError("not found")), pytest.raises(ValueError, match="DNS resolution failed"):
        validate_remote_url("https://api.example.com/v1", {"api.example.com"})


def make_target(url="https://api.example.com:8443/v1"):
    with patch.dict(os.environ, {"REDSENTINEL_REMOTE_ALLOWLIST": "api.example.com"}), patch("socket.getaddrinfo", return_value=PUBLIC_DNS):
        return OpenAICompatibleTarget(url, "sk-abcdefgh", timeout=0.01)


def test_endpoint_pins_ip_and_preserves_path_port_and_host():
    private_dns = [(2, 1, 6, "", ("10.0.0.8", 0))]
    with (
        patch.dict(os.environ, {"REDSENTINEL_REMOTE_ALLOWLIST": "api.example.com"}),
        patch("socket.getaddrinfo", side_effect=[PUBLIC_DNS, private_dns]) as resolver,
    ):
        target = OpenAICompatibleTarget("https://api.example.com:8443/v1", "sk-abcdefgh", timeout=0.01)
    assert resolver.call_count == 1
    assert target.pinned_ip == "93.184.216.34"
    assert target.port == 8443
    assert target.request_path == "/v1/chat/completions"
    assert target.host_header == "api.example.com:8443"


def test_http_connection_uses_only_pinned_ip():
    connection = PinnedHTTPConnection("api.example.com", "93.184.216.34", 8080, 3)
    fake_socket = MagicMock()
    with patch("socket.create_connection", return_value=fake_socket) as create_connection:
        connection.connect()
    create_connection.assert_called_once_with(("93.184.216.34", 8080), 3)


def test_https_connection_pins_ip_but_uses_original_hostname_for_sni():
    context = MagicMock()
    raw_socket = MagicMock()
    connection = PinnedHTTPSConnection("api.example.com", "93.184.216.34", 443, 3, context=context)
    with patch("socket.create_connection", return_value=raw_socket) as create_connection:
        connection.connect()
    create_connection.assert_called_once_with(("93.184.216.34", 443), 3)
    context.wrap_socket.assert_called_once_with(raw_socket, server_hostname="api.example.com")


def test_invoke_has_no_second_dns_and_preserves_host_header():
    target = make_target()
    response = MagicMock(status=200)
    response.read.return_value = json.dumps({"choices": [{"message": {"content": "safe"}}]}).encode()
    connection = MagicMock()
    connection.getresponse.return_value = response
    with patch.object(target, "_make_connection", return_value=connection), patch("socket.getaddrinfo", side_effect=AssertionError("unexpected DNS lookup")):
        result = target.invoke(get_case("PI-DIRECT-001"))
    assert result.text == "safe"
    request = connection.request.call_args
    assert request.args[:2] == ("POST", "/v1/chat/completions")
    assert request.kwargs["headers"]["Host"] == "api.example.com:8443"
    connection.close.assert_called_once()


def test_redirect_response_fails_closed():
    target = make_target()
    connection = MagicMock()
    connection.getresponse.return_value = MagicMock(status=302)
    with patch.object(target, "_make_connection", return_value=connection):
        response = target.invoke(get_case("PI-DIRECT-001"))
    assert response.error == "remote redirects are disabled"


def test_timeout_error_is_normalized_and_redacted():
    target = make_target()
    connection = MagicMock()
    connection.request.side_effect = urllib.error.URLError("Authorization: Bearer secret")
    with patch.object(target, "_make_connection", return_value=connection):
        response = target.invoke(get_case("PI-DIRECT-001"))
    assert response.error and "secret" not in response.error
    assert response.text == ""
