# BBFlow Presentation Agent Notes

## Project Goal

Build and maintain a detailed web-based presentation for the paper:

**Learning conformational ensembles of proteins based on backbone geometry**  
Nicolas Wolf, Leif Seute, Vsevolod Viliuga, Simon Wagner, Jan Stuehmer, Frauke Graeter  
arXiv:2503.05738v2, NeurIPS 2025.

The intended audience is scientifically trained but mixed across backgrounds, so the deck should explain prerequisite concepts before the BBFlow model:

- Protein conformational ensembles and molecular dynamics.
- Transformers and attention.
- Geometric deep learning, SE(3), equivariance, and protein backbone frames.
- AlphaFold's Invariant Point Attention (IPA).
- Clifford Frame Attention (CFA) and GAFL.
- Flow matching on Euclidean spaces and SE(3) manifolds.
- Prior work on protein ensemble generation.
- BBFlow method, results, ablations, limitations, and takeaways.

## Source Files

- `2503.05738v2.pdf`: local source paper.
- `bbflow_paper.txt`: text extracted from the PDF using `pdftotext -layout`.
- `index.html`: main web presentation (42 slides).
- `styles.css`: deck layout, theme, charts, SVG styling, and laser pointer styling.
- `slides.js`: slide navigation, keyboard controls, progress, laser pointer, and fullscreen.
- `screenshot_slides.js`: Playwright script to render all slides to PNG (run with `node screenshot_slides.js`).
- `notes/paper-summary.md`: detailed technical summary of the BBFlow paper.
- `notes/literature-notes.md`: prerequisite and earlier-work notes.
- `notes/slide-outline.md`: slide sequence and teaching goals.
- `notes/references.md`: reference list used for slide footers.
- `review/slides/`: PNG screenshots of all 42 slides (1280×720).
- `review/contact-sheet-all.png`: full contact sheet of all 42 slides.

## Presentation Controls

The deck is designed to be opened directly in a browser:

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`.

Keyboard controls:

- `ArrowRight`, `Space`, `PageDown`, `N`: next slide.
- `ArrowLeft`, `PageUp`, `P`: previous slide.
- `Home`: first slide.
- `End`: final slide.
- `L`: toggle laser pointer.
- `F`: toggle fullscreen.
- `?`: toggle keyboard help overlay.
- `Esc`: close help overlay or disable laser pointer.

## Slide Sequence (42 slides)

### Original 34 slides
1. Title, 2. Talk Map, 3. Ensembles, 4. ~~Energy Landscape~~→ now slide 5, 5. Molecular Dynamics, 6. ~~Emulator~~→ now slide 8, 7. Attention, 8. Protein Attention, 9. Equivariance, 10. Backbone Frames, 11. IPA, 12. CFA, 13. ~~Flow Matching~~→ now slide 16, 14. SE3 Flow, 15. Earlier Work, 16. Gap, 17. BBFlow Idea, 18. BBFlow Pipeline, 19. Encoding, 20. Conditional Prior, 21. Architecture, 22. Loss, 23. Algorithm, 24. ATLAS, 25. ~~Metrics~~→ now slide 29, 26. ATLAS Results, 27. Speed Accuracy, 28. De Novo, 29. Multi Chain, 30. Ablation, 31. One Minute, 32. Limitations, 33. Takeaways, 34. References.

### 8 new slides added for diverse audiences
- **Slide 4 — Backbone Anatomy:** What the protein backbone is (N–Cα–C chain, frames vs. side chains). For non-biologists.
- **Slide 7 — Why Dynamics Matter:** Allostery, induced fit, cryptic pockets. Why conformational dynamics are biologically essential.
- **Slide 15 — Flow vs Diffusion:** Compares diffusion models and flow matching for an ML or physics audience. Explains why BBFlow uses flow matching.
- **Slide 28 — RMSF Visualized:** Visual explanation of RMSF metric with profile diagram. For audiences unfamiliar with structural biology metrics.
- **Slide 32 — BioEmu Context:** Three-way comparison of BBFlow, BioEmu, and AlphaFlow-T. Clarifies which tool fits which use case.
- **Slide 35 — BBFlow in Practice:** Step-by-step workflow from PDB to ensemble. Practical guide for any scientific audience.
- **Slide 37 — Training Budget:** GPU-day comparison of BBFlow vs. AlphaFold-scale training. Shows accessibility of the approach.
- **Slide 40 — Future Directions:** Six open directions: side chains, longer timescales, cryptic pockets, protein-ligand, custom MD, RNA/IDPs.

## Content Guidelines

- Keep slide footers concise and source-specific.
- Prefer original SVG diagrams and schematic recreations over copied paper figures.
- When reproducing quantitative results, use values from the paper tables and cite the paper footer.
- Keep formulas in MathJax-compatible LaTeX.
- Preserve accessibility: readable contrast, large text, and meaningful labels.
- Avoid presenting BBFlow as a full replacement for MD. It is an MD-emulation model for short-timescale ensemble distributions similar to the training data.

## Verified Core Facts

- BBFlow conditions on an equilibrium backbone structure, not on an MSA or folding-model trunk.
- It models \(p(x \mid x_{\mathrm{eq}})\), where \(x\) is a conformation and \(x_{\mathrm{eq}}\) is the equilibrium structure.
- The backbone is represented as per-residue frames in \(SE(3)^N\).
- The conditional prior is built by geodesic interpolation:
  \[
  x_0 = \gamma(x_{\mathrm{uncond}}, x_{\mathrm{eq}}, \xi), \quad \xi = 0.2.
  \]
- Equilibrium encodings include binned pairwise distances and local pairwise directions.
- BBFlow adapts GAFL/CFA, uses 6 message-passing blocks, and omits residue-index encoding.
- Main ATLAS result: about `0.8 s` per generated 302-residue conformation, with RMSF MAE `0.42 A` and pairwise RMSD MAE `0.77 A`.
- AlphaFlow-T is about `32.6 s` per conformation in the same timing setup.
- BBFlow generalizes to de novo proteins and demonstrated multi-chain proteins despite monomer-only training.

