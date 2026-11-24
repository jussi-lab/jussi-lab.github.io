"""Render public portfolio content as static HTML."""
from datetime import date
from html import escape
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://jussi-lab.github.io"
DATA = json.loads((ROOT / "content/portfolio.json").read_text(encoding="utf-8"))
NAME = escape(DATA["name"])
CONTACT = escape(DATA["contact"])
DESCRIPTION = "Jussi Rahkama is a technical operations leader in Helsinki, Finland, with approximately 30 years of automotive experience."
SECTIONS = {
    "home": "Home",
    "profile": "Professional Profile",
    "career": "Career Timeline",
    "achievements": "Achievements",
    "cases": "Case Studies",
    "leadership": "Leadership Philosophy",
    "technology": "Technology and AI",
    "automotive": "Automotive 2.0",
    "mobility": "Autonomous Mobility",
    "contact": "CV and Contact",
}


def section(key, body, modifier=""):
    return f'<section class="section {modifier}" id="{key}" aria-labelledby="{key}-title"><div class="wrap"><h2 id="{key}-title">{SECTIONS[key]}</h2>{body}</div></section>'


def layout(title, path, description, body):
    url = SITE + path
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/social.png">
<meta property="og:image:alt" content="Jussi Rahkama, technical operations leadership">
<link rel="stylesheet" href="/site.css">
<link rel="icon" href="/icon.png">
<script src="/theme.js" defer></script>
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{body}
</body>
</html>
"""


def career_list():
    rows = []
    for job in DATA["career"]:
        employer, role, period, summary = (escape(job[key]) for key in ("employer", "role", "period", "summary"))
        rows.append(f'<li><div class="career-meta"><h3>{employer}</h3><p>{period}</p></div><div><p class="role">{role}</p><p>{summary}</p></div></li>')
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def approved_cases():
    allowed_evidence = {"owner-supplied", "verified"}
    fields = ("employer", "role", "project", "challenge", "actions", "results", "evidenceStatus", "publicationStatus", "lastUpdated")
    for item in DATA["caseStudies"]:
        if item.get("publicationStatus") != "approved" or item.get("evidenceStatus") not in allowed_evidence:
            raise ValueError("Public content must contain only approved cases with a publishable evidence status")
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in fields):
            raise ValueError("Case studies require all documented fields")
        date.fromisoformat(item["lastUpdated"])
    return DATA["caseStudies"]


def case_card(item):
    employer, role, project = (escape(item[key]) for key in ("employer", "role", "project"))
    details = "".join(f"<dt>{key.title()}</dt><dd>{escape(item[key])}</dd>" for key in ("challenge", "actions", "results"))
    return f'<article class="case"><p class="eyebrow">{employer} · {role}</p><h3>{project}</h3><dl>{details}</dl></article>'


def metric_card(metric):
    value, label, context = (escape(metric[key]) for key in ("value", "label", "context"))
    return f'<div class="metric"><strong>{value}</strong><h3>{label}</h3><p>{context}</p></div>'


def header():
    links = "".join(f'<a href="#{key}">{SECTIONS[key]}</a>' for key in SECTIONS)
    return f"""<header class="top"><div class="wrap top-inner">
<a class="brand" href="#home"><span class="mark" aria-hidden="true">JR</span>{NAME}</a>
<nav class="primary" aria-label="Primary"><a href="#career">Career</a><a href="#cases">Case Studies</a><a href="#technology">Technology</a><a href="#contact">Contact</a></nav>
<div class="utilities">
<button type="button" id="theme" hidden>Use light theme</button>
<details class="menu"><summary>Explore</summary><nav aria-label="All sections">{links}</nav></details>
</div>
</div></header>"""


def footer():
    return f'<footer><div class="wrap footer-inner"><span>{NAME} · {escape(DATA["location"])}</span><a href="{CONTACT}">LinkedIn</a></div></footer>'


def home():
    cases = approved_cases()
    metrics = "".join(metric_card(item["metric"]) for item in cases if "metric" in item)
    competencies = "".join(f"<li>{escape(item)}</li>" for item in DATA["competencies"])
    leadership = DATA["leadership"]
    principles = "".join(f'<div><h3>{escape(item["title"])}</h3><p>{escape(item["body"])}</p></div>' for item in leadership["principles"])
    development = "".join(
        f'<section class="development-card" id="{escape(item["id"])}" aria-labelledby="{escape(item["id"])}-title"><p class="eyebrow">{escape(item["status"])}</p><h2 id="{escape(item["id"])}-title">{escape(item["title"])}</h2><p>{escape(item["body"])}</p></section>'
        for item in DATA["development"]
    )
    parts = [
        f"""<section class="hero" id="home" aria-labelledby="hero-title"><div class="wrap hero-inner">
