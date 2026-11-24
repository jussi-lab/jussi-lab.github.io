"""Finnish copy overlays shared facts while routes and IDs stay stable."""
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FINNISH_CONTENT = json.loads((ROOT / "content/fi.json").read_text(encoding="utf-8"))
FINNISH = FINNISH_CONTENT["strings"]
SHARED_KEYS = {
    "id", "slug", "careerId", "publicationStatus", "evidenceStatus", "lastUpdated",
    "kind", "year", "value", "period", "contact", "name", "organisation",
}
MONTHS = dict(zip(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec Present".split(),
    "tammikuu helmikuu maaliskuu huhtikuu toukokuu kesäkuu heinäkuu elokuu syyskuu lokakuu marraskuu joulukuu nykyhetki".split(),
))
NUMBER = re.compile(r"\d+(?:\.\d+)?")
SAME = {"completed", "ongoing"}


def route_for(path, language):
    return "/fi" + path if language == "fi" else path


def translate(text):
    template = NUMBER.sub("{}", text)
    if template != text and template in FINNISH:
        return FINNISH[template].format(*NUMBER.findall(text))
    try:
        return FINNISH[text]
    except KeyError as exc:
        raise ValueError(f"Missing Finnish copy: {text!r}") from exc


def localize(data, key=""):
    if key in SHARED_KEYS:
        return data
    if isinstance(data, dict):
        return {
            translate(name) if key == "competencies" else name: localize(value, name)
            for name, value in data.items()
        }
    if isinstance(data, list):
        return [localize(item) for item in data]
    if isinstance(data, str) and data and data not in SAME:
        if key == "employer":
            return FINNISH.get(data, data)
        if key == "location":
            return data.replace(", Finland", ", Suomi").replace(", Spain", ", Espanja")
        return translate(data)
    return data


def format_period(period, language):
    if language == "en":
        return period
    return re.sub(r"\b[A-Z][a-z]+\b", lambda match: MONTHS.get(match[0], match[0]), period)
