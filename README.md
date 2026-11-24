# Jussi Rahkama · Professional portfolio

A dependency-free static portfolio and printable CV for GitHub Pages.

## Build and preview

Requires Python 3.9 or newer. Run these commands from the repository root.

```sh
python3 scripts/build.py
python3 scripts/check.py
python3 -m http.server 8000 --directory dist
```

Open http://localhost:8000/. The site's paths assume a GitHub Pages user site
served from the domain root. The canonical domain is set in `scripts/build.py`.
Use the print button on the CV page to print or save a PDF with the browser.

## Update content

`content/portfolio.json` holds approved public content. `scripts/build.py`
renders shared layout, career records, metrics and case studies. `src/` holds
the CSS, progressive enhancements and social assets. `dist/` is generated.

Each case study has an `employer`, `role`, `project`, `challenge`, `actions`,
`results`, `evidenceStatus`, `publicationStatus` and `lastUpdated` in ISO date
format. Set `publicationStatus` to `approved` after the owner confirms
publication. `owner-supplied` identifies a claim supplied and approved by the
owner. Use `verified` when its basis has also been checked. The build rejects
other evidence and publication statuses for case studies. The optional
`metric` field supplies the achievement display. Review other public fields
against the same standards before committing. Keep unresolved claims and
private evidence outside this repository.

## GitHub Pages

Pull requests run the build and static checks without a deployment job.
After the owner approves public release and the PR is merged, set **Settings →
Pages → Build and deployment → Source** to **GitHub Actions**. In **Actions**,
run **Portfolio** manually from the default branch (the deployment job checks
that branch). Confirm the Pages URL and its CV route after deployment.
Each subsequent release also requires a manual workflow run.

See [AGENTS.md](AGENTS.md) for maintenance and publishing guidance.

## Extend the portfolio

Career entries require `employer` and `role`. Add an approved `period` and
`summary` when available. Set `current: true` on the current entry to feature
its employer and title on the homepage and CV. Both timelines read the same
ordered career list. `positioning` defines the homepage profile focus areas.

A case study uses a unique lowercase hyphenated `slug` for its detail-page
URL. The core Challenge, Actions and Results fields support the summary card.
Add `background`, `analysis`, `lessonsLearned` and
`transferableCompetencies` when approved. Optional `metric.kind: "scope"`
identifies the scale of responsibility. The default kind is a measured result.
Builds regenerate the sitemap and output so retired routes do not linger.

- `leadership.topics` takes entries with `title` and `body` for the leadership page.
- `credentials` supports lists of approved `education`, `languages` and
  `certifications` entries in the CV.
- `expertise` and `articles` take entries with `title` and `body`.
- `feedback` takes lists of title and body entries under `recommendations`,
  `assessments` or `professional`. Use names or quotes only with permission.
- `projects` takes `title`, `body` and a `status` of `completed`,
  `in-progress`, `concept` or `future`.

Populate optional sections once there is approved content. Existing development
summaries use `development`. If expanding an existing summary into a project,
publish one maintained description for it.

See [PORTFOLIO_ROADMAP.md](PORTFOLIO_ROADMAP.md) for planned content and the
material needed from the ChatGPT project.
