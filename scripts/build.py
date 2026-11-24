"""Render public portfolio content as static HTML."""
import argparse
from datetime import date
from html import escape
import json
import re
from pathlib import Path
import shutil

from localization import FINNISH_CONTENT, format_period, localize, route_for, translate

ROOT = Path(__file__).resolve().parents[1]
SITE = "https://jussi-lab.github.io"
LANGUAGE = "en"
REVIEW = False
SOURCE = json.loads((ROOT / "content/portfolio.json").read_text(encoding="utf-8"))
DATA = SOURCE
NAME = escape(DATA["name"])
CONTACT = escape(DATA["contact"])
DESCRIPTION = "Jussi Rahkama is an operations and development leader focused on operational transformation, technical operations, business development and systems thinking."
CAREER = {job["id"]: job for job in DATA["career"]}
CASES = DATA["caseStudies"]
DEVELOPMENT_PATHS = {"technology": "/technology/", "automotive": "/automotive-2-0/"}
AUTOMOTIVE = next(item for item in DATA["development"] if item["id"] == "automotive")
AUTOMOTIVE_PROJECT = AUTOMOTIVE["project"]
CONCEPTS = AUTOMOTIVE_PROJECT["studies"]
CONCEPT_SECTIONS = {
    "problem": "Problem being explored",
    "context": "Operational context",
    "principles": "Proposed principles",
    "solution": "Conceptual solution",
    "dependencies": "Dependencies",
    "benefits": "Potential benefits",
    "risks": "Risks and limitations",
    "validation": "Validation requirements",
    "status": "Development status",
}
CASE_SECTIONS = {
    "background": "Starting point",
    "challenge": "Challenge",
    "analysis": "Approach",
    "contribution": "My contribution",
    "actions": "Team and project actions",
    "results": "Results",
    "lessonsLearned": "Lessons learned",
    "transferableCompetencies": "Transferable capabilities",
}
SECTIONS = {
    "home": "Home",
    "profile": "Professional Profile",
    "capabilities": "Core Capabilities",
    "career": "Career Timeline",
    "achievements": "Achievements",
    "cases": "Case Studies",
    "approach": "How I Work",
    "operating-model": "Operating Model",
    "leadership": "Leadership Philosophy",
    "insights": "Professional Insights",
    "qualifications": "Education and Qualifications",
    "technology": "Technology and AI",
    "automotive": "Automotive 2.0",
    "mobility": "Autonomous Mobility",
    "contact": "CV and Contact",
}


def ui(text):
    return translate(text) if LANGUAGE == "fi" else text


def language_switch(path):
    links = []
    for language, name in (("fi", "Suomi"), ("en", "English")):
        active = ' aria-current="page"' if language == LANGUAGE else ""
        links.append(f'<a href="{route_for(path, language)}" hreflang="{language}" lang="{language}" aria-label="{name}"{active}>{language.upper()}</a>')
    return f'<nav class="language-switch" aria-label="{ui("Language")}">' + '<span aria-hidden="true">|</span>'.join(links) + "</nav>"


def section(key, body, modifier=""):
    return f'<section class="section {modifier}" id="{key}" aria-labelledby="{key}-title"><div class="wrap"><h2 id="{key}-title">{ui(SECTIONS[key])}</h2>{body}</div></section>'


