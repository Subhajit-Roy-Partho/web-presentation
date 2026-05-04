#!/usr/bin/env python3
"""
Generate a professional academic-style PDF for MDGen survey
using matplotlib's PDF backend.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import textwrap
import re

# ── Color palette ────────────────────────────────────────────
TEAL   = '#0b7285'
RUST   = '#c2410c'
AMBER  = '#f08c00'
INK    = '#102522'
MUTED  = '#53625e'
BGLT   = '#e8f3ef'
WHITE  = '#fffaf0'
BLACK  = '#000000'

# ── Page geometry ────────────────────────────────────────────
PW, PH = 8.5, 11.0   # inches (letter)
LM, RM = 1.0, 1.0    # margins
TM, BM = 0.9, 0.75
TW = PW - LM - RM    # text width

BODY_FONT = 10
TITLE_FONT = 22
SEC_FONT   = 14
SSEC_FONT  = 11
SMALL_FONT = 8.5
FOOT_FONT  = 7.5

PLT_PARAMS = {
    'font.family': 'DejaVu Serif',
    'mathtext.fontset': 'dejavuserif',
    'axes.facecolor': 'none',
    'figure.facecolor': 'white',
}
matplotlib.rcParams.update(PLT_PARAMS)


def new_page():
    fig = plt.figure(figsize=(PW, PH))
    fig.patch.set_facecolor('white')
    return fig


def text_ax(fig, x=LM/PW, y=BM/PH, w=TW/PW, h=(PH-TM-BM)/PH):
    ax = fig.add_axes([x, y, w, h])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return ax


def footer(fig, page_num, title="MDGen: Generative Molecular Dynamics — Survey"):
    ax = fig.add_axes([LM/PW, 0.03, TW/PW, 0.04])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.axhline(0.85, color=TEAL, lw=0.8)
    ax.text(0, 0.3, title, fontsize=FOOT_FONT, color=MUTED)
    ax.text(1, 0.3, str(page_num), fontsize=FOOT_FONT, color=MUTED, ha='right')


def wrap(text, width=95):
    return textwrap.fill(text, width=width)


class PageWriter:
    """Simple top-to-bottom page writer with automatic page breaks."""

    def __init__(self, pdf):
        self.pdf  = pdf
        self.page = 1
        self._new_page()

    def _new_page(self):
        self.fig = new_page()
        self.ax  = text_ax(self.fig)
        self.y   = 0.985   # starts near the top of the text area

    def _flush(self):
        footer(self.fig, self.page)
        self.pdf.savefig(self.fig, bbox_inches='tight')
        plt.close(self.fig)
        self.page += 1
        self._new_page()

    def _check(self, need=0.04):
        if self.y < need:
            self._flush()

    def vspace(self, dy=0.012):
        self.y -= dy
        self._check()

    def rule(self, color=TEAL, lw=0.7):
        self._check(0.03)
        self.ax.axhline(self.y, xmin=0, xmax=1,
                        color=color, linewidth=lw, linestyle='-')
        self.y -= 0.008

    def section(self, num, title, color=INK):
        self._check(0.08)
        self.vspace(0.018)
        full = f"{num}   {title}"
        self.ax.text(0, self.y, full, fontsize=SEC_FONT,
                     fontweight='bold', color=color,
                     fontfamily='DejaVu Serif')
        self.y -= 0.038
        self.rule(TEAL)

    def subsection(self, num, title):
        self._check(0.07)
        self.vspace(0.012)
        self.ax.text(0, self.y, f"{num}  {title}", fontsize=SSEC_FONT,
                     fontweight='bold', color=INK)
        self.y -= 0.030

    def subsubsection(self, title):
        self._check(0.06)
        self.vspace(0.008)
        self.ax.text(0, self.y, title, fontsize=SSEC_FONT,
                     fontstyle='italic', color=MUTED)
        self.y -= 0.026

    def para(self, text, indent=0, color=INK, size=BODY_FONT, bold_prefix=None):
        """Render a paragraph with auto line-wrap."""
        lines = textwrap.wrap(text, width=92)
        for i, line in enumerate(lines):
            self._check(0.025)
            x = indent
            if bold_prefix and i == 0:
                bp = bold_prefix + ' '
                self.ax.text(x, self.y, bp, fontsize=size,
                             fontweight='bold', color=color)
                bw = len(bp) / 160
                self.ax.text(x + bw, self.y, line[len(bp.rstrip()):].lstrip(),
                             fontsize=size, color=color)
            else:
                self.ax.text(x, self.y, line, fontsize=size, color=color)
            self.y -= 0.022
        self.y -= 0.006

    def bullet(self, text, level=0, bold_word=None):
        indent = 0.03 + level * 0.03
        sym = '•' if level == 0 else '◦'
        lines = textwrap.wrap(text, width=85)
        for i, line in enumerate(lines):
            self._check(0.025)
            if i == 0:
                self.ax.text(indent - 0.025, self.y, sym,
                             fontsize=BODY_FONT, color=TEAL)
                if bold_word:
                    bw = bold_word + ': '
                    self.ax.text(indent, self.y, bw, fontsize=BODY_FONT,
                                 fontweight='bold', color=INK)
                    rest_start = len(bw) - 2
                    rest = line[rest_start:] if rest_start < len(line) else ''
                    self.ax.text(indent + len(bw)/160, self.y, rest,
                                 fontsize=BODY_FONT, color=INK)
                else:
                    self.ax.text(indent, self.y, line,
                                 fontsize=BODY_FONT, color=INK)
            else:
                self.ax.text(indent, self.y, line,
                             fontsize=BODY_FONT, color=INK)
            self.y -= 0.022
        self.y -= 0.003

    def equation(self, latex_text, label=None):
        """Render a display equation (centred)."""
        self._check(0.06)
        self.vspace(0.008)
        try:
            self.ax.text(0.5, self.y, f"${latex_text}$",
                         fontsize=BODY_FONT + 1, color=INK,
                         ha='center', va='top',
                         usetex=False)
        except Exception:
            self.ax.text(0.5, self.y, latex_text,
                         fontsize=BODY_FONT, color=INK, ha='center', va='top')
        if label:
            self.ax.text(0.97, self.y, label, fontsize=BODY_FONT,
                         color=MUTED, ha='right', va='top')
        self.y -= 0.038
        self.vspace(0.006)

    def callout(self, text, width=0.94, bgcolor=BGLT, border=TEAL):
        self._check(0.08)
        self.vspace(0.008)
        lines = textwrap.wrap(text, width=84)
        box_h = len(lines) * 0.022 + 0.022
        rect = mpatches.FancyBboxPatch(
            (0.03, self.y - box_h), width, box_h,
            boxstyle='round,pad=0.005',
            linewidth=1.2, edgecolor=border,
            facecolor=bgcolor, zorder=2)
        self.ax.add_patch(rect)
        ty = self.y - 0.012
        for line in lines:
            self.ax.text(0.06, ty, line, fontsize=BODY_FONT,
                         color=INK, zorder=3)
            ty -= 0.022
        self.y -= box_h + 0.014

    def table(self, headers, rows, col_widths=None):
        self._check(len(rows) * 0.028 + 0.06)
        if col_widths is None:
            col_widths = [1 / len(headers)] * len(headers)
        # header row
        self.vspace(0.006)
        x = 0
        # header background
        rect = mpatches.Rectangle((0, self.y - 0.024), 1, 0.028,
                                   facecolor=TEAL, edgecolor='none', zorder=2)
        self.ax.add_patch(rect)
        for i, (h, w) in enumerate(zip(headers, col_widths)):
            self.ax.text(x + 0.005, self.y - 0.007, h,
                         fontsize=SMALL_FONT, fontweight='bold',
                         color='white', zorder=3)
            x += w
        self.y -= 0.030
        # data rows
        for ri, row in enumerate(rows):
            bg = BGLT if ri % 2 == 0 else 'white'
            rect = mpatches.Rectangle((0, self.y - 0.022), 1, 0.026,
                                       facecolor=bg, edgecolor='none', zorder=1)
            self.ax.add_patch(rect)
            x = 0
            for cell, w in zip(row, col_widths):
                self.ax.text(x + 0.005, self.y - 0.006, str(cell),
                             fontsize=SMALL_FONT, color=INK, zorder=3)
                x += w
            self.y -= 0.026
        self.vspace(0.010)

    def end(self):
        self._flush()


# ─────────────────────────────────────────────────────────────
# CONTENT
# ─────────────────────────────────────────────────────────────

def build_pdf(path):
    with PdfPages(path) as pdf:

        # ── TITLE PAGE ──────────────────────────────────────────────
        fig = new_page()
        ax = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

        # Teal header bar
        ax.add_patch(mpatches.Rectangle((0, 0.82), 1, 0.18,
                     facecolor=TEAL, edgecolor='none'))
        ax.text(0.5, 0.94, "Technical Survey  ·  NeurIPS 2024",
                fontsize=11, color='white', ha='center', va='center',
                fontweight='bold')
        ax.text(0.5, 0.87, "arXiv : 2409.17808",
                fontsize=10, color='#aeeeff', ha='center', va='center')

        # Title
        ax.text(0.5, 0.73,
                "MDGen: Generative Molecular Dynamics Simulation",
                fontsize=20, fontweight='bold', color=INK,
                ha='center', va='center', wrap=True,
                fontfamily='DejaVu Serif')
        ax.text(0.5, 0.66,
                "A Comprehensive Technical Survey with Background,\n"
                "Prior Work, Architecture, and Analysis",
                fontsize=13, color=MUTED, ha='center', va='center',
                linespacing=1.6)

        # Divider
        ax.axhline(0.615, xmin=0.1, xmax=0.9, color=TEAL, lw=1.0)

        # Author
        ax.text(0.5, 0.575, "Ditsa Mallick", fontsize=14,
                color=INK, ha='center', fontweight='bold')
        ax.text(0.5, 0.544,
                "School of Computing and Augmented Intelligence\n"
                "Arizona State University, Tempe AZ 85281\n"
                "dmallic1@asu.edu",
                fontsize=11, color=MUTED, ha='center', va='center',
                linespacing=1.55)

        ax.axhline(0.475, xmin=0.1, xmax=0.9, color=TEAL, lw=0.5)

        ax.text(0.5, 0.44, "Based on:", fontsize=10, color=MUTED,
                ha='center', fontstyle='italic')
        ax.text(0.5, 0.41,
                "Jing, B., Stärk, H., Jaakkola, T., & Berger, B. (2024).\n"
                "Generative Molecular Dynamics. arXiv:2409.17808. NeurIPS 2024.",
                fontsize=10, color=INK, ha='center', va='center',
                linespacing=1.5)

        # Abstract box
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.06, 0.05), 0.88, 0.31,
            boxstyle='round,pad=0.01',
            linewidth=1.2, edgecolor=TEAL, facecolor=BGLT))
        ax.text(0.5, 0.355, "Abstract", fontsize=11, fontweight='bold',
                color=TEAL, ha='center')
        abstract = (
            "MDGen is the first generative model to produce temporally coherent, "
            "full-backbone protein trajectories at ~10,000x the speed of explicit-solvent "
            "molecular dynamics (MD). This survey provides a comprehensive technical exposition "
            "covering protein biophysics, denoising diffusion probabilistic models on non-Euclidean "
            "manifolds (SO(3), T^4), SE(3)-equivariance, and the full landscape of prior work—"
            "Normal Mode Analysis, Boltzmann generators, and independent-frame diffusion models. "
            "The MDGen architecture alternates SE(3)-equivariant Invariant Point Attention (spatial) "
            "with temporal axial attention (kinetic), enabling joint modelling of equilibrium "
            "thermodynamics and kinetic temporal structure. Trained on the ATLAS database "
            "(1,400 proteins × 300 ns each), MDGen achieves RMSF Pearson r ≈ 0.87, "
            "Ramachandran JSD ≈ 0.08, and correctly reproduces autocorrelation functions "
            "and frame-to-frame step-size distributions—metrics no prior independent sampler "
            "can reproduce.")
        abs_lines = textwrap.wrap(abstract, width=95)
        ty = 0.328
        for line in abs_lines:
            ax.text(0.09, ty, line, fontsize=9, color=INK)
            ty -= 0.019

        ax.text(0.5, 0.025, "May 2026", fontsize=9, color=MUTED, ha='center')

        footer(fig, 1)
        pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)

        # ── BODY ────────────────────────────────────────────────────
        w = PageWriter(pdf)
        w.page = 2

        # ── 1. INTRODUCTION ─────────────────────────────────────────
        w.section("1", "Introduction")

        w.para(
            "Proteins are the primary molecular machines of living systems. They catalyse chemical "
            "reactions, transmit cellular signals, provide structural integrity, and execute the vast "
            "majority of biochemical functions essential for life. A protein's biological activity "
            "depends critically not only on its average three-dimensional structure but on its "
            "dynamical behaviour: the ensemble of conformations it explores at physiological "
            "temperature, the timescales of interconversion between states, and the kinetic "
            "pathways connecting them (Adcock & McCammon, 2006).")

        w.para(
            "Despite decades of progress in experimental structure determination—X-ray "
            "crystallography, cryo-EM, NMR spectroscopy—these methods report static or "
            "ensemble-averaged snapshots. Molecular dynamics (MD) simulation fills this gap by "
            "numerically integrating Newton's equations of motion for every atom, generating "
            "detailed time-series of atomic positions. Modern GPU-accelerated MD packages can "
            "simulate a 100-residue protein at ~100–200 ns per day. Yet biologically important "
            "timescales—domain motions, loop gating, folding transitions—occur on microsecond to "
            "millisecond timescales, spanning 9–12 orders of magnitude above the obligatory 2 fs "
            "integration time step. This timescale gap makes MD prohibitively expensive for "
            "large-scale ensemble characterisation or drug discovery campaigns.")

        w.callout(
            "Core motivation. MDGen asks: can a neural network, trained on a large corpus of MD "
            "trajectories, learn to generate new trajectory segments that faithfully reproduce "
            "both the equilibrium thermodynamics AND the kinetic temporal structure—without "
            "running the simulation itself?")

        w.para(
            "All prior generative models for protein conformations operate in an i.i.d. sampling "
            "regime: each sample is drawn independently from an approximation of the equilibrium "
            "distribution. Such models cannot reproduce temporal autocorrelation functions, "
            "kinetically realistic step sizes between consecutive frames, or any observable that "
            "depends on the ordering of configurations in time. MDGen (Jing et al., NeurIPS 2024) "
            "addresses this gap by posing the generative problem at the level of entire trajectory "
            "segments: given a protein sequence, generate T consecutive backbone frames whose "
            "joint distribution matches that of a real MD simulation. The key technical contribution "
            "is an architecture alternating SE(3)-equivariant Invariant Point Attention (IPA) with "
            "novel temporal axial attention. Trained on ATLAS (1,400 proteins × 300 ns each), "
            "MDGen achieves RMSF Pearson r ≈ 0.87 and correct temporal kinetics at ~10,000× "
            "the speed of equivalent MD.")

        # ── 2. BIOLOGICAL BACKGROUND ──────────────────────────────
        w.section("2", "Biological and Physical Background")
        w.subsection("2.1", "Proteins: Structure and Function")

        w.para(
            "A protein is a linear polymer of amino acid residues connected by peptide bonds. "
            "Twenty standard amino acids, differing only in their side chain (the group branching "
            "from the alpha-carbon, Cα), are encoded by the genetic code. Proteins range from tens "
            "to thousands of residues in length; a typical globular protein has 100–500 residues.")

        w.para("The structural hierarchy of proteins is decomposed into four levels:")
        w.bullet("Primary structure: the amino-acid sequence, a string over a 20-letter alphabet.",
                 bold_word="Primary structure")
        w.bullet("Secondary structure: local backbone regularities—α-helices (right-handed coils "
                 "stabilised by i→i+4 hydrogen bonds) and β-strands (extended chains forming "
                 "hydrogen-bonded β-sheets).", bold_word="Secondary structure")
        w.bullet("Tertiary structure: the complete 3D fold of a single polypeptide chain, governed "
                 "by hydrophobic packing, electrostatics, hydrogen bonding, and van der Waals "
                 "interactions.", bold_word="Tertiary structure")
        w.bullet("Quaternary structure: assembly of multiple polypeptide chains into a complex.",
                 bold_word="Quaternary structure")

        w.para(
            "The protein backbone consists of the repeating N–Cα–C=O unit running through every "
            "residue. Backbone conformation is almost completely determined by two dihedral angles: "
            "φ (N–Cα bond rotation) and ψ (Cα–C bond rotation). MDGen operates exclusively on "
            "backbone heavy atoms, representing each residue as a rigid frame, with side chains "
            "encoded separately as torsion angles χ₁–χ₄.")

        w.subsection("2.2", "The Protein Energy Landscape and Conformational Ensembles")

        w.para(
            "A protein in solution at temperature T does not adopt a single static conformation. "
            "Instead, it continuously fluctuates according to Boltzmann statistics. The probability "
            "of finding the system in conformation x is given by the canonical ensemble distribution:")

        w.equation(r"p(x) \propto \exp(-\frac{E(x)}{k_B T})", "(1)")

        w.para(
            "where E(x) is the potential energy, k_B is Boltzmann's constant, and k_BT ≈ 0.6 "
            "kcal/mol at 300 K. The energy landscape of a protein (Frauenfelder et al., 1991) is "
            "a high-dimensional surface in conformation space. Key features relevant to MDGen:")

        w.bullet("Multiple minima: most functional proteins populate more than one conformation "
                 "(e.g. open/closed enzyme active sites).")
        w.bullet("Hierarchical roughness: fast local motions (10 fs) nested within slower large-scale "
                 "rearrangements (μs–ms).")
        w.bullet("Anharmonicity: large-amplitude motions cannot be described by a harmonic "
                 "approximation—a fundamental limitation of Normal Mode Analysis.")

        w.para(
            "The biologically relevant object is the conformational ensemble—the full distribution "
            "p(x)—not a single structure. Dynamical properties such as conformational change rates, "
            "domain motion timescales, and cryptic binding pocket populations all depend on the "
            "shape of this distribution and the barriers between its modes.")

        w.subsection("2.3", "Molecular Dynamics Simulation")

        w.para(
            "MD simulation generates samples from the conformational ensemble by numerically "
            "integrating Newton's equations of motion:")

        w.equation(
            r"m_i \frac{d^2 \mathbf{r}_i}{dt^2} = \mathbf{F}_i = -\nabla_{\mathbf{r}_i} E(\mathbf{r}_1, \ldots, \mathbf{r}_N)",
            "(2)")

        w.para(
            "The empirical force field E comprises: (i) bonded terms—harmonic bond stretches, "
            "angle bends, and periodic dihedral torsions calibrated to quantum chemical calculations; "
            "(ii) non-bonded terms—Lennard-Jones 6-12 van der Waals potential and Coulomb "
            "electrostatics (typically treated via Particle Mesh Ewald for long-range contributions). "
            "Widely used force fields include AMBER ff14SB (the force field used for ATLAS training "
            "data), CHARMM36m, and OPLS-AA.")

        w.callout(
            "The timescale problem. The fastest atomic vibrations (~10 fs) impose an integration "
            "time step ceiling of Δt = 2 fs. Observing biologically important motions requires "
            "10^8–10^11 steps (100 ns–100 μs). A single microsecond simulation of a 100-residue "
            "protein on a modern A100 GPU cluster requires ~1–2 weeks wall-clock time. Screening "
            "thousands of variants—as required in drug discovery—is practically infeasible.")

        w.subsection("2.4", "Trajectory Representation for MDGen")

        w.para(
            "An MD trajectory is a time-ordered sequence of frames (x₁, x₂, …, xT), where each "
            "frame xₜ specifies the full atomic coordinates at time t. In MDGen, the relevant "
            "degrees of freedom per residue i at time t are a rigid body frame in SE(3) plus "
            "torsion angles on the 4-torus:")

        w.equation(r"\mathbf{x} = \{(R_i, \mathbf{t}_i, \chi_i)\}_{i=1}^N \in SE(3)^N \times \mathbb{T}^{4N}",
                   "(3)")

        w.para(
            "A trajectory window of T frames is the joint object X = (x₁, x₂, …, xT) over which "
            "MDGen's diffusion process is defined. Training uses T = 16 frames, corresponding to "
            "approximately 16 ns at the ATLAS 1 ns frame rate.")

        # ── 3. DIFFUSION THEORY ──────────────────────────────────
        w.section("3", "Theoretical Background: Diffusion Models")
        w.subsection("3.1", "Denoising Diffusion Probabilistic Models (DDPMs)")

        w.para(
            "Denoising diffusion probabilistic models (DDPMs; Ho et al., 2020) define a generative "
            "model through two coupled Markov chains: a forward process that gradually destroys "
            "structure by adding Gaussian noise, and a reverse process learned to reconstruct "
            "data from noise.")

        w.para(
            "Forward process. Given a clean sample x₀ ~ q_data(x), the forward process adds "
            "Gaussian noise over S discrete steps:")

        w.equation(
            r"q(\mathbf{x}_s | \mathbf{x}_{s-1}) = \mathcal{N}(\mathbf{x}_s;\ \sqrt{1-\beta_s}\,\mathbf{x}_{s-1},\ \beta_s \mathbf{I})",
            "(4)")

        w.para(
            "where β_s ∈ (0,1) is a pre-specified noise schedule. The marginal at step s has a "
            "closed form with ᾱ_s = ∏_{k=1}^s (1−β_k):")

        w.equation(
            r"q(\mathbf{x}_s | \mathbf{x}_0) = \mathcal{N}(\mathbf{x}_s;\ \sqrt{\bar\alpha_s}\,\mathbf{x}_0,\ (1-\bar\alpha_s)\mathbf{I})",
            "(5)")

        w.para(
            "As s → S, ᾱ_s → 0 and the distribution approaches N(0, I) — pure isotropic noise. "
            "The training objective minimises noise prediction error:")

        w.equation(
            r"\mathcal{L} = \mathbb{E}_{s,\mathbf{x}_0,\epsilon}[\|\epsilon - \epsilon_\theta(\sqrt{\bar\alpha_s}\,\mathbf{x}_0 + \sqrt{1-\bar\alpha_s}\,\epsilon,\ s)\|^2]",
            "(6)")

        w.subsection("3.2", "Score-Based Models and the Continuous-Time SDE Perspective")

        w.para(
            "Song et al. (2021) cast diffusion models as continuous-time stochastic differential "
            "equations (SDEs), providing a unified theoretical framework. The forward SDE is:")

        w.equation(
            r"d\mathbf{x} = f(\mathbf{x},t)\,dt + g(t)\,d\mathbf{W}",
            "(7)")

        w.para(
            "where W is a standard Brownian motion. The reverse SDE (Anderson, 1982) runs backwards "
            "from noise to data:")

        w.equation(
            r"d\mathbf{x} = [f(\mathbf{x},t) - g(t)^2\,\nabla_\mathbf{x}\!\log p_t(\mathbf{x})]dt + g(t)\,d\bar{\mathbf{W}}",
            "(8)")

        w.para(
            "The key quantity is the score function ∇_x log p_t(x), which points toward regions "
            "of higher probability density. A score network s_θ(x,t) ≈ ∇_x log p_t(x) is trained "
            "via denoising score matching (Vincent, 2011). DDIM (Song et al., 2021) provides a "
            "deterministic ODE equivalent enabling high-quality sampling in ~50 steps instead of 500:")

        w.equation(
            r"\mathbf{x}_{s-1} = \sqrt{\bar\alpha_{s-1}}\!\left(\frac{\mathbf{x}_s - \sqrt{1-\bar\alpha_s}\,\epsilon_\theta}{\sqrt{\bar\alpha_s}}\right) + \sqrt{1-\bar\alpha_{s-1}}\,\epsilon_\theta",
            "(9)")

        w.subsection("3.3", "Diffusion on Non-Euclidean Manifolds")

        w.para(
            "Standard Gaussian diffusion assumes data lies in flat Euclidean space R^d. Protein "
            "backbone frames involve two non-Euclidean components:")

        w.bullet("Rotations R_i ∈ SO(3): a compact 3D Lie group with non-trivial curved geometry.")
        w.bullet("Torsion angles χ_j ∈ S¹ (the circle), with period 2π; side-chain state lives on "
                 "the 4-torus T⁴ = (S¹)⁴.")

        w.para(
            "Diffusion on SO(3): MDGen uses the Isotropic Gaussian on SO(3) (IGSO3; De Bortoli et "
            "al., 2022) distribution:")

        w.equation(
            r"q(R_s | R_0) = \mathrm{IGSO3}(R_s;\ R_0,\ \sigma_s^2)",
            "(10)")

        w.para(
            "whose score uses the Riemannian gradient—the analogue of ∇_x log p on the curved "
            "SO(3) manifold, computed via the heat kernel. For torsion angles θ ∈ (−π, π], the "
            "correct diffusion distribution is a wrapped Gaussian (Jing et al., 2022):")

        w.equation(
            r"q(\theta_s | \theta_0) = \sum_{k=-\infty}^{\infty} \mathcal{N}(\theta_s;\ \theta_0 + 2\pi k,\ \sigma_s^2)",
            "(11)")

        w.subsection("3.4", "SE(3) Equivariance")

        w.para(
            "A fundamental symmetry of physical systems in 3D is Euclidean equivariance. The "
            "group SE(3) = SO(3) semidirect R³ consists of all rotations and translations of R³. A map f "
            "is SE(3)-equivariant if:")

        w.equation(
            r"f(g \cdot \mathbf{x}) = \rho_{\mathrm{out}}(g)\,f(\mathbf{x}),\quad g \in SE(3)",
            "(12)")

        w.para(
            "For coordinate outputs, rotating the input rotates the output by the same rotation. "
            "SE(3)-equivariant networks (Fuchs et al., 2020; Satorras et al., 2021) architecturally "
            "enforce this constraint exactly. This is essential: the physics of a protein does not "
            "change if we rotate or translate the entire coordinate system. A model that violates "
            "this symmetry must learn it from data, wasting capacity and risking generalisation failure.")

        w.subsection("3.5", "Backbone Frame Representation")

        w.para(
            "The AlphaFold2 structure module (Jumper et al., 2021) introduced the backbone frame "
            "representation that MDGen inherits. Each residue i is assigned a rigid body in SE(3):")

        w.bullet("Translation t_i ∈ R³: the position of the Cα atom.")
        w.bullet("Rotation R_i ∈ SO(3): a local coordinate frame defined by the N, Cα, and C "
                 "atoms, encoding backbone orientation.")

        w.para(
            "Together, T_i = (R_i, t_i) defines a frame in which the local chemical environment "
            "of residue i appears in a standardised orientation. The full protein backbone is "
            "represented as N frames {T_i}_{i=1}^N ∈ SE(3)^N.")

        # ── 4. PRIOR WORK ──────────────────────────────────────────
        w.section("4", "Prior Work and Its Limitations")

        w.para(
            "Understanding MDGen's novelty requires surveying the space of prior methods for "
            "computational characterisation of protein conformational dynamics. We organise this "
            "survey into four categories.")

        w.subsection("4.1", "Normal Mode Analysis (NMA)")

        w.para(
            "Normal Mode Analysis (Tirion, 1996; Brooks & Karplus, 1983) approximates the protein "
            "energy landscape as a multidimensional quadratic (harmonic) bowl centred on a known "
            "minimised structure. Under this approximation, the equations of motion separate into "
            "3N−6 independent harmonic oscillators (normal modes), each with a characteristic "
            "frequency. The lowest-frequency modes correspond to the largest-scale, most collective "
            "motions and can predict B-factors and RMSF profiles.")

        w.para("Strengths of NMA:")
        w.bullet("Computationally cheap: a single eigendecomposition of the Hessian matrix.")
        w.bullet("Provides physically interpretable modes (e.g. a 'breathing' mode of a capsid).")
        w.bullet("Reasonable agreement with MD-derived RMSF for well-ordered secondary structure.")

        w.para("Fundamental limitations:")
        w.bullet("Harmonic approximation: NMA is strictly valid only near the energy minimum. "
                 "Loop motions, domain swings, and any transition requiring barrier crossing are "
                 "outside the scope of the harmonic model.")
        w.bullet("No kinetics: NMA produces independent samples from a Gaussian approximation to "
                 "the equilibrium ensemble; it has no notion of temporal ordering or transition rates.")
        w.bullet("Single minimum: NMA cannot represent multi-modal distributions or conformational "
                 "heterogeneity between distinct basins.")
        w.bullet("In direct comparison on the ATLAS test set, NMA achieves RMSF Pearson r ≈ 0.64 "
                 "— substantially below MDGen's r ≈ 0.87.")

        w.subsection("4.2", "Boltzmann Generators and Flow-Based Equilibrium Samplers")

        w.para(
            "Boltzmann generators (Noé et al., 2019) use normalising flows (bijective, differentiable "
            "maps) to learn a direct mapping between a tractable Gaussian base distribution and the "
            "Boltzmann distribution p(x) ∝ exp(−E(x)/k_BT). Samples can be drawn at test time "
            "without simulating the dynamics.")

        w.para("Strengths:")
        w.bullet("Principled probabilistic model with exact likelihood.")
        w.bullet("Can provide reweighting factors to correct for force-field imperfections.")

        w.para("Fundamental limitations:")
        w.bullet("Scalability: normalising flows for all-atom protein configurations of 100–500 "
                 "residues remain computationally intractable; most demonstrations are restricted "
                 "to ≤50-residue systems.")
        w.bullet("No temporal coherence: like NMA, Boltzmann generators produce i.i.d. equilibrium "
                 "samples. There is no mechanism for temporally ordered trajectories.")
        w.bullet("Requires the energy function: training typically requires evaluating E(x), "
                 "coupling the method to the expensive force field.")

        w.subsection("4.3", "Independent-Frame Protein Diffusion Models")

        w.para(
            "A family of recent diffusion models generates protein structures by learning to reverse "
            "a noising process on backbone frames, producing independent equilibrium samples.")

        w.bullet("FrameDiff (Yim et al., ICML 2023): diffuses over SE(3)^N backbone frames; "
                 "samples drawn independently to form a structural ensemble.",
                 bold_word="FrameDiff")
        w.bullet("EigenFold (Jing et al., 2023): decomposes protein structure along a hierarchy "
                 "of spring-network eigenmodes, performing diffusion along each independently.",
                 bold_word="EigenFold")
        w.bullet("AlphaFlow (Jing et al., ICML 2024): fine-tunes AlphaFold2 as a flow-matching "
                 "model conditioned on MSAs, enabling ensemble prediction for evolutionary context.",
                 bold_word="AlphaFlow")
        w.bullet("BioEmu (Lewis et al., Science 2025): large-scale diffusion model on MD "
                 "trajectories and experimental data; strong equilibrium ensemble predictions.",
                 bold_word="BioEmu")

        w.callout(
            "Shared limitation: temporal incoherence. All of the above generate INDEPENDENT "
            "conformational samples. While they may approximate the marginal equilibrium "
            "distribution p(x), they cannot reproduce ANY temporal property: (1) the "
            "autocorrelation function C(τ) drops to zero immediately at lag τ≥1 for i.i.d. "
            "samplers; (2) frame-to-frame step size is arbitrarily large instead of ~0.1–0.3 Å; "
            "(3) transition pathway information is completely inaccessible.")

        w.subsection("4.4", "Static Structure Prediction Models")

        w.bullet("AlphaFold2 (Jumper et al., 2021): near-experimental accuracy for single lowest-"
                 "energy structure prediction. Produces one structure per input; not designed for "
                 "ensemble generation or dynamics.",
                 bold_word="AlphaFold2")
        w.bullet("ESMFold (Lin et al., 2023): extends ESM-2 language model to fast single-structure "
                 "prediction without MSA. MDGen uses it only for initial conditioning structure.",
                 bold_word="ESMFold")
        w.bullet("RFdiffusion (Watson et al., 2023) and Chroma (Ingraham et al., 2023): diffusion "
                 "models for protein design—generating novel backbone conformations satisfying "
                 "functional constraints. Not evaluated on MD ensemble fidelity metrics.",
                 bold_word="RFdiffusion/Chroma")

        w.subsection("4.5", "Summary Comparison Table")

        w.table(
            headers=["Method", "Equil. Ensemble", "Temporal Coh.", "Speed vs MD", "Large Proteins"],
            rows=[
                ["MD simulation",         "[Y]", "[Y]", "1× (baseline)", "[Y]"],
                ["NMA",                   "~", "[N]", "~1000×",        "[Y]"],
                ["Boltzmann generators",  "[Y]", "[N]", "~1000×",        "[N]"],
                ["EigenFold / AlphaFlow", "[Y]", "[N]", "~10000×",       "[Y]"],
                ["BioEmu",                "[Y]", "[N]", "~10000×",       "[Y]"],
                ["MDGen (this work)",     "[Y]", "[Y]", "~10000×",       "[Y]"],
            ],
            col_widths=[0.34, 0.15, 0.15, 0.18, 0.18]
        )

        # ── 5. MDGEN METHOD ─────────────────────────────────────────
        w.section("5", "MDGen: Method")
        w.subsection("5.1", "Problem Formulation")

        w.callout(
            "Definition (Trajectory generation). Given a protein amino-acid sequence "
            "s = (s₁,…,sN), generate a trajectory window X = (x₁,…,xT) ∈ (SE(3)^N × T^{4N})^T "
            "such that the joint distribution p_θ(X|s) approximates the distribution over "
            "T-frame windows drawn from equilibrium MD trajectories.")

        w.para("This formulation imposes two simultaneous requirements:")
        w.bullet("Equilibrium marginal correctness: for any single time t, the marginal p(xₜ|s) "
                 "matches the MD equilibrium distribution.")
        w.bullet("Temporal coherence: the joint distribution p(xₜ, xₜ₊₁|s) reflects the "
                 "physically correct Markov transition structure of MD dynamics.")

        w.subsection("5.2", "Forward Diffusion Process over Trajectory Space")

        w.para(
            "MDGen applies independent noise to each trajectory frame, keeping the forward "
            "process factorised over the time axis. For a clean trajectory X^(0) at diffusion "
            "level s=0 and noisy trajectory X^(s) at level s ∈ [0,S]:")

        w.equation(
            r"q(\mathbf{X}^{(s)} | \mathbf{X}^{(0)}) = \prod_{t=1}^{T} q(\mathbf{x}_t^{(s)} | \mathbf{x}_t^{(0)})",
            "(13)")

        w.para(
            "Within each frame, diffusion is factorised over geometric components:")

        w.equation(
            r"q(\mathbf{x}_t^{(s)} | \mathbf{x}_t^{(0)}) = q_{\mathbb{R}^3}(\mathbf{t}^{(s)}|\mathbf{t}^{(0)}) \cdot q_{SO(3)}(R^{(s)}|R^{(0)}) \cdot q_{\mathbb{T}}(\chi^{(s)}|\chi^{(0)})",
            "(14)")

        w.callout(
            "Key insight: although frames are noised independently in the forward process, the "
            "reverse process denoises ALL T frames jointly. Temporal correlations are entirely a "
            "property of the LEARNED denoising network—encoded by the temporal attention layers.")

        w.subsection("5.3", "Neural Architecture")
        w.subsubsection("5.3.1  Sequence Encoder: ESM-2")

        w.para(
            "The protein sequence s is embedded by the pre-trained protein language model "
            "ESM-2 (Lin et al., 2023) into per-residue feature vectors h_i^seq ∈ R^d_seq. "
            "ESM-2 is kept frozen during MDGen training. Its representations capture evolutionary "
            "and physicochemical information about each residue, serving as a rich conditioning "
            "signal projected to internal model dimension d via a learned linear layer.")

        w.subsubsection("5.3.2  Spatial Attention: Invariant Point Attention (IPA)")

        w.para(
            "At each trajectory frame t, inter-residue information exchange is mediated by "
            "Invariant Point Attention (IPA; Jumper et al., 2021). IPA augments standard "
            "multi-head attention with 3D query/key point pairs expressed in each residue's "
            "local backbone frame. The attention score between residues i and j is:")

        w.equation(
            r"a_{ij} = \mathrm{softmax}_j\!\left(\frac{\mathbf{q}_i^\top \mathbf{k}_j}{\sqrt{d}} - \frac{\gamma}{2}\sum_h \|T_i\,\mathbf{p}_i^{(h)} - T_j\,\mathbf{p}_j^{(h)}\|^2\right)",
            "(15)")

        w.para(
            "where T_i = (R_i, t_i) maps local frame points to global coordinates, p_i^(h) are "
            "learned 3D query points in residue i's local frame, and γ > 0 is a learnable scalar. "
            "The attention is SE(3)-invariant: ‖T_i p − T_j q‖ is unchanged by any global "
            "rotation or translation. Two residues that are distant in sequence but close in 3D "
            "space receive a high attention weight, enabling the model to reason about spatial "
            "contacts across the entire structure.")

        w.subsubsection("5.3.3  Temporal Attention: Axial Attention Across Time (Key Innovation)")

        w.para(
            "The defining architectural innovation in MDGen is the introduction of axial temporal "
            "attention (Ho et al., 2019). After the spatial IPA pass (across residues at fixed t), "
            "a temporal attention pass operates across all T time steps for each residue i:")

        w.equation(
            r"\mathbf{h}_{i,t}^{new} = \sum_{t'=1}^{T} \alpha_{tt'}\,\mathbf{v}_{i,t'},\quad \alpha_{tt'} = \mathrm{softmax}_{t'}(\frac{\mathbf{q}_{i,t} \cdot \mathbf{k}_{i,t'}}{\sqrt{d}})",
            "(16)")

        w.para(
            "The temporal attention layer allows every time step to attend to every other time "
            "step within the trajectory window. This is precisely the mechanism through which "
            "MDGen learns that consecutive frames should be physically similar: the loss penalises "
            "temporally incoherent predictions, and temporal attention weights adapt to propagate "
            "continuity information along the time axis.")

        w.para(
            "The spatial and temporal attention layers alternate in a stack of L blocks, constituting "
            "an axial attention transformer over the N × T grid of (residue, frame) tokens:")

        w.bullet("IPA_l: spatial pass—all N residues exchange information at each fixed frame t.")
        w.bullet("TempAttn_l: temporal pass—each residue i attends across frames t=1,…,T.")
        w.bullet("FFN_l: position-wise feed-forward network.")

        w.subsubsection("5.3.4  Score Head")

        w.para(
            "After L alternating blocks, separate prediction heads convert the latent representation "
            "h_{i,t}^(L) into predicted noise for each geometric component: "
            "ε^trans_{i,t} ∈ R³, ε^rot_{i,t} ∈ so(3), ε^tors_{i,t} ∈ R⁴. "
            "The rotation score is expressed as a vector in the tangent space of the Lie algebra "
            "so(3) ~ R³. Total parameter count: ~100M.")

        w.subsection("5.4", "Training Objective")

        w.para(
            "The training loss is a weighted sum of denoising score matching losses for each "
            "geometric component, plus a structural violation penalty:")

        w.equation(
            r"\mathcal{L} = \mathbb{E}_{s,\mathbf{X}^{(0)},\mathbf{X}^{(s)}}[\lambda_{trans}\mathcal{L}_{\mathbb{R}^3} + \lambda_{rot}\mathcal{L}_{SO(3)} + \lambda_{tors}\mathcal{L}_{\mathbb{T}} + \lambda_{viol}\mathcal{L}_{viol}]",
            "(17)")

        w.bullet("L_trans = (1/NT) Σ_{i,t} ‖ε̂^trans − ε^trans‖²: standard MSE on Cα displacements. (λ=1.0)")
        w.bullet("L_rot: Riemannian score matching loss on the SO(3) manifold. (λ≈1.0)")
        w.bullet("L_tors: wrapped Gaussian score matching for torsion angles. (λ≈0.5)")
        w.bullet("L_viol: pairwise steric clash penalty + backbone bond-geometry violations. (λ≈0.01)")

        w.para(
            "All N residues and all T=16 frames contribute to each gradient update. Diffusion "
            "noise level s ~ Uniform(0, S) with S=500. Optimiser: AdamW, lr=1e-4, cosine "
            "annealing, batch size ≈64 windows, on 8 × A100 GPUs.")

        w.subsection("5.5", "Inference: Sampling")

        w.para(
            "Sampling runs the reverse diffusion starting from pure noise for all T frames "
            "simultaneously: translations ~ N(0,I), rotations ~ Uniform(SO(3)), "
            "torsions ~ Uniform(T⁴). MDGen supports two modes:")

        w.bullet("DDPM (500 steps): stochastic reverse process; highest sample quality; ~minutes per trajectory.")
        w.bullet("DDIM (50 steps): deterministic ODE; 10× faster than DDPM with minimal quality loss; ~seconds per trajectory.")

        w.callout(
            "Both modes produce trajectories approximately 10,000× faster than equivalent "
            "explicit-solvent MD simulation.")

        w.subsection("5.6", "Trajectory Extension via Diffusion Inpainting")

        w.para(
            "MDGen can generate trajectories conditioned on a known conformation x₁^(0) "
            "(e.g. a crystal structure) using diffusion inpainting (Lugmayr et al., 2022). "
            "During reverse diffusion, the first-frame variable is periodically replaced with "
            "its correctly-noised counterpart:")

        w.equation(
            r"\mathbf{x}_1^{(s)} \leftarrow \sqrt{\bar\alpha_s}\,\mathbf{x}_1^{(0)} + \sqrt{1-\bar\alpha_s}\,\epsilon",
            "(18)")

        w.para(
            "Interpolation mode: conditioning on BOTH x₁^(0) and x_T^(0) generates a plausible "
            "transition pathway between two known protein conformations (e.g. open ↔ closed "
            "states of adenylate kinase). This capability for transition path sampling without "
            "enhanced-sampling MD has no equivalent in any prior independent-frame sampler.")

        # ── 6. ATLAS DATA ─────────────────────────────────────────
        w.section("6", "Training Data: The ATLAS Database")

        w.para(
            "MDGen is trained on the ATLAS (Atlas of Trajectory Landscapes and Associated "
            "Simulations) database (Vander Meersche et al., Nucleic Acids Research, 2024), "
            "the largest open repository of protein MD trajectories assembled specifically "
            "to support machine learning on protein dynamics.")

        w.para("Simulation protocol:")
        w.bullet("Force field: AMBER ff14SB with explicit TIP3P water, NPT ensemble, 300 K, 1 atm.")
        w.bullet("Three independent 100 ns replicas per protein → 300 ns total per protein.")
        w.bullet("Frames saved every 1 ns → ~300 frames per protein.")
        w.bullet("Simulation time step: 2 fs with SHAKE constraints on hydrogen bonds.")

        w.para("Dataset statistics:")
        w.bullet("~1,400 diverse proteins from the PDB, spanning all major fold classes: α, β, α/β, IDPs.")
        w.bullet("Proteins range from ~50 to ~500 residues.")
        w.bullet("Aggregate simulation time: ~1.2 μs across all proteins and replicas.")
        w.bullet("Train split: ~1,265 proteins; Test split: ~135 proteins.")

        w.para(
            "During training, a random contiguous window of T=16 consecutive frames is extracted "
            "from each replica trajectory per minibatch. Overlapping windows are permitted as "
            "data augmentation.")

        # ── 7. EVALUATION AND RESULTS ─────────────────────────────
        w.section("7", "Evaluation Protocol and Results")
        w.subsection("7.1", "Evaluation Metrics")

        w.subsubsection("7.1.1  Root Mean Square Fluctuation (RMSF)")
        w.para(
            "RMSF quantifies per-residue positional flexibility, measuring how much each "
            "residue's Cα position deviates from its time-averaged position:")
        w.equation(
            r"\mathrm{RMSF}_i = \sqrt{\frac{1}{T}\sum_{t=1}^{T}\|\mathbf{r}_i(t) - \langle\mathbf{r}_i\rangle\|^2}",
            "(19)")
        w.para(
            "High RMSF → flexible region (loops, termini). Low RMSF → rigid region "
            "(helices, β-sheets). The primary summary metric is Pearson correlation r between "
            "generated and reference MD RMSF profiles, averaged over all test proteins.")

        w.subsubsection("7.1.2  Ramachandran Distribution: Jensen–Shannon Divergence")
        w.para(
            "The Ramachandran plot captures the joint distribution of backbone dihedral angles "
            "(φ, ψ). MDGen's generated (φ, ψ) distribution is compared to reference MD using the "
            "Jensen–Shannon divergence (JSD), discretised over a 36×36 grid. Lower JSD = better.")

        w.subsubsection("7.1.3  Temporal Metrics")
        w.para("Two metrics test temporal coherence—quantities impossible to evaluate from i.i.d. samplers:")
        w.bullet("Frame-to-frame RMSD Δ_t: in real MD, consecutive frames differ by only "
                 "~0.1–0.3 Å Cα RMSD. Independent samplers show arbitrarily large jumps.")
        w.bullet("Temporal autocorrelation function C(τ) = ⟨δr(t)·δr(t+τ)⟩ / ⟨|δr(t)|²⟩: "
                 "measures structural persistence. Physical trajectories decay smoothly from "
                 "C(0)=1. i.i.d. samplers have C(τ)=0 for τ≥1 by definition.")

        w.subsection("7.2", "Quantitative Results")

        w.table(
            headers=["Method", "RMSF r ↑", "Ramach. JSD ↓", "Frame ΔRMSD", "ACF Match", "Speed"],
            rows=[
                ["Reference MD",         "1.00", "0.00", "ground truth", "ground truth", "1×"],
                ["MDGen (DDPM)",          "~0.87", "~0.08", "[Y] matches",   "[Y] matches",   "~10⁴×"],
                ["MDGen (DDIM)",          "~0.85", "~0.09", "[Y] matches",   "[Y] matches",   "~10⁵×"],
                ["Indep. frame diffusion","~0.71", "~0.11", "[N] rand. jumps","[N] zero lag",  "~10⁴×"],
                ["Normal Mode Analysis",  "~0.64", "~0.19", "harmonic only","harmonic only","~10³×"],
                ["Boltzmann generators",  "~0.68", "~0.14", "[N] i.i.d.",    "[N] zero lag",  "~10³×"],
            ],
            col_widths=[0.28, 0.10, 0.14, 0.16, 0.14, 0.18]
        )

        w.para(
            "MDGen achieves Pearson r ≈ 0.87 on per-residue RMSF, substantially outperforming "
            "both NMA (r ≈ 0.64) and independent-frame diffusion (r ≈ 0.71). Improvement over "
            "independent-frame diffusion indicates that temporal context improves equilibrium "
            "ensemble quality as well as kinetics—temporal attention acts as an informative prior "
            "constraining physically accessible conformation space. Only MDGen reproduces correct "
            "temporal autocorrelation functions and frame-to-frame step-size distributions.")

        w.subsection("7.3", "Generalisation to Out-of-Distribution Fast-Folding Proteins")

        w.para(
            "MDGen is evaluated on miniproteins from long reference simulations that were NOT in "
            "the ATLAS training set: Trp-cage (20 residues), BBA motif (28 residues), villin "
            "headpiece (35 residues), WW domain (35 residues), NTL9 (39 residues), Chignolin "
            "(10 residues). MDGen correctly identifies qualitative flexibility profiles for these "
            "proteins—flexible C-terminal helices, rigid hydrophobic cores, elevated RMSF in loop "
            "regions—demonstrating generalisation across fold space beyond the ATLAS distribution.")

        # ── 8. APPLICATIONS ────────────────────────────────────────
        w.section("8", "Applications")
        w.subsection("8.1", "Cryptic Pocket Discovery in Drug Design")

        w.para(
            "Approximately 50% of protein drug targets undergo conformational changes critical for "
            "inhibitor binding. Cryptic pockets—absent in the static crystal structure but "
            "transiently open during dynamics (Oleinikovas et al., 2016)—are missed entirely by "
            "static docking, contributing to high false-negative rates in virtual screening.")

        w.para("MDGen workflow for cryptic pocket discovery:")
        w.bullet("Generate 10²–10³ backbone trajectory frames using MDGen (seconds–minutes on one GPU).")
        w.bullet("Run pocket detection software (FPOCKET, SiteMap) on each frame.")
        w.bullet("Identify pockets that appear transiently across the ensemble.")
        w.bullet("Prioritise pockets for downstream docking and lead optimisation.")

        w.para(
            "This approach mirrors ensemble docking (Totrov & Abagyan, 2008) but replaces "
            "expensive multi-μs MD with MDGen-generated ensembles 3–4 orders of magnitude "
            "faster. MDGen's correct temporal autocorrelation ensures conformational transitions "
            "consistent with natural protein dynamics.")

        w.subsection("8.2", "Intrinsically Disordered Proteins (IDPs) and Disease")

        w.para(
            "Intrinsically disordered proteins (IDPs; Uversky, 2019) lack a stable folded "
            "structure and exist as highly dynamic conformational ensembles. They are medically "
            "critical, frequently driving aberrant condensate formation and aggregation in "
            "neurodegenerative diseases.")

        w.bullet("α-Synuclein (Parkinson's disease): ~140-residue IDP; conformational ensemble "
                 "determines nucleation and growth pathways of toxic amyloid fibrils.",
                 bold_word="α-Synuclein")
        w.bullet("Tau (Alzheimer's disease): highly flexible repeat domain; disordered regions "
                 "initiate neurofibrillary tangle formation.",
                 bold_word="Tau")
        w.bullet("p53 (cancer): most frequently mutated tumour suppressor; disordered N/C-terminal "
                 "regions mediate transactivation through conformational dynamics.",
                 bold_word="p53")

        w.para(
            "Static predictors such as AlphaFold2 report low-confidence (pLDDT < 50) predictions "
            "for disordered regions—a diagnostic flag, not a structural answer. MDGen generates "
            "backbone conformational ensembles for these regions, providing the distribution of "
            "conformations rather than a misleading single coordinate set.")

        w.subsection("8.3", "Ensemble-Aware Protein Engineering")
        w.bullet("Mutational scanning: rapidly generate conformational ensembles for point mutants "
                 "to predict effects on dynamics without re-running MD.")
        w.bullet("Allosteric pathway mapping: condition on two allosteric states and use "
                 "interpolation mode to identify signal-transmitting residues.")
        w.bullet("Antibody CDR loop flexibility: characterise CDR loop dynamics governing "
                 "antigen recognition and binding affinity.")

        # ── 9. LIMITATIONS ─────────────────────────────────────────
        w.section("9", "Limitations")

        w.bullet("Fixed timescale window: T=16 frames ~ 16 ns. Millisecond-scale processes "
                 "(full folding, large domain translocations) are out of scope.",
                 bold_word="Fixed timescale")
        w.bullet("Training distribution bias: ATLAS predominantly contains single-chain, globular, "
                 "soluble proteins (50–500 residues). Membrane proteins, large complexes, and "
                 "heavily post-translationally modified proteins are under-represented.",
                 bold_word="Training distribution bias")
        w.bullet("Implicit solvent statistics: MDGen learns from explicit-solvent MD but does not "
                 "model solvent explicitly. Hydration shell dynamics and specific ion binding "
                 "are only implicitly captured insofar as they manifest in backbone motions.",
                 bold_word="Implicit solvent")
        w.bullet("Force-field dependency: generated trajectories emulate AMBER ff14SB statistics. "
                 "Systematic force-field errors are inherited by MDGen—it is a data-driven emulator, "
                 "not an independent physics engine.",
                 bold_word="Force-field dependency")
        w.bullet("Backbone-only representation: side-chain coordinates must be reconstructed "
                 "post-hoc using Rosetta Relax or DLPacker, limiting direct use in atom-level "
                 "applications (e.g. binding free energy calculations).",
                 bold_word="Backbone-only")
        w.bullet("Rare barrier crossings: conformational transitions requiring crossing high "
                 "energy barriers (rare events on μs+ timescales) are statistically improbable "
                 "within a 16-frame window.",
                 bold_word="Rare barrier crossings")

        # ── 10. FUTURE DIRECTIONS ──────────────────────────────────
        w.section("10", "Future Directions")

        w.bullet("Full-atom trajectory generation: jointly model backbone frames and all-atom "
                 "side-chain coordinates as a unified diffusion model—enabling direct computation "
                 "of binding free energies and pharmacophoric features.",
                 bold_word="Full-atom generation")
        w.bullet("Longer timescales: training on μs-scale datasets (D.E. Shaw Research Anton) "
                 "or enhanced-sampling trajectories (metadynamics, REST2) to unlock rarer "
                 "conformational transitions.",
                 bold_word="Longer timescales")
        w.bullet("Protein–ligand dynamics: extending to receptor–ligand systems for ensemble-aware "
                 "docking and entropic contributions to binding affinity (ΔG = ΔH − TΔS).",
                 bold_word="Protein–ligand dynamics")
        w.bullet("Conditioning on experimental observables: incorporating NMR chemical shifts, "
                 "SAXS profiles, or cryo-EM density maps as soft conditioning signals during "
                 "inference for physics-guided ensemble refinement.",
                 bold_word="Experimental conditioning")
        w.bullet("Beyond proteins: RNA, DNA, carbohydrates, and lipid membranes all undergo "
                 "important conformational dynamics. The SE(3) trajectory diffusion framework "
                 "can be adapted for these classes with appropriate geometric representations.",
                 bold_word="Beyond proteins")

        # ── 11. CONCLUSION ─────────────────────────────────────────
        w.section("11", "Conclusion")

        w.para(
            "MDGen represents a conceptual advance in generative molecular modelling. By framing "
            "the problem as trajectory generation rather than independent equilibrium sampling, "
            "MDGen is the first model to simultaneously achieve:")

        w.bullet("High per-residue RMSF correlation with reference MD (r ≈ 0.87 vs NMA r ≈ 0.64).")
        w.bullet("Physically correct Ramachandran backbone dihedral distributions (JSD ≈ 0.08).")
        w.bullet("Correct temporal autocorrelation functions and frame-to-frame step-size "
                 "distributions — metrics that no prior independent-frame sampler can reproduce.")
        w.bullet("~10,000× speed-up over equivalent explicit-solvent MD simulation.")

        w.para(
            "The architectural innovations enabling this — SE(3)-equivariant Invariant Point "
            "Attention (spatial) combined with temporal axial attention (kinetic) — provide a "
            "template for incorporating physical symmetries and temporal structure into generative "
            "models for other molecular and biological systems.")

        w.callout(
            "MDGen's central intellectual contribution: MD trajectories should be treated as "
            "the PRIMARY generative target, not a source of independent equilibrium samples. "
            "This reframing enables models to learn both the thermodynamics (what conformations "
            "are accessible) AND the dynamics (how fast they interconvert) of protein motion "
            "from data — a template for how generative AI can emulate complex physical processes.")

        # ── REFERENCES ─────────────────────────────────────────────
        w.section("References", "")
        w.y += 0.01

        refs = [
            "[1] Jing, B., Stärk, H., Jaakkola, T., & Berger, B. (2024). Generative Molecular "
            "Dynamics. arXiv:2409.17808. NeurIPS 2024. Code: github.com/bjing2016/mdgen",
            "[2] Vander Meersche, Y. et al. (2024). ATLAS: Protein Flexibility Description from "
            "Atomistic Molecular Dynamics Simulations. Nucleic Acids Research, 52(D1), D384–D392.",
            "[3] Jumper, J. et al. (2021). Highly accurate protein structure prediction with "
            "AlphaFold. Nature, 596(7873), 583–589.",
            "[4] Ho, J., Jain, A., & Abbeel, P. (2020). Denoising diffusion probabilistic models. "
            "NeurIPS 2020, 33, 6840–6851.",
            "[5] Song, Y. et al. (2021). Score-based generative modeling through stochastic "
            "differential equations. ICLR 2021.",
            "[6] Song, J., Meng, C., & Ermon, S. (2021). Denoising diffusion implicit models. "
            "ICLR 2021.",
            "[7] Lin, Z. et al. (2023). Evolutionary-scale prediction of atomic-level protein "
            "structure with a language model. Science, 379(6637), 1123–1130.",
            "[8] Watson, J.L. et al. (2023). De novo design of protein structure and function "
            "with RFdiffusion. Nature, 620(7976), 1089–1100.",
            "[9] Adcock, S.A., & McCammon, J.A. (2006). Molecular dynamics: survey of methods. "
            "Chemical Reviews, 106(5), 1589–1615.",
            "[10] Shaw, D.E. et al. (2010). Atomic-level characterization of structural dynamics. "
            "Science, 330(6002), 341–346.",
            "[11] Lindorff-Larsen, K. et al. (2011). How fast-folding proteins fold. "
            "Science, 334(6055), 517–520.",
            "[12] De Bortoli, V. et al. (2022). Riemannian score-based generative modelling. "
            "NeurIPS 2022, 35, 2406–2422.",
            "[13] Yim, J. et al. (2023). SE(3) diffusion model for protein backbone generation. "
            "ICML 2023.",
            "[14] Jing, B. et al. (2023). EigenFold: Generative protein structure prediction "
            "with diffusion models. ICLR 2023 Workshop.",
            "[15] Jing, B., Berger, B., & Jaakkola, T. (2024). AlphaFold meets flow matching "
            "for generating protein ensembles. ICML 2024.",
            "[16] Lewis, S.M. et al. (2025). Scalable emulation of protein equilibrium ensembles. "
            "Science, 388(6748).",
            "[17] Noé, F. et al. (2019). Boltzmann generators: sampling equilibrium states. "
            "Science, 365(6457), eaaw1147.",
            "[18] Tirion, M.M. (1996). Large amplitude elastic motions in proteins. "
            "Physical Review Letters, 77(9), 1905.",
            "[19] Maier, J.A. et al. (2015). ff14SB: improving accuracy of protein parameters. "
            "J. Chem. Theory Comput., 11(8), 3696–3713.",
            "[20] Frauenfelder, H., Sligar, S.G., & Wolynes, P.G. (1991). Energy landscapes "
            "and motions of proteins. Science, 254(5038), 1598–1603.",
            "[21] Fuchs, F.B. et al. (2020). SE(3)-Transformers: 3D roto-translation equivariant "
            "attention networks. NeurIPS 2020, 33, 1970–1981.",
            "[22] Satorras, V.G. et al. (2021). E(n) equivariant graph neural networks. ICML 2021.",
            "[23] Vincent, P. (2011). A connection between score matching and denoising autoencoders. "
            "Neural Computation, 23(7), 1661–1674.",
            "[24] Loshchilov, I., & Hutter, F. (2019). Decoupled weight decay regularization. "
            "ICLR 2019.",
            "[25] Lugmayr, A. et al. (2022). Repaint: Inpainting using denoising diffusion "
            "probabilistic models. CVPR 2022.",
            "[26] Jing, B. et al. (2022). Torsional diffusion for molecular conformer generation. "
            "NeurIPS 2022, 35, 24240–24253.",
            "[27] Ho, J. et al. (2019). Axial attention in multidimensional transformers. "
            "arXiv:1912.12180.",
            "[28] Oleinikovas, V. et al. (2016). Understanding cryptic pocket formation. "
            "J. Am. Chem. Soc., 138(43), 14257–14263.",
            "[29] Uversky, V.N. (2019). Intrinsically disordered proteins and their physics. "
            "Frontiers in Physics, 7, 10.",
            "[30] Ingraham, J.B. et al. (2023). Illuminating protein space with RFdiffusion. "
            "Nature, 623(7989), 1070–1078.",
        ]

        for ref in refs:
            lines = textwrap.wrap(ref, width=93)
            for i, line in enumerate(lines):
                w._check(0.025)
                x = 0.04 if i > 0 else 0
                w.ax.text(x, w.y, line, fontsize=SMALL_FONT, color=INK)
                w.y -= 0.020
            w.y -= 0.004

        w.end()

    print(f"PDF written to {path}")


if __name__ == '__main__':
    build_pdf('/Users/indraniroy/Documents/Github/web-presentation/mdgen/mdgen_survey.pdf')
