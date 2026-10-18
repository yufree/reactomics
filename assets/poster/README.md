# Poster figures: paradigm shift of reactomics

Print-ready figures for a reactomics poster, focused on the **metabolites → reactions** paradigm shift.

Regenerate vector/PDF/PNG schematics:

```bash
python scripts/generate_poster_figures.py
```

## Suggested poster layout

| File | Role on poster |
|------|----------------|
| `fig0_paradigm_shift_hero.jpg` | Optional hero / title-panel illustration |
| `fig1_paradigm_shift.{svg,pdf,png}` | **Main figure** — traditional metabolomics vs reactomics |
| `fig2_pmd_as_reaction_detector.{svg,pdf,png}` | MS as reaction detector + PMD → reaction table |
| `fig2b_pmd_detector_hero.jpg` | Alternate illustrated version of fig2 |
| `fig3_reaction_level_quantification.{svg,pdf,png}` | Workflow + static vs dynamic quantification |
| `fig4_practical_consequences.{svg,pdf,png}` | Four consequences of reaction-first analysis |
| `fig5_unit_of_analysis.{svg,pdf,png}` | Unit of analysis flip (molecule → reaction) |
| `fig5b_unit_of_analysis_hero.jpg` | Alternate illustrated version of fig5 |
| `../pmd-orbitals.png` | Existing quantized PMD orbital figure (reuse) |

## Format notes

- Prefer **SVG/PDF** for the poster master file (Illustrator, Inkscape, PowerPoint, Affinity, LaTeX).
- PNGs are 300 dpi raster exports for quick preview.
- JPG “hero” files are conceptual illustrations; use SVG/PDF when labels must stay editable.

## Narrative arc

1. **Fig 5 / Fig 1** — state the shift (unit = reaction; edges become analytes).
2. **Fig 2** — why it works (Δm encodes chemistry).
3. **`pmd-orbitals.png`** — why PMDs are discrete (cofactor quantization).
4. **Fig 3** — how to quantify without compound IDs (static / dynamic).
5. **Fig 4** — what you gain in practice.
