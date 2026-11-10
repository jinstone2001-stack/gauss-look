# Changelog

## 1.1.0 - 2026-11-10

- Fix chk→fchk parsing of fixed-width C/H strings, including `Full title (5/4)`; retain strict numeric/logical and truncated-array validation.
- Add spin-resolved frontier selections, energy diagrams, occupation tables and paired MO phase surfaces with cube caching. Link matching logs/checkpoints with rigid alignment and provenance.
- Highlight/filter imaginary modes; animate each mode on its reference geometry, with speed/amplitude, vectors, equilibrium and displaced-XYZ controls.
- Add per-frame electronic energy and atomic Cartesian force tables/vectors/CSV, gradient sign conversion, input-to-standard axis rotation, unit conversion and separate optimization criteria.
- Prefer printed Hartree energies and preserve the supplemental parser conversion convention; distinguish CCD from CCSD.
- Add polarizability tensors, source/frequency selection, high-precision archive parsing, mean/anisotropy/eigenvalues and CSV export.
- Embed searchable offline help, F1 access and individual hover explanations in both frontends. Correct original chk reload and command-line startup conversion.
- Expand core/API/adapter regression tests to 42 and web DOM/API coverage; document X11 and external-tool validation limits.
- Preserve LICENSE and planning baseline. Track this release on `ver-1.1` and `main` and persist the latest-on-main release policy in AGENTS.md.

## 1.0.0 - 2026-11-10

- X11 native Tkinter frontend and offline web frontend, launched with `python GaussLook.py`.
- Shared parser, calculation model, source provenance, quality checks, structures, paths, vibrational and electronic properties.
- Cube mesh/field operations, Gaussian utility adapters, spectral broadening, low-frequency entropy corrections and isotope Hessian analysis.
- SMILES conformers and Cartesian Gaussian input generation, project snapshots and data export.
- Planning document and 140-item implementation status catalog.
- LICENSE copied unchanged from the owner's Ligand- repository.
- 24 automated core/API tests; public output, X11 and mocked DOM validation documented separately.
