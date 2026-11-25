"""Check generated local links, landmarks and index metadata."""
import argparse
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree

from build import AUTOMOTIVE_PROJECT, CASES, CASE_SECTIONS, CONCEPTS, CONCEPT_SECTIONS, CONTACT, DATA, DEVELOPMENT_PATHS, SECTIONS, SITE, case_metrics, case_path, concept_path

from localization import localize, route_for, translate

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.urls = []
        self.canonical = None
        self.alternates = {}
        self.language_links = {}
        self.title = None
        self.in_title = False
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
        if tag == "title":
            self.in_title = True
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
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs["hreflang"]] = attrs["href"]
        if tag == "a" and "hreflang" in attrs:
            language = attrs["hreflang"]
            assert language not in self.language_links
            assert attrs.get("lang") == language and attrs.get("aria-label")
            self.language_links[language] = (attrs["href"], attrs.get("aria-current"))
        if attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "meta" and "content" in attrs:
            self.metadata[attrs.get("name") or attrs.get("property")] = attrs["content"]

    def handle_data(self, data):
        if self.in_title:
            self.title = data

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False


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
    localized_routes = {route_for(path, language): (path, language) for path in expected for language in ("en", "fi")}
    assert localized_routes.keys() == pages.keys(), "Unexpected generated routes"
    for language, data in (("en", DATA), ("fi", localize(DATA))):
        current = [item for item in data["career"] if item.get("current")]
        assert len(current) == 1, "Exactly one role should be marked current"
        separator = " – " if language == "fi" else " at "
        position = escape(current[0]["role"] + separator + current[0]["employer"])
        for route in ("/", "/profile/", "/cv/"):
            text = (output / route_for(route, language).lstrip("/") / "index.html").read_text(encoding="utf-8")
            assert text.count('class="current-role"') == 1 and position in text, route
        moved = {"career", "qualifications"}
        assert set(SECTIONS) - moved <= pages[route_for("/", language)].ids
        assert moved | {"competencies"} <= pages[route_for("/profile/", language)].ids
    for path in expected:
        en, fi = pages[path], pages[route_for(path, "fi")]
        assert en.title and fi.title and en.title != fi.title, path
        assert en.metadata["description"] != fi.metadata["description"], path
        assert en.ids == fi.ids, path
    for route, page in pages.items():
        html = (output / route.strip("/") / "index.html").read_text(encoding="utf-8").casefold()
        for label in ("owner-reported", "owner-supplied", "omistajan ilmoittama"):
            assert label not in html, (route, label)
        path, language = localized_routes[route]
        assert page.alternates == {code: SITE + route_for(path, code) for code in ("fi", "en", "x-default")}, route
        assert page.language_links == {
            code: (route_for(path, code), "page" if code == language else None) for code in ("fi", "en")
        }, route
        assert page.language == language and page.h1 == page.main == 1, route
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
            if target in pages and parsed.path and url not in {link[0] for link in page.language_links.values()} and not parsed.netloc:
                assert localized_routes[target][1] == language, (route, url)
            if target in pages:
                assert not parsed.fragment or parsed.fragment in pages[target].ids, url
            else:
                assert (output / target.lstrip("/")).is_file() and not parsed.fragment, url

    sitemap = ElementTree.parse(output / "sitemap.xml")
    assert {item.text for item in sitemap.findall(".//{*}loc")} == {SITE + route for route in pages}
    for entry in sitemap.findall("{*}url"):
        path, _ = localized_routes[urlsplit(entry.find("{*}loc").text).path]
        assert {link.get("hreflang"): link.get("href") for link in entry.findall("{http://www.w3.org/1999/xhtml}link")} == {
            code: SITE + route_for(path, code) for code in ("en", "fi", "x-default")
        }
    robots = (output / "robots.txt").read_text()
    assert ("Disallow: /" if args.review else f"Sitemap: {SITE}/sitemap.xml") in robots
    for language in ("en", "fi"):
        label_for = translate if language == "fi" else str
        inchcape = next(item for item in CASES if item["careerId"] == "inchcape")
        for base in ("/", "/profile/", "/cv/", case_path(inchcape)):
            route = route_for(base, language)
            html = (output / route.strip("/") / "index.html").read_text(encoding="utf-8")
            for metric in case_metrics(inchcape):
                label = metric.get("homeLabel", metric["label"]) if base == "/" else metric["label"]
                assert escape(metric["value"]) in html.replace(" %", "%"), (route, metric)
                assert escape(label_for(label)) in html, (route, metric)
            if base == "/":
                achievements = html.split('id="achievements"', 1)[1].split("</section>", 1)[0]
                assert all(job["employer"] not in achievements for job in DATA["career"]), route
                measured, scope = achievements.split(label_for("Scope of responsibility"), 1)
                assert "<strong>27</strong>" not in measured and "<strong>27</strong>" in scope, route
                assert label_for("Profitability maintained") in measured, route
        cv_route = route_for("/cv/", language)
        cv_html = (output / cv_route.strip("/") / "index.html").read_text(encoding="utf-8")
        assert f'>{label_for("Print CV")}</button>' in cv_html
        assert "@media print" in (output / "site.css").read_text(encoding="utf-8")

        for item in CASES:
            html = (output / route_for(case_path(item), language).strip("/") / "index.html").read_text(encoding="utf-8")
            status_heading = "Current development status" if item["status"] == "ongoing" else "Results"
            for heading in (status_heading if key == "results" else label for key, label in CASE_SECTIONS.items()):
                assert f"<h2>{label_for(heading)}</h2>" in html, (item["slug"], heading)
        automotive = route_for(DEVELOPMENT_PATHS["automotive"], language)
        for item in CONCEPTS:
            route = route_for(concept_path(item), language)
            assert route in pages[automotive].urls, route
            assert automotive + "#concept-studies" in pages[route].urls, route
            html = (output / route.strip("/") / "index.html").read_text(encoding="utf-8")
            for label in CONCEPT_SECTIONS.values():
                assert f"<h2>{label_for(label)}</h2>" in html, (route, label)
        for link in AUTOMOTIVE_PROJECT["caseLinks"]:
            route = route_for(case_path(link), language)
            assert route in pages[automotive].urls, route
            assert automotive + "#professional-connections" in pages[route].urls, route
    print(f"Checked {len(pages)} pages, homepage and full professional profile, the current role, accessible labels, internal links, SEO metadata and sitemap.")


if __name__ == "__main__":
    main()
