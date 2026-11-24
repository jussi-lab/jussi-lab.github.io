"""Check generated local links, landmarks and index metadata."""
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

from build import CONTACT, DATA, SECTIONS, SITE, approved_cases, case_path

DIST = Path(__file__).resolve().parents[1] / "dist"


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.urls = []
        self.canonical = None
        self.metadata = {}
        self.h1 = 0
        self.main = 0
        self.language = None
        self.labels = []
        self.feed(path.read_text(encoding="utf-8"))

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "main":
            self.main += 1
        if tag == "h1":
            self.h1 += 1
        if "id" in attrs:
            assert attrs["id"] not in self.ids, f"Duplicate ID: {attrs['id']}"
            self.ids.add(attrs["id"])
        if "aria-labelledby" in attrs:
            self.labels.extend(attrs["aria-labelledby"].split())
        if "href" in attrs:
            self.urls.append(attrs["href"])
        if "src" in attrs:
            self.urls.append(attrs["src"])
        if attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "meta" and "content" in attrs:
            self.metadata[attrs.get("name") or attrs.get("property")] = attrs["content"]


def main():
    pages = {
        "/" + ("" if path.parent == DIST else path.parent.relative_to(DIST).as_posix() + "/"): Page(path)
        for path in DIST.rglob("index.html")
    }
    expected = {"/", "/cv/", "/leadership/"} | {case_path(item) for item in approved_cases()}
    assert expected == pages.keys(), "Unexpected generated routes"
    current = [item for item in DATA["career"] if item.get("current")]
    assert len(current) == 1, "Exactly one role should be marked current"
    position = f'{escape(current[0]["role"])} at {escape(current[0]["employer"])}'
    for route in ("/", "/cv/"):
        text = (DIST / route.lstrip("/") / "index.html").read_text(encoding="utf-8")
        assert text.count('class="current-role"') == 1 and position in text, route
    assert set(SECTIONS) <= pages["/"].ids, "Required section missing"
    for route, page in pages.items():
        assert page.language == "en" and page.h1 == page.main == 1, route
        assert set(page.labels) <= page.ids, route
        assert "#main" in page.urls and "main" in page.ids, route
        assert page.canonical == page.metadata["og:url"] == SITE + route, route
        for key in ("viewport", "description", "og:type", "og:title", "og:description", "og:image:alt"):
            assert page.metadata[key], key
        for url in page.urls + [page.metadata["og:image"]]:
            parsed = urlsplit(url)
            if parsed.netloc and parsed.netloc != urlsplit(SITE).netloc:
                assert url == CONTACT, f"Unexpected external link: {url}"
                continue
            target = parsed.path or route
            if target in pages:
                assert not parsed.fragment or parsed.fragment in pages[target].ids, url
            else:
                assert (DIST / target.lstrip("/")).is_file() and not parsed.fragment, url

    sitemap = ElementTree.parse(DIST / "sitemap.xml")
    assert {item.text for item in sitemap.findall(".//{*}loc")} == {SITE + route for route in pages}
    assert f"Sitemap: {SITE}/sitemap.xml" in (DIST / "robots.txt").read_text()
    print(f"Checked {len(pages)} pages, ten home sections, the current role, accessible labels, internal links, SEO metadata and sitemap.")


if __name__ == "__main__":
    main()
