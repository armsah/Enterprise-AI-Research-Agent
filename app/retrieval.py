import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.models import ResearchSource


MAX_BYTES = 1_000_000


def validate_public_url(url: str) -> str:
    parsed = urlparse(url)

    if parsed.scheme not in {"http", "https"}:
        raise ValueError("Only HTTP and HTTPS URLs are allowed.")

    if not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Invalid URL.")

    if parsed.port not in {None, 80, 443}:
        raise ValueError("Only standard web ports are allowed.")

    try:
        addresses = socket.getaddrinfo(
            parsed.hostname, parsed.port or 443,
            type=socket.SOCK_STREAM,
        )
    except socket.gaierror as exc:
        raise ValueError("Unable to resolve hostname.") from exc

    for address in addresses:
        ip = ipaddress.ip_address(address[4][0])
        if not ip.is_global:
            raise ValueError("Private or reserved network addresses are blocked.")

    return url


def fetch_public_source(url: str, timeout: float = 10.0) -> ResearchSource:
    validate_public_url(url)

    with httpx.Client(
        timeout=timeout,
        follow_redirects=False,
        trust_env=False,
    ) as client:
        with client.stream("GET", url) as response:
            response.raise_for_status()

            if response.status_code in {301, 302, 303, 307, 308}:
                raise ValueError("Redirects are not permitted.")

            content_type = response.headers.get("content-type", "").lower()
            if "text/html" not in content_type:
                raise ValueError("Only HTML pages are supported.")

            chunks = []
            total = 0

            for chunk in response.iter_bytes():
                total += len(chunk)
                if total > MAX_BYTES:
                    raise ValueError("Web page exceeds the size limit.")
                chunks.append(chunk)

    soup = BeautifulSoup(b"".join(chunks), "html.parser")

    for element in soup(["script", "style", "nav", "footer"]):
        element.decompose()

    title = soup.title.get_text(" ", strip=True) if soup.title else url
    text = soup.get_text(" ", strip=True)

    return ResearchSource(
        title=title[:300] or url,
        url=url,
        snippet=text[:3000],
    )