def layout(title, path, description, body):
    url = SITE + route_for(path, LANGUAGE)
    if LANGUAGE == "fi":
        body = re.sub(r'href="(/(?!/)[^"]*)"', lambda match: f'href="{route_for(match[1], LANGUAGE)}"', body)
    body = body.replace("<!--language-switch-->", language_switch(path))
    alternates = "\n".join(
        f'<link rel="alternate" hreflang="{language}" href="{SITE}{route_for(path, language)}">'
        for language in ("en", "fi", "x-default")
    )
    return f"""<!doctype html>
<html lang="{LANGUAGE}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark light">
{'<meta name="robots" content="noindex, nofollow">' if REVIEW else ""}
<title>{escape(title)}</title>
<meta name="description" content="{escape(description)}">
<link rel="canonical" href="{url}">
{alternates}
<meta property="og:locale" content="{'fi_FI' if LANGUAGE == 'fi' else 'en_GB'}">
<meta property="og:type" content="website">
<meta property="og:title" content="{escape(title)}">
<meta property="og:description" content="{escape(description)}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/social.png">
<meta property="og:image:alt" content="{ui("Jussi Rahkama, technical operations leadership")}">
<link rel="stylesheet" href="/site.css">
<link rel="icon" href="/icon.png">
<script src="/theme.js" defer></script>
</head>
<body>
<a class="skip" href="#main">{ui("Skip to content")}</a>
{body}
</body>
</html>
"""


def current_position():
    job = next((item for item in DATA["career"] if item.get("current")), None)
    if job:
        separator = " – " if LANGUAGE == "fi" else " at "
        return f'<p class="current-role">{escape(job["role"] + separator + job["employer"])}</p>'
    return ""


def paragraphs(values):
    return "".join(f"<p>{escape(value)}</p>" for value in values)


def bullet_list(values):
    return "<ul>" + "".join(f"<li>{escape(value)}</li>" for value in values) + "</ul>"


def case_metrics(item):
    primary = [item["metric"]] if "metric" in item else []
    return primary + item.get("additionalMetrics", [])


def case_results(item, include_metrics=False):
    result = escape(item["results"])
    if include_metrics and item.get("additionalMetrics"):
        metrics = "; ".join(f'{escape(metric["label"])} {escape(metric["value"])}' for metric in case_metrics(item))
        result = f"{metrics}. {result}"
    if item["evidenceStatus"] == "owner-supplied":
        result = f'{ui("Owner-reported")}: {result}'
    return result


def career_list(include_achievements=True):
    cases_by_career = {item["careerId"]: item for item in CASES}
    rows = []
    for job in DATA["career"]:
        employer, role = (escape(job[key]) for key in ("employer", "role"))
        period = format_period(job.get("period") or ("Present" if job.get("current") else ""), LANGUAGE)
        context = " · ".join(value for value in (period, job.get("location")) if value)
        date_line = paragraphs([context]) if context else ""
        case = cases_by_career.get(job["id"])
        summary = ""
        if case:
            if include_achievements:
                summary += f'<p><strong>{ui("Scope of responsibility")}:</strong> {escape(case["background"])}</p>'
            else:
                summary += paragraphs([job["summary"]])
            summary += f'<p><strong>{ui("Key actions")}:</strong> {escape(case["contribution"])}</p>'
            if case["status"] == "ongoing" or include_achievements:
                label = "Ongoing development" if case["status"] == "ongoing" else "Key achievements"
                summary += f'<p><strong>{ui(label)}:</strong> {case_results(case, include_metrics=True)}</p>'
            if include_achievements:
                summary += f'<p><a href="{case_path(case)}">{ui("Read the {employer} case study").format(employer=employer)}</a></p>'
        elif job.get("summary"):
            summary = f'<p><strong>{ui("Key contributions")}:</strong> {escape(job["summary"])}</p>'
        assignment = job.get("assignment")
        if job.get("responsibilities"):
            summary += bullet_list(job["responsibilities"])
        if assignment:
            assignment_label = " · ".join((assignment["employer"], assignment["location"], format_period(assignment["period"], LANGUAGE)))
            summary += f'<p class="assignment"><strong>{escape(assignment_label)}</strong></p>'
            summary += paragraphs([assignment["summary"]])
        rows.append(f'<li><div class="career-meta"><h3>{employer}</h3>{date_line}</div><div><p class="role">{role}</p>{summary}</div></li>')
    return '<ol class="timeline">' + "".join(rows) + "</ol>"


