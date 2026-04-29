# Slide Outline (42 slides)

New slides added for a diverse scientific audience are marked **[NEW]**.

## Prerequisites and biology (slides 1–14)

1. **Title**: BBFlow and the goal of fast MD-like protein ensembles.
2. **Talk map**: prerequisites, earlier work, BBFlow, results, limitations.
3. **Static structures are not enough**: one structure versus an ensemble.
4. **Backbone Anatomy** [NEW]: What the protein backbone is — N–Cα–C chain, side chains, why BBFlow models only frames. For non-biologists.
5. **Proteins as energy landscapes**: Boltzmann distribution and conformational probabilities.
6. **Molecular dynamics**: how MD samples motion and why it is expensive.
7. **Why Dynamics Matter** [NEW]: Allostery, induced fit, cryptic pockets — why conformational dynamics are biologically essential and relevant to drug discovery.
8. **What an emulator learns**: replace repeated simulation with learned sampling.
9. **Transformer attention**: basic attention equation and intuition.
10. **From tokens to residues**: why protein models need pair and geometry information.
11. **Coordinate symmetry**: invariance/equivariance and SE(3).
12. **Backbone frames**: represent each residue as a local rigid frame.
13. **AlphaFold IPA**: attention with learned points in residue frames.
14. **CFA**: Clifford Frame Attention, not frame averaging.

## Generative model background (slides 15–17)

15. **Flow vs. Diffusion** [NEW]: Compares diffusion models and flow matching for an ML or physics audience. Explains why flow matching allows non-Gaussian priors, why BBFlow uses 20 steps vs. 100–1000 for diffusion.
16. **Flow matching**: learn a vector field from prior to data.
17. **Flow on SE(3)^N**: geodesics for rotations and translations.

## Earlier work and motivation (slides 18–20)

18. **Earlier ensemble models**: Boltzmann generators, AlphaFlow, ConfDiff, BioEmu.
19. **Gap**: sequence/evolutionary dependence, cost, and de novo limitations.
20. **BBFlow idea**: model \(p(x\mid x_{\mathrm{eq}})\).

## BBFlow method (slides 21–26)

21. **BBFlow pipeline**: equilibrium structure to conditional prior to ensemble samples.
22. **Equilibrium geometry encoding**: distances and local directions.
23. **Conditional prior**: interpolate noise toward the equilibrium backbone.
24. **Network architecture**: GAFL/CFA graph network with six blocks.
25. **Loss and training**: geodesic interpolation and vector-field regression.
26. **Training algorithm**: step-by-step procedure.

## Evaluation (slides 27–31)

27. **Dataset**: ATLAS and standardized 3 × 100 ns MD trajectories.
28. **RMSF Visualized** [NEW]: What RMSF means visually — per-residue flexibility profile, rigid cores, flexible loops. Formula and interpretation for audiences unfamiliar with structural biology metrics.
29. **Metrics**: RMSF, pairwise RMSD, DCCM, PCA W₂, transient contacts.
30. **Main ATLAS result**: speed/accuracy table.
31. **Speed/accuracy Pareto**: simplified chart.

## Results and context (slides 32–37)

32. **BioEmu Context** [NEW]: Three-way comparison — BBFlow, BioEmu, AlphaFlow-T. Which tool fits which scientific question. No MSA vs. ESM vs. full evolutionary machinery.
33. **De novo proteins**: why BBFlow helps when evolutionary information is absent.
34. **Multi-chain generalization**: no residue-index assumption.
35. **BBFlow in Practice** [NEW]: Step-by-step workflow from PDB to ensemble — practical guide for any scientific audience. Includes GitHub link.
36. **Ablation**: what model components mattered.
37. **Training Budget** [NEW]: 3 days on 2× A100 from scratch vs. AlphaFold-scale training. Shows the approach is accessible to labs with modest compute.

## Synthesis and conclusion (slides 38–42)

38. **How to explain BBFlow in one minute**: teaching synthesis.
39. **Limitations**: scope boundaries.
40. **Future Directions** [NEW]: Six open directions — side chains, longer timescales, cryptic pockets, protein-ligand systems, custom MD distributions, RNA/IDPs.
41. **Takeaways**: final summary.
42. **Reference map**: source categories and where to read next.
