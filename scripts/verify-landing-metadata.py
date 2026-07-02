#!/usr/bin/env python3
"""Verify static social/search metadata for the local landing page."""

from __future__ import annotations

import json
from html.parser import HTMLParser
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "site" / "index.html"


class MetadataParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.meta = {}
        self.links = []
        self.ld_json = []
        self._in_ld_json = False
        self._buffer = []

    def handle_starttag(self, tag, attrs):
        data = dict(attrs)
        if tag == "meta":
            key = data.get("property") or data.get("name")
            if key:
                self.meta[key] = data.get("content")
        if tag == "link":
            self.links.append(data)
        if tag == "script" and data.get("type") == "application/ld+json":
            self._in_ld_json = True
            self._buffer = []

    def handle_data(self, data):
        if self._in_ld_json:
            self._buffer.append(data)

    def handle_endtag(self, tag):
        if tag == "script" and self._in_ld_json:
            self.ld_json.append(json.loads("".join(self._buffer)))
            self._in_ld_json = False


def main() -> int:
    text = HTML.read_text(encoding="utf-8")
    parser = MetadataParser()
    parser.feed(text)

    required_meta = {
        "description",
        "keywords",
        "theme-color",
        "og:type",
        "og:site_name",
        "og:title",
        "og:description",
        "og:image",
        "og:image:alt",
        "twitter:card",
        "twitter:title",
        "twitter:description",
        "twitter:image",
        "twitter:image:alt",
    }
    missing = sorted(required_meta - set(parser.meta))
    if missing:
        raise AssertionError(f"missing metadata: {missing}")

    assert parser.meta["og:image"] == "assets/keysurgeon-social.png"
    assert parser.meta["twitter:image"] == "assets/keysurgeon-social.png"
    assert parser.meta["twitter:card"] == "summary_large_image"
    icons = [link for link in parser.links if link.get("rel") == "icon"]
    assert icons == [{"rel": "icon", "href": "assets/keysurgeon-mark.svg", "type": "image/svg+xml"}], icons
    keyword_meta = parser.meta["keywords"].lower()
    for keyword in ("keyboard chatter", "keyboard tester", "double typing", "dead keys", "rich", "textual"):
        assert keyword in keyword_meta, keyword

    if len(parser.ld_json) != 1:
        raise AssertionError(f"expected one JSON-LD block, found {len(parser.ld_json)}")
    app = parser.ld_json[0]
    assert app["@type"] == "SoftwareApplication"
    assert app["name"] == "KeySurgeon"
    assert app["applicationSubCategory"] == "Keyboard diagnostics"
    assert app["operatingSystem"] == "Windows"
    assert app["softwareVersion"] == "0.2.0"
    keyword_json = app["keywords"].lower()
    for keyword in ("keyboard chatter", "keyboard tester", "double typing", "dead keys", "rich", "textual"):
        assert keyword in keyword_json, keyword
    assert app["image"] == "assets/keysurgeon-social.png"
    assert app["screenshot"] == [
        "assets/keysurgeon-landing-desktop.png",
        "assets/keysurgeon-demo.png",
        "assets/keysurgeon-app.png",
    ]
    assert app["programmingLanguage"] == "Python"
    assert app["runtimePlatform"] == "Windows"
    assert app["codeRepository"] == "https://github.com/nosafune/keysurgeon"
    assert app["issueTracker"] == "https://github.com/nosafune/keysurgeon/issues"
    assert app["downloadUrl"] == "https://github.com/nosafune/keysurgeon"
    assert app["isAccessibleForFree"] is True
    assert app["offers"]["price"] == "0"

    if 'rel="canonical"' in text.lower():
        raise AssertionError("canonical URL must not be set before Pages exists")

    print("LANDING_METADATA_OK", len(required_meta), len(parser.ld_json))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