def validate_publication(review):
    if not review and DATA.get("publicationStatus") != "approved":
        raise ValueError("Owner approval is required. Use --review for a local preview.")
    if not review and FINNISH_CONTENT["publicationStatus"] != "approved":
        raise ValueError("Owner approval is required for the Finnish translation. Use --review for a local preview.")
    if len(CAREER) != len(DATA["career"]):
        raise ValueError("Career entries require unique IDs")
    records = DATA["career"] + [job["assignment"] for job in DATA["career"] if "assignment" in job]
    records += [item for group in DATA["credentials"].values() for item in group]
    records += CASES + CONCEPTS
    if any(item["evidenceStatus"] not in {"documented", "owner-supplied", "verified", "qualitative", "ongoing", "independent-concept"} for item in records):
        raise ValueError("Invalid evidence status")
    allowed = {"approved", "pending-review"} if review else {"approved"}
    if any(item["publicationStatus"] not in allowed for item in records):
        raise ValueError("Unapproved professional evidence")
    slugs = set()
    for item in CASES:
        slug = item["slug"]
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug in slugs:
            raise ValueError(f"Invalid or duplicate case study slug: {slug!r}")
        slugs.add(slug)
        if item["careerId"] not in CAREER or item["status"] not in {"completed", "ongoing"}:
            raise ValueError(f"Invalid career reference or status: {slug}")
        for key in CASE_SECTIONS:
            value = item[key]
            if key == "actions":
                valid = isinstance(value, list) and value and all(isinstance(action, str) and action.strip() for action in value)
            else:
                valid = isinstance(value, str) and value.strip()
            if not valid:
                raise ValueError(f"Invalid {key} for {slug}")
        if item["status"] == "ongoing" and case_metrics(item):
            raise ValueError(f"Ongoing case cannot present a completed metric: {slug}")
        date.fromisoformat(item["lastUpdated"])
    links = [item["slug"] for item in AUTOMOTIVE_PROJECT["caseLinks"]]
    if len(set(links)) != len(links) or not set(links) <= slugs:
        raise ValueError("Automotive 2.0 career references must be valid and unique")
    concept_slugs = [item["slug"] for item in CONCEPTS]
    if len(set(concept_slugs)) != len(concept_slugs) or any(
        not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) for slug in concept_slugs
    ):
        raise ValueError("Invalid or duplicate Automotive 2.0 concept slug")
    for item in CONCEPTS:
        if any(not isinstance(item.get(key), str) or not item[key].strip() for key in CONCEPT_SECTIONS):
            raise ValueError(f"Incomplete Automotive 2.0 concept: {item['slug']}")



def case_card(item):
    job = CAREER[item["careerId"]]
    status = "Ongoing development" if item["status"] == "ongoing" else "Completed career work"
    return f'<article class="case"><p class="eyebrow">{escape(job["employer"])} · {ui(status)}</p><h3><a href="{case_path(item)}">{escape(item["project"])}</a></h3><p>{escape(item["challenge"])}</p></article>'


def case_path(item):
    return f'/case-studies/{item["slug"]}/'


def detail_page(title, path, description, back_url, back_label, body):
    return layout(f"{title} | {DATA['name']}", path, description, f"""
<header class="top"><div class="wrap top-inner"><a class="brand" href="{back_url}">{ui(back_label)}</a><!--language-switch--></div></header>
<main id="main" class="wrap cv detail" tabindex="-1">
<h1>{escape(title)}</h1>
{body}
</main>{footer()}""")


def content_sections(items):
    return "".join(f'<section><h2>{escape(item["title"])}</h2><p>{escape(item["body"])}</p></section>' for item in items)


