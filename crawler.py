"""
crawler.py — small polite BFS crawler that writes webpages.txt in the
same format main.py expects:

    NEWPAGE <url>
    <word>
    <word>
    <http(s):// link>
    ...

Usage:
    python crawler.py https://www.[university name].edu
    python crawler.py https://www.[university name].edu --max-pages 100 --delay 1.0
    python crawler.py https://apple.com --output webpages.txt --domain apple.com

Only the standard library is used (urllib, html.parser), so no pip
install is required.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from collections import deque
from html.parser import HTMLParser
from typing import Optional, Set, Tuple

USER_AGENT = "cpsc-hw1-crawler/1.0 (educational use; contact: student)"
WORD_RE = re.compile(r"[A-Za-z]+")
SKIP_TAGS = {"script", "style", "noscript"}


class PageParser(HTMLParser):
    """Extracts plain-text words and absolute hyperlink targets from one page."""

    def __init__(self, base_url: str) -> None:
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.words: Set[str] = set()
        self.links: Set[str] = set()
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in SKIP_TAGS:
            self._skip_depth += 1
            return
        if tag == "a":
            href = dict(attrs).get("href")
            if not href:
                return
            absolute = urllib.parse.urljoin(self.base_url, href)
            parsed = urllib.parse.urlparse(absolute)
            if parsed.scheme in ("http", "https"):
                # Drop the fragment; keep query strings, matching how a
                # real crawler would treat distinct query URLs as distinct pages.
                cleaned = parsed._replace(fragment="").geturl()
                self.links.add(cleaned)

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1

    def handle_data(self, data: str) -> None:
        if self._skip_depth > 0:
            return
        for token in WORD_RE.findall(data.lower()):
            if len(token) > 1:  # drop single letters, matches typical stopword trimming
                self.words.add(token)


def registrable_domain(hostname: str) -> str:
    """Crude last-two-labels heuristic (good enough for .edu/.com/.org etc.)."""
    parts = hostname.split(".")
    return ".".join(parts[-2:]) if len(parts) >= 2 else hostname


def same_site(url: str, base_domain: str) -> bool:
    host = urllib.parse.urlparse(url).hostname or ""
    return host == base_domain or host.endswith("." + base_domain)


def fetch(url: str, timeout: float) -> Optional[Tuple[str, str]]:
    """Returns (final_url, html_text) or None on any failure / non-HTML response."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "text/html" not in content_type:
                return None
            charset = resp.headers.get_content_charset() or "utf-8"
            raw = resp.read()
            return resp.geturl(), raw.decode(charset, errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError):
        return None


def load_robots(seed_url: str, timeout: float) -> urllib.robotparser.RobotFileParser:
    parsed = urllib.parse.urlparse(seed_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            rp.parse(resp.read().decode("utf-8", errors="replace").splitlines())
    except Exception:
        rp.allow_all = True  # no robots.txt / unreachable -> assume allowed
    return rp


def crawl(seed_url: str, max_pages: int, delay: float, timeout: float, domain_override: Optional[str]) -> dict:
    seed_host = urllib.parse.urlparse(seed_url).hostname or ""
    base_domain = domain_override or registrable_domain(seed_host)

    robots = load_robots(seed_url, timeout)

    visited: Set[str] = set()
    queue = deque([seed_url])
    pages: dict = {}  # url -> {"words": set, "links": set}

    while queue and len(pages) < max_pages:
        url = queue.popleft()
        if url in visited:
            continue
        visited.add(url)

        if not robots.can_fetch(USER_AGENT, url):
            print(f"[skip: robots.txt disallows] {url}")
            continue

        print(f"[{len(pages) + 1}/{max_pages}] crawling {url}")
        result = fetch(url, timeout)
        if result is None:
            continue
        final_url, html_text = result

        parser = PageParser(final_url)
        try:
            parser.feed(html_text)
        except Exception as exc:
            print(f"  parse error, skipping: {exc}")
            continue

        pages[final_url] = {"words": parser.words, "links": parser.links}

        for link in parser.links:
            if link not in visited and same_site(link, base_domain):
                queue.append(link)

        time.sleep(delay)

    return pages


def write_webpages_file(pages: dict, output_path: str) -> None:
    with open(output_path, "w", encoding="utf-8") as f:
        for url, data in pages.items():
            f.write(f"NEWPAGE {url}\n")
            for word in sorted(data["words"]):
                f.write(word + "\n")
            for link in sorted(data["links"]):
                f.write(link + "\n")


def main() -> None:
    ap = argparse.ArgumentParser(description="Crawl a site into webpages.txt format for the hw1 search engine.")
    ap.add_argument("seed_url", help="Starting URL, e.g. https://www.[university name].edu")
    ap.add_argument("--max-pages", type=int, default=50, help="Max pages to crawl (default: 50)")
    ap.add_argument("--delay", type=float, default=0.5, help="Seconds to wait between requests (default: 0.5)")
    ap.add_argument("--timeout", type=float, default=10.0, help="Per-request timeout in seconds (default: 10)")
    ap.add_argument("--output", default="webpages.txt", help="Output file path (default: webpages.txt)")
    ap.add_argument("--domain", default=None, help="Restrict crawl to this registrable domain (default: inferred from seed URL)")
    args = ap.parse_args()

    pages = crawl(args.seed_url, args.max_pages, args.delay, args.timeout, args.domain)
    write_webpages_file(pages, args.output)
    print(f"\nWrote {len(pages)} pages to {args.output}")


if __name__ == "__main__":
    main()