<div class="hero-copy"><p class="eyebrow">Technical Operations Leadership</p>
<h1 id="hero-title">{escape(DATA["headline"])}</h1>
<p class="support">{escape(DATA["supportingHeadline"])}</p>
<div class="actions"><a class="button" href="#cases">Explore case studies</a><a class="button secondary" href="/cv/">View CV</a></div>
</div><div class="hero-art" aria-hidden="true"><div class="track track-a"></div><div class="track track-b"></div><div class="track track-c"></div><div class="track track-d"></div><span class="junction"></span></div>
</div></section>""",
        section("achievements", f'<div class="metric-grid">{metrics}</div>', "achievement-section"),
        section("profile", f'<div class="profile-grid"><p class="lede">{escape(DATA["summary"])}</p><ul class="competencies">{competencies}</ul></div>'),
        section("career", career_list(), "alternate"),
        section("cases", '<div class="case-grid">' + "".join(map(case_card, cases)) + "</div>"),
        section("leadership", f'<div class="leadership-intro"><h3>{escape(leadership["heading"])}</h3><p>{escape(leadership["body"])}</p></div><div class="principles">{principles}</div>', "alternate"),
        f'<div class="section"><div class="wrap development-grid">{development}</div></div>',
        section("contact", f'<p class="lede">Based in {escape(DATA["location"])}. Connect with me on LinkedIn or view the printable CV for a summary of my career.</p><div class="actions"><a class="button" href="{CONTACT}">Connect on LinkedIn</a><a class="button secondary" href="/cv/">View printable CV</a></div>', "contact"),
    ]
    return layout(f"{DATA['name']} | Technical Operations Leadership", "/", DESCRIPTION, header() + '<main id="main" tabindex="-1">' + "".join(parts) + "</main>" + footer())


def cv():
    skills = " · ".join(map(escape, DATA["competencies"]))
    highlights = "".join(
        f'<li><strong>{escape(item["employer"])}</strong> · {escape(item["results"])}</li>'
        for item in approved_cases()
    )
    return layout(f"CV | {DATA['name']}", "/cv/", f"Printable professional CV for {DATA['name']}.", f"""
<header class="top cv-header"><div class="wrap top-inner"><a class="brand" href="/">Portfolio home</a><button type="button" id="print" hidden>Print CV</button></div></header>
<main id="main" class="wrap cv" tabindex="-1">
<h1>{NAME}</h1><p class="lede">Technical Operations Leadership</p>
<p>{escape(DATA["location"])} · <a href="{CONTACT}">LinkedIn</a></p>
<h2>Professional profile</h2><p>{escape(DATA["summary"])}</p>
<h2>Core competencies</h2><p>{skills}</p>
<h2>Selected achievements</h2><ul>{highlights}</ul>
<h2>Career history</h2>{career_list()}
</main>{footer()}""")


def main():
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    (output / "cv").mkdir(exist_ok=True)
    for filename in ("site.css", "theme.js", "social.png", "icon.png"):
        shutil.copyfile(ROOT / "src" / filename, output / filename)
    files = {
        "index.html": home(),
        "cv/index.html": cv(),
        "sitemap.xml": f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE}/</loc></url><url><loc>{SITE}/cv/</loc></url></urlset>\n',
        "robots.txt": f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n",
        ".nojekyll": "",
    }
    for filename, content in files.items():
        (output / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