def case_page(item):
    job = CAREER[item["careerId"]]
    ongoing = item["status"] == "ongoing"
    sections = []
    for key, label in CASE_SECTIONS.items():
        heading = "Current development status" if key == "results" and ongoing else label
        if key == "actions":
            body = bullet_list(item[key])
        elif key == "results":
            body = f"<p>{case_results(item)}</p>"
        else:
            body = paragraphs([item[key]])
        sections.append(f"<section><h2>{ui(heading)}</h2>{body}</section>")
    cards = "".join(metric_card(metric, heading="h2") for metric in case_metrics(item))
    metric = f'<div class="metric-grid">{cards}</div>' if cards else ""
    context = " · ".join((job["employer"], job["role"], format_period(job["period"], LANGUAGE)))
    intro = f'<p class="lede">{escape(context)}</p>'
    if assignment := job.get("assignment"):
        assignment_context = " · ".join((assignment["employer"], assignment["location"], format_period(assignment["period"], LANGUAGE)))
        intro += paragraphs([assignment_context])
    related = ""
    if any(link["slug"] == item["slug"] for link in AUTOMOTIVE_PROJECT["caseLinks"]):
        related = f'<p class="section-link"><a href="{DEVELOPMENT_PATHS["automotive"]}#professional-connections">{ui("How this experience informs Automotive 2.0")}</a></p>'
    return detail_page(item["project"], case_path(item), item["challenge"], "/#cases", "All case studies", intro + "".join(sections) + metric + related)


def text_cards(items, heading="h3"):
    return "".join(
        f'<article class="case"><{heading}>{escape(item["title"])}</{heading}><p>{escape(item["body"])}</p></article>'
        for item in items
    )


def leadership_page():
    leadership = DATA["leadership"]
    body = paragraphs([leadership["body"]]) + content_sections(leadership["principles"])
    body += f'<p class="section-link"><a href="/operating-model/">{ui("See the operating model in practice")}</a></p>'
    return detail_page(leadership["heading"], "/leadership/", leadership["body"], "/#leadership", "Portfolio home", body)


def operating_page():
    model = DATA["operatingModel"]
    steps = "".join(
        f'<li><h2>{escape(step["title"])}</h2><p>{escape(step["body"])}</p></li>'
        for step in model["steps"]
    )
    body = paragraphs([model["body"]]) + f'<ol class="operating-steps">{steps}</ol>'
    body += f'<p class="section-link"><a href="/leadership/">{ui("Read the leadership principles behind this approach")}</a></p>'
    return detail_page(model["title"], "/operating-model/", model["body"], "/#operating-model", "Portfolio home", body)


def insight_page():
    insight = DATA["insight"]
    body = paragraphs([insight["body"]]) + content_sections(insight["sections"])
    return detail_page(insight["title"], "/insights/reliability/", insight["body"], "/#insights", "Professional insights", body)


def concept_path(item):
    return f'{DEVELOPMENT_PATHS["automotive"]}concepts/{item["slug"]}/'


def concept_card(item):
    return f"""<article class="case">
<p class="eyebrow">{escape(item["status"])}</p>
<h3><a href="{concept_path(item)}">{escape(item["title"])}</a></h3>
<p>{escape(item["problem"])}</p>
</article>"""


def concept_page(item):
    sections = [{"title": ui(label), "body": item[key]} for key, label in CONCEPT_SECTIONS.items()]
    intro = f'<p class="eyebrow">{ui("Automotive 2.0 · Independent concept study")}</p>'
    return detail_page(
        item["title"], concept_path(item), item["problem"],
        DEVELOPMENT_PATHS["automotive"] + "#concept-studies", "All concept studies",
        intro + content_sections(sections),
    )


