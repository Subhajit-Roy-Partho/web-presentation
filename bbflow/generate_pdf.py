#!/usr/bin/env python3
"""
BBFlow Technical Survey -- PDF generator (v4).
Loads Arial Unicode TTF for proper rendering.
Uses proper Unicode math notation throughout.
"""

import matplotlib
matplotlib.use('Agg')
from matplotlib.mathtext import math_to_image
from matplotlib.font_manager import FontProperties
from PIL import Image as PILImage
import numpy as np
import io

import pypdfium2 as pdfium
import pypdfium2.raw as pdfium_r
import ctypes, textwrap, os

_EQ_PROP = FontProperties(size=11)
_EQ_DPI  = 150
_EQ_PTS_PER_PX = 72.0 / _EQ_DPI

def _render_eq_png(latex_expr):
    """Render a LaTeX math expression via matplotlib mathtext; return (PIL.Image, w_pt, h_pt)."""
    buf = io.BytesIO()
    math_to_image(f'${latex_expr}$', buf, prop=_EQ_PROP, dpi=_EQ_DPI, format='png')
    buf.seek(0)
    img = PILImage.open(buf).convert('RGBA')
    w_px, h_px = img.size
    return img, w_px * _EQ_PTS_PER_PX, h_px * _EQ_PTS_PER_PX

# -- Page geometry (A4 @ 72 pt/inch) --
PW, PH = 595, 842
ML, MR = 65, 65
MT, MB = 70, 52
TW     = PW - ML - MR    # 465 pt

# -- Font sizes --
FS_TITLE   = 17
FS_SEC     = 13
FS_SUBSEC  = 11
FS_BODY    = 9.5
FS_SMALL   = 8.5
FS_CAPTION = 8.0
FS_EQ      = 9.5
FS_FOOT    = 7.5

LEAD = 1.55
CW   = 0.52

_FONT_PATHS = {
    "regular":    "/Library/Fonts/Arial Unicode.ttf",
    "bold":       "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "italic":     "/System/Library/Fonts/Supplemental/Arial Italic.ttf",
    "bolditalic": "/System/Library/Fonts/Supplemental/Arial Bold Italic.ttf",
}

def _cols(size, width=None):
    w = width if width is not None else TW
    return max(12, int(w / (size * CW)))


class Writer:
    """Single-cursor PDF layout engine with loaded Unicode fonts."""

    def __init__(self):
        self.doc     = pdfium.PdfDocument.new()
        self._fonts  = {}
        self._fbuf   = {}
        self._load_fonts()
        self._pg_num = 0
        self._start_page()

    def _load_font(self, key, path):
        with open(path, "rb") as f:
            data = f.read()
        buf = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
        self._fbuf[key] = buf
        handle = pdfium_r.FPDFText_LoadFont(
            self.doc.raw,
            ctypes.cast(buf, ctypes.POINTER(ctypes.c_ubyte)),
            len(data), pdfium_r.FPDF_FONT_TRUETYPE, True)
        self._fonts[key] = handle

    def _load_fonts(self):
        for key, path in _FONT_PATHS.items():
            if os.path.exists(path):
                self._load_font(key, path)
            else:
                self._fonts[key] = None

    def _font_handle(self, style):
        mapping = {
            "Helvetica":             "regular",
            "Helvetica-Bold":        "bold",
            # Italic/bolditalic always fall back to regular (Arial Unicode) so that
            # Greek letters and math symbols render correctly — Arial Italic/Bold
            # only cover Latin-1 and lack the full Unicode math range.
            "Helvetica-Oblique":     "regular",
            "Helvetica-BoldOblique": "regular",
        }
        key = mapping.get(style, "regular")
        return self._fonts.get(key) or self._fonts["regular"]

    def _start_page(self):
        if hasattr(self, "_pg"):
            self._draw_footer()
            pdfium_r.FPDFPage_GenerateContent(self._pg.raw)
        self._pg     = self.doc.new_page(PW, PH)
        self._pg_num += 1
        self.y       = PH - MT

    def section_break(self):
        """New page, but avoid blank pages by skipping if already at page top."""
        if self.y >= PH - MT - 25:
            self.gap(10)
        else:
            self._start_page()

    def _draw_footer(self):
        s  = str(self._pg_num)
        fx = PW / 2 - len(s) * FS_FOOT * CW / 2
        fy = MB - 18
        self._raw_text(s, fx, fy, "Helvetica", FS_FOOT, (160, 160, 160))

    def _check(self, height):
        if self.y - height < MB:
            self._start_page()

    def _raw_text(self, text, x, y, font_style, size, color=(0, 0, 0)):
        if not text:
            return
        fh  = self._font_handle(font_style)
        rp  = self._pg.raw
        obj = pdfium_r.FPDFPageObj_CreateTextObj(self.doc.raw, fh, float(size))
        enc = text.encode("utf-16-le") + b"\x00\x00"
        pdfium_r.FPDFText_SetText(
            obj, ctypes.cast(enc, ctypes.POINTER(ctypes.c_ushort)))
        r, g, b = color
        pdfium_r.FPDFPageObj_SetFillColor(obj, r, g, b, 255)
        pdfium_r.FPDFPageObj_Transform(obj, 1, 0, 0, 1, float(x), float(y))
        pdfium_r.FPDFPage_InsertObject(rp, obj)

    def _put(self, text, x, font, size, color=(0, 0, 0)):
        step = size * LEAD
        self._check(step)
        if text:
            self._raw_text(text, x, self.y, font, size, color)
        self.y -= step

    def gap(self, pts):
        if self.y - pts < MB:
            self._start_page()
        else:
            self.y -= pts

    def rule(self, r=120, g=120, b=120):
        self._check(8)
        rp  = self._pg.raw
        obj = pdfium_r.FPDFPageObj_CreateNewPath(float(ML), float(self.y))
        pdfium_r.FPDFPath_SetDrawMode(obj, 0, 1)
        pdfium_r.FPDFPageObj_SetStrokeColor(obj, r, g, b, 255)
        pdfium_r.FPDFPageObj_SetStrokeWidth(obj, 0.7)
        pdfium_r.FPDFPath_LineTo(obj, float(PW - MR), float(self.y))
        pdfium_r.FPDFPage_InsertObject(rp, obj)
        self.y -= 6

    def _draw_rect(self, x, y_bottom, width, height, r=245, g=246, b=252):
        """Draw a filled rectangle (used for equation backgrounds)."""
        rp  = self._pg.raw
        x1, y1 = float(x), float(y_bottom)
        x2, y2 = float(x + width), float(y_bottom + height)
        obj = pdfium_r.FPDFPageObj_CreateNewPath(x1, y1)
        pdfium_r.FPDFPath_LineTo(obj, x2, y1)
        pdfium_r.FPDFPath_LineTo(obj, x2, y2)
        pdfium_r.FPDFPath_LineTo(obj, x1, y2)
        pdfium_r.FPDFPath_LineTo(obj, x1, y1)
        pdfium_r.FPDFPath_SetDrawMode(obj, 1, 0)
        pdfium_r.FPDFPageObj_SetFillColor(obj, r, g, b, 255)
        pdfium_r.FPDFPage_InsertObject(rp, obj)

    def line(self, text, font="Helvetica", size=FS_BODY,
             color=(0, 0, 0), indent=0, center=False):
        x = ML + indent
        if center:
            x = max(ML, (PW - len(text) * size * CW) / 2)
        self._put(text, x, font, size, color)

    def wrap(self, text, font="Helvetica", size=FS_BODY,
             color=(0, 0, 0), indent=0, width=None, after=3):
        if not text or not text.strip():
            self.gap(size * LEAD)
            return
        avail = (width if width is not None else TW) - indent
        for ln in textwrap.wrap(text, _cols(size, avail)):
            self._put(ln, ML + indent, font, size, color)
        self.gap(after)

    def para(self, text, indent=0):
        self.wrap(text, indent=indent, after=4)

    def heading1(self, num, title):
        self.gap(10)
        label = f"{num}  {title}" if num else title
        self._put(label, ML, "Helvetica-Bold", FS_SEC, (0, 40, 120))
        self.rule(80, 120, 180)

    def heading2(self, num, title):
        self.gap(7)
        self._put(f"  {num}  {title}", ML,
                  "Helvetica-Bold", FS_SUBSEC, (30, 70, 160))
        self.gap(3)

    def heading3(self, title):
        self.gap(4)
        self._put(f"    {title}", ML,
                  "Helvetica-BoldOblique", FS_BODY, (40, 40, 40))
        self.gap(2)

    def bullet(self, text, indent=14):
        avail = TW - indent - 10
        lines = textwrap.wrap(text, _cols(FS_BODY, avail))
        for i, ln in enumerate(lines):
            step = FS_BODY * LEAD
            self._check(step)
            if i == 0:
                self._raw_text("–", ML + indent, self.y, "Helvetica", FS_BODY)
            self._raw_text(ln, ML + indent + 10, self.y, "Helvetica", FS_BODY)
            self.y -= step
        self.gap(2)

    def _embed_img(self, pil_img, x, y_bottom, w_pt, h_pt):
        """Embed a PIL RGBA image into the current page at (x, y_bottom) with given pt dimensions."""
        arr = np.array(pil_img)
        arr_bgra = arr[:, :, [2, 1, 0, 3]]
        w_px, h_px = pil_img.size
        data_bytes = arr_bgra.tobytes()
        buf_c = (ctypes.c_ubyte * len(data_bytes)).from_buffer_copy(data_bytes)
        bitmap = pdfium_r.FPDFBitmap_CreateEx(
            w_px, h_px, pdfium_r.FPDFBitmap_BGRA,
            ctypes.cast(buf_c, ctypes.c_void_p), w_px * 4)
        img_obj = pdfium_r.FPDFPageObj_NewImageObj(self.doc.raw)
        pages_arr = (pdfium_r.FPDF_PAGE * 0)()
        pdfium_r.FPDFImageObj_SetBitmap(pages_arr, 0, img_obj, bitmap)
        pdfium_r.FPDFImageObj_SetMatrix(img_obj, w_pt, 0, 0, h_pt,
                                        float(x), float(y_bottom))
        pdfium_r.FPDFPage_InsertObject(self._pg.raw, img_obj)
        pdfium_r.FPDFBitmap_Destroy(bitmap)

    def eq(self, label, latex_expr):
        """Render a properly typeset equation via matplotlib mathtext and embed as image."""
        self.gap(4)
        img, w_pt, h_pt = _render_eq_png(latex_expr)
        # Scale down if too wide for text area (reserve ~40pt for eq number)
        max_w = TW - 60
        if w_pt > max_w:
            scale = max_w / w_pt
            new_w = max(1, int(img.size[0] * scale))
            new_h = max(1, int(img.size[1] * scale))
            img = img.resize((new_w, new_h), PILImage.LANCZOS)
            w_pt, h_pt = new_w * _EQ_PTS_PER_PX, new_h * _EQ_PTS_PER_PX
        total_h = h_pt + 10
        self._check(total_h)
        # Light blue-gray background
        self._draw_rect(ML + 30, self.y - h_pt - 4, TW - 30, h_pt + 8)
        # Center the equation in the text area
        x_img = ML + 30 + (TW - 60 - w_pt) / 2
        y_bottom = self.y - h_pt
        self._embed_img(img, x_img, y_bottom, w_pt, h_pt)
        # Right-aligned equation number
        if label:
            lbl = f"({label})"
            lx  = PW - MR - len(lbl) * FS_EQ * CW - 2
            self._raw_text(lbl, lx, self.y - h_pt / 2,
                           "Helvetica", FS_CAPTION, (100, 100, 100))
        self.y -= h_pt + 4
        self.gap(4)

    def eq2(self, label, expr1, expr2):
        """Two-line display equation: render both lines as separate images."""
        self.eq(None, expr1)
        self.eq(label, expr2)

    def caption(self, text):
        self.wrap(text, "Helvetica-Oblique", FS_CAPTION,
                  (80, 80, 80), indent=10, width=TW - 20, after=6)

    def table(self, headers, rows, col_x, col_w,
              bold_last=False, caption_text=""):
        self._table_row(headers, col_x, col_w,
                        font="Helvetica-Bold", color=(0, 30, 110))
        self._check(2)
        # Draw separator line 2 pts below the header text block
        line_y = self.y - 2
        rp  = self._pg.raw
        obj = pdfium_r.FPDFPageObj_CreateNewPath(float(ML), float(line_y))
        pdfium_r.FPDFPath_SetDrawMode(obj, 0, 1)
        pdfium_r.FPDFPageObj_SetStrokeColor(obj, 160, 160, 160, 255)
        pdfium_r.FPDFPageObj_SetStrokeWidth(obj, 0.4)
        pdfium_r.FPDFPath_LineTo(obj, float(PW - MR), float(line_y))
        pdfium_r.FPDFPage_InsertObject(rp, obj)
        # Leave 8 pts below the line so data-row numbers (cap-height ~5.6 pt) clear it
        self.y = line_y - 8
        for i, row in enumerate(rows):
            bold = bold_last and (i == len(rows) - 1)
            fn   = "Helvetica-Bold" if bold else "Helvetica"
            col  = (0, 60, 0) if bold else (0, 0, 0)
            self._table_row(row, col_x, col_w, font=fn, color=col)
        self.gap(2)
        if caption_text:
            self.caption(caption_text)

    def _table_row(self, cells, col_x, col_w,
                   font="Helvetica", color=(0, 0, 0)):
        wrapped = []
        max_ln  = 1
        for cell, w in zip(cells, col_w):
            lns = textwrap.wrap(str(cell), _cols(FS_CAPTION, w - 4))
            if not lns:
                lns = [""]
            wrapped.append(lns)
            max_ln = max(max_ln, len(lns))
        row_h  = max_ln * FS_CAPTION * LEAD + 2
        self._check(row_h + 2)
        base_y = self.y
        for lns, x in zip(wrapped, col_x):
            ly = base_y
            for ln in lns:
                self._raw_text(ln, x + 2, ly, font, FS_CAPTION, color)
                ly -= FS_CAPTION * LEAD
        self.y -= row_h

    def save(self, path):
        self._draw_footer()
        pdfium_r.FPDFPage_GenerateContent(self._pg.raw)
        self.doc.save(path)
        print(f"Saved → {path}  ({self._pg_num} pages)")


