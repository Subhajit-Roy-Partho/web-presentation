# Literature and Prerequisite Notes

## Transformers and Attention

A transformer uses attention to let each token build a context-dependent representation from all other tokens.

\[
\mathrm{Attention}(Q,K,V)=\mathrm{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V
\]

Intuition:

- \(Q\): what a token is looking for.
- \(K\): what each token offers as a match.
- \(V\): the information passed if attention is high.
- Multi-head attention repeats this with different learned projections.

Reference: Vaswani et al., *Attention Is All You Need*, NeurIPS 2017, arXiv:1706.03762.

## Equivariance

For geometric data, a model should not depend on the arbitrary coordinate frame used to store a molecule.

\[
f(g\cdot x)=\rho_{\mathrm{out}}(g)f(x)
\]

If \(\rho_{\mathrm{out}}(g)=I\), the function is invariant. If the output rotates/translates in the corresponding way, it is equivariant.

Important groups:

- \(SO(3)\): 3D rotations.
- \(SE(3)\): 3D rotations plus translations.
- \(E(3)\): rotations, translations, and reflections.

References: Tensor Field Networks; SE(3)-Transformer; EGNN.

## AlphaFold Invariant Point Attention

AlphaFold's structure module represents each residue as a local backbone frame. IPA combines:

- Scalar/single-residue features.
- Pair features.
- Learned 3D query/key/value points.

Learned points are projected from local residue frames into the global coordinate system. Attention includes squared distances between query and key points, which are invariant to global rotation and translation. Output points are transformed back into local frames.

Reference: Jumper et al., *Highly accurate protein structure prediction with AlphaFold*, Nature 2021.

## CFA Terminology

In BBFlow and GAFL, **CFA means Clifford Frame Attention**. It is an extension of IPA using projective geometric algebra. It should not be confused with frame averaging or conformal frame averaging.

Clifford Frame Attention:

- Represents frames and geometric features as projective geometric algebra multivectors.
- Supports points, lines, planes, frames, and geometric products.
- Enables higher-order geometric messages between residues.

Reference: Wagner et al., *Generating Highly Designable Proteins with Geometric Algebra Flow Matching*, NeurIPS 2024.

## Frame Averaging as a Separate Symmetry Method

Frame averaging is a separate technique for building invariant/equivariant networks by averaging predictions over a finite set of canonical group elements:

\[
f_{\mathrm{eq}}(x)=\frac{1}{|F(x)|}\sum_{g\in F(x)}g\cdot\phi(g^{-1}x)
\]

This is useful context for symmetry, but it is not the CFA block used by BBFlow.

Reference: Puny et al., *Frame Averaging for Invariant and Equivariant Network Design*, ICLR 2022.

## Flow Matching

Flow matching learns a vector field that transports samples from a simple prior distribution \(p_0\) into a data distribution \(p_1\).

\[
\frac{dx_t}{dt}=v_\theta(x_t,t)
\]

For a simple Euclidean conditional path:

\[
x_t=(1-t)x_0+tx_1,\qquad u_t=x_1-x_0
\]

Loss:

\[
\mathbb{E}\left[\|v_\theta(x_t,t)-u_t\|^2\right]
\]

On manifolds such as \(SE(3)^N\), straight lines are replaced by geodesics:

\[
x_t=\gamma(x_0,x_1,t),\qquad u_t=\frac{d}{dt}\gamma(x_0,x_1,t)
\]

References: Lipman et al., ICLR 2023; Chen and Lipman, ICLR 2024.

## Protein Backbone Flow Matching

A protein backbone can be represented as a sequence of residue frames:

\[
T_i=(R_i,z_i)\in SE(3),\qquad T\in SE(3)^N
\]

FrameDiff introduced diffusion over residue frames. FrameFlow adapted this setup to flow matching for faster protein backbone generation. BBFlow reuses this geometric generative framing but changes the task from designing new backbones to generating MD-like ensembles conditioned on a known equilibrium backbone.

References: Yim et al., FrameDiff, ICML 2023; Yim et al., FrameFlow, arXiv:2310.05297.

## Protein Ensembles and Boltzmann Intuition

At equilibrium, conformations are distributed according to:

\[
p(x)\propto \exp\left(-\frac{E(x)}{k_BT}\right)
\]

MD samples this distribution by integrating equations of motion, but rare transitions and long relaxation times make exhaustive sampling expensive. Ensemble generative models try to amortize this cost by learning from MD trajectories or experimental ensembles.

Reference: Adcock and McCammon, *Molecular dynamics: survey of methods for simulating protein activity*, Chemical Reviews 2006.

## Earlier and Related Ensemble Work

- **Boltzmann Generators**: normalizing-flow samplers for equilibrium molecular states, often system-specific.
- **ATLAS**: standardized all-atom MD trajectories for 1390 proteins; used for AlphaFlow and BBFlow evaluation.
- **AlphaFlow / ESMFlow**: flow matching applied to fine-tuned AlphaFold/ESMFold-like models for ensemble generation.
- **BioEmu**: scalable sequence-conditioned equilibrium ensemble emulator trained on large heterogeneous data.
- **ConfDiff**: force-guided SE(3) diffusion for protein conformations.
- **MDGen**: generative modeling of time-consistent molecular dynamics trajectories.
- **Str2Str / ESMDiff / structure language models**: alternative structure-to-structure or language-model approaches.
- **MSA clustering and AF2 sampling**: perturb evolutionary inputs to coax AlphaFold into alternative conformations.

