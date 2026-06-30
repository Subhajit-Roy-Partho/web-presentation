# web-presentation

A collection of interactive web-based slide presentations built with plain HTML, CSS, and JavaScript. Each sub-folder is a self-contained deck that opens directly in any browser with no build step.

**Live site:** <https://subhajit-roy-partho.github.io/web-presentation/>

## Presentations

| Deck | Description |
|------|-------------|
| [`bbflow/`](bbflow/) | BBFlow — Learning Conformational Ensembles of Proteins Based on Backbone Geometry (42 slides, NeurIPS 2025) |
| [`bbflow2/`](bbflow2/) | IDPFlow — BBFlow variant focused on intrinsically disordered proteins |
| [`bbflow3/`](bbflow3/) | BBFlow proposal (incomplete) |
| [`fastdna/`](fastdna/) | fastDNA presentation |
| [`mdgen/`](mdgen/) | MDGen survey &amp; presentation |
| [`mdgen2/`](mdgen2/) | MDGen proposal presentation |

### Controls

Arrow keys, Space (next), L (laser pointer), F (fullscreen), ? (help).

## Run locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Deployment

A GitHub Actions workflow (`.github/workflows/deploy.yml`) automatically deploys
the `main` branch to GitHub Pages on every push.

### One-time setup

1. Go to repo **Settings → Pages**.
2. Under **Source**, select **GitHub Actions** (not a branch).
3. Push to `main` — the workflow will deploy automatically.

## Repository structure

```
web-presentation/
├── index.html            # Landing page with links to all decks
├── .github/workflows/    # GitHub Actions deployment workflow
├── bbflow/               # BBFlow paper walkthrough
├── bbflow2/              # IDPFlow presentation
├── bbflow3/              # BBFlow proposal (incomplete)
├── fastdna/              # fastDNA presentation
├── mdgen/                # MDGen survey
└── mdgen2/               # MDGen proposal
```

## Adding a new presentation

1. Create a new sub-folder: `mkdir my-talk`
2. Add an `index.html` (and any CSS/JS assets).
3. Add an entry to this README and to the root `index.html` landing page.
4. Add agent documentation to `AGENTS.md` if using AI-assisted authoring.
