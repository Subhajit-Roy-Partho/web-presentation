#!/usr/bin/env python3
"""
MDGen Survey PDF generator — clean single-line layout engine.
Every rendered element is one ax.text() call; no inline bold/normal mixing.
All text anchored at va='top' so the y-cursor is always the TOP of content.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
import textwrap

# ── Colour palette ────────────────────────────────────────────
TEAL  = '#0b7285'
RUST  = '#c2410c'
INK   = '#102522'
MUTED = '#53625e'
BGLT  = '#e8f3ef'

# ── Page geometry (Letter: 8.5 × 11 inches) ──────────────────
PW, PH = 8.5, 11.0
LM = 1.05          # left margin (in)
BM = 0.80          # bottom margin
TM = 0.90          # top margin
TW = PW - 2 * LM  # text width
TH = PH - TM - BM  # text height

# axes box as fractions of the full figure
AX_L = LM / PW
AX_B = BM / PH
AX_W = TW / PW
AX_H = TH / PH

# ── Font sizes ────────────────────────────────────────────────
FS_BODY   = 10
FS_SMALL  = 8.5
FS_SEC    = 14
FS_SSEC   = 11
FS_SSSEC  = 10
FS_FOOT   = 7.5

# ── Line heights (axis-fraction units; 1 unit = TH inches) ───
# 1 axis unit = TH inches = 9.3 in → 1 pt = 1/72/9.3 ≈ 0.0015
LH_BODY  = 0.028   # generous leading for 10 pt body text
LH_SMALL = 0.025
LH_SEC   = 0.048   # section header
LH_SSEC  = 0.038
LH_SSSEC = 0.032
LH_EQ    = 0.058   # display equation (allows for fractions)

PARA_GAP  = 0.010  # extra space after each paragraph / block
SEC_ABOVE = 0.020  # extra space before a section heading

matplotlib.rcParams.update({
    'font.family':        'DejaVu Serif',
    'mathtext.fontset':   'dejavuserif',
    'axes.facecolor':     'none',
    'figure.facecolor':   'white',
})


# ── Helpers ───────────────────────────────────────────────────

def new_fig():
    fig = plt.figure(figsize=(PW, PH))
    fig.patch.set_facecolor('white')
    return fig


def make_text_ax(fig):
    ax = fig.add_axes([AX_L, AX_B, AX_W, AX_H])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    return ax


def draw_footer(fig, page_num):
    ax = fig.add_axes([AX_L, 0.025, AX_W, 0.045])
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
    ax.axhline(0.90, color=TEAL, lw=0.7)
    ax.text(0,   0.25, 'MDGen: Generative Molecular Dynamics — Technical Survey',
            fontsize=FS_FOOT, color=MUTED, va='bottom')
    ax.text(1.0, 0.25, str(page_num),
            fontsize=FS_FOOT, color=MUTED, ha='right', va='bottom')


# ── Page Writer ───────────────────────────────────────────────

class Doc:
    """
    Cursor-based document writer.
    self.y is always the TOP of the next element (axis fraction, 0=bottom 1=top).
    All text uses va='top' so the element occupies [y-height, y].
    """

    MARGIN_TOP  = 0.985   # start just below the very top of the text area
    PAGE_BOTTOM = 0.030   # minimum y before forcing a new page

    def __init__(self, pdf_path):
        self._pdf_path = pdf_path
        self._pdf      = None     # opened in __enter__
        self.page      = 0
        self.fig       = None
        self.ax        = None
        self.y         = self.MARGIN_TOP

    def __enter__(self):
        self._pdf = PdfPages(self._pdf_path)
        self._new_page()
        return self

    def __exit__(self, *_):
        self._flush()
        self._pdf.close()

    # ── internal ─────────────────────────────────────────────

    def _new_page(self):
        self.fig = new_fig()
        self.ax  = make_text_ax(self.fig)
        self.y   = self.MARGIN_TOP
        self.page += 1

    def _flush(self):
        draw_footer(self.fig, self.page)
        self._pdf.savefig(self.fig, bbox_inches='tight')
        plt.close(self.fig)

    def _need(self, height):
        """Ensure at least `height` axis-units remain; page-break if not."""
        if self.y - height < self.PAGE_BOTTOM:
            self._flush()
            self._new_page()

    def _put(self, text, x=0.0, size=FS_BODY, color=INK,
             weight='normal', style='normal', ha='left'):
        """Place one text line at current y (va=top), advance cursor."""
        self.ax.text(x, self.y, text,
                     fontsize=size, color=color,
                     fontweight=weight, fontstyle=style,
                     ha=ha, va='top')

    def _advance(self, line_h):
        self.y -= line_h

    # ── public API ───────────────────────────────────────────

    def vspace(self, h=PARA_GAP):
        self._need(h)
        self._advance(h)

    def hline(self, color=TEAL, lw=0.6, margin=0.0):
        self._need(0.010)
        self.ax.axhline(self.y, xmin=margin, xmax=1 - margin,
                        color=color, linewidth=lw)
        self._advance(0.010)

    # ── Section / subsection headings ────────────────────────

    def section(self, number, title):
        need = LH_SEC + 0.014 + SEC_ABOVE
        self._need(need)
        self.vspace(SEC_ABOVE)
        label = f'{number}   {title}' if number else title
        self._put(label, size=FS_SEC, weight='bold', color=INK)
        self._advance(LH_SEC)
        self.hline(TEAL, lw=0.7)
        self.vspace(0.006)

    def subsection(self, number, title):
        need = LH_SSEC + 0.012
        self._need(need)
        self.vspace(0.012)
        self._put(f'{number}  {title}', size=FS_SSEC, weight='bold', color=INK)
        self._advance(LH_SSEC)
        self.vspace(0.004)

    def subsubsection(self, title):
        need = LH_SSSEC + 0.010
        self._need(need)
        self.vspace(0.008)
        self._put(title, size=FS_SSSEC, style='italic', color=MUTED)
        self._advance(LH_SSSEC)
        self.vspace(0.004)

    # ── Body text ─────────────────────────────────────────────

    def para(self, text, indent=0.0, size=FS_BODY, color=INK):
        """Paragraph: word-wrap, one ax.text per line, single style."""
        col_w = int(88 - indent * 120)
        col_w = max(col_w, 40)
        lines = textwrap.wrap(text, width=col_w)
        for line in lines:
            self._need(LH_BODY)
            self._put(line, x=indent, size=size, color=color)
            self._advance(LH_BODY)
        self.vspace(PARA_GAP)

    def bold_para(self, bold_part, rest='', indent=0.0):
        """
        Renders a paragraph whose FIRST LINE starts with bold text.
        Bold part and rest are on separate lines to avoid width-estimation.
        bold_part ends with ':' by convention.
        """
        self._need(LH_BODY * 2)
        self._put(bold_part, x=indent, size=FS_BODY, weight='bold', color=INK)
        self._advance(LH_BODY)
        if rest:
            self.para(rest, indent=indent + 0.02)
        else:
            self.vspace(PARA_GAP)

    # ── Bullets ───────────────────────────────────────────────

    def bullet(self, text, indent=0.03, bold_label=None):
        """
        Bullet item.
        If bold_label given, renders:
            •  BOLD LABEL:
               body text indented one more level
        Otherwise renders:
            •  full text (word-wrapped, continuation lines indented)
        """
        sym = '•'   # •
        sym_w = 0.022    # width reserved for the bullet symbol

        if bold_label:
            # Line 1: bullet + bold label
            self._need(LH_BODY)
            self.ax.text(indent, self.y, sym,
                         fontsize=FS_BODY, color=TEAL, va='top')
            self.ax.text(indent + sym_w, self.y,
                         bold_label + ':',
                         fontsize=FS_BODY, color=INK,
                         fontweight='bold', va='top')
            self._advance(LH_BODY)
            # Continuation: body text, indented more
            body_indent = indent + sym_w + 0.01
            col_w = int(88 - body_indent * 120)
            lines = textwrap.wrap(text, width=max(col_w, 35))
            for line in lines:
                self._need(LH_BODY)
                self._put(line, x=body_indent, size=FS_BODY, color=INK)
                self._advance(LH_BODY)
        else:
            # Wrap the full text; first line gets bullet, rest indented
            body_indent = indent + sym_w
            col_w = int(88 - body_indent * 120)
            lines = textwrap.wrap(text, width=max(col_w, 40))
            for i, line in enumerate(lines):
                self._need(LH_BODY)
                if i == 0:
                    self.ax.text(indent, self.y, sym,
                                 fontsize=FS_BODY, color=TEAL, va='top')
                    self._put(line, x=body_indent, size=FS_BODY, color=INK)
                else:
                    self._put(line, x=body_indent, size=FS_BODY, color=INK)
                self._advance(LH_BODY)

        self.vspace(0.004)

    # ── Equations ─────────────────────────────────────────────

    def equation(self, latex, tag=''):
        """Centred display equation with optional right-hand tag."""
        self._need(LH_EQ + 0.010)
        self.vspace(0.006)
        try:
            self.ax.text(0.50, self.y, f'${latex}$',
                         fontsize=FS_BODY + 1, color=INK,
                         ha='center', va='top', usetex=False)
        except Exception:
            # Fallback: plain text if mathtext can't parse
            self.ax.text(0.50, self.y, latex,
                         fontsize=FS_BODY, color=INK,
                         ha='center', va='top')
        if tag:
            self.ax.text(0.99, self.y, tag,
                         fontsize=FS_BODY, color=MUTED,
                         ha='right', va='top')
        self._advance(LH_EQ)
        self.vspace(0.006)

    # ── Callout box ───────────────────────────────────────────

    def callout(self, text, bg=BGLT, border=TEAL):
        """Tinted highlight box. Renders line-by-line after drawing the box."""
        lines  = textwrap.wrap(text, width=82)
        n      = len(lines)
        pad    = 0.014
        box_h  = n * LH_BODY + 2 * pad

        self._need(box_h + 0.012)
        self.vspace(0.008)

        rect = mpatches.FancyBboxPatch(
            (0.02, self.y - box_h),
            0.96, box_h,
            boxstyle='round,pad=0.006',
            linewidth=1.2, edgecolor=border,
            facecolor=bg, zorder=1, clip_on=False)
        self.ax.add_patch(rect)

        ty = self.y - pad
        for line in lines:
            self.ax.text(0.05, ty, line,
                         fontsize=FS_BODY, color=INK,
                         va='top', zorder=2)
            ty -= LH_BODY

        self._advance(box_h)
        self.vspace(0.012)

    # ── Table ─────────────────────────────────────────────────

    def table(self, headers, rows, col_widths=None):
        """Simple grid table. Each cell wraps to a single line (truncated)."""
        nc = len(headers)
        if col_widths is None:
            col_widths = [1.0 / nc] * nc

        ROW_H = 0.028   # height of one table row

        # Estimate total needed height (header + all rows + gap)
        needed = ROW_H * (1 + len(rows)) + 0.016
        self._need(needed)
        self.vspace(0.008)

        # ── header row ───────────────────────────────────────
        # Draw background rectangle
        self.ax.add_patch(mpatches.Rectangle(
            (0, self.y - ROW_H), 1.0, ROW_H,
            facecolor=TEAL, edgecolor='none', zorder=1, clip_on=False))
        x = 0.0
        for h, cw in zip(headers, col_widths):
            self.ax.text(x + 0.006, self.y - ROW_H * 0.15,
                         str(h),
                         fontsize=FS_SMALL, color='white',
                         fontweight='bold', va='top', zorder=2, clip_on=False)
            x += cw
        self._advance(ROW_H)

        # ── data rows ────────────────────────────────────────
        for ri, row in enumerate(rows):
            bg = BGLT if ri % 2 == 0 else '#f7fbf9'
            self.ax.add_patch(mpatches.Rectangle(
                (0, self.y - ROW_H), 1.0, ROW_H,
                facecolor=bg, edgecolor='none', zorder=1, clip_on=False))
            x = 0.0
            for cell, cw in zip(row, col_widths):
                self.ax.text(x + 0.006, self.y - ROW_H * 0.18,
                             str(cell),
                             fontsize=FS_SMALL, color=INK,
                             va='top', zorder=2, clip_on=False)
                x += cw
            self._advance(ROW_H)

        self.vspace(0.012)


# ══════════════════════════════════════════════════════════════
# CONTENT
# ══════════════════════════════════════════════════════════════

def build(path):
    with Doc(path) as d:

        # ── TITLE PAGE ──────────────────────────────────────────────
        # (custom figure, not using Doc cursor)
        d._flush()          # save the blank first internal page
        d._new_page()       # fresh page for title

        fig = d.fig
        ax  = fig.add_axes([0, 0, 1, 1])
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')

        # header bar
        ax.add_patch(mpatches.Rectangle((0, 0.830), 1, 0.170,
                     facecolor=TEAL, edgecolor='none'))
        ax.text(0.5, 0.940, 'Technical Survey  ·  NeurIPS 2024',
                fontsize=11, color='white', ha='center', va='center',
                fontweight='bold')
        ax.text(0.5, 0.875, 'arXiv : 2409.17808',
                fontsize=10, color='#aeeeff', ha='center', va='center')

        # main title
        ax.text(0.5, 0.760,
                'MDGen: Generative Molecular Dynamics Simulation',
                fontsize=20, fontweight='bold', color=INK,
                ha='center', va='center')
        ax.text(0.5, 0.700,
                'A Comprehensive Technical Survey\n'
                'with Background, Prior Work, Architecture and Analysis',
                fontsize=12, color=MUTED, ha='center', va='center',
                linespacing=1.65)

        ax.axhline(0.648, xmin=0.12, xmax=0.88, color=TEAL, lw=0.9)

        ax.text(0.5, 0.616, 'Ditsa Mallick', fontsize=14, fontweight='bold',
                color=INK, ha='center', va='center')
        ax.text(0.5, 0.572,
                'School of Computing and Augmented Intelligence\n'
                'Arizona State University, Tempe AZ 85281\n'
                'dmallic1@asu.edu',
                fontsize=11, color=MUTED, ha='center', va='center',
                linespacing=1.6)

        ax.axhline(0.512, xmin=0.12, xmax=0.88, color=TEAL, lw=0.5)

        ax.text(0.5, 0.485, 'Based on:', fontsize=10, color=MUTED,
                ha='center', fontstyle='italic')
        ax.text(0.5, 0.450,
                'Jing B, Stark H, Jaakkola T, Berger B (2024). '
                'Generative Molecular Dynamics.\n'
                'arXiv:2409.17808. NeurIPS 2024.',
                fontsize=10, color=INK, ha='center', va='center',
                linespacing=1.5)

        # abstract box
        abstract = (
            'MDGen is the first generative model to produce temporally coherent, '
            'full-backbone protein trajectories at ~10,000x the speed of '
            'explicit-solvent molecular dynamics (MD). This survey provides a '
            'comprehensive technical exposition covering protein biophysics, '
            'denoising diffusion probabilistic models on non-Euclidean manifolds '
            '(SO(3), T^4), SE(3)-equivariance, and a complete landscape of prior '
            'work—Normal Mode Analysis, Boltzmann generators, and independent-frame '
            'diffusion models. The MDGen architecture alternates SE(3)-equivariant '
            'Invariant Point Attention (IPA) with temporal axial attention, '
            'enabling joint modelling of equilibrium thermodynamics and kinetic '
            'temporal structure. Trained on ATLAS (1,400 proteins x 300 ns each), '
            'MDGen achieves RMSF Pearson r approx 0.87, Ramachandran JSD approx 0.08, '
            'and correctly reproduces autocorrelation functions and frame-to-frame '
            'step-size distributions.')

        abs_lines = textwrap.wrap(abstract, width=88)
        box_top  = 0.390
        box_h    = len(abs_lines) * 0.026 + 0.038
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.06, box_top - box_h), 0.88, box_h,
            boxstyle='round,pad=0.01',
            linewidth=1.2, edgecolor=TEAL, facecolor=BGLT))
        ax.text(0.50, box_top - 0.012, 'Abstract', fontsize=11,
                fontweight='bold', color=TEAL, ha='center', va='top')
        ty = box_top - 0.042
        for line in abs_lines:
            ax.text(0.09, ty, line, fontsize=8.8, color=INK, va='top')
            ty -= 0.026

        ax.text(0.5, 0.028, 'May 2026', fontsize=9, color=MUTED, ha='center')
        draw_footer(fig, d.page)
        d._pdf.savefig(fig, bbox_inches='tight')
        plt.close(fig)
        d._new_page()   # start fresh page for body text

        # ══════════════════════════════════════════════════════════
        # 1. INTRODUCTION
        # ══════════════════════════════════════════════════════════
        d.section('1', 'Introduction')

        d.para(
            'Proteins are the primary molecular machines of living systems. They catalyse '
            'chemical reactions, transmit cellular signals, provide structural integrity, '
            'and execute the vast majority of biochemical functions essential for life. '
            'A protein\'s biological activity depends critically not only on its average '
            'three-dimensional structure but on its dynamical behaviour: the ensemble of '
            'conformations it explores at physiological temperature, the timescales of '
            'interconversion between states, and the kinetic pathways connecting them '
            '(Adcock & McCammon, 2006).')

        d.para(
            'Despite decades of progress in experimental structure determination—X-ray '
            'crystallography, cryo-EM, NMR spectroscopy—these methods report static or '
            'ensemble-averaged snapshots. Molecular dynamics (MD) simulation fills this '
            'gap by numerically integrating Newton\'s equations of motion for every atom, '
            'generating detailed time-series of atomic positions. Modern GPU-accelerated '
            'MD packages can simulate a 100-residue protein at ~100-200 ns per day. Yet '
            'biologically important timescales—domain motions, loop gating, folding '
            'transitions—occur on microsecond to millisecond timescales, spanning 9-12 '
            'orders of magnitude above the obligatory 2 fs integration time step. This '
            'timescale gap makes MD prohibitively expensive for large-scale ensemble '
            'characterisation or drug discovery campaigns.')

        d.callout(
            'Core motivation. MDGen asks: can a neural network, trained on a large corpus '
            'of MD trajectories, learn to generate new trajectory segments that faithfully '
            'reproduce both the equilibrium thermodynamics AND the kinetic temporal '
            'structure of real MD—without running the simulation itself?')

        d.para(
            'All prior generative models for protein conformations operate in an i.i.d. '
            'sampling regime: each sample is drawn independently from an approximation of '
            'the equilibrium distribution. Such models cannot reproduce temporal '
            'autocorrelation functions, kinetically realistic step sizes between '
            'consecutive frames, or any observable that depends on the ordering of '
            'configurations in time. MDGen (Jing et al., NeurIPS 2024) addresses this '
            'gap by posing the generative problem at the level of entire trajectory '
            'segments: given a protein sequence, generate T consecutive backbone frames '
            'whose joint distribution matches that of a real MD simulation. The key '
            'technical contribution is an architecture alternating SE(3)-equivariant '
            'Invariant Point Attention (IPA) with novel temporal axial attention. '
            'Trained on ATLAS (1,400 proteins x 300 ns each), MDGen achieves RMSF '
            'Pearson r ~0.87 and correct temporal kinetics at ~10,000x the speed of MD.')

        # ══════════════════════════════════════════════════════════
        # 2. BIOLOGICAL BACKGROUND
        # ══════════════════════════════════════════════════════════
        d.section('2', 'Biological and Physical Background')
        d.subsection('2.1', 'Proteins: Structure and Function')

        d.para(
            'A protein is a linear polymer of amino acid residues connected by peptide '
            'bonds. Twenty standard amino acids, differing only in their side chain, are '
            'encoded by the genetic code. Proteins range from tens to thousands of '
            'residues; a typical globular protein has 100-500 residues.')

        d.para('The structural hierarchy is decomposed into four levels:')
        d.bullet('Primary structure: the amino-acid sequence, a string over a 20-letter '
                 'alphabet.',
                 bold_label='Primary structure')
        d.bullet('Secondary structure: local backbone regularities—alpha-helices '
                 '(right-handed coils stabilised by i to i+4 hydrogen bonds) and '
                 'beta-strands (extended chains forming hydrogen-bonded beta-sheets).',
                 bold_label='Secondary structure')
        d.bullet('Tertiary structure: the complete 3D fold of a single polypeptide chain, '
                 'governed by hydrophobic packing, electrostatics, hydrogen bonding, and '
                 'van der Waals interactions.',
                 bold_label='Tertiary structure')
        d.bullet('Quaternary structure: assembly of multiple polypeptide chains into '
                 'a complex.',
                 bold_label='Quaternary structure')

        d.para(
            'The protein backbone consists of the repeating N-Ca-C=O unit running through '
            'every residue. Backbone conformation is almost completely determined by two '
            'dihedral angles: phi (N-Ca bond rotation) and psi (Ca-C bond rotation). '
            'MDGen operates exclusively on backbone heavy atoms, representing each residue '
            'as a rigid frame in SE(3), with side chains encoded separately as torsion '
            'angles chi_1 to chi_4.')

        d.subsection('2.2', 'The Protein Energy Landscape and Conformational Ensembles')

        d.para(
            'A protein in solution at temperature T does not adopt a single static '
            'conformation. Instead, it continuously fluctuates according to Boltzmann '
            'statistics. The probability of finding the system in conformation x is:')

        d.equation(r'p(x) \propto \exp(-E(x)\,/\,k_B T)', '(1)')

        d.para(
            'where E(x) is the potential energy, k_B is Boltzmann\'s constant, and '
            'k_B T ~ 0.6 kcal/mol at 300 K (Frauenfelder et al., 1991). '
            'Key features of the energy landscape relevant to MDGen:')

        d.bullet('Multiple minima: most functional proteins populate more than one '
                 'conformation (e.g., open/closed enzyme active sites).')
        d.bullet('Hierarchical roughness: fast local motions (10 fs) nested within '
                 'slower large-scale rearrangements (us-ms).')
        d.bullet('Anharmonicity: large-amplitude motions cannot be described by a '
                 'harmonic approximation—a fundamental limitation of Normal Mode Analysis.')

        d.subsection('2.3', 'Molecular Dynamics Simulation')

        d.para('MD simulation numerically integrates Newton\'s equations of motion:')

        d.equation(
            r'm_i\,\ddot{\mathbf{r}}_i = \mathbf{F}_i = -\nabla_{\mathbf{r}_i} E(\mathbf{r}_1,\ldots,\mathbf{r}_N)',
            '(2)')

        d.para(
            'The empirical force field E comprises bonded terms (harmonic bond '
            'stretches, angle bends, periodic dihedral torsions) and non-bonded terms '
            '(Lennard-Jones 6-12 van der Waals, Coulomb electrostatics via Particle Mesh '
            'Ewald). Widely used force fields include AMBER ff14SB (used for ATLAS), '
            'CHARMM36m, and OPLS-AA.')

        d.callout(
            'Timescale problem. The fastest atomic vibrations (~10 fs) impose an '
            'integration ceiling of dt = 2 fs. Observing biologically important motions '
            'requires 10^8 to 10^11 steps (100 ns to 100 us). A single microsecond '
            'simulation of a 100-residue protein on an A100 GPU cluster takes ~1-2 weeks. '
            'Screening thousands of variants, as required in drug discovery, is '
            'practically infeasible with standard MD.')

        d.subsection('2.4', 'Trajectory Representation for MDGen')

        d.para(
            'An MD trajectory is a time-ordered sequence of frames (x_1, x_2, ..., x_T), '
            'where each frame x_t specifies the full atomic coordinates at time t. '
            'In MDGen, the relevant degrees of freedom per residue i at time t are a '
            'rigid body frame in SE(3) plus torsion angles on the 4-torus:')

        d.equation(
            r'\mathbf{x} = \{(R_i,\,\mathbf{t}_i,\,\chi_i)\}_{i=1}^N '
            r'\in SE(3)^N \times \mathbb{T}^{4N}',
            '(3)')

        d.para(
            'A trajectory window of T frames is the joint object X = (x_1, ..., x_T). '
            'Training uses T = 16 frames, corresponding to ~16 ns at the ATLAS 1 ns '
            'frame rate.')

        # ══════════════════════════════════════════════════════════
        # 3. DIFFUSION THEORY
        # ══════════════════════════════════════════════════════════
        d.section('3', 'Theoretical Background: Diffusion Models')
        d.subsection('3.1', 'Denoising Diffusion Probabilistic Models (DDPMs)')

        d.para(
            'DDPMs (Ho et al., 2020) define a generative model through two coupled '
            'Markov chains: a forward process that gradually destroys structure by '
            'adding Gaussian noise, and a reverse process learned to reconstruct data '
            'from noise.')

        d.para('Forward process. Given clean data x_0, the forward process is:')

        d.equation(
            r'q(\mathbf{x}_s | \mathbf{x}_{s-1}) = '
            r'\mathcal{N}(\mathbf{x}_s;\,\sqrt{1-\beta_s}\,\mathbf{x}_{s-1},\,\beta_s\mathbf{I})',
            '(4)')

        d.para(
            'The marginal at step s has a closed form with '
            'alpha-bar_s = product_{k=1}^s (1 - beta_k):')

        d.equation(
            r'q(\mathbf{x}_s | \mathbf{x}_0) = '
            r'\mathcal{N}(\mathbf{x}_s;\,\sqrt{\bar\alpha_s}\,\mathbf{x}_0,\,'
            r'(1-\bar\alpha_s)\mathbf{I})',
            '(5)')

        d.para(
            'As s -> S, the distribution approaches N(0, I) — pure isotropic noise. '
            'The training objective minimises noise prediction error:')

        d.equation(
            r'\mathcal{L} = \mathbb{E}_{s,\mathbf{x}_0,\epsilon}\,'
            r'\|\epsilon - \epsilon_\theta(\sqrt{\bar\alpha_s}\,\mathbf{x}_0 '
            r'+ \sqrt{1-\bar\alpha_s}\,\epsilon,\,s)\|^2',
            '(6)')

        d.subsection('3.2', 'Score-Based Models and the Continuous-Time SDE Perspective')

        d.para(
            'Song et al. (2021) cast diffusion models as continuous-time stochastic '
            'differential equations (SDEs). The forward SDE is:')

        d.equation(r'd\mathbf{x} = f(\mathbf{x},t)\,dt + g(t)\,d\mathbf{W}', '(7)')

        d.para(
            'where W is a standard Brownian motion. The reverse SDE (Anderson, 1982) '
            'runs backwards from noise to data:')

        d.equation(
            r'd\mathbf{x} = [f - g^2\,\nabla_\mathbf{x}\log p_t]\,dt + g\,d\bar{\mathbf{W}}',
            '(8)')

        d.para(
            'The key quantity is the score function: the gradient of the log density, '
            'which points toward higher probability regions. A score network s_theta(x,t) '
            'is trained via denoising score matching (Vincent, 2011). DDIM (Song et al., '
            '2021) provides a deterministic ODE equivalent enabling high-quality sampling '
            'in ~50 steps instead of 500:')

        d.equation(
            r'\mathbf{x}_{s-1} = \sqrt{\bar\alpha_{s-1}}'
            r'\left(\frac{\mathbf{x}_s - \sqrt{1-\bar\alpha_s}\,\epsilon_\theta}{\sqrt{\bar\alpha_s}}\right)'
            r'+ \sqrt{1-\bar\alpha_{s-1}}\,\epsilon_\theta',
            '(9)')

        d.subsection('3.3', 'Diffusion on Non-Euclidean Manifolds')

        d.para(
            'Standard Gaussian diffusion assumes flat Euclidean space R^d. Protein '
            'backbone frames involve two non-Euclidean components: rotations R_i in '
            'SO(3) (a compact curved Lie group) and torsion angles in the circle S^1 '
            '(with side-chain state on the 4-torus T^4).')

        d.para(
            'Diffusion on SO(3). MDGen uses the Isotropic Gaussian on SO(3) (IGSO3; '
            'De Bortoli et al., 2022):')

        d.equation(r'q(R_s | R_0) = \mathrm{IGSO3}(R_s;\,R_0,\,\sigma_s^2)', '(10)')

        d.para(
            'Its score uses the Riemannian gradient—the analogue of the Euclidean score '
            'on the curved SO(3) manifold, computed via the heat kernel on SO(3). '
            'For torsion angles theta, the correct distribution is a wrapped Gaussian:')

        d.equation(
            r'q(\theta_s | \theta_0) = '
            r'\sum_{k=-\infty}^{\infty} \mathcal{N}(\theta_s;\,\theta_0+2\pi k,\,\sigma_s^2)',
            '(11)')

        d.subsection('3.4', 'SE(3) Equivariance')

        d.para(
            'The group SE(3) = SO(3) x R^3 consists of all rotations and translations '
            'of R^3. A map f is SE(3)-equivariant if rotating/translating the input '
            'produces a correspondingly rotated/translated output:')

        d.equation(
            r'f(g \cdot \mathbf{x}) = \rho_{\mathrm{out}}(g)\,f(\mathbf{x}), '
            r'\quad g \in SE(3)',
            '(12)')

        d.para(
            'SE(3)-equivariant networks (Fuchs et al., 2020; Satorras et al., 2021) '
            'architecturally enforce this constraint exactly. The physics of a protein '
            'does not change if we rotate or translate the entire coordinate system; a '
            'model violating this symmetry must learn it from data, wasting capacity.')

        d.subsection('3.5', 'Backbone Frame Representation')

        d.para(
            'AlphaFold2 (Jumper et al., 2021) introduced the backbone frame '
            'representation that MDGen inherits. Each residue i is assigned a rigid '
            'body in SE(3): a translation t_i (C_alpha position) and a rotation R_i '
            '(local backbone orientation defined by N, C_alpha, C atoms). Together, '
            'T_i = (R_i, t_i) defines a frame in which the local chemical environment '
            'appears in a standardised orientation.')

        # ══════════════════════════════════════════════════════════
        # 4. PRIOR WORK
        # ══════════════════════════════════════════════════════════
        d.section('4', 'Prior Work and Its Limitations')

        d.para(
            'Understanding MDGen\'s novelty requires surveying the space of prior '
            'methods for computational characterisation of protein conformational '
            'dynamics, organised into four categories.')

        d.subsection('4.1', 'Normal Mode Analysis (NMA)')

        d.para(
            'NMA (Tirion, 1996; Brooks & Karplus, 1983) approximates the protein energy '
            'landscape as a multidimensional harmonic bowl centred on a minimised '
            'structure. The equations of motion separate into 3N-6 independent harmonic '
            'oscillators (normal modes). The lowest-frequency modes correspond to '
            'large-scale collective motions and predict B-factors and RMSF profiles.')

        d.para('Strengths of NMA:')
        d.bullet('Computationally cheap: a single eigendecomposition of the Hessian.')
        d.bullet('Provides physically interpretable collective modes.')
        d.bullet('Reasonable agreement with MD-derived RMSF for ordered secondary '
                 'structure elements.')

        d.para('Fundamental limitations:')
        d.bullet('Harmonic approximation: strictly valid only near the energy minimum. '
                 'Loop motions, domain swings, and barrier-crossing transitions are '
                 'entirely outside the scope of the harmonic model.')
        d.bullet('No kinetics: NMA produces i.i.d. Gaussian samples with no notion of '
                 'temporal ordering or transition rates.')
        d.bullet('Single minimum: cannot represent multi-modal distributions or '
                 'conformational heterogeneity between distinct energy basins.')
        d.bullet('RMSF Pearson r ~ 0.64 on ATLAS test set—substantially below '
                 'MDGen\'s r ~ 0.87.')

        d.subsection('4.2', 'Boltzmann Generators and Flow-Based Samplers')

        d.para(
            'Boltzmann generators (Noe et al., 2019) use normalising flows to learn '
            'a direct mapping between a Gaussian base distribution and the Boltzmann '
            'distribution p(x) proportional to exp(-E(x)/k_B T). Samples can be drawn '
            'without simulating the dynamics.')

        d.para('Strengths:')
        d.bullet('Principled probabilistic model with exact likelihood.')
        d.bullet('Can provide reweighting factors to correct force-field imperfections.')

        d.para('Fundamental limitations:')
        d.bullet('Scalability: normalising flows for all-atom configurations of '
                 '100-500 residues remain computationally intractable; most '
                 'demonstrations are restricted to <= 50-residue systems.')
        d.bullet('No temporal coherence: like NMA, produces i.i.d. equilibrium samples '
                 'with no mechanism for temporally ordered trajectories.')
        d.bullet('Requires the energy function: training evaluates E(x), coupling the '
                 'method to the expensive force field evaluation.')

        d.subsection('4.3', 'Independent-Frame Protein Diffusion Models')

        d.para(
            'A family of recent diffusion models generates protein structures by '
            'reversing a noising process on backbone frames, producing independent '
            'equilibrium samples.')

        d.bullet('FrameDiff (Yim et al., ICML 2023): diffuses over SE(3)^N backbone '
                 'frames; samples drawn independently.',
                 bold_label='FrameDiff')
        d.bullet('EigenFold (Jing et al., 2023): decomposes protein structure along '
                 'spring-network eigenmodes; coarse-to-fine generation.',
                 bold_label='EigenFold')
        d.bullet('AlphaFlow (Jing et al., ICML 2024): fine-tunes AlphaFold2 as a '
                 'flow-matching model conditioned on MSAs.',
                 bold_label='AlphaFlow')
        d.bullet('BioEmu (Lewis et al., Science 2025): large-scale diffusion model '
                 'trained on MD trajectories and experimental data.',
                 bold_label='BioEmu')

        d.callout(
            'Shared limitation: ALL of the above generate INDEPENDENT conformational '
            'samples. They cannot reproduce: (1) the temporal autocorrelation function '
            'C(tau) — which drops to zero immediately at lag >= 1 for i.i.d. samplers; '
            '(2) physically realistic frame-to-frame step sizes (~0.1-0.3 A RMSD); '
            '(3) transition pathway information. These are not aesthetic deficiencies—'
            'kinetic rate constants, mean first-passage times, and committed fractions '
            'are fundamentally temporal and inaccessible to equilibrium samplers.')

        d.subsection('4.4', 'Static Structure Prediction Models')

        d.bullet('AlphaFold2 (Jumper et al., 2021): near-experimental accuracy for the '
                 'single lowest-energy structure. Produces one structure per input; not '
                 'designed for ensemble generation or dynamics.',
                 bold_label='AlphaFold2')
        d.bullet('ESMFold (Lin et al., 2023): fast single-structure prediction via '
                 'language model without MSA. MDGen uses it only for the initial '
                 'conditioning structure.',
                 bold_label='ESMFold')
        d.bullet('RFdiffusion (Watson et al., 2023) and Chroma (Ingraham et al., 2023): '
                 'diffusion models for protein design—generating novel backbones '
                 'satisfying functional constraints. Not evaluated on MD ensemble metrics.',
                 bold_label='RFdiffusion / Chroma')

        d.subsection('4.5', 'Summary Comparison Table')

        d.table(
            headers=['Method', 'Equil. Ensemble', 'Temporal Coh.', 'Speed vs MD', 'Large Proteins'],
            rows=[
                ['MD simulation',          'Yes', 'Yes', '1x (baseline)', 'Yes'],
                ['NMA',                    'Partial', 'No',  '~1000x',  'Yes'],
                ['Boltzmann generators',   'Yes', 'No',  '~1000x',       'No'],
                ['EigenFold / AlphaFlow',  'Yes', 'No',  '~10000x',      'Yes'],
                ['BioEmu',                 'Yes', 'No',  '~10000x',      'Yes'],
                ['MDGen (this work)',       'Yes', 'Yes', '~10000x',      'Yes'],
            ],
            col_widths=[0.32, 0.14, 0.14, 0.20, 0.20],
        )

        # ══════════════════════════════════════════════════════════
        # 5. MDGEN METHOD
        # ══════════════════════════════════════════════════════════
        d.section('5', 'MDGen: Method')
        d.subsection('5.1', 'Problem Formulation')

        d.callout(
            'Definition (Trajectory generation). Given a protein sequence '
            's = (s_1, ..., s_N), generate a trajectory window '
            'X = (x_1, ..., x_T) in (SE(3)^N x T^4N)^T such that the joint '
            'distribution p_theta(X|s) approximates the distribution over '
            'T-frame windows drawn from equilibrium MD trajectories.')

        d.para('This formulation requires two simultaneous properties:')
        d.bullet('Equilibrium marginal correctness: the marginal p(x_t | s) for any '
                 'single time t matches the MD equilibrium distribution.')
        d.bullet('Temporal coherence: the joint p(x_t, x_{t+1} | s) reflects the '
                 'physically correct Markov transition structure of MD dynamics.')

        d.subsection('5.2', 'Forward Diffusion over Trajectory Space')

        d.para(
            'MDGen applies independent noise to each trajectory frame, keeping the '
            'forward process factorised over the time axis:')

        d.equation(
            r'q(\mathbf{X}^{(s)} | \mathbf{X}^{(0)}) = '
            r'\prod_{t=1}^{T} q(\mathbf{x}_t^{(s)} | \mathbf{x}_t^{(0)})',
            '(13)')

        d.para(
            'Within each frame, diffusion is factorised over geometric components '
            '(translation, rotation, torsion angles):')

        d.equation(
            r'q(\mathbf{x}_t^{(s)} | \mathbf{x}_t^{(0)}) = '
            r'q_{\mathbb{R}^3}(\mathbf{t}^{(s)}|\mathbf{t}^{(0)}) \cdot '
            r'q_{SO(3)}(R^{(s)}|R^{(0)}) \cdot '
            r'q_{\mathbb{T}}(\chi^{(s)}|\chi^{(0)})',
            '(14)')

        d.callout(
            'Key insight: frames are noised independently in the forward process, '
            'but the reverse process denoises ALL T frames jointly. Temporal '
            'correlations are entirely encoded in the LEARNED denoising network—'
            'specifically in the temporal attention layers.')

        d.subsection('5.3', 'Neural Architecture')
        d.subsubsection('5.3.1  Sequence Encoder: ESM-2')

        d.para(
            'The protein sequence s is embedded by the pre-trained protein language '
            'model ESM-2 (Lin et al., 2023) into per-residue feature vectors '
            'h_i^seq in R^d. ESM-2 is kept frozen during MDGen training. Its '
            'representations capture evolutionary and physicochemical information, '
            'projected to internal dimension d via a learned linear layer.')

        d.subsubsection('5.3.2  Spatial Attention: Invariant Point Attention (IPA)')

        d.para(
            'At each trajectory frame t, inter-residue information exchange is '
            'mediated by Invariant Point Attention (IPA; Jumper et al., 2021). IPA '
            'augments standard multi-head attention with 3D query/key point pairs '
            'expressed in each residue\'s local backbone frame:')

        d.equation(
            r'a_{ij} = \mathrm{softmax}_j\!\left('
            r'\frac{\mathbf{q}_i^\top \mathbf{k}_j}{\sqrt{d}} '
            r'- \frac{\gamma}{2}\sum_h \|T_i\mathbf{p}_i^h - T_j\mathbf{p}_j^h\|^2'
            r'\right)',
            '(15)')

        d.para(
            'Here T_i = (R_i, t_i) maps local frame points to global coordinates, '
            'p_i^h are learned 3D query points in residue i\'s local frame, and '
            'gamma > 0 is a learnable scalar. The attention is SE(3)-invariant: '
            'the point-distance term is unchanged by any global rotation or '
            'translation. Two residues distant in sequence but close in 3D space '
            'receive a high attention weight—enabling the model to reason about '
            'spatial contacts across the structure.')

        d.subsubsection('5.3.3  Temporal Attention: Axial Attention Across Time')

        d.para(
            'The defining architectural innovation in MDGen is axial temporal '
            'attention (Ho et al., 2019). After the spatial IPA pass (across '
            'residues at fixed frame t), a temporal attention pass operates across '
            'all T time steps for each residue i:')

        d.equation(
            r'\mathbf{h}_{i,t}^{new} = \sum_{s=1}^{T} \alpha_{ts}\,\mathbf{v}_{i,s},'
            r'\quad \alpha_{ts} = \mathrm{softmax}_{s}\left('
            r'\frac{\mathbf{q}_{i,t}\cdot\mathbf{k}_{i,s}}{\sqrt{d}}\right)',
            '(16)')

        d.para(
            'This allows every time step to attend to every other time step within '
            'the trajectory window. The loss penalises temporally incoherent '
            'predictions, and the temporal attention weights adapt to propagate '
            'continuity information along the time axis. The spatial and temporal '
            'attention layers alternate in a stack of L blocks:')

        d.bullet('IPA_l (spatial pass): all N residues exchange information at each '
                 'fixed frame t.')
        d.bullet('TempAttn_l (temporal pass): each residue i attends across frames '
                 't = 1, ..., T.')
        d.bullet('FFN_l: position-wise feed-forward network.')

        d.subsubsection('5.3.4  Score Head and Model Size')

        d.para(
            'After L alternating blocks, separate prediction heads convert the latent '
            'representation into predicted noise for each geometric component: '
            'epsilon_trans in R^3, epsilon_rot in so(3), epsilon_tors in R^4. '
            'The rotation score is expressed as a vector in the Lie algebra '
            'so(3) ~ R^3. Total parameter count: approximately 100M.')

        d.subsection('5.4', 'Training Objective')

        d.para(
            'The training loss is a weighted sum of denoising score matching losses '
            'for each geometric component, plus a structural violation penalty:')

        d.equation(
            r'\mathcal{L} = \mathbb{E}\,[\,\lambda_t\,\mathcal{L}_{\mathbb{R}^3} '
            r'+ \lambda_r\,\mathcal{L}_{SO(3)} '
            r'+ \lambda_x\,\mathcal{L}_{\mathbb{T}} '
            r'+ \lambda_v\,\mathcal{L}_{viol}\,]',
            '(17)')

        d.bullet('L_trans: standard MSE on C_alpha displacements. Weight lambda_t = 1.0.')
        d.bullet('L_rot: Riemannian score matching loss on the SO(3) manifold. Weight ~ 1.0.')
        d.bullet('L_tors: wrapped Gaussian score matching for torsion angles. Weight ~ 0.5.')
        d.bullet('L_viol: steric clash penalty and backbone bond-geometry violations. Weight ~ 0.01.')

        d.para(
            'All N residues and all T = 16 frames contribute to each gradient update. '
            'Diffusion noise level s ~ Uniform(0, S) with S = 500. Optimiser: AdamW, '
            'lr = 1e-4, cosine annealing, batch size ~64 windows, on 8 x A100 GPUs.')

        d.subsection('5.5', 'Inference: Sampling')

        d.para(
            'Sampling runs the reverse diffusion starting from pure noise for all T '
            'frames simultaneously: translations ~ N(0, I), rotations ~ Uniform(SO(3)), '
            'torsions ~ Uniform(T^4). MDGen supports two modes:')

        d.bullet('DDPM (500 steps): stochastic reverse process; highest sample quality; '
                 '~minutes per trajectory.')
        d.bullet('DDIM (50 steps): deterministic ODE; 10x faster than DDPM with minimal '
                 'quality loss; ~seconds per trajectory.')

        d.callout(
            'Both modes produce trajectories approximately 10,000x faster than '
            'equivalent explicit-solvent MD simulation.')

        d.subsection('5.6', 'Trajectory Extension via Diffusion Inpainting')

        d.para(
            'MDGen can generate trajectories conditioned on a known conformation '
            'x_1^(0) (e.g., a crystal structure) using diffusion inpainting '
            '(Lugmayr et al., 2022). During reverse diffusion, the first-frame '
            'variable is periodically replaced with its correctly-noised counterpart:')

        d.equation(
            r'\mathbf{x}_1^{(s)} \leftarrow \sqrt{\bar\alpha_s}\,\mathbf{x}_1^{(0)} '
            r'+ \sqrt{1-\bar\alpha_s}\,\epsilon',
            '(18)')

        d.para(
            'Interpolation mode: conditioning on BOTH x_1^(0) and x_T^(0) generates '
            'a plausible transition pathway between two known protein conformations '
            '(e.g., open <-> closed states of adenylate kinase). This has no '
            'equivalent in any prior independent-frame sampler.')

        # ══════════════════════════════════════════════════════════
        # 6. ATLAS DATA
        # ══════════════════════════════════════════════════════════
        d.section('6', 'Training Data: The ATLAS Database')

        d.para(
            'MDGen is trained on the ATLAS (Atlas of Trajectory Landscapes and '
            'Associated Simulations) database (Vander Meersche et al., Nucleic Acids '
            'Research, 2024), the largest open repository of protein MD trajectories '
            'assembled to support machine learning on protein dynamics.')

        d.para('Simulation protocol:')
        d.bullet('Force field: AMBER ff14SB with explicit TIP3P water, NPT ensemble, '
                 '300 K, 1 atm.')
        d.bullet('Three independent 100 ns replicas per protein, yielding 300 ns total.')
        d.bullet('Frames saved every 1 ns (~300 frames per protein).')
        d.bullet('Simulation time step: 2 fs with SHAKE hydrogen-bond constraints.')

        d.para('Dataset statistics:')
        d.bullet('~1,400 diverse proteins from the PDB: alpha, beta, alpha/beta folds, IDPs.')
        d.bullet('Protein lengths: ~50 to ~500 residues.')
        d.bullet('Aggregate simulation time: ~1.2 us across all proteins and replicas.')
        d.bullet('Train split: ~1,265 proteins; Test split: ~135 held-out proteins.')

        d.para(
            'During training, a random contiguous window of T = 16 consecutive frames '
            'is extracted from each replica trajectory per minibatch. Overlapping '
            'windows are permitted as data augmentation.')

        # ══════════════════════════════════════════════════════════
        # 7. EVALUATION AND RESULTS
        # ══════════════════════════════════════════════════════════
        d.section('7', 'Evaluation Protocol and Results')
        d.subsection('7.1', 'Evaluation Metrics')

        d.subsubsection('7.1.1  Root Mean Square Fluctuation (RMSF)')
        d.para('RMSF quantifies per-residue positional flexibility:')
        d.equation(
            r'\mathrm{RMSF}_i = \sqrt{\frac{1}{T}\sum_{t=1}^{T}'
            r'\|\mathbf{r}_i(t) - \langle\mathbf{r}_i\rangle\|^2}',
            '(19)')
        d.para(
            'High RMSF = flexible region (loops, termini). Low RMSF = rigid region '
            '(helices, beta-sheets). The primary summary metric is Pearson correlation r '
            'between generated and reference MD RMSF profiles, averaged over test '
            'proteins.')

        d.subsubsection('7.1.2  Ramachandran Distribution: Jensen-Shannon Divergence')
        d.para(
            'MDGen\'s generated (phi, psi) backbone dihedral distribution is compared '
            'to reference MD using Jensen-Shannon Divergence (JSD), discretised over a '
            '36x36 grid of (phi, psi) bins. Lower JSD indicates better agreement.')

        d.subsubsection('7.1.3  Temporal Metrics (unique to MDGen)')
        d.para(
            'Two metrics test temporal coherence—quantities impossible to evaluate '
            'from i.i.d. samplers:')
        d.bullet(
            'Frame-to-frame RMSD: in real MD, consecutive frames differ by only '
            '~0.1-0.3 A C_alpha RMSD. Independent samplers show arbitrarily large '
            'random jumps.')
        d.bullet(
            'Temporal autocorrelation function C(tau) = <delta_r(t) . delta_r(t+tau)> '
            '/ <|delta_r(t)|^2>: measures structural persistence over lag tau. '
            'Physical trajectories decay smoothly from C(0)=1. i.i.d. samplers '
            'have C(tau) = 0 for all tau >= 1 by definition.')

        d.subsection('7.2', 'Quantitative Results')

        d.table(
            headers=['Method', 'RMSF r', 'Ramach. JSD', 'Frame RMSD', 'ACF', 'Speed'],
            rows=[
                ['Reference MD',          '1.00', '0.00',  'ground truth',  'ground truth', '1x'],
                ['MDGen (DDPM)',           '~0.87','~0.08', 'Correct',       'Correct',      '~10^4x'],
                ['MDGen (DDIM)',           '~0.85','~0.09', 'Correct',       'Correct',      '~10^5x'],
                ['Indep. frame diffusion', '~0.71','~0.11', 'Wrong (random)','Zero lag',     '~10^4x'],
                ['Normal Mode Analysis',  '~0.64', '~0.19', 'Harmonic only', 'Harmonic only','~10^3x'],
                ['Boltzmann generators',  '~0.68', '~0.14', 'Wrong (i.i.d.)','Zero lag',     '~10^3x'],
            ],
            col_widths=[0.26, 0.10, 0.12, 0.17, 0.17, 0.18],
        )

        d.para(
            'MDGen achieves Pearson r ~ 0.87 on per-residue RMSF, outperforming both '
            'NMA (r ~ 0.64) and independent-frame diffusion (r ~ 0.71). Improvement '
            'over independent-frame diffusion confirms that temporal context improves '
            'equilibrium ensemble quality as well as kinetics. Only MDGen reproduces '
            'correct temporal autocorrelation functions and frame-to-frame step-size '
            'distributions.')

        d.subsection('7.3', 'Generalisation to Out-of-Distribution Fast-Folding Proteins')

        d.para(
            'MDGen is evaluated on miniproteins from long reference simulations NOT '
            'in the ATLAS training set: Trp-cage (20 res.), BBA motif (28 res.), '
            'villin headpiece (35 res.), WW domain (35 res.), NTL9 (39 res.), '
            'Chignolin (10 res.). MDGen correctly identifies qualitative flexibility '
            'profiles: flexible C-terminal helices, rigid hydrophobic cores, elevated '
            'RMSF in loop regions. This demonstrates generalisation across protein '
            'fold space beyond the ATLAS training distribution.')

        # ══════════════════════════════════════════════════════════
        # 8. APPLICATIONS
        # ══════════════════════════════════════════════════════════
        d.section('8', 'Applications')
        d.subsection('8.1', 'Cryptic Pocket Discovery in Drug Design')

        d.para(
            'Approximately 50% of protein drug targets undergo conformational changes '
            'critical for inhibitor binding. Cryptic pockets—absent in the static '
            'crystal structure but transiently open during dynamics (Oleinikovas et '
            'al., 2016)—are missed entirely by static docking. MDGen workflow:')

        d.bullet('Generate 100-1000 backbone trajectory frames using MDGen '
                 '(seconds to minutes on one GPU).')
        d.bullet('Run pocket detection (FPOCKET, SiteMap) on each generated frame.')
        d.bullet('Identify transiently open druggable pockets across the ensemble.')
        d.bullet('Prioritise pockets for downstream docking and lead optimisation.')

        d.para(
            'This replaces expensive multi-us MD with MDGen-generated ensembles '
            '3-4 orders of magnitude faster. MDGen\'s correct temporal autocorrelation '
            'ensures conformational transitions consistent with natural protein dynamics.')

        d.subsection('8.2', 'Intrinsically Disordered Proteins (IDPs) and Disease')

        d.para(
            'IDPs (Uversky, 2019) lack a stable folded structure and exist as dynamic '
            'conformational ensembles. They are medically critical, frequently driving '
            'aberrant aggregation in neurodegenerative diseases.')

        d.bullet(
            '~140-residue IDP; conformational ensemble determines nucleation pathways '
            'of toxic amyloid fibrils in Parkinson\'s disease.',
            bold_label='alpha-Synuclein')
        d.bullet(
            'Highly flexible repeat domain; disordered regions initiate neurofibrillary '
            'tangle formation in Alzheimer\'s disease.',
            bold_label='Tau')
        d.bullet(
            'Most frequently mutated tumour suppressor; disordered N/C-terminal regions '
            'mediate transactivation through conformational dynamics.',
            bold_label='p53 (cancer)')

        d.para(
            'AlphaFold2 reports low-confidence (pLDDT < 50) predictions for disordered '
            'regions—a diagnostic flag, not a structural answer. MDGen generates backbone '
            'conformational ensembles for these regions, providing a distribution of '
            'conformations rather than a misleading single coordinate set.')

        d.subsection('8.3', 'Ensemble-Aware Protein Engineering')
        d.bullet('Mutational scanning: generate conformational ensembles for point '
                 'mutants to predict effects on dynamics without re-running MD.')
        d.bullet('Allosteric pathway mapping: condition on two allosteric states and '
                 'use interpolation mode to identify signal-transmitting residues.')
        d.bullet('Antibody CDR loop flexibility: characterise loop dynamics governing '
                 'antigen recognition and binding affinity.')

        # ══════════════════════════════════════════════════════════
        # 9. LIMITATIONS
        # ══════════════════════════════════════════════════════════
        d.section('9', 'Limitations')

        d.bullet(
            'T = 16 frames ~ 16 ns. Millisecond-scale processes (full folding, large '
            'domain translocations) are out of scope.',
            bold_label='Fixed timescale')
        d.bullet(
            'ATLAS predominantly contains single-chain, globular, soluble proteins '
            '(50-500 residues). Membrane proteins, large complexes, and heavily '
            'post-translationally modified proteins are under-represented.',
            bold_label='Training distribution bias')
        d.bullet(
            'MDGen learns from explicit-solvent MD but does not model solvent '
            'explicitly. Hydration shell dynamics and specific ion effects are '
            'captured only insofar as they manifest in backbone motions.',
            bold_label='Implicit solvent')
        d.bullet(
            'Generated trajectories emulate AMBER ff14SB statistics. Systematic '
            'force-field errors are inherited—MDGen is a data-driven emulator, '
            'not an independent physics engine.',
            bold_label='Force-field dependency')
        d.bullet(
            'Side-chain coordinates must be reconstructed post-hoc using Rosetta '
            'Relax or DLPacker, limiting direct use in atom-level applications '
            'such as binding free energy calculations.',
            bold_label='Backbone-only representation')
        d.bullet(
            'Conformational transitions requiring crossing high energy barriers '
            '(rare events on us+ timescales) are statistically improbable within '
            'a 16-frame window.',
            bold_label='Rare barrier crossings')

        # ══════════════════════════════════════════════════════════
        # 10. FUTURE DIRECTIONS
        # ══════════════════════════════════════════════════════════
        d.section('10', 'Future Directions')

        d.bullet(
            'Jointly model backbone frames and all-atom side-chain coordinates '
            'as a unified diffusion model—enabling direct computation of binding '
            'free energies and pharmacophoric features without post-hoc reconstruction.',
            bold_label='Full-atom trajectory generation')
        d.bullet(
            'Training on us-scale datasets (D.E. Shaw Research Anton) or enhanced-'
            'sampling trajectories (metadynamics, REST2) to unlock rarer '
            'conformational transitions.',
            bold_label='Longer timescales')
        d.bullet(
            'Extending to receptor-ligand systems for ensemble-aware docking and '
            'entropic contributions to binding affinity (Delta_G = Delta_H - T*Delta_S).',
            bold_label='Protein-ligand dynamics')
        d.bullet(
            'Incorporating NMR chemical shifts, SAXS profiles, or cryo-EM density '
            'maps as soft conditioning signals during inference for physics-guided '
            'ensemble refinement.',
            bold_label='Experimental conditioning')
        d.bullet(
            'The SE(3) trajectory diffusion framework can be adapted for RNA, DNA, '
            'carbohydrates, and lipid membranes with appropriate geometric '
            'representations.',
            bold_label='Beyond proteins')

        # ══════════════════════════════════════════════════════════
        # 11. CONCLUSION
        # ══════════════════════════════════════════════════════════
        d.section('11', 'Conclusion')

        d.para(
            'MDGen represents a conceptual advance in generative molecular modelling. '
            'By framing the problem as trajectory generation rather than independent '
            'equilibrium sampling, MDGen is the first model to simultaneously achieve:')

        d.bullet('High per-residue RMSF correlation with reference MD (r ~ 0.87 vs '
                 'NMA r ~ 0.64).')
        d.bullet('Physically correct Ramachandran backbone dihedral distributions '
                 '(JSD ~ 0.08 vs MD reference).')
        d.bullet('Correct temporal autocorrelation functions and frame-to-frame step-'
                 'size distributions—metrics no prior independent sampler reproduces.')
        d.bullet('Approximately 10,000x speed-up over equivalent explicit-solvent MD.')

        d.para(
            'The architectural innovations—SE(3)-equivariant Invariant Point Attention '
            '(spatial) combined with temporal axial attention (kinetic)—provide a '
            'template for incorporating physical symmetries and temporal structure into '
            'generative models for other molecular and biological systems.')

        d.callout(
            'Central intellectual contribution: MD trajectories should be treated as '
            'the PRIMARY generative target, not a source of independent equilibrium '
            'samples. This reframing enables learning both the thermodynamics '
            '(what conformations are accessible) AND the dynamics (how fast they '
            'interconvert) from data—a template for how generative AI can emulate '
            'complex physical processes that govern molecular biology.')

        # ══════════════════════════════════════════════════════════
        # REFERENCES
        # ══════════════════════════════════════════════════════════
        d.section('References', '')

        refs = [
            '[1] Jing B, Stark H, Jaakkola T, Berger B (2024). Generative Molecular Dynamics. arXiv:2409.17808. NeurIPS 2024.',
            '[2] Vander Meersche Y et al. (2024). ATLAS: Protein Flexibility from Atomistic MD. Nucleic Acids Res 52(D1):D384.',
            '[3] Jumper J et al. (2021). Highly accurate protein structure prediction with AlphaFold. Nature 596:583.',
            '[4] Ho J, Jain A, Abbeel P (2020). Denoising diffusion probabilistic models. NeurIPS 33:6840.',
            '[5] Song Y et al. (2021). Score-based generative modeling through stochastic differential equations. ICLR.',
            '[6] Song J, Meng C, Ermon S (2021). Denoising diffusion implicit models. ICLR.',
            '[7] Lin Z et al. (2023). Evolutionary-scale prediction of atomic-level protein structure. Science 379:1123.',
            '[8] Watson JL et al. (2023). De novo design of protein structure and function with RFdiffusion. Nature 620:1089.',
            '[9] Adcock SA, McCammon JA (2006). Molecular dynamics: survey of methods for simulating protein activity. Chem Rev 106:1589.',
            '[10] Shaw DE et al. (2010). Atomic-level characterization of structural dynamics of proteins. Science 330:341.',
            '[11] Lindorff-Larsen K et al. (2011). How fast-folding proteins fold. Science 334:517.',
            '[12] De Bortoli V et al. (2022). Riemannian score-based generative modelling. NeurIPS 35:2406.',
            '[13] Leach A et al. (2022). Denoising diffusion probabilistic models on SO(3). ICLR Workshop.',
            '[14] Yim J et al. (2023). SE(3) diffusion model for protein backbone generation. ICML.',
            '[15] Jing B et al. (2023). EigenFold: Generative protein structure prediction. ICLR Workshop.',
            '[16] Jing B, Berger B, Jaakkola T (2024). AlphaFold meets flow matching for protein ensembles. ICML.',
            '[17] Lewis SM et al. (2025). Scalable emulation of protein equilibrium ensembles. Science 388.',
            '[18] Noe F et al. (2019). Boltzmann generators: sampling equilibrium states with deep learning. Science 365:eaaw1147.',
            '[19] Tirion MM (1996). Large amplitude elastic motions in proteins from single-parameter analysis. Phys Rev Lett 77:1905.',
            '[20] Brooks B, Karplus M (1983). Harmonic dynamics of proteins: normal modes and fluctuations. PNAS 80:6571.',
            '[21] Maier JA et al. (2015). ff14SB: Improving accuracy of protein backbone and side chain parameters. J Chem Theory Comput 11:3696.',
            '[22] Frauenfelder H, Sligar SG, Wolynes PG (1991). The energy landscapes and motions of proteins. Science 254:1598.',
            '[23] Fuchs FB et al. (2020). SE(3)-Transformers: 3D roto-translation equivariant attention networks. NeurIPS 33:1970.',
            '[24] Satorras VG, Hoogeboom E, Welling M (2021). E(n) equivariant graph neural networks. ICML.',
            '[25] Vincent P (2011). A connection between score matching and denoising autoencoders. Neural Comput 23:1661.',
            '[26] Loshchilov I, Hutter F (2019). Decoupled weight decay regularization. ICLR.',
            '[27] Lugmayr A et al. (2022). Repaint: Inpainting using denoising diffusion probabilistic models. CVPR.',
            '[28] Jing B et al. (2022). Torsional diffusion for molecular conformer generation. NeurIPS 35:24240.',
            '[29] Ho J et al. (2019). Axial attention in multidimensional transformers. arXiv:1912.12180.',
            '[30] Oleinikovas V et al. (2016). Understanding cryptic pocket formation by enhanced sampling. JACS 138:14257.',
            '[31] Uversky VN (2019). Intrinsically disordered proteins and their physics. Front Phys 7:10.',
            '[32] Ingraham JB et al. (2023). Illuminating protein space with a programmable generative model. Nature 623:1070.',
        ]

        for ref in refs:
            lines = textwrap.wrap(ref, width=90)
            for i, line in enumerate(lines):
                d._need(LH_SMALL)
                d._put(line,
                       x=0.04 if i > 0 else 0.0,
                       size=FS_SMALL, color=INK)
                d._advance(LH_SMALL)
            d.vspace(0.004)

    print(f'PDF written: {path}')


if __name__ == '__main__':
    out = '/Users/indraniroy/Documents/Github/web-presentation/mdgen/mdgen_survey.pdf'
    build(out)
