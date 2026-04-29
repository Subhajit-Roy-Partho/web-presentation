# Agent Notes — web-presentation

This repository stores self-contained interactive web presentations. Each sub-folder is an independent deck. This file documents conventions and guidance for AI-assisted authoring of presentations in this repo.

---

## Repository conventions

- Every presentation lives in its own sub-folder (e.g. `bbflow/`).
- Each deck is a single `index.html` + CSS + JS — no bundler, no framework, no server-side rendering.
- Slide navigation is implemented in `slides.js`; slides are `<section class="slide">` elements shown/hidden by an `.active` class.
- MathJax 3 (CDN) renders LaTeX equations written as `\(...\)` (inline) or `\[...\]` (display).
- SVG diagrams are hand-authored inline; styling is done via shared CSS classes, not inline attributes.
- Screenshots of all slides are stored in `review/slides/` and a contact sheet in `review/contact-sheet-all.png`.

## Slide screenshot workflow

```bash
# from inside a presentation sub-folder:
npm install playwright
npx playwright install chromium
node screenshot_slides.js   # outputs to review/slides_new/, then copy over review/slides/
```

The script (`screenshot_slides.js`) navigates via URL hash (`#slide-N`), waits 4 s for MathJax to finish, and captures each slide at 1280×720 px.

## CSS class reference (shared across decks)

| Class | Purpose |
|-------|---------|
| `.slide` | Hidden slide container (`display:none` by default) |
| `.slide.active` | Currently visible slide |
| `.two-col` | Two-column grid layout (text left, figure right) |
| `.svg-card` | Styled figure box for inline SVG diagrams |
| `.wide-figure` | Full-width figure for pipeline/flowchart slides |
| `.formula-box` | Dark-background box for LaTeX equations |
| `.callout` | Green-tinted highlight box |
| `.warning` | Yellow-tinted warning box |
| `.compare` | Two-column side-by-side comparison |
| `.card-grid.three` | Three-card grid layout |
| `.info-card` | Card inside a grid |
| `.metric-strip` | Row of three numbered metric boxes |
| `.algorithm` | Numbered step list with circular badges |
| `.storyline` | Same as `.algorithm`, narrative style |
| `.result-table` / `.table-row` | Benchmark results table |
| `.takeaway-grid` | Three-column conclusion grid |
| `.section-tag` | Monospace eyebrow label above the slide title |

## Content guidelines

- Keep slide footers concise and source-specific (paper title, authors, venue, year).
- Prefer original SVG schematics over copied figures; use CSS classes for consistent styling.
- Write MathJax-compatible LaTeX for all mathematical content.
- Do not add features or slides beyond the stated scope of each task.
- Limit inline SVG comments; use semantic `aria-label` and `role="img"` on every `<svg>`.
- When adding slides for diverse audiences, prefer concrete analogies and visual diagrams over abstract descriptions.

---

## Presentations in this repo

### `bbflow/`

BBFlow paper walkthrough — 42 slides. See [`bbflow/AGENTS.md`](bbflow/AGENTS.md) for full source-of-truth documentation, verified facts, and per-slide notes.
