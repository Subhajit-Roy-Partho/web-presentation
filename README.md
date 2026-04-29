# web-presentation

A collection of interactive web-based slide presentations built with plain HTML, CSS, and JavaScript. Each sub-folder is a self-contained deck that opens directly in any browser with no build step.

## Presentations

### [`bbflow/`](bbflow/)

**Learning Conformational Ensembles of Proteins Based on Backbone Geometry**

A 42-slide walkthrough of the BBFlow paper (Wolf, Seute et al., NeurIPS 2025, arXiv:2503.05738). Designed for a mixed scientific audience — covers prerequisite biology, machine-learning background, the BBFlow method, results, and open questions.

| Feature | Details |
|---------|---------|
| Slides | 42 |
| Audience | Mixed scientific (biologists, physicists, ML researchers) |
| Source paper | arXiv:2503.05738v2 |
| Controls | Arrow keys, Space, L (laser), F (fullscreen), ? (help) |

**To run locally:**

```bash
cd bbflow
python3 -m http.server 8000
# then open http://localhost:8000
```

**To regenerate slide screenshots:**

```bash
cd bbflow
npm install playwright
npx playwright install chromium
node screenshot_slides.js
```

## Repository structure

```
web-presentation/
└── bbflow/                  # BBFlow paper walkthrough
    ├── index.html           # Main presentation (42 slides)
    ├── styles.css           # Deck theme and SVG styling
    ├── slides.js            # Navigation, keyboard, laser pointer
    ├── fixes-slides-*.css   # Per-section layout fixes
    ├── 2503.05738v2.pdf     # Source paper (local copy)
    ├── bbflow_paper.txt     # Extracted paper text
    ├── screenshot_slides.js # Playwright screenshot tool
    ├── notes/               # Paper summary, outline, references
    └── review/              # PNG screenshots of all 42 slides
```

## Adding a new presentation

1. Create a new sub-folder: `mkdir my-talk`
2. Copy the `bbflow/` structure as a starting point or build from scratch.
3. Add an entry to this README.
4. Add agent documentation to `AGENTS.md` if using AI-assisted authoring.
