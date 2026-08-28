from __future__ import annotations

import http.client
import ipaddress
import json
import os
import socket
import ssl
import time
from typing import Protocol
from urllib.parse import urlparse

from .models import TargetResponse, TestCase
from .redaction import redact


class Target(Protocol):
    def invoke(self, case: TestCase) -> TargetResponse: ...


class PinnedHTTPConnection(http.client.HTTPConnection):
    """HTTP connection whose TCP destination is an already validated IP."""

    def __init__(self, hostname: str, pinned_ip: str, port: int, timeout: float) -> None:
        super().__init__(hostname, port=port, timeout=timeout)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        self.sock = socket.create_connection((self.pinned_ip, self.port), self.timeout)


class PinnedHTTPSConnection(http.client.HTTPSConnection):
    """Pinned TCP destination with TLS identity bound to the original hostname."""

    def __init__(self, hostname: str, pinned_ip: str, port: int, timeout: float, context: ssl.SSLContext | None = None) -> None:
        self.tls_context = context or ssl.create_default_context()
        super().__init__(hostname, port=port, timeout=timeout, context=self.tls_context)
        self.pinned_ip = pinned_ip

    def connect(self) -> None:
        raw_socket = socket.create_connection((self.pinned_ip, self.port), self.timeout)
        self.sock = self.tls_context.wrap_socket(raw_socket, server_hostname=self.host)


class SafeMockTarget:
    """Deterministic simulator. It never executes tools or performs network I/O."""

    def __init__(self, mode: str = "secure") -> None:
        self.mode = mode

    def invoke(self, case: TestCase) -> TargetResponse:
        start = time.perf_counter()
        if self.mode == "vulnerable":
            if case.id == "AGENCY-001":
                response = TargetResponse("Synthetic action accepted.", False, ["transfer_funds_test"])
            elif case.id == "MISINFO-001":
                response = TargetResponse("Veloria was founded in 1842.", False)
            else:
                response = TargetResponse(f"Synthetic response: {case.markers[0] if case.markers else 'accepted'}", False)
        elif case.expected_policy == "block":
            response = TargetResponse("Request blocked by the authorization and data-safety policy.", True)
        else:
            response = TargetResponse("I cannot verify that fictional fact from available evidence.", False)
        response.latency_ms = round((time.perf_counter() - start) * 1000, 3)
        return response


def _resolved_addresses(host: str) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        return {ipaddress.ip_address(host)}
    except ValueError:
        try:
            records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise ValueError("remote host DNS resolution failed") from exc
        addresses = {ipaddress.ip_address(record[4][0]) for record in records}
        if not addresses:
            raise ValueError("remote host DNS resolution returned no addresses") from None
        return addresses


def _validate_and_resolve(url: str, allow_hosts: set[str]) -> tuple[str, str, set[ipaddress.IPv4Address | ipaddress.IPv6Address]]:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("remote target must be an http(s) URL without embedded credentials")
    host = parsed.hostname.lower()
    if host not in allow_hosts:
        raise ValueError("remote host is not in REDSENTINEL_REMOTE_ALLOWLIST")
    addresses = _resolved_addresses(host)
    if any(not address.is_global for address in addresses):
        raise ValueError("all resolved remote addresses must be globally routable")
    return url.rstrip("/"), host, addresses


def validate_remote_url(url: str, allow_hosts: set[str]) -> str:
    validated, _, _ = _validate_and_resolve(url, allow_hosts)
    return validated


def _validated_endpoint(url: str, allow_hosts: set[str]) -> tuple[str, str, int, str, str, str]:
    validated, hostname, addresses = _validate_and_resolve(url, allow_hosts)
    parsed = urlparse(validated)
    pinned_ip = str(sorted(addresses, key=lambda address: (address.version, int(address)))[0])
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    base_path = parsed.path.rstrip("/")
    request_path = f"{base_path}/chat/completions" or "/chat/completions"
    if parsed.query:
        request_path = f"{request_path}?{parsed.query}"
    default_port = 443 if parsed.scheme == "https" else 80
    host_header = hostname if port == default_port else f"{hostname}:{port}"
    return parsed.scheme, hostname, port, pinned_ip, request_path, host_header


class OpenAICompatibleTarget:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, model: str | None = None, timeout: float | None = None) -> None:
        allow_hosts = {h.strip().lower() for h in os.getenv("REDSENTINEL_REMOTE_ALLOWLIST", "").split(",") if h.strip()}
        self.base_url = base_url or os.environ["REDSENTINEL_REMOTE_URL"]
        self.api_key = api_key or os.getenv("REDSENTINEL_REMOTE_API_KEY", "")
        self.model = model or os.getenv("REDSENTINEL_REMOTE_MODEL", "test-model")
        self.timeout = timeout or float(os.getenv("REDSENTINEL_REMOTE_TIMEOUT", "10"))
        self.scheme, self.hostname, self.port, self.pinned_ip, self.request_path, self.host_header = _validated_endpoint(self.base_url, allow_hosts)

    def _make_connection(self) -> http.client.HTTPConnection:
        if self.scheme == "https":
            return PinnedHTTPSConnection(self.hostname, self.pinned_ip, self.port, self.timeout)
        return PinnedHTTPConnection(self.hostname, self.pinned_ip, self.port, self.timeout)

    def invoke(self, case: TestCase) -> TargetResponse:
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": case.payload}], "temperature": 0}).encode()
        start = time.perf_counter()
        connection = self._make_connection()
        try:
            connection.request(
                "POST",
                self.request_path,
                body=body,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                    "Host": self.host_header,
                },
            )
            response = connection.getresponse()
            if 300 <= response.status < 400:
                raise ValueError("remote redirects are disabled")
            if response.status < 200 or response.status >= 300:
                raise ValueError(f"remote target returned HTTP {response.status}")
            data = json.loads(response.read())
            text = str(data["choices"][0]["message"]["content"])
            return TargetResponse(text, False, latency_ms=round((time.perf_counter() - start) * 1000, 3))
        except (TimeoutError, OSError, http.client.HTTPException, ValueError, KeyError, json.JSONDecodeError) as exc:
            return TargetResponse("", False, latency_ms=round((time.perf_counter() - start) * 1000, 3), error=redact(str(exc)))
        finally:
            connection.close()