def automotive_page():
    project = AUTOMOTIVE_PROJECT
    method = project["method"]
    areas = "".join(
        f'<section class="case"><h3>{escape(area["title"])}</h3><p>{escape(area["body"])}</p>{bullet_list(area["topics"])}</section>'
        for area in project["areas"]
    )
    cases_by_slug = {item["slug"]: item for item in CASES}
    connections = []
    for link in project["caseLinks"]:
        case = cases_by_slug[link["slug"]]
        employer = CAREER[case["careerId"]]["employer"]
        connections.append(f'<li><a href="{case_path(case)}">{escape(employer)} · {escape(case["project"])}</a><p>{escape(link["connection"])}</p></li>')
    body = f"""
<p class="eyebrow">{escape(AUTOMOTIVE["status"])}</p>
<p class="lede">{escape(project["subtitle"])}</p>
<div class="project-intro">{paragraphs(project["introduction"])}</div>
<nav class="project-nav" aria-label="{ui("On this page")}"><ul>
<li><a href="#development-areas">{ui("Development areas")}</a></li>
<li><a href="#research-method">{ui("Research method")}</a></li>
<li><a href="#concept-studies">{ui("Concept studies")}</a></li>
<li><a href="#professional-connections">{ui("Professional experience")}</a></li>
</ul></nav>
<section id="development-areas" aria-labelledby="development-areas-title">
<h2 id="development-areas-title">{ui("Core development areas")}</h2>
<div class="project-grid">{areas}</div>
</section>
<section id="research-method" aria-labelledby="research-method-title">
<h2 id="research-method-title">{ui("Research and development methodology")}</h2>
<div class="project-grid">
<section><h3>{ui("Analytical perspectives")}</h3>{bullet_list(method["perspectives"])}</section>
<section><h3>{ui("Types of evidence and research outputs")}</h3>{bullet_list(method["evidence"])}</section>
</div>
{paragraphs([method["review"]])}
</section>
<section id="concept-studies" aria-labelledby="concept-studies-title">
<h2 id="concept-studies-title">{ui("Selected concept studies")}</h2>
<p>{ui("Each study describes a proposal, potential benefits and the checks needed to evaluate it.")}</p>
<div class="project-grid">{"".join(map(concept_card, CONCEPTS))}</div>
</section>
<section id="professional-connections" aria-labelledby="professional-connections-title">
<h2 id="professional-connections-title">{ui("Professional experience informing the initiative")}</h2>
<p>{ui("These career cases provide practical context for this independent research.")}</p>
<ul class="project-links">{"".join(connections)}</ul>
<p class="section-link"><a href="/leadership/">{ui("Read the leadership philosophy")}</a></p>
</section>"""
    return detail_page(project["title"], DEVELOPMENT_PATHS["automotive"], AUTOMOTIVE["body"], "/#automotive", "Portfolio home", body)


def development_page(item):
    body = paragraphs([item["body"]]) + content_sections(item.get("sections", []))
    if item.get("topics"):
        body += f'<h2>{ui("Areas of exploration")}</h2>' + bullet_list(item["topics"])
    return detail_page(item["title"], DEVELOPMENT_PATHS[item["id"]], item["body"], f'/#{item["id"]}', "Portfolio home", body)


def development_card(item):
    key = escape(item["id"])
    path = DEVELOPMENT_PATHS.get(key)
    link = f'<p class="section-link"><a href="{path}">{ui("Explore {title}").format(title=escape(item["title"]))}</a></p>' if path else ""
    return f'<section class="development-card" id="{key}" aria-labelledby="{key}-title"><p class="eyebrow">{escape(item["status"])}</p><h2 id="{key}-title">{escape(item["title"])}</h2><p>{escape(item["body"])}</p>{link}</section>'


