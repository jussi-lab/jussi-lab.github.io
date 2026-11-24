"""Check generated local links, landmarks and index metadata."""
import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

from build import AUTOMOTIVE_PROJECT, CASES, CASE_SECTIONS, CONCEPTS, CONCEPT_SECTIONS, CONTACT, DATA, DEVELOPMENT_PATHS, SECTIONS, SITE, case_path, concept_path

ROOT = Path(__file__).resolve().parents[1]


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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", action="store_true")
    args = parser.parse_args()
    output = ROOT / ("dist-review" if args.review else "dist")
    pages = {
        "/" + ("" if path.parent == output else path.parent.relative_to(output).as_posix() + "/"): Page(path)
        for path in output.rglob("index.html")
    }
    expected = {"/", "/profile/", "/cv/", "/leadership/", "/operating-model/", "/insights/reliability/"}
    expected.update(DEVELOPMENT_PATHS.values())
    expected.update(map(case_path, CASES))
    expected.update(map(concept_path, CONCEPTS))
    assert expected == pages.keys(), "Unexpected generated routes"
    current = [item for item in DATA["career"] if item.get("current")]
    assert len(current) == 1, "Exactly one role should be marked current"
    position = f'{escape(current[0]["role"])} at {escape(current[0]["employer"])}'
    for route in ("/", "/profile/", "/cv/"):
        text = (output / route.lstrip("/") / "index.html").read_text(encoding="utf-8")
        assert text.count('class="current-role"') == 1 and position in text, route
    moved = {"career", "qualifications"}
    assert set(SECTIONS) - moved <= pages["/"].ids, "Required home section missing"
    assert moved | {"competencies"} <= pages["/profile/"].ids, "Required profile section missing"
    for route, page in pages.items():
        assert page.language == "en" and page.h1 == page.main == 1, route
        assert set(page.labels) <= page.ids, route
        assert "#main" in page.urls and "main" in page.ids, route
        assert page.canonical == page.metadata["og:url"] == SITE + route, route
        assert (page.metadata.get("robots") == "noindex, nofollow") == args.review, route
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
                assert (output / target.lstrip("/")).is_file() and not parsed.fragment, url

    sitemap = ElementTree.parse(output / "sitemap.xml")
    assert {item.text for item in sitemap.findall(".//{*}loc")} == {SITE + route for route in pages}
    robots = (output / "robots.txt").read_text()
    assert ("Disallow: /" if args.review else f"Sitemap: {SITE}/sitemap.xml") in robots
    for item in CASES:
        html = (output / case_path(item).strip("/") / "index.html").read_text(encoding="utf-8")
        status_heading = "Current development status" if item["status"] == "ongoing" else "Results"
        for heading in (status_heading if key == "results" else label for key, label in CASE_SECTIONS.items()):
            assert f"<h2>{heading}</h2>" in html, (item["slug"], heading)
    automotive = DEVELOPMENT_PATHS["automotive"]
    for item in CONCEPTS:
        route = concept_path(item)
        assert route in pages[automotive].urls, route
        assert automotive + "#concept-studies" in pages[route].urls, route
        html = (output / route.strip("/") / "index.html").read_text(encoding="utf-8")
        for label in CONCEPT_SECTIONS.values():
            assert f"<h2>{label}</h2>" in html, (route, label)
    for link in AUTOMOTIVE_PROJECT["caseLinks"]:
        route = case_path(link)
        assert route in pages[automotive].urls, route
        assert automotive + "#professional-connections" in pages[route].urls, route
    print(f"Checked {len(pages)} pages, homepage and full professional profile, the current role, accessible labels, internal links, SEO metadata and sitemap.")


if __name__ == "__main__":
    main()
