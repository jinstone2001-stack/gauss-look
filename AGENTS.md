# GaussLook project instructions

- Maintain a single Python analysis engine shared by the native X11 and web frontends.
- Prioritize Gaussian log/checkpoint MO/HOMO/LUMO, normal-mode animation/imaginary frequencies, per-frame energies/Cartesian forces, and polarizability analysis.
- Preserve missing values, units, energy types and source provenance. Never infer a successful calculation from checkpoint availability alone.
- Explain controls in the built-in offline manual and add button-specific hover descriptions in both frontends.
- For each release, keep the requested version branch (for example `ver-1.1`) and `main` at the latest validated release commit. Update `main` with a normal fast-forward after checking the current remote head; preserve other people's changes.
- Update version, changelog, user guide and validation evidence with releases. Run core/API tests, compile checks and the mocked web DOM/API test. Clearly distinguish mock utilities/renderers from actual Gaussian or WebGL validation.
- Keep LICENSE identical to the owner's Ligand- repository unless the owner explicitly requests a license change.
- Keep original planning documents as the baseline; document implemented changes separately.