def extra_sections():
    sections = []
    for key, title in (("expertise", "Professional Expertise"), ("articles", "Articles")):
        if DATA.get(key):
            sections.append(f'<section class="section"><div class="wrap"><h2>{ui(title)}</h2><div class="case-grid">{text_cards(DATA[key])}</div></div></section>')
    projects = DATA.get("projects", [])
    if projects:
        labels = {
            "completed": "Completed project",
            "in-progress": "In progress",
            "concept": "Concept",
            "future": "Future development area",
        }
        cards = "".join(
            f'<article class="case"><p class="eyebrow">{ui(labels[item["status"]])}</p><h3>{escape(item["title"])}</h3><p>{escape(item["body"])}</p></article>'
            for item in projects
        )
        sections.append(f'<section class="section"><div class="wrap"><h2>{ui("Development Projects")}</h2><div class="case-grid">{cards}</div></div></section>')
    feedback = DATA.get("feedback", {})
    groups = []
    for key, label in (
        ("recommendations", "Professional recommendations"),
        ("assessments", "Leadership assessment"),
        ("professional", "Professional feedback"),
    ):
        if feedback.get(key):
            groups.append(f'<section><h3>{ui(label)}</h3><div class="case-grid">{text_cards(feedback[key], heading="h4")}</div></section>')
    if groups:
        sections.append(f'<section class="section"><div class="wrap"><h2>{ui("External Feedback")}</h2>' + "".join(groups) + "</div></section>")
    return "".join(sections)


def credential_sections(heading="h3"):
    groups = []
    for key, label in (("education", "Education"), ("certifications", "Professional training and certifications"), ("languages", "Languages")):
        items = DATA["credentials"].get(key, [])
        if not items:
            continue
        rows = []
        for item in items:
            info = " · ".join(item[field] for field in ("organisation", "year", "note") if item.get(field))
            rows.append(f'<li><strong>{escape(item["title"])}</strong><br>{escape(info)}</li>')
        groups.append(f'<section><{heading}>{ui(label)}</{heading}><ul>{"".join(rows)}</ul></section>')
    return '<div class="qualification-groups">' + "".join(groups) + "</div>"


def competency_groups():
    groups = "".join(
        f'<section><h3>{escape(title)}</h3>{bullet_list(values)}</section>'
        for title, values in DATA["competencies"].items()
    )
    return f'<div class="competency-groups">{groups}</div>'


def metric_card(metric, heading="h3"):
    value, label, context = (escape(metric[key]) for key in ("value", "label", "context"))
    return f'<div class="metric"><strong>{value}</strong><{heading}>{label}</{heading}><p>{context}</p></div>'


def header():
    destinations = {"career": "/profile/#career", "qualifications": "/profile/#qualifications", "automotive": DEVELOPMENT_PATHS["automotive"]}
    links = "".join(
        f'<a href="{destinations.get(key, "#" + key)}">{ui(label)}</a>'
        for key, label in SECTIONS.items()
    )
    return f"""<header class="top"><div class="wrap top-inner">
<a class="brand" href="#home"><span class="mark" aria-hidden="true">JR</span>{NAME}</a>
<nav class="primary" aria-label="{ui("Primary")}"><a href="/profile/#career">{ui("Career")}</a><a href="#cases">{ui("Case Studies")}</a><a href="#technology">{ui("Technology")}</a><a href="#contact">{ui("Contact")}</a></nav>
<div class="utilities">
<!--language-switch-->
<button type="button" id="theme" data-light="{ui("Use light theme")}" data-dark="{ui("Use dark theme")}" hidden>{ui("Use light theme")}</button>
<details class="menu"><summary>{ui("Explore")}</summary><nav aria-label="{ui("All sections")}">{links}</nav></details>
</div>
</div></header>"""


def footer():
    return f'<footer><div class="wrap footer-inner"><span>{NAME} · {escape(DATA["location"])}</span><a href="{CONTACT}">LinkedIn</a></div></footer>'


def profile_page():
    positioning = " · ".join(map(escape, DATA["positioning"]))
    body = f"""
<p class="positioning">{positioning}</p>
{current_position()}
<div class="profile-copy">{paragraphs(DATA["summary"])}</div>
<section id="competencies"><h2>{ui("Core competencies")}</h2>{competency_groups()}</section>
<section id="career"><h2>{ui("Career timeline")}</h2>{career_list()}</section>
<section id="qualifications"><h2>{ui("Education and qualifications")}</h2>{credential_sections()}</section>
<p class="section-link"><a href="/cv/">{ui("View printable CV")}</a></p>"""
    return detail_page(ui(SECTIONS["profile"]), "/profile/", ui(DESCRIPTION), "/", "Portfolio home", body)