# =============================================================================
# Document content
# =============================================================================

def build(out_path):
    w = Writer()

    # =========================================================================
    # TITLE PAGE
    # =========================================================================
    w.gap(30)
    for ln in textwrap.wrap(
            "BBFlow: Learning Conformational Ensembles of Proteins "
            "Based on Backbone Geometry", _cols(FS_TITLE, TW)):
        w.line(ln, "Helvetica-Bold", FS_TITLE, (0, 30, 100), center=True)

    w.gap(6)
    w.line("A Comprehensive Technical Survey",
           "Helvetica-Oblique", FS_SUBSEC, (60, 60, 60), center=True)
    w.gap(10)
    w.rule(100, 140, 200)
    w.gap(6)

    for ln in [
        "Nicolas Wolf*  ·  Leif Seute*  ·  Vsevolod Viliuga  ·  Simon Wagner",
        "Jan Stühmer  ·  Frauke Gräter",
    ]:
        w.line(ln, "Helvetica", FS_BODY + 0.5, (20, 20, 20), center=True)
    w.gap(5)
    for ln in [
        "* Equal contribution",
        "Max Planck Institute for Polymer Research  ·  Heidelberg Institute for Theoretical Studies",
        "IWR, Heidelberg University  ·  SciLifeLab Stockholm  ·  KIT Karlsruhe",
    ]:
        w.line(ln, "Helvetica-Oblique", FS_SMALL, (90, 90, 90), center=True)
    w.gap(5)
    w.line("arXiv:2503.05738v2  —  NeurIPS 2025",
           "Helvetica-Oblique", FS_SMALL, (120, 70, 0), center=True)
    w.gap(12)
    w.rule(100, 140, 200)
    w.gap(8)

    w.line("Abstract", "Helvetica-Bold", FS_SUBSEC, (0, 40, 120), center=True)
    w.gap(4)
    w.wrap(
        "Proteins are dynamic entities whose biological function is governed by the ensemble "
        "of conformations they adopt at thermal equilibrium. Molecular Dynamics (MD) simulation "
        "provides the rigorous route to sampling this Boltzmann distribution, but at computational "
        "costs that often make large-scale application infeasible. Recent deep generative approaches "
        "emulate MD by learning from trajectory data, yet the dominant paradigm fine-tunes large "
        "pre-trained folding models (AlphaFold 2, ESMFold) and consumes evolutionary sequence "
        "information from Multiple Sequence Alignments (MSAs), limiting applicability to natural "
        "proteins and incurring prohibitive inference costs. "
        "This document provides a comprehensive technical exposition of BBFlow, a conditional "
        "SE(3) flow-matching model that generates MD-like protein backbone conformational ensembles "
        "from the equilibrium backbone structure alone — without MSAs, language-model embeddings, "
        "or pre-trained folding weights. Two key innovations drive the method: (1) a geometric "
        "encoding of the equilibrium structure as invariant pairwise distances and equivariant "
        "local directions, and (2) a conditional prior distribution on SE(3)^N based on geodesic "
        "interpolation toward the equilibrium structure. BBFlow achieves 41× speedup over the "
        "best accuracy-comparable baseline (AlphaFlow-T), generalises to de novo proteins and "
        "multi-chain complexes without modification, and was trained from scratch in three GPU-days.",
        "Helvetica-Oblique", FS_BODY, (20, 20, 20), indent=20, width=TW - 40, after=6)
    w.rule(100, 140, 200)

    # =========================================================================
    # 1. INTRODUCTION
    # =========================================================================
    w.section_break()
    w.heading1("1", "Introduction")

    w.para(
        "The determination of protein structure has been one of the defining scientific challenges "
        "of the past century. The advent of AlphaFold 2 and related methods has largely resolved "
        "the static structure prediction problem: given an amino-acid sequence, an accurate "
        "equilibrium structure can now be predicted in seconds. However, protein function does not "
        "reside in a single static conformation. Enzymes use induced-fit and conformational "
        "selection to bind substrates; allosteric proteins communicate regulatory signals via "
        "long-range correlated motions; intrinsically disordered regions adopt transient structure "
        "upon binding partners. In each case it is the ensemble of accessible conformations — "
        "and the free-energy landscape connecting them — that encodes biological activity."
    )
    w.para(
        "Molecular Dynamics (MD) simulation integrates Newton's equations of motion for all atoms, "
        "sampling from the Boltzmann distribution at fixed temperature and pressure. Although MD is "
        "physically rigorous, covering the conformational state space exhaustively requires long "
        "simulation times (microseconds to seconds for biologically relevant transitions), while "
        "each integration step is on the order of femtoseconds. A typical soluble protein of ~300 "
        "residues requires hundreds of CPU-hours per 100 ns trajectory. Three 100-ns trajectories "
        "per protein — the ATLAS benchmark standard — cost roughly 300 CPU-hours per protein, "
        "making large-scale screening computationally prohibitive."
    )
    w.para(
        "Recent machine-learning MD emulators address this gap by training generative models on "
        "pre-computed trajectory data and generating new conformations at inference without "
        "simulating physics. The dominant strategy repurposes protein folding architectures: "
        "AlphaFlow fine-tunes AlphaFold 2, ConfDiff uses AlphaFold 2's Evoformer representation, "
        "and BioEmu builds an AlphaFold-like model trained on heterogeneous trajectory data. "
        "While accurate, these approaches are slow (MSA computation or Evoformer processing), "
        "potentially biased toward natural proteins for which evolutionary data is abundant, and "
        "inapplicable to de novo designed proteins that lack evolutionary history."
    )

    w.heading2("1.1", "Main Contributions of BBFlow")
    w.bullet(
        "Geometry-only conditioning. The equilibrium backbone structure x_eq encodes the fold "
        "as invariant pairwise Cα distances and equivariant local directions — no MSA, no "
        "language-model embedding, no pre-trained weights required."
    )
    w.bullet(
        "Conditional prior via geodesic interpolation. Rather than starting ODE integration "
        "from unconditioned noise, BBFlow samples x₀ by geodesically interpolating 20% of the "
        "way from random noise toward x_eq on SE(3)^N, providing the correct fold topology as "
        "a starting point."
    )
    w.bullet(
        "State-of-the-art speed/accuracy trade-off. 41× faster than AlphaFlow-T at comparable "
        "or superior accuracy across five of six standard ensemble metrics on the ATLAS benchmark."
    )
    w.bullet(
        "Generalisation to de novo proteins. No degradation on proteins with no evolutionary "
        "history, unlike AlphaFlow (no templates) whose RMSF correlation collapses from 0.86 to 0.47."
    )
    w.bullet(
        "First ensemble model for multi-chain proteins. Omitting residue-index features and "
        "conditioning purely on geometry enables zero-shot transfer from monomers to dimers and "
        "trimers — a setting no prior model had addressed."
    )
    w.bullet(
        "Trained from scratch. No pre-trained folding weights; 3 GPU-days on 2× NVIDIA A100-40 GB, "
        "18.2 M parameters — orders of magnitude lighter than AlphaFold 2 (93 M parameters, "
        "months of training on PDB + UniRef)."
    )

    # =========================================================================
    # 2. BACKGROUND
    # =========================================================================
    w.section_break()
    w.heading1("2", "Background and Prerequisite Concepts")

    w.heading2("2.1", "Protein Structure: Backbone Frames on SE(3)^N")
    w.para(
        "A protein is a polypeptide chain of N amino-acid residues drawn from an alphabet of "
        "20 genetically encoded types. Adjacent residues are covalently linked by peptide bonds, "
        "forming a backbone of repeating N–Cα–C units. The local geometry is described by the "
        "dihedral angles φ (rotation around N–Cα) and ψ (rotation around Cα–C); the ω angle "
        "(rotation around C–N) is approximately fixed at 180° due to resonance. Allowed (φ, ψ) "
        "regions define the Ramachandran plot, with α-helices near (−60°, −45°) and β-strands "
        "near (−120°, +120°)."
    )
    w.para(
        "In the frame-based representation introduced by AlphaFold 2, each residue i is assigned "
        "a local coordinate frame constructed from the N, Cα, C atom positions via the "
        "Gram–Schmidt process:"
    )
    w.eq("1", r"T_i = (R_i, z_i) \in SE(3),\quad R_i \in SO(3),\quad z_i \in \mathbb{R}^3\;(C_\alpha\;\mathrm{position})")
    w.para("The complete backbone of a protein with N residues is the ordered tuple:")
    w.eq("2", r"x = (T_1, T_2, \ldots, T_N) \in SE(3)^N")
    w.para(
        "a point on the 6N-dimensional Riemannian product manifold M ≡ SE(3)^N. The frame "
        "representation is coordinate-free (relative geometry is read from T_i⁻¹T_j without "
        "a global frame), supports geometrically meaningful interpolation via geodesics, and "
        "provides a natural basis for equivariant message-passing."
    )

    w.heading2("2.2", "Conformational Ensembles and the Boltzmann Distribution")
    w.para(
        "At thermodynamic equilibrium, the probability of observing a protein in conformation x "
        "is governed by the Boltzmann distribution:"
    )
    w.eq("3", r"p(x) \propto \exp\!\left(-\frac{E(x)}{k_B T}\right)")
    w.para(
        "where E(x) is the potential energy, k_B is Boltzmann's constant, and T is absolute "
        "temperature. The free-energy landscape F(x) = −k_BT ln p(x) encodes both equilibrium "
        "thermodynamics and kinetics: local minima are metastable states, barriers determine "
        "transition rates, and the width of a basin determines flexibility. The conformational "
        "ensemble is the set of conformations weighted by p(x). Thermodynamic quantities — "
        "free energies, entropies, binding affinities — are expectations under this distribution "
        "and cannot be obtained from a single static structure alone."
    )

    w.heading2("2.3", "Molecular Dynamics Simulation")
    w.para("MD numerically integrates Newton's equations for all n atoms:")
    w.eq("4", r"m_k \ddot{r}_k = -\nabla_{r_k} E(r_1, \ldots, r_n),\quad \text{for all } k")
    w.para(
        "using a molecular force field — an empirically parameterised potential combining bonded "
        "terms (harmonic bonds, angles, periodic dihedrals) and non-bonded terms (Lennard-Jones "
        "van der Waals, Coulomb electrostatics). The ATLAS dataset used to benchmark BBFlow was "
        "generated with GROMACS using the CHARMM36m force field and explicit TIP3P water at 310 K. "
        "At a 2-fs integration timestep, 100 ns of simulation requires 5 × 10⁷ force evaluations. "
        "For a 300-residue protein in explicit solvent (~30,000 atoms) this costs ~100 CPU-hours, "
        "placing whole-proteome ensemble annotation far beyond current budgets."
    )
    w.para(
        "Short-timescale MD (100–300 ns) is insufficient for large-scale conformational transitions "
        "(folding, allosteric switching) but captures: (i) local backbone and side-chain flexibility; "
        "(ii) binding-site plasticity relevant to drug design; (iii) correlated motions underlying "
        "allosteric communication; (iv) secondary-structure fraying. These are the properties "
        "BBFlow targets."
    )

    w.heading2("2.4", "The Lie Groups SO(3) and SE(3)")
    w.para(
        "SO(3) is the group of 3×3 rotation matrices with unit determinant. SE(3) is the "
        "semidirect product of SO(3) with R³ — the group of rigid-body motions:"
    )
    w.eq("5", r"SE(3) = SO(3) \ltimes \mathbb{R}^3,\quad (R_1,z_1)\cdot(R_2,z_2) = (R_1 R_2,\; z_1 + R_1 z_2)")
    w.para(
        "A Riemannian metric on SE(3)^N is needed to define geodesics and tangent vectors for "
        "flow matching. Following FrameFlow (Yim et al., 2023), the metric is a product: the "
        "rotation part uses the bi-invariant trace metric on so(3), and the translation part "
        "uses the standard Euclidean metric. Geodesics on SE(3)^N decompose per-residue into "
        "independent rotation and translation geodesics. The geodesic from R₀ to R₁ at "
        "interpolation fraction t is:"
    )
    w.eq("6", r"R_t = R_0 \cdot \exp\!\left(t\,\log(R_0^\top R_1)\right)")
    w.para(
        "where R₀^T denotes the transpose. The tangent vector at R_t pointing toward R₁ is "
        "Log_{R_t}(R₁) = R_t log(R_t^T R₁). For translations the geodesic is the straight "
        "line  z_t = (1−t)z₀ + t z₁  with constant tangent  z₁ − z₀."
    )

    w.heading2("2.5", "SE(3)-Equivariance in Neural Networks")
    w.para(
        "A function f is G-equivariant if applying the group action g before f equals applying "
        "the corresponding transformed output after:"
    )
    w.eq("7", r"f(\rho_{\mathrm{in}}(g) \cdot x) = \rho_{\mathrm{out}}(g) \cdot f(x)\quad \forall g \in G,\; x \in \mathcal{X}")
    w.para(
        "For molecular geometry, G = SE(3). Physical observables must be invariant or covariant "
        "under global rotations and translations — there is no privileged coordinate frame in "
        "space. Key SE(3)-equivariant architectures include Tensor Field Networks "
        "(Thomas et al., 2018), SE(3)-Transformers (Fuchs et al., 2020), E(n) Equivariant GNNs "
        "(Satorras et al., 2021), and Frame Averaging (Puny et al., 2022). BBFlow builds on the "
        "GAFL architecture, which achieves equivariance via Clifford Frame Attention on SE(3) "
        "backbone frames."
    )

    w.heading2("2.6", "Transformer Self-Attention and Invariant Point Attention")
    w.para(
        "The transformer (Vaswani et al., 2017) processes token embeddings {h_i} ∈ R^d "
        "via scaled dot-product self-attention:"
    )
    w.eq("8", r"\mathrm{Attention}(Q,K,V) = \mathrm{softmax}\left(\frac{QK^\top}{\sqrt{d_k}}\right)V")
    w.para(
        "where Q = HW_Q, K = HW_K, V = HW_V are linear projections. The query q_i encodes "
        "what residue i seeks; key k_j encodes what residue j provides; value v_j carries "
        "the information transferred when attention is high."
    )
    w.para(
        "Invariant Point Attention (IPA), introduced in AlphaFold 2, extends scalar attention "
        "to 3D geometry. Each residue learns local 3D query and key points projected to global "
        "coordinates via the residue frame T_i. The attention logits include squared Euclidean "
        "distances between global query and key points — invariant to global SE(3) "
        "transformations. Output points are rotated back into local frames, making IPA as a "
        "whole SE(3)-equivariant. IPA is the core architectural primitive for FrameDiff, "
        "FrameFlow, GAFL, and BBFlow."
    )

    w.heading2("2.7", "Clifford Frame Attention (CFA)")
    w.para(
        "GAFL (Wagner et al., NeurIPS 2024) extends IPA to Clifford Frame Attention (CFA), "
        "representing geometric features — points, lines, planes, and rigid frames — as "
        "elements of the projective geometric algebra (PGA) G(R^{3,0,1}). In PGA, grade-0 "
        "elements are scalars, grade-1 are planes, grade-2 are lines, grade-3 are points, "
        "and motors (even subalgebra elements) encode rigid-body motions as sandwich products: "
        "p' = M p M_rev  (where M_rev is the reverse of motor M)."
    )
    w.para(
        "In CFA, residue frames T_i are represented as motors M_i. Edge features between "
        "residues i and j are multivectors constructed from the relative motor M_i⁻¹M_j. "
        "Messages between residues use bilinear products of the algebra (outer, inner, geometric "
        "product), enabling higher-order geometric interactions beyond scalar inner products. "
        "This is the architecture inherited by BBFlow's flow vector-field network."
    )

    w.heading2("2.8", "Flow Matching on Riemannian Manifolds")
    w.para(
        "Flow matching (Lipman et al., ICLR 2023; Chen & Lipman, ICLR 2024) learns a "
        "time-dependent vector field v_θ : M×[0,1] → TM that transports samples from a "
        "prior p₀ to the data distribution p₁ via an ODE:"
    )
    w.eq("9", r"\frac{dx_t}{dt} = v_\theta(x_t, t),\qquad x_0 \sim p_0")
    w.para(
        "Training is made tractable by conditional flow matching (CFM): connect individual data "
        "pairs (x₀, x₁) by a simple conditional path ψ(x₀, x₁, t), compute the conditional "
        "vector field u_t analytically, and regress:"
    )
    w.eq("10", r"\mathcal{L}_{\mathrm{FM}} = \mathbb{E}\left[\|v_\theta(x_t, t) - u_t\|^2\right],\quad x_t = \psi(x_0, x_1, t)")
    w.para(
        "The conditional and marginal losses share the same gradient, so minimising the "
        "conditional loss yields the correct marginal vector field. On manifolds M, straight "
        "paths are replaced by geodesics γ(x₀, x₁, t) and u_t is the geodesic velocity. "
        "On SE(3)^N the ground-truth conditional vector fields are:"
    )
    w.eq("11", r"v_{SO(3)}(R_t, t \mid R_1) = \frac{\mathrm{Log}_{R_t}(R_1)}{1-t}")
    w.eq("12", r"v_{\mathbb{R}^3}(z_t, t \mid z_1) = \frac{z_1 - z_t}{1-t}")
    w.para(
        "Key advantages over diffusion: (i) straight geodesic paths allow accurate ODE "
        "integration in as few as 20 steps (vs. 50–1000 for diffusion); (ii) no Gaussian "
        "prior requirement — any p₀ can be used, enabling BBFlow's conditional prior; "
        "(iii) the Riemannian extension is analytically cleaner than heat-kernel diffusion."
    )

    # =========================================================================
    # 3. PRIOR WORK
    # =========================================================================
    w.section_break()
    w.heading1("3", "Prior Work: Approaches to Conformational Ensemble Generation")

    w.heading2("3.1", "Classical and Semi-Classical Methods")
    w.heading3("Molecular Dynamics (Gold Standard)")
    w.para(
        "MD is physically rigorous and requires no training data. Its primary limitation is "
        "cost: O(10⁴–10⁶) CPU-hours per protein for trajectories long enough to capture "
        "biologically relevant transitions. Even short-timescale MD (100–300 ns) costs "
        "~100–300 CPU-hours per protein, making proteome-scale screening impractical."
    )

    w.heading3("Normal Mode Analysis (NMA, Case 1994)")
    w.para(
        "NMA approximates the energy surface near equilibrium as a quadratic and analytically "
        "computes normal modes — directions of concerted motion with definite frequencies. "
        "NMA is extremely fast (minutes per protein) but is a linear approximation that "
        "systematically underestimates ensemble spread and cannot capture anharmonic or "
        "large-amplitude motions. Benchmarks show NMA consistently worse than all generative "
        "baselines on ATLAS metrics."
    )

    w.heading3("MSA Subsampling (Wayment-Steele et al., Nature 2024)")
    w.para(
        "By running AlphaFold 2 with different MSA subsets, one can coax alternative "
        "conformations. This is powerful for proteins whose conformational substates are "
        "encoded in evolutionary variation, but is limited to proteins with rich MSA coverage "
        "and cannot sample thermally accessible states not reflected in sequence variation. "
        "It also inherits the full cost of MSA construction and AlphaFold 2 inference."
    )

    w.heading2("3.2", "Boltzmann Generators (Noé et al., Science 2019)")
    w.para(
        "Boltzmann Generators (BGs) train normalising flows to map a Gaussian latent space "
        "directly to the Boltzmann distribution p(x) ∝ exp(−E(x)/k_BT), combining maximum "
        "likelihood on MD samples with physics-based free-energy minimisation. BGs can in "
        "principle sample thermodynamically equilibrated configurations including rare states "
        "not visited by short MD."
    )
    w.para(
        "Critical limitation: BGs must be trained per protein. The normalising flow is fitted "
        "to the specific energy landscape of one molecule and is not transferable. A model "
        "trained on ubiquitin cannot generate ensembles for lysozyme without retraining. "
        "This severely limits practical utility for screening — each new target requires a "
        "fresh training run with sufficient MD data."
    )

    w.heading2("3.3", "AlphaFlow: AlphaFold-Based Ensemble Generation (Jing et al., ICML 2024)")
    w.para(
        "AlphaFlow proposed the first transferable protein ensemble generation model by "
        "reformulating ensemble generation as a structure denoising task within AlphaFold 2. "
        "Four variants are published:"
    )
    w.bullet(
        "AlphaFlow (no templates). Pre-trained AlphaFold 2 is fine-tuned on ATLAS trajectory "
        "data. At inference the model predicts a conformation from sequence + MSA, starting "
        "from a noisy structure. MSA computation is required per sequence. Time: 32.0 s/conf."
    )
    w.bullet(
        "AlphaFlow-T (with templates). The equilibrium structure x_eq is provided as a "
        "template to AlphaFold's template processing module, substantially improving accuracy. "
        "A full AlphaFold forward pass is required at each of the 10 flow timesteps. "
        "Time: 32.6 s/conf."
    )
    w.bullet(
        "ESMFlow-T. Uses ESMFold protein language model (PLM) embeddings instead of the "
        "MSA-based Evoformer, avoiding per-sequence MSA computation but still depending on PLM "
        "weights trained on natural proteins. Time: 11.2 s/conf."
    )
    w.bullet(
        "Distilled variants (AlphaFlow-T_dist, AlphaFlow-T_12L,dist). Consistency distillation "
        "reduces timesteps from 10 to 1; the 12-layer variant also shrinks depth. "
        "Times: 3.3 s and 1.2 s/conf respectively, at reduced accuracy."
    )
    w.para(
        "Core limitations: (1) evolutionary-information dependency — even AlphaFlow-T uses MSA "
        "or PLM embeddings unavailable for de novo proteins; (2) inference cost — 32.6 s/conf; "
        "(3) over-stabilisation — AlphaFlow-T predicts median RMSF 1.17 Å vs. MD reference "
        "1.48 Å, systematically under-exploring conformational space; (4) single-chain only."
    )

    w.heading2("3.4", "ConfDiff: Force-Guided SE(3) Diffusion (Wang et al., ICML 2024)")
    w.para(
        "ConfDiff replaces AlphaFold 2's structure module with an SE(3) diffusion model "
        "conditioned on the pre-trained Evoformer embedding of the input sequence, optionally "
        "augmented with a force-field energy guidance signal. The energy guidance improves "
        "physical plausibility of generated conformations. Like AlphaFlow, ConfDiff requires "
        "the Evoformer (hence MSA), has inference time 20.2 s/conf, and underperforms "
        "AlphaFlow-T on ATLAS metrics in most categories."
    )

    w.heading2("3.5", "BioEmu: Scalable Equilibrium Ensemble Emulation (Lewis et al., Science 2025)")
    w.para(
        "BioEmu trains an AlphaFold-like model on a large heterogeneous dataset of MDs of "
        "varying lengths and temperatures plus NMR and crystallographic ensemble data. "
        "It targets general equilibrium ensembles — including rare alternative folded states — "
        "rather than the specific distribution induced by a fixed MD protocol. Because it is "
        "not trained to reproduce the ATLAS distribution, it performs unfavourably on the ATLAS "
        "benchmark (RMSF MAE 1.29 Å vs. BBFlow's 0.42 Å), though this is expected given the "
        "mismatch in training objectives. BioEmu still relies on MSA and an AlphaFold-like "
        "architecture with inference time 1.9 s/conf."
    )

    w.heading2("3.6", "MDGen: Time-Consistent All-Atom Trajectories (Jing et al., NeurIPS 2024)")
    w.para(
        "MDGen models the joint distribution over consecutive MD frames rather than independent "
        "snapshots, generating time-consistent all-atom trajectories in a token-based discrete "
        "architecture. Although fast (0.15 s/conf) and trained on ATLAS, MDGen achieves "
        "substantially lower ensemble accuracy than BBFlow: RMSF MAE 0.81 vs. 0.42 Å; "
        "DCCM correlation 0.54 vs. 0.87."
    )

    w.heading2("3.7", "The Gap BBFlow Addresses")
    w.para(
        "Surveying prior work reveals four simultaneous limitations that no existing method solves:"
    )
    w.bullet("Accurate but slow: AlphaFlow-T reaches RMSF r = 0.92 but requires 32.6 s/conf and MSA.")
    w.bullet("Fast but inaccurate: AlphaFlow-T_12L,dist (1.2 s) and BioEmu (1.9 s) sacrifice quality.")
    w.bullet("No multi-chain support: residue-index features in all prior models prevent application to protein complexes.")
    w.bullet("Evolutionary-information dependency: all accurate models fail for de novo proteins lacking MSA coverage.")
    w.para(
        "BBFlow addresses all four simultaneously by conditioning on backbone geometry rather "
        "than sequence, introducing a conditional prior that reduces the flow's learning burden, "
        "and omitting residue-index features to enable geometry-only chain-agnostic inference."
    )

    # =========================================================================
    # 4. METHOD
    # =========================================================================
    w.section_break()
    w.heading1("4", "BBFlow: Method")

    w.heading2("4.1", "Problem Formulation")
    w.para(
        "BBFlow models the conformational ensemble as the conditional distribution p(x | x_eq), "
        "where x ∈ SE(3)^N is a backbone conformation and x_eq ∈ SE(3)^N is the equilibrium "
        "backbone structure. This formulation is natural for MD emulation since MD itself also "
        "requires an initial (equilibrium) structure. Conditioning on x_eq rather than the "
        "sequence encodes the fold identity without requiring evolutionary data."
    )
    w.eq("13", r"x \sim p(x \mid x_{\mathrm{eq}}) \approx \phi_1(x_0;\, x_{\mathrm{eq}}),\quad x_0 \sim p_0(\cdot \mid x_{\mathrm{eq}})")
    w.para(
        "where φ₁ is the flow endpoint (t = 1 solution of the ODE starting from x₀) and "
        "p₀(· | x_eq) is the novel conditional prior described in Section 4.4."
    )

    w.heading2("4.2", "Conditional Flow Matching for Ensemble Generation")
    w.para(
        "Extending the flow ODE to include the conditioning signal x_eq, BBFlow learns:"
    )
    w.eq("14", r"v(x, t, x_{\mathrm{eq}}) : \mathcal{M} \times [0,1] \times \mathcal{M}_{\mathrm{eq}} \to T_x \mathcal{M}")
    w.para("defining the conditional flow φ_t(· | x_eq) via:")
    w.eq("15", r"\frac{d}{dt}\phi_t(x \mid x_{\mathrm{eq}}) = v(\phi_t, t, x_{\mathrm{eq}}),\quad \phi_0(x \mid x_{\mathrm{eq}}) = x")
    w.para("The conditional training loss is:")
    w.eq("16", r"\mathcal{L}_{\mathrm{FM}} = \mathbb{E}\!\left[\left\|v - \hat{v}(x_t, t, x_{\mathrm{eq}})\right\|^2_{SE(3)}\right]")
    w.para(
        "The expectation is over t ~ U(0,1), (x₁, x_eq) ~ p_data, x₀ ~ p₀(· | x_eq), "
        "x_t = γ(x₀, x₁, t) (geodesic interpolation), and v is the ground-truth conditional "
        "vector field from Equations (11)–(12). The SE(3) norm decomposes as:"
    )
    w.eq("17", r"\|v\|^2_{SE(3)} = \frac{1}{2}\mathrm{Tr}(v_r v_r^\top) + \|v_z\|^2")
    w.para(
        "measuring rotational and translational components independently. The network predicts "
        "x̂₁ = x̂_θ(x_t, t, x_eq) and the predicted field v̂ is recovered from x̂₁ via "
        "Equations (11)–(12)."
    )

    w.heading2("4.3", "Encoding the Equilibrium Structure")
    w.para(
        "The equilibrium structure x_eq = {(R_i^eq, z_i^eq)} is encoded as initial edge "
        "features of the message-passing network via two complementary representations."
    )
    w.heading3("Distance encoding")
    w.para(
        "Inspired by the interpretation of evolutionary co-variation as a learned contact map, "
        "pairwise Cα–Cα distances are binned into 22 uniform bins spanning [0, 20] Å:"
    )
    w.eq("18", r"s_{ij} = \mathrm{bin}\left(\|z_i^{\mathrm{eq}} - z_j^{\mathrm{eq}}\|_2\right) \in \mathbb{R}^{22}")
    w.para(
        "This 22-dimensional one-hot edge feature is invariant to global rigid-body "
        "transformations and provides coarse fold topology information analogous to a contact map."
    )
    w.heading3("Direction encoding")
    w.para(
        "For residue pairs within 5 Å, the unit vector from residue i to residue j is expressed "
        "in the local co-rotating frame of residue i:"
    )
    w.eq("19", r"e_{ij} = (R_i^{\mathrm{eq}})^{-1} \cdot \frac{z_i^{\mathrm{eq}} - z_j^{\mathrm{eq}}}{\|z_i^{\mathrm{eq}} - z_j^{\mathrm{eq}}\|_2} \in \mathbb{R}^3")
    w.para(
        "Transforming into the local frame makes the direction components invariant to global "
        "rotations. Together with s_ij, this provides geometrically richer information analogous "
        "to equivariant tensor-network features, enabling better discrimination of local "
        "structural context."
    )
    w.heading3("Amino-acid identity")
    w.para(
        "A 20-dimensional one-hot encoding of residue type is projected to a 128-dimensional "
        "node embedding by a linear layer. This encodes local backbone degrees of freedom "
        "(proline is rigid, glycine is highly flexible) without providing global sequence context. "
        "An ablation (Section 7) shows the model remains competitive even without amino-acid "
        "identity, demonstrating that backbone geometry alone suffices."
    )

    w.heading2("4.4", "Conditional Prior Distribution")
    w.para(
        "Standard flow matching uses an unconditional prior: Gaussian translations and uniform "
        "rotations. The flow must then assemble a coherent fold from complete noise — a "
        "challenging task that increases variance. BBFlow introduces a conditional prior "
        "p₀(· | x_eq) based on geodesic interpolation on SE(3)^N:"
    )
    w.eq("20", r"x_{\mathrm{uncond}} \sim p_{\mathrm{uncond}},\qquad x_0 = \gamma(x_{\mathrm{uncond}},\, x_{\mathrm{eq}},\, \xi)")
    w.para(
        "where γ is the product geodesic on SE(3)^N (factoring per-residue into rotation and "
        "translation geodesics) and ξ ∈ (0,1) is a hyperparameter:"
    )
    w.eq("21", r"\gamma(x_{\mathrm{uncond}}, x_{\mathrm{eq}}, 0) = x_{\mathrm{uncond}},\quad \gamma(x_{\mathrm{uncond}}, x_{\mathrm{eq}}, 1) = x_{\mathrm{eq}}")
    w.para(
        "At ξ = 0.2 (used in all main experiments), the prior sample is 20% of the geodesic "
        "distance toward the equilibrium structure — the backbone topology is approximately "
        "correct, but with enough noise diversity to generate varied conformations. This is a "
        "principled generalisation of partial denoising from diffusion models to the manifold "
        "flow matching framework. An ablation study of ξ (Section 7.2) confirms that ξ = 0.2 "
        "optimally balances accuracy and ensemble diversity."
    )

    w.heading2("4.5", "Network Architecture")
    w.para(
        "The vector field network v̂_θ(x_t, t, x_eq) is adapted from GAFL (Wagner et al., "
        "NeurIPS 2024), itself an extension of FrameDiff (Yim et al., ICML 2023) and "
        "FrameFlow (Yim et al., 2023). Six CFA message-passing blocks iteratively update "
        "node features, edge features, and backbone frames. Each block: "
        "(1) computes geometric messages between all residue pairs using Clifford Frame "
        "Attention; (2) aggregates messages to update node features; (3) predicts an "
        "incremental frame update; (4) updates edge features from new node features and "
        "inter-frame geometry."
    )
    w.para(
        "Inputs: current frames {(R_i^t, z_i^t)}, flow time t, amino-acid identity embeddings, "
        "and — as initial edge features — equilibrium distance s_ij^eq (22 dims), equilibrium "
        "direction e_ij (3 dims), and current pairwise distance s_ij^t (22 dims). This expands "
        "the edge feature dimension by 25 relative to the unconditional GAFL baseline."
    )
    w.para(
        "Critical design choice — omitting residue indices: Unlike AlphaFold 2, FrameDiff, "
        "FrameFlow, and AlphaFlow, BBFlow does not use absolute residue indices as node "
        "features. This (1) reduces the risk of per-residue memorisation from training data; "
        "(2) makes the architecture agnostic to chain identity, enabling zero-shot transfer "
        "from monomers to multi-chain complexes. The ablation confirms that adding residue "
        "indices does not improve accuracy on monomers but causes failure on multi-chain proteins."
    )
    w.para(
        "BBFlow has ~18.2 M learnable parameters and was trained for 3 days on two NVIDIA "
        "A100-40 GB GPUs, starting from random initialisation (no pre-trained folding weights). "
        "BBFlow-light (3 CFA blocks, feature dims 96/48) has 2.5 M parameters and achieves "
        "~200× speedup over AlphaFlow at modestly reduced accuracy."
    )

    w.heading2("4.6", "Training Algorithm")
    w.para(
        "At each training step: (1) sample (x_eq, x₁) from ATLAS; "
        "(2) sample x₀ ~ p₀(·|x_eq) via geodesic interpolation with ξ = 0.2; "
        "(3) sample t ~ U(0,1); "
        "(4) compute x_t = γ(x₀, x₁, t); "
        "(5) compute ground-truth vector field v from Eqs. (11)–(12); "
        "(6) compute x̂₁ = x̂_θ(x_t, t, x_eq) and predicted field v̂; "
        "(7) update θ to minimise ℒ = ‖v − v̂‖²_{SE(3)} + ℒ_aux(x₁, x̂₁), "
        "where ℒ_aux (from FrameFlow) regresses directly on x₁ and accelerates convergence."
    )

    w.heading2("4.7", "Inference")
    w.para(
        "Given x_eq: (1) sample x_uncond ~ p_uncond; (2) compute x₀ = γ(x_uncond, x_eq, 0.2); "
        "(3) integrate the conditional flow ODE using 20 Euler steps on SE(3)^N (per-residue "
        "rotation update via exponential map + translation update); (4) endpoint x₁ = "
        "φ₁(x₀ | x_eq) is one independent conformation sample from p(x | x_eq). "
        "Repeat steps 1–4 for each desired conformation (all samples are independent given x_eq). "
        "Using only 20 steps — vs. 50–1000 for diffusion — is possible because flow-matching "
        "trajectories are nearly straight geodesics."
    )

    # =========================================================================
    # 5. EXPERIMENTAL SETUP
    # =========================================================================
    w.gap(14)
    w.heading1("5", "Experimental Setup")

    w.heading2("5.1", "ATLAS Dataset")
    w.para(
        "ATLAS (Vander Meersche et al., Nucleic Acids Research 2024) provides standardised "
        "all-atom MD trajectories for 1390 structurally diverse monomeric proteins from the "
        "Protein Data Bank. Each protein has three independent 100-ns simulations at 310 K, "
        "CHARMM36m force field, explicit TIP3P water, GROMACS engine. Standardised conditions "
        "make ensemble metrics comparable across proteins and models — a key requirement for "
        "benchmarking. The same training/validation/test split as AlphaFlow is used: "
        "1265 / 39 / 82 proteins. 250 conformations are generated per protein for evaluation."
    )

    w.heading2("5.2", "De Novo Protein Dataset")
    w.para(
        "To evaluate generalisation beyond natural proteins, 50 de novo proteins were generated "
        "with RFdiffusion and FrameFlow, each subjected to three 100-ns MD simulations following "
        "the ATLAS protocol. Equilibrium structures were obtained with ESMFold (the only folding "
        "model without an MSA requirement). This dataset is challenging because all MSA-dependent "
        "baselines face a near-zero evolutionary signal."
    )

    w.heading2("5.3", "Multi-Chain Systems")
    w.para(
        "Five well-studied complexes were simulated: barnase–barstar dimer (1BGS), homotrimeric "
        "foldon (1RFO), homodimeric fructokinase (5EY7), nanobody–SARS-CoV-2 RBD heterodimer "
        "(7KGK), and nanobody–TNFRSF17 heterodimer (8HXR). Total residues range from 80 to 590. "
        "BBFlow was applied without any modification despite being trained only on monomers."
    )

    w.heading2("5.4", "Evaluation Metrics")
    w.para(
        "All metrics use Cα atoms after superimposition to the equilibrium structure. "
        "MD bootstrapping (100 replicates) estimates uncertainty in MD-derived statistics."
    )
    w.bullet(
        "RMSF (Root Mean Square Fluctuation): per-residue Cα deviation magnitude. "
        "Reported: Pearson correlation r (profile shape), MAE (amplitude accuracy), "
        "and median RMSF (over/under-stabilisation; MD reference = 1.48 Å on ATLAS)."
    )
    w.bullet(
        "Pairwise RMSD (pwRMSD): mean Cα RMSD across all conformation pairs, "
        "quantifying ensemble spread without a reference state. Reported: MAE vs. MD."
    )
    w.bullet(
        "DCCM (Dynamic Cross-Correlation Matrix): DCCM_ij = normalised covariance of Cα "
        "displacements for residues i, j. Values +1 / −1 / 0 indicate correlated / "
        "anti-correlated / uncorrelated motion. Reported: Pearson r of flattened matrix."
    )
    w.bullet(
        "PCA Wasserstein-2 (W₂): generated and MD conformations projected onto the first two "
        "MD principal components; W₂ distance between the resulting 2D distributions."
    )
    w.bullet(
        "Transient contact Jaccard (J_tr): Jaccard similarity between transient contact sets "
        "(pairs separated > 8 Å in x_eq but < 8 Å in ≥ 10% of ensemble conformations) "
        "for MD vs. generated ensembles."
    )

    # =========================================================================
    # 6. RESULTS
    # =========================================================================
    w.gap(14)
    w.heading1("6", "Results")

    w.heading2("6.1", "ATLAS Benchmark")
    w.para(
        "Table 1 — ATLAS test set (82 proteins). Median over proteins. "
        "RMSF Median: MD reference = 1.48 Å. Inference time: protein 7c45A (302 residues), "
        "NVIDIA A100-80 GB. (↑) higher is better, (↓) lower is better."
    )
    cx1 = [ML, ML+90, ML+142, ML+194, ML+244, ML+296, ML+348, ML+395]
    cw1 = [90,    52,     52,     50,     52,     52,     47,     70]
    w.table(
        ["Method", "RMSF r(↑)", "RMSF MAE(↓)", "PwRMSD(↓)", "DCCM r(↑)", "PCA W2(↓)", "Jtr%(↑)", "Time(s)(↓)"],
        [
            ["BioEmu*",          "0.83", "1.29", "2.84", "0.80", "1.65", "36", "1.9"],
            ["AlphaFlow",        "0.86", "0.59", "1.35", "0.86", "1.47", "41", "32.0"],
            ["ConfDiff",         "0.88", "0.62", "1.45", "0.86", "1.41", "39", "20.2"],
            ["AlphaFlow-T",      "0.92", "0.41", "0.91", "0.89", "1.28", "47", "32.6"],
            ["ESMFlow-T",        "0.92", "0.52", "1.22", "0.89", "1.48", "47", "11.2"],
            ["AlphaFlow-Tdist",  "0.92", "0.68", "1.41", "0.88", "1.43", "42", "3.3"],
            ["AlphaFlow-T12L,d", "0.90", "0.85", "1.80", "0.87", "1.60", "24", "1.2"],
            ["BBFlow",           "0.90", "0.42", "0.77", "0.87", "1.33", "29", "0.8"],
        ],
        cx1, cw1, bold_last=True,
        caption_text=(
            "* BioEmu not trained on ATLAS; comparison is illustrative only. "
            "BBFlow row in bold. Median RMSF of BBFlow = 1.49 Å ≈ MD reference 1.48 Å."
        )
    )

    w.para("Key observations from Table 1:")
    w.bullet(
        "Speed/accuracy Pareto. BBFlow is 41× faster than AlphaFlow-T (0.8 vs. 32.6 s/conf) "
        "while matching or exceeding it on 5 of 6 metrics — the only model below 4 s/conf "
        "that achieves competitive accuracy."
    )
    w.bullet(
        "Over-stabilisation in AlphaFlow-T. AlphaFlow-T predicts median RMSF 1.17 Å vs. "
        "MD reference 1.48 Å — a 21% underestimate of ensemble spread. BBFlow predicts 1.49 Å, "
        "closely matching MD. Over-stabilisation is attributed to the folding model's strong "
        "prior toward equilibrium structures."
    )
    w.bullet(
        "Pairwise RMSD. BBFlow achieves the best pwRMSD MAE (0.77 Å), indicating superior "
        "capture of the magnitude of conformational changes vs. all baselines including "
        "AlphaFlow-T (0.91 Å)."
    )
    w.bullet(
        "Transient contacts. BBFlow underperforms MSA-based models on J_tr (29% vs. 47%). "
        "Transient contacts are rare, large-amplitude excursions best predicted using "
        "evolutionary co-variation signals unavailable to BBFlow."
    )

    w.heading2("6.2", "De Novo Proteins")
    w.para("Table 2 — De novo proteins (50 systems). MD reference RMSF median = 0.91 Å.")
    cx2 = [ML, ML+90, ML+142, ML+194, ML+244, ML+296, ML+348, ML+395]
    cw2 = [90,    52,     52,     50,     52,     52,     47,     70]
    w.table(
        ["Method", "RMSF r(↑)", "RMSF MAE(↓)", "PwRMSD(↓)", "DCCM r(↑)", "PCA W2(↓)", "Jtr%(↑)", "Time(s)(↓)"],
        [
            ["BioEmu*",          "0.60", "4.24", "8.29", "0.64", "1.53", "23", "1.9"],
            ["AlphaFlow",        "0.47", "4.76", "7.40", "0.58", "1.64", "17", "32.0"],
            ["ConfDiff",         "0.62", "3.82", "7.26", "0.65", "1.72", "15", "20.2"],
            ["AlphaFlow-T",      "0.89", "0.25", "0.38", "0.85", "0.66", "55", "32.6"],
            ["ESMFlow-T",        "0.89", "0.28", "0.43", "0.86", "0.63", "55", "11.2"],
            ["AlphaFlow-Tdist",  "0.88", "0.46", "0.77", "0.84", "0.69", "51", "3.3"],
            ["AlphaFlow-T12L,d", "0.87", "0.58", "0.97", "0.83", "0.75", "38", "1.2"],
            ["BBFlow",           "0.84", "0.26", "0.32", "0.83", "0.67", "32", "0.8"],
        ],
        cx2, cw2, bold_last=True,
        caption_text=(
            "AlphaFlow (no templates) and BioEmu degrade catastrophically without MSA. "
            "BBFlow RMSF correlation drops only from 0.90 to 0.84 (Δ = 0.06); "
            "AlphaFlow drops from 0.86 to 0.47 (Δ = 0.39). "
            "BBFlow achieves the best pairwise RMSD MAE (0.32 Å) among all models."
        )
    )

    w.heading2("6.3", "Multi-Chain Proteins")
    w.para(
        "Table 3 — Five multi-chain systems. BBFlow trained on monomers only. "
        "MD reference RMSF median = 1.20 Å. No other baseline produced physically valid states."
    )
    cx3 = [ML, ML+100, ML+175, ML+232, ML+288, ML+350]
    cw3 = [100,    75,     57,     56,     62,    115]
    w.table(
        ["Method", "RMSF r(↑)", "RMSF MAE(↓)", "PwRMSD(↓)", "DCCM r(↑)", "PCA W2(↓)"],
        [["BBFlow", "0.82", "0.31", "0.41", "0.85", "0.71"]],
        cx3, cw3, bold_last=True,
        caption_text=(
            "BBFlow correctly captures both intra-chain fluctuations and inter-chain "
            "allosteric communication (DCCM r = 0.85) despite never training on multimers. "
            "AlphaFlow with parser-modified multi-chain input generates unphysical states."
        )
    )

    w.heading2("6.4", "Sequence-to-Ensemble Pipeline")
    w.para(
        "When only a sequence is available, BBFlow can be combined with AlphaFold 2 "
        "in a two-stage pipeline: AF2 predicts x_eq once, then BBFlow generates all "
        "conformations. Because AF2 runs only once (not once per conformation), this "
        "pipeline is ~30× faster than AlphaFlow."
    )
    w.para("Table 4 — Sequence-to-ensemble pipeline, ATLAS test set.")
    cx4 = [ML, ML+120, ML+178, ML+238, ML+293, ML+348, ML+400]
    cw4 = [120,    58,     60,     55,     55,     52,     65]
    w.table(
        ["Method", "RMSF r", "RMSF MAE", "PwRMSD", "DCCM r", "PCA W2", "Time(s)"],
        [
            ["AlphaFlow",    "0.86", "0.59", "1.35", "0.86", "1.47", "32.0"],
            ["AF2 + BBFlow", "0.87", "0.52", "1.07", "0.85", "1.47", "1.1"],
        ],
        cx4, cw4, bold_last=True,
        caption_text=(
            "AF2 + BBFlow outperforms stand-alone AlphaFlow on most metrics and is "
            "29× faster (1.1 s = 0.3 s AF2 + 0.8 s BBFlow vs. 32.0 s AlphaFlow)."
        )
    )

    # =========================================================================
    # 7. ABLATION
    # =========================================================================
    w.gap(14)
    w.heading1("7", "Ablation Study")

    w.heading2("7.1", "Component Ablations")
    w.para(
        "Table 5 — Component ablations on ATLAS test set. Each variant removes or replaces "
        "one component of BBFlow. Cond.P = conditional prior; Dist = distance encoding; "
        "Dir = direction encoding; AA = amino-acid identity; Idx = residue index."
    )
    cx5 = [ML, ML+105, ML+147, ML+182, ML+214, ML+245, ML+276, ML+368]
    cw5 = [105,    42,     35,     32,     31,     31,     92,     97]
    w.table(
        ["Variant", "Cond.P", "Dist", "Dir", "AA", "Idx", "RMSF MAE(↓)", "PwRMSD(↓)"],
        [
            ["BBFlow",        "YES", "YES", "YES", "YES", "NO",  "0.42", "0.77"],
            ["(a) no dir.",   "NO",  "YES", "NO",  "YES", "YES", "0.52", "1.15"],
            ["(b) no prior",  "NO",  "YES", "YES", "YES", "YES", "0.48", "0.90"],
            ["(c) + index",   "YES", "YES", "YES", "YES", "YES", "0.42", "0.82"],
            ["(d) no AA",     "YES", "YES", "NO",  "NO",  "YES", "0.54", "0.93"],
            ["(e) no dist.",  "YES", "NO",  "NO",  "YES", "YES", "5.88", "7.08"],
        ],
        cx5, cw5, bold_last=False,
        caption_text=(
            "Removing the distance encoding (e) is catastrophic — RMSF MAE 0.42 → 5.88 Å — "
            "confirming it as the essential fold-identity signal. Direction encoding (a) and "
            "conditional prior (b) each give measurable improvements. Residue indices (c) "
            "are neutral for monomers but harmful for multi-chain transfer."
        )
    )

    w.para("Detailed findings:")
    w.bullet(
        "Distance encoding (e) — ESSENTIAL. Removing it is catastrophic: RMSF MAE "
        "0.42 → 5.88 Å, PwRMSD 0.77 → 7.08 Å. Without distance encoding the model has no "
        "information about which fold to generate; the result is worse than random generation."
    )
    w.bullet(
        "Direction encoding (a) — IMPORTANT. Removes fine-grained local geometry: RMSF MAE "
        "0.42 → 0.52 Å, PwRMSD 0.77 → 1.15 Å. The direction vectors encode which way "
        "neighbouring residues point within the local frame, enabling better discrimination of "
        "structurally similar but dynamically different local environments."
    )
    w.bullet(
        "Conditional prior (b) — BENEFICIAL. RMSF MAE 0.42 → 0.48 Å, PwRMSD 0.77 → 0.90 Å. "
        "The improvement in final accuracy is modest, but the conditional prior also "
        "substantially accelerates convergence during training."
    )
    w.bullet(
        "Residue index (c) — NEUTRAL for monomers, HARMFUL for multimers. Adding indices does "
        "not improve accuracy on the ATLAS benchmark (RMSF MAE identical; PwRMSD slightly worse "
        "at 0.82 vs. 0.77 Å). Residue indices cause catastrophic failure on multi-chain proteins "
        "because they encode a single-chain assumption."
    )
    w.bullet(
        "Amino-acid identity (d) — HELPFUL but not essential. Removing AA identity degrades "
        "RMSF MAE 0.42 → 0.54 Å. The model without any sequence information still outperforms "
        "AlphaFlow (0.59 Å) and all distilled models, confirming that backbone geometry alone "
        "is sufficient for competitive ensemble generation."
    )

    w.heading2("7.2", "Hyperparameter ξ — Conditional Prior Strength")
    w.para(
        "The hyperparameter ξ controls how close the prior sample x₀ is to the equilibrium "
        "structure x_eq. Smaller ξ increases ensemble diversity but demands the flow learn a "
        "larger transformation from noise; larger ξ constrains diversity. Table 6 shows the "
        "inference-time ablation for the model trained at ξ = 0.2."
    )
    w.para("Table 6 — Inference-time ablation of ξ (model trained with ξ = 0.2).")
    cx6 = [ML, ML+42, ML+94, ML+150, ML+212, ML+268, ML+318, ML+368]
    cw6 = [42,    52,    56,     62,     56,     50,     50,     97]
    w._check(160)   # keep entire table on one page
    w.table(
        ["ξ", "RMSF r", "RMSF MAE", "RMSF Med.", "PwRMSD", "DCCM r", "PCA W2", "Note"],
        [
            ["0.01", "0.70", "7.61", "11.16", "10.83", "0.73", "2.85", ""],
            ["0.05", "0.81", "3.89", " 5.43", " 5.38", "0.78", "2.06", ""],
            ["0.10", "0.88", "1.32", " 2.62", " 2.21", "0.84", "1.51", ""],
            ["0.20", "0.90", "0.42", " 1.49", " 0.77", "0.87", "1.33", "← optimal"],
            ["0.30", "0.89", "0.47", " 1.37", " 1.02", "0.86", "1.69", ""],
            ["0.40", "0.86", "0.64", " 1.65", " 1.31", "0.80", "2.12", ""],
            ["0.50", "0.79", "0.80", " 1.82", " 1.50", "0.74", "3.00", ""],
            ["0.60", "0.73", "0.82", " 1.70", " 1.65", "0.70", "4.51", ""],
        ],
        cx6, cw6, bold_last=False,
        caption_text=(
            "ξ = 0.20 is optimal. Below 0.2 the flow must learn too large a transformation; "
            "above 0.2 the prior is too constrained toward x_eq, reducing ensemble diversity."
        )
    )

    # =========================================================================
    # 8. DISCUSSION
    # =========================================================================
    w.gap(14)
    w.heading1("8", "Discussion")

    w.heading2("8.1", "What Makes BBFlow Conceptually Novel?")
    w.heading3("Decoupling ensemble generation from sequence modelling")
    w.para(
        "Every prior transferable ensemble generation model — AlphaFlow, ESMFlow, ConfDiff, "
        "BioEmu — inherits the architecture of protein folding models, framing ensemble "
        "generation as a sequence-to-structure problem. This coupling is not necessary: the "
        "fold of a protein is already fully captured in its equilibrium structure x_eq, which "
        "can serve as the conditioning signal directly. BBFlow demonstrates that the entire "
        "sequence-level machinery (MSA computation, Evoformer, language-model pretraining) is "
        "not a prerequisite for high-quality MD emulation. The resulting model is faster, "
        "lighter, unbiased toward natural-protein sequence statistics, and applicable to any "
        "protein for which a structural model exists."
    )
    w.heading3("Conditional prior in Riemannian flow matching")
    w.para(
        "The concept of a geometry-conditioned prior in flow matching is novel. Prior work used "
        "either unconditional priors (GAFL, FrameFlow) or non-Gaussian but still unconditional "
        "priors (Chroma). BBFlow's conditional prior generalises partial denoising from diffusion "
        "models to the manifold flow matching framework, providing a principled geometrically "
        "correct way to bias generation toward a known reference structure while retaining "
        "sufficient diversity. This concept is broadly applicable to any generative modelling "
        "problem on curved spaces where a reference point is available."
    )
    w.heading3("Zero-shot multi-chain transfer via geometry-only conditioning")
    w.para(
        "Omitting residue-index features — and conditioning on geometry alone — enables "
        "zero-shot generalisation from monomers to multimers. It reveals that the chain-identity "
        "information encoded by residue indices is precisely what prevents prior models from "
        "handling multi-chain inputs: they bake in a single-chain assumption. By replacing this "
        "with the geometry of x_eq (which naturally encodes chain boundaries as spatial "
        "discontinuities in the distance matrix), BBFlow extends to protein complexes without "
        "any architectural modification — the first ensemble model to do so."
    )

    w.heading2("8.2", "Qualitative Comparison with Baselines")
    w.para("Table 7 — Qualitative comparison of ensemble generation approaches.")
    cx7 = [ML, ML+95, ML+127, ML+159, ML+191, ML+229, ML+267, ML+312, ML+364]
    cw7 = [95,    32,     32,     32,     38,     38,     45,     52,    101]
    w.table(
        ["Method", "MSA", "PLM", "FT", "Struct", "Multi", "Time(s)", "RMSF MAE", "Notes"],
        [
            ["AlphaFlow",   "Y", "N", "Y", "N", "N", "32.0", "0.59", "Evoformer+MSA"],
            ["AlphaFlow-T", "Y", "N", "Y", "Y", "N", "32.6", "0.41", "Over-stabilises"],
            ["ESMFlow-T",   "N", "Y", "Y", "Y", "N", "11.2", "0.52", "ESM embeddings"],
            ["ConfDiff",    "Y", "N", "Y", "N", "N", "20.2", "0.62", "Force-guided"],
            ["BioEmu",      "Y", "N", "Y", "N", "N", "1.9",  "1.29", "Non-ATLAS target"],
            ["MDGen",       "N", "N", "N", "N", "N", "0.15", "0.81", "Time-consistent"],
            ["BBFlow",      "N", "N", "N", "Y", "Y", "0.8",  "0.42", "This work"],
        ],
        cx7, cw7, bold_last=True,
        caption_text=(
            "MSA = requires MSA. PLM = protein language model. FT = fine-tunes pre-trained "
            "weights. Struct = conditions on equilibrium structure. Multi = multi-chain support."
        )
    )

    w.heading2("8.3", "Limitations")
    w.bullet(
        "MD distribution emulation. BBFlow reproduces the distribution of 300-ns "
        "CHARMM36m GROMACS trajectories at 310 K. It cannot predict rare alternative folded "
        "states, millisecond-timescale transitions, protein unfolding, or "
        "ligand-binding-induced large-scale conformational changes."
    )
    w.bullet(
        "Transient contact accuracy. Systematic underperformance (J_tr = 29% vs. 47% for "
        "AlphaFlow-T) on rare large-amplitude excursions that create new inter-residue contacts. "
        "Evolutionary co-variation, which encodes information about alternative structural states, "
        "appears especially beneficial for predicting these rare events."
    )
    w.bullet(
        "Backbone only. BBFlow generates Cα-only backbone conformations. Side-chain "
        "ensembles and protein–ligand interactions require additional modelling."
    )
    w.bullet(
        "Requires an equilibrium structure. This is not a practical limitation for MD "
        "emulation (MD also requires an initial structure), but it does require a structure "
        "prediction step for purely sequence-based inputs. The AF2 + BBFlow pipeline "
        "handles this and remains 29× faster than AlphaFlow."
    )

    w.heading2("8.4", "Practical Applications")
    w.bullet(
        "Drug discovery. Rapid screening of protein flexibility and cryptic-pocket availability "
        "across candidate targets at 0.8 s/conformation — feasible for whole-proteome annotation."
    )
    w.bullet(
        "Antibody and nanobody engineering. Multi-chain support enables ensemble generation "
        "for antibody–antigen complexes and evaluation of binding-site dynamics."
    )
    w.bullet(
        "De novo protein design. Integration into design pipelines (RFdiffusion + ProteinMPNN "
        "+ BBFlow) to screen designed sequences for desired dynamic properties — a capability "
        "absent from current design workflows."
    )
    w.bullet(
        "Large-scale structural annotation. At 0.8 s/conf, generating 250 conformations for "
        "all ~200,000 proteins in the AlphaFold Database requires ~10 GPU-days."
    )

    # =========================================================================
    # 9. CONCLUSION
    # =========================================================================
    w.gap(14)
    w.heading1("9", "Conclusion")
    w.para(
        "This document has provided a comprehensive technical exposition of BBFlow, covering "
        "all prerequisite concepts (protein backbone geometry, Boltzmann ensembles, molecular "
        "dynamics, SE(3) Lie groups, equivariant neural networks, transformer attention, "
        "Clifford Frame Attention, and Riemannian flow matching), a thorough survey of prior "
        "ensemble generation approaches (Boltzmann Generators, AlphaFlow/ESMFlow, ConfDiff, "
        "BioEmu, MDGen), and a full technical derivation of every BBFlow component."
    )
    w.para(
        "BBFlow makes three fundamental contributions: (1) it demonstrates that the sequence "
        "machinery of protein folding models is unnecessary for high-quality MD emulation — "
        "backbone geometry alone is sufficient; (2) it introduces a conditional prior via "
        "geodesic interpolation on SE(3)^N, a principled generalisation of partial denoising "
        "to manifold flow matching; and (3) it shows that geometry-only conditioning enables "
        "zero-shot transfer from monomers to multi-chain complexes."
    )
    w.para(
        "On the ATLAS benchmark, BBFlow achieves 41× speedup over AlphaFlow-T at comparable "
        "or superior accuracy across five of six metrics, correctly calibrates ensemble spread "
        "(median RMSF 1.49 Å vs. MD reference 1.48 Å), and is the only model with competitive "
        "accuracy that does not degrade on de novo proteins. The model was trained from scratch "
        "in three GPU-days with 18.2 M parameters — a fraction of the resources required by "
        "AlphaFold-based baselines."
    )
    w.para(
        "The two core ideas — structure conditioning as a replacement for evolutionary "
        "information, and conditional priors in Riemannian flow matching — are broadly "
        "applicable beyond protein ensemble generation and may inform future work in structural "
        "biology, generative chemistry, and geometric deep learning."
    )
    w.para("Code and pre-trained weights: https://github.com/graeter-group/bbflow")
    w.gap(10)
    w.rule()

    # =========================================================================
    # REFERENCES
    # =========================================================================
    w.heading1("", "References")
    refs = [
        "[1]  Abraham et al. GROMACS: High performance molecular simulations through "
        "multi-level parallelism. SoftwareX 1-2:19-25, 2015.",
        "[2]  Adcock & McCammon. Molecular dynamics: survey of methods for simulating "
        "the activity of proteins. Chem. Rev. 106:1589-1615, 2006.",
        "[3]  Baek et al. Accurate prediction of protein structures and interactions "
        "using a three-track neural network. Science 373:871-876, 2021.",
        "[4]  Benkovic, Hammes & Hammes-Schiffer. Free-energy landscape of enzyme "
        "catalysis. Biochemistry 47:3317-3321, 2008.",
        "[5]  Bose et al. SE(3)-stochastic flow matching for protein backbone generation. "
        "ICLR 2024.",
        "[6]  Case. Normal mode analysis of protein dynamics. "
        "Curr. Opin. Struct. Biol. 4:285-290, 1994.",
        "[7]  Chen & Lipman. Flow matching on general geometries. ICLR 2024.",
        "[8]  Fuchs et al. SE(3)-Transformers: 3D roto-translation equivariant attention "
        "networks. NeurIPS 2020.",
        "[9]  Ingraham et al. Illuminating protein space with a programmable generative "
        "model. Nature, 2023.",
        "[10] Jing, Berger & Jaakkola. AlphaFold meets flow matching for generating "
        "protein ensembles. ICML 2024.",
        "[11] Jing et al. Generative modeling of molecular dynamics trajectories. "
        "NeurIPS 2024.",
        "[12] Jorgensen et al. Comparison of simple potential functions for simulating "
        "liquid water. J. Chem. Phys. 79:926-935, 1983.",
        "[13] Jumper et al. Highly accurate protein structure prediction with AlphaFold. "
        "Nature 596:583-589, 2021.",
        "[14] Klein, Kramer & Noé. Equivariant flow matching. NeurIPS 2023.",
        "[15] Lewis et al. Scalable emulation of protein equilibrium ensembles with "
        "generative deep learning. Science 389:eadv9817, 2025.",
        "[16] Lin et al. Evolutionary-scale prediction of atomic-level protein structure "
        "with a language model. Science 379:1123-1130, 2023.",
        "[17] Lipman et al. Flow matching for generative modeling. ICLR 2023.",
        "[18] Lu et al. Str2Str: A score-based framework for zero-shot protein "
        "conformation sampling. ICLR 2024.",
        "[19] Noé et al. Boltzmann generators: Sampling equilibrium states of many-body "
        "systems with deep learning. Science 365:eaaw1147, 2019.",
        "[20] Puny et al. Frame averaging for invariant and equivariant network design. "
        "ICLR 2022.",
        "[21] Satorras, Hoogeboom & Welling. E(n) equivariant graph neural networks. "
        "ICML 2021.",
        "[22] Schütt, Unke & Gastegger. Equivariant message passing for tensorial "
        "properties and molecular spectra. ICML 2021.",
        "[23] Song et al. Score-based generative modeling through stochastic differential "
        "equations. ICLR 2021.",
        "[24] Thomas et al. Tensor field networks: Rotation- and translation-equivariant "
        "neural networks for 3D point clouds. arXiv:1802.08219, 2018.",
        "[25] Vander Meersche et al. ATLAS: Protein flexibility description from atomistic "
        "MD simulations. Nucleic Acids Res. 52:D384-D392, 2024.",
        "[26] Vaswani et al. Attention is all you need. NeurIPS 2017.",
        "[27] Wagner et al. Generating highly designable proteins with geometric algebra "
        "flow matching. NeurIPS 2024.",
        "[28] Wang et al. Protein conformation generation via force-guided SE(3) diffusion "
        "models. ICML 2024.",
        "[29] Watson et al. De novo design of protein structure and function with "
        "RFdiffusion. Nature 620:1089-1100, 2023.",
        "[30] Wayment-Steele et al. Predicting multiple conformations via sequence "
        "clustering and AlphaFold2. Nature 625:832-839, 2024.",
        "[31] Wolf, Seute, Viliuga, Wagner, Stühmer & Gräter. Learning conformational "
        "ensembles of proteins based on backbone geometry. NeurIPS 2025. arXiv:2503.05738v2.",
        "[32] Yim et al. SE(3) diffusion model with application to protein backbone "
        "generation. ICML 2023.",
        "[33] Yim et al. Fast protein backbone generation with SE(3) flow matching. "
        "arXiv:2310.05297, 2023.",
    ]
    for ref in refs:
        w.wrap(ref, size=FS_SMALL, indent=16, width=TW - 16, after=2)

    w.save(out_path)


if __name__ == "__main__":
    out = "/Users/indraniroy/Documents/Github/web-presentation/bbflow/bbflow_survey.pdf"
    build(out)
