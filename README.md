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

Keep private evidence and unresolved claims outside the repository. Review
timeline entries, metadata, CV text and case studies against owner approval
before adding changes to a public branch.

## GitHub Pages

Pull requests run the build and static checks without a deployment job.
After the owner approves public release and the PR is merged, set **Settings →
Pages → Build and deployment → Source** to **GitHub Actions**. In **Actions**,
run **Portfolio** manually from the default branch (the deployment job checks
that branch). Confirm the Pages URL and its CV route after deployment.
Each subsequent release also requires a manual workflow run.

See [AGENTS.md](AGENTS.md) for maintenance and publishing guidance.

## Extend the portfolio

Career entries have stable IDs. Home and CV render the same current role and
timeline, including assignments nested under the employer. Case studies use
`careerId` to reference an employer, role and dates without duplicating them.
Use a unique lowercase slug for each case. Supply professional context,
challenge, approach, personal contribution, team and project actions, results or current status, lessons and
transferable capabilities. Mark ongoing work with `status: "ongoing"`.
Optional `metric.kind: "scope"` identifies the scale of responsibility.
Evidence status identifies the nature of a claim. Publication status records
owner approval separately.

The homepage profile is a list of paragraphs. The CV uses the opening profile
paragraphs and the same competency groups. Qualification records support titles,
organisations, historical years and notes. `operatingModel`, `leadership`,
`insight` and `development` hold the working approach, philosophy, insight
and technology material. Optional `projects` use `completed`, `in-progress`,
`concept` or `future`. Optional `feedback` lists sit under `recommendations`,
`assessments` or `professional`. Use names or quotes only with permission.

## Review unpublished content locally

Run `python3 scripts/build.py --review` and `python3 scripts/check.py --review`.
The output is separate from production in `dist-review/`. Serve that directory
only in a private environment. A production build requires approved content
at the portfolio and evidence-record levels. Keep pending files outside
public Git branches and pull requests.

See [PORTFOLIO_ROADMAP.md](PORTFOLIO_ROADMAP.md) for outstanding review tasks.

### Automotive 2.0

The Automotive 2.0 development record contains the project introduction,
development areas, research methodology, concept studies and references to
existing career case slugs. Each concept has a stable slug, nine narrative
fields, an evidence status and separate publication approval. Concept pages,
cross-links and sitemap entries are generated from these records. Keep private
research, sources and unapproved material outside the public repository.
