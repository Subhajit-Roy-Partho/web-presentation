# Paper Summary: BBFlow

## Citation

Wolf, Nicolas; Seute, Leif; Viliuga, Vsevolod; Wagner, Simon; Stuehmer, Jan; Graeter, Frauke. **Learning conformational ensembles of proteins based on backbone geometry**. arXiv:2503.05738v2, NeurIPS 2025.

## One-Sentence Summary

BBFlow is a transferable SE(3) flow-matching model that generates short-timescale, MD-like protein backbone conformational ensembles from an equilibrium backbone structure, avoiding MSAs, protein language model embeddings, and pre-trained folding model weights.

## Problem

Protein function often depends on conformational ensembles rather than a single structure. Molecular dynamics (MD) can sample these ensembles, but broad sampling is computationally expensive. Recent ML approaches can emulate ensembles but often rely on AlphaFold-like sequence/evolutionary machinery, which is expensive and can be biased toward natural proteins.

## Main Contributions

1. **Structure-conditioned MD emulation**: BBFlow models the ensemble distribution as \(p(x \mid x_{\mathrm{eq}})\), where \(x_{\mathrm{eq}}\) is an equilibrium backbone structure.
2. **Backbone-only geometric conditioning**: The model uses distances and local directions from the equilibrium backbone, plus optional amino-acid identity.
3. **Conditional prior**: Instead of starting from completely unconditioned noise, BBFlow samples a prior by partially interpolating noise toward \(x_{\mathrm{eq}}\).
4. **No evolutionary information**: It does not require MSA search, an Evoformer, ESM embeddings, or pre-trained folding weights.
5. **Speed and transferability**: It is much faster than AlphaFlow-style baselines at comparable accuracy and generalizes to de novo and multi-chain proteins.

## Mathematical Core

Backbone representation:

\[
x=(r,z)\in SE(3)^N
\]

where each residue has a rotation \(r\in SO(3)\) and translation \(z\in\mathbb{R}^3\).

Conditional vector field:

\[
v(x,t,x_{\mathrm{eq}}):M\times[0,1]\times M_{\mathrm{eq}}\to T_xM
\]

Conditional flow:

\[
\frac{d}{dt}\phi_t(x\mid x_{\mathrm{eq}})=v(\phi_t,t,x_{\mathrm{eq}}),\qquad \phi_0(x\mid x_{\mathrm{eq}})=x
\]

SE(3) vector-field parameterization:

\[
v_{SO(3)}(r_t,t\mid r_1)=\frac{\log_{r_t}(r_1)}{1-t},
\qquad
v_{\mathbb{R}^3}(z_t,t\mid z_1)=\frac{z_1-z_t}{1-t}
\]

Distance encoding:

\[
s_{ij}=\mathrm{bin}(\|z_i-z_j\|_2)
\]

Direction encoding:

\[
e_{ij}=r_i^{-1}\left(\frac{z_i-z_j}{\|z_i-z_j\|_2}\right)
\]

Conditional prior:

\[
x_{\mathrm{uncond}}\sim p_{\mathrm{uncond}},
\qquad
x_0=\gamma(x_{\mathrm{uncond}},x_{\mathrm{eq}},\xi)
\]

with \(\xi=0.2\) in the main experiments.

Flow matching loss:

\[
\mathcal{L}_{FM}=
\mathbb{E}\left[\|v-\hat{v}(x_t,t,x_{\mathrm{eq}})\|^2_{SE(3)}\right]
\]

where:

\[
t\sim U(0,1),\qquad
(x_1,x_{\mathrm{eq}})\sim p_{\mathrm{data}},\qquad
x_0\sim p_0(\cdot\mid x_{\mathrm{eq}})
\]

and:

\[
\|v\|^2_{SE(3)}=\mathrm{Tr}(v_rv_r^T)/2+\|v_z\|_2^2.
\]

## Architecture

- Adapted from GAFL, which extends FrameDiff/FrameFlow-style protein generation.
- SE(3)-equivariant graph neural network.
- Uses Clifford Frame Attention (CFA), an extension of AlphaFold's Invariant Point Attention (IPA).
- Operates on structural frames and geometric pair features.
- Uses 6 message-passing blocks.
- Omits residue-index encoding to reduce memorization and improve multi-chain transfer.
- Does not use AlphaFold's Evoformer, MSA features, or pre-trained folding weights.

## Dataset and Training

- Dataset: ATLAS, a standardized MD dataset with 1390 proteins and three 100 ns trajectories per protein.
- Split follows AlphaFlow: 1265 training proteins, 39 validation proteins, 82 test proteins.
- Trained from scratch for 3 days on two NVIDIA A100-40GB GPUs.
- Main model uses 20 flow timesteps.
- Evaluation generates 250 conformations per protein.
- Metrics are computed using C-alpha atoms.

## Main Results

ATLAS benchmark:

- RMSF correlation: `0.90`
- RMSF MAE: `0.42 A`
- Median RMSF: `1.49 A`, close to MD value `1.48 A`
- Pairwise RMSD MAE: `0.77 A`
- DCCM correlation: `0.87`
- PCA \(W_2\): `1.33`
- Transient contact Jaccard: `29%`
- Inference time: `0.8 s` per generated conformation for the 302-residue protein 7c45A

The main tradeoff:

- AlphaFlow-T: stronger on some RMSF/PCA metrics but about `32.6 s` per conformation and tends to over-stabilize ensembles.
- BBFlow: much faster, captures ensemble spread well, and avoids dependence on evolutionary information.

## De Novo Protein Results

BBFlow remains accurate for de novo proteins where evolutionary sequence information is scarce:

- RMSF correlation: `0.84`
- RMSF MAE: `0.26 A`
- Pairwise RMSD MAE: `0.32 A`
- DCCM correlation: `0.83`
- PCA \(W_2\): `0.67`

AlphaFlow without templates, BioEmu, and ConfDiff degrade substantially in this setting.

## Multi-Chain Results

BBFlow is shown on five multi-chain systems, despite being trained only on monomeric proteins:

- RMSF correlation: `0.82`
- RMSF MAE: `0.31 A`
- Pairwise RMSD MAE: `0.41 A`
- DCCM correlation: `0.85`
- PCA \(W_2\): `0.71`

The authors report that AlphaFlow required parser modifications and produced unphysical states on a tested multimer input.

## Ablation Takeaways

- Conditional prior improves ensemble spread and accuracy.
- Direction encoding helps.
- Distance encoding is essential; removing it is catastrophic.
- Omitting residue indices supports transfer and avoids unnecessary chain-order assumptions.
- Amino-acid identity helps but the model remains surprisingly competitive without it.

## Limitations

- BBFlow emulates the MD distribution it was trained on; it is not a general predictor of rare alternative folded states.
- The main MD scale is short, around three 100 ns trajectories.
- It underperforms MSA/template-aware models on transient contacts.
- It needs an initial/equilibrium structure, although MD also requires one.
- It generates backbone conformations, not side-chain ensembles or protein-ligand interaction ensembles.