def home():
    cases = CASES
    metrics = [metric for item in cases for metric in case_metrics(item)]
    achievement_groups = "".join(
        f'<div class="achievement-group"><h3>{ui(label)}</h3><div class="metric-grid">{cards}</div></div>'
        for kind, label in (("result", "Measured results"), ("scope", "Scope of responsibility"))
        if (cards := "".join(metric_card(metric, heading="h4") for metric in metrics if metric.get("kind", "result") == kind))
    )
    leadership = DATA["leadership"]
    model = DATA["operatingModel"]
    insight = DATA["insight"]
    positioning = " · ".join(map(escape, DATA["positioning"]))
    summary = paragraphs(DATA["summary"][:1])
    development = "".join(map(development_card, DATA["development"]))
    parts = [
        f"""<section class="hero" id="home" aria-labelledby="hero-title"><div class="wrap hero-inner">
<div class="hero-copy"><p class="eyebrow">{ui("Technical Operations Leadership")}</p>
<h1 id="hero-title">{escape(DATA["headline"])}</h1>
<p class="support">{escape(DATA["supportingHeadline"])}</p>
{current_position()}
<div class="actions"><a class="button" href="#cases">{ui("Explore case studies")}</a><a class="button secondary" href="/cv/">{ui("View CV")}</a></div>
</div><div class="hero-art" aria-hidden="true"><div class="track track-a"></div><div class="track track-b"></div><div class="track track-c"></div><div class="track track-d"></div><span class="junction"></span></div>
</div></section>""",
        section("achievements", f'<p class="lede">{escape(DATA["industryExperience"])}</p><div class="achievement-groups">{achievement_groups}</div>', "achievement-section"),
        section("profile", f'<div class="profile-copy"><p class="positioning">{positioning}</p>{summary}<p class="section-link"><a href="/profile/">{ui("Read the full professional profile")}</a></p></div>'),
        section("capabilities", f'<div class="capability-grid">{text_cards(DATA["capabilities"])}</div><p class="section-link"><a href="/profile/#competencies">{ui("View competencies by category")}</a></p>'),
        section("cases", '<div class="case-grid">' + "".join(map(case_card, cases)) + "</div>"),
        section("approach", f"""
<div class="case-grid">
<article class="case" id="operating-model"><h3><a href="/operating-model/">{escape(model["title"])}</a></h3><p>{ui("Seven steps from observing the work to improving and scaling it.")}</p></article>
<article class="case" id="leadership"><h3><a href="/leadership/">{ui("Leadership philosophy")}</a></h3><p>{escape(leadership["heading"])}</p></article>
<article class="case" id="insights"><h3><a href="/insights/reliability/">{escape(insight["title"])}</a></h3><p>{ui("How service operations support customer reliability across the product lifecycle.")}</p></article>
</div>""", "alternate"),
        f'<div class="section"><div class="wrap development-grid">{development}</div></div>',
        extra_sections(),
        section("contact", f'<p class="lede">{ui("Based in {location}. Connect with me on LinkedIn or view the printable CV for a summary of my career.").format(location=escape(DATA["location"]))}</p><div class="actions"><a class="button" href="{CONTACT}">{ui("Connect on LinkedIn")}</a><a class="button secondary" href="/cv/">{ui("View printable CV")}</a></div>', "contact"),
    ]
    return layout(f"{NAME} | {ui('Technical Operations Leadership')}", "/", ui(DESCRIPTION), header() + '<main id="main" tabindex="-1">' + "".join(parts) + "</main>" + footer())


