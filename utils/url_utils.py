from __future__ import annotations

from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse


SKIP_SCHEMES = ("javascript:", "mailto:", "tel:", "#")
TRACKING_PARAMS = {"from", "source", "spm", "session", "timestamp", "ref"}
BLOCKED_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".svg",
    ".webp",
    ".bmp",
    ".css",
    ".js",
    ".json",
    ".xml",
    ".zip",
    ".rar",
    ".7z",
    ".exe",
}


def make_absolute_url(base_url: str, link: str | None) -> str | None:
    if not link:
        return None
    link = link.strip()
    if not link or link.startswith(SKIP_SCHEMES):
        return None
    return normalize_url(urljoin(base_url, link))


def normalize_url(url: str) -> str:
    parsed = urlparse(url.strip())
    query_items = [
        (key, value)
        for key, value in parse_qsl(parsed.query, keep_blank_values=False)
        if key.lower() not in TRACKING_PARAMS and not key.lower().startswith("utm_")
    ]
    path = parsed.path or "/"
    return urlunparse(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            path,
            "",
            urlencode(query_items, doseq=True),
            "",
        )
    )


def get_domain(url: str) -> str:
    return urlparse(url).netloc.lower()


def is_same_domain(url: str, base_url: str) -> bool:
    domain = get_domain(url)
    base_domain = get_domain(base_url)
    return domain == base_domain or domain.endswith(f".{base_domain}") or base_domain.endswith(f".{domain}")


def has_blocked_extension(url: str) -> bool:
    path = urlparse(url).path.lower()
    return any(path.endswith(ext) for ext in BLOCKED_EXTENSIONS)
