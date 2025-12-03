from urllib.request import urlopen, Request
from urllib.parse import urlparse
from mimetypes import guess_type
from base64 import b64encode
import socket
import ipaddress

MAX_IMAGE_SIZE = 2 * 1024 * 1024  # 2 MB
REQUEST_TIMEOUT = 5  # seconds


def _is_private_address(hostname: str) -> bool:
    #prevent SSRF to internal services like 127.0.0.1 or 10.x.x.x.
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(hostname))
    except Exception:
        # If we can't resolve it reliably, treat as unsafe
        return True
    return ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved


def _is_safe_image_url(url: str) -> bool:

    #Basic safety checks
    #- Only http/https
    #- Hostname present
    #- Host does not resolve to private/loopback ranges

    parsed = urlparse(url)

    if parsed.scheme not in ("http", "https"):
        return False

    if not parsed.hostname:
        return False

    if _is_private_address(parsed.hostname):
        return False

    return True


def download(url: str):

    if not _is_safe_image_url(url):
        raise ValueError("Unsafe image URL.")

    # Set a simple User-Agent and enforce timeout
    req = Request(url, headers={"User-Agent": "EVFA-ProfileImageFetcher/1.0"})

    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        content_type = response.headers.get("Content-Type", "").split(";")[0].strip()

        if not content_type.startswith("image/"):
            raise ValueError("URL does not point to an image.")

        # Read with a size limit
        data = response.read(MAX_IMAGE_SIZE + 1)
        if len(data) > MAX_IMAGE_SIZE:
            raise ValueError("Image is too large.")

        return data, content_type


def get_base64_image_blob(url: str) -> str:

    data, content_type = download(url)
    mimetype = content_type or guess_type(url)[0] or "image/png"
    encoded = b64encode(data).decode("ascii")

    return f"data:{mimetype};base64,{encoded}"