def cv():
    highlights = "".join(
        f'<li><strong>{escape(CAREER[item["careerId"]]["employer"])}</strong> · {case_results(item, include_metrics=True)}</li>'
        for item in CASES if item["status"] == "completed"
    )
    positioning = " · ".join(map(escape, DATA["positioning"]))
    return layout(f"{ui('CV')} | {DATA['name']}", "/cv/", ui("Printable professional CV for {name}.").format(name=DATA["name"]), f"""
<header class="top cv-header"><div class="wrap top-inner"><a class="brand" href="/">{ui("Portfolio home")}</a><div class="utilities"><button type="button" id="print" hidden>{ui("Print CV")}</button><!--language-switch--></div></div></header>
<main id="main" class="wrap cv" tabindex="-1">
<h1>{NAME}</h1><p class="lede">{positioning}</p>
{current_position()}
<p>{escape(DATA["location"])} · <a href="{CONTACT}">LinkedIn</a></p>
<h2>{ui("Professional profile")}</h2>{paragraphs(DATA["summary"][:3])}
<h2>{ui("Core competencies")}</h2>{competency_groups()}
<h2>{ui("Selected achievements")}</h2><ul>{highlights}</ul>
<h2>{ui("Career history")}</h2>{career_list(include_achievements=False)}
<h2>{ui("Education and qualifications")}</h2>{credential_sections()}
</main>{footer()}""")


def render_pages(language):
    global LANGUAGE, DATA, CAREER, CASES, AUTOMOTIVE, AUTOMOTIVE_PROJECT, CONCEPTS
    LANGUAGE = language
    DATA = localize(SOURCE) if language == "fi" else SOURCE
    CAREER = {job["id"]: job for job in DATA["career"]}
    CASES = DATA["caseStudies"]
    AUTOMOTIVE = next(item for item in DATA["development"] if item["id"] == "automotive")
    AUTOMOTIVE_PROJECT = AUTOMOTIVE["project"]
    CONCEPTS = AUTOMOTIVE_PROJECT["studies"]
    pages = {
        "/": home(), "/profile/": profile_page(), "/cv/": cv(), "/leadership/": leadership_page(),
        "/operating-model/": operating_page(), "/insights/reliability/": insight_page(),
        DEVELOPMENT_PATHS["automotive"]: automotive_page(),
    }
    pages.update({DEVELOPMENT_PATHS[item["id"]]: development_page(item) for item in DATA["development"] if item["id"] == "technology"})
    pages.update({case_path(item): case_page(item) for item in CASES})
    pages.update({concept_path(item): concept_page(item) for item in CONCEPTS})
    return pages


def main():
    global REVIEW
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--review", action="store_true", help="Build pending content locally for owner review")
    args = parser.parse_args()
    REVIEW = args.review
    validate_publication(REVIEW)
    output = ROOT / ("dist-review" if args.review else "dist")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir()
    for filename in ("site.css", "theme.js", "social.png", "icon.png"):
        shutil.copyfile(ROOT / "src" / filename, output / filename)
    pages = {}
    for language in ("en", "fi"):
        pages.update({route_for(path, language): html for path, html in render_pages(language).items()})
    for path, html in pages.items():
        directory = output / path.lstrip("/")
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "index.html").write_text(html, encoding="utf-8")
    urls = []
    for path in pages:
        base = path.removeprefix("/fi") if path.startswith("/fi/") else path
        alternate = "".join(
            f'<xhtml:link rel="alternate" hreflang="{language}" href="{SITE}{route_for(base, language)}"/>'
            for language in ("en", "fi", "x-default")
        )
        urls.append(f"<url><loc>{SITE}{path}</loc>{alternate}</url>")
    files = {
        "sitemap.xml": f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">{"".join(urls)}</urlset>\n',
        "robots.txt": "User-agent: *\nDisallow: /\n" if args.review else f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n",
        ".nojekyll": "",
    }
    for filename, content in files.items():
        (output / filename).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
