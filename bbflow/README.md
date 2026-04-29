# BBFlow Web Presentation

This folder contains a static browser presentation for the paper **Learning conformational ensembles of proteins based on backbone geometry**.

Run it locally:

```bash
python3 -m http.server 8000
```

Then open:

```text
http://localhost:8000
```

Open `index.html` directly also works, but serving through localhost is more reliable for browser features.

## Files

- `index.html`: slide content.
- `styles.css`: visual design.
- `slides.js`: navigation, keyboard shortcuts, progress, laser pointer, fullscreen, and help overlay.
- `notes/`: detailed background notes, paper summary, outline, and references.
- `2503.05738v2.pdf`: source paper.
- `bbflow_paper.txt`: extracted text from the PDF.

## Controls

- Next: `ArrowRight`, `Space`, `PageDown`, `N`, or the `Next` button.
- Previous: `ArrowLeft`, `PageUp`, `P`, or the `Prev` button.
- Laser pointer: `L` or the `Laser` button.
- Fullscreen: `F`.
- Help: `?`.
- First/last slide: `Home` / `End`.

