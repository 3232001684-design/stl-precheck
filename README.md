# stl-precheck

**Free, open-source, 5-point pre-print sanity check for 3D printing meshes.**

Run it on any STL/OBJ/PLY/GLB *before* you slice, and catch the five problems
behind most failed prints:

| # | Check | Why it matters |
|---|-------|----------------|
| 1 | Watertight | Open surfaces make your slicer guess where the solid is |
| 2 | Normals & volume sign | Inside-out meshes slice into walls of zero thickness |
| 3 | Scale sanity | Unit-less STL files arrive in meters or microns more often than you'd think |
| 4 | Overhang fraction | Area-based estimate of what will need supports (or a better orientation) |
| 5 | Degenerate faces | Zero-area faces from CAD booleans choke some slicers |

```bash
pip install trimesh numpy
python checklist.py part.stl
```

```
== part.stl: ATTENTION NEEDED ==
[ok ] watertight: closed surface
[ok ] normals_and_volume: normals consistent, volume positive
[!! ] scale_sanity: bbox mm = [0.04, 0.03, 0.01] — suspicious for a typical FDM part; check units
[ok ] overhang_fraction: 0.0% of surface is downward-facing beyond 45 deg (walls and bed face excluded) — fine unsupported
[ok ] degenerate_faces: no zero-area faces
```

Exit code is 0 either way; the verdict line tells you whether to proceed.
`--json` gives machine-readable output for CI or batch scripts.

## Why open source?

The checks themselves are simple — you should not have to pay for them.
They're documented in the article
[The 10-minute STL pre-print checklist that saves failed prints](https://dev.to/cy_cy_a73a75ea2dde2b6cf02/the-10-minute-stl-pre-print-checklist-that-saves-failed-prints-288i).

What costs real engineering time is everything *around* the checks:

- **[Mesh Rescue](https://boshen3d.gumroad.com/l/guzgnx)** — the full toolkit:
  automatic hole closing with convergence reporting, duplicate/degenerate face
  cleanup, quadric decimation (PyMeshLab-backed, boundary-preserving), print-bed
  orientation scoring, and calibrated export to STL/OBJ/PLY.
- **[G-code Tuner](https://boshen3d.gumroad.com/l/thywm)** — post-slice
  G-code post-processing: z-hop cleanup with per-segment control, fan speed
  floors, speed scaling and caps, print-time re-estimation. Zero dependencies.
- **[PrintIQ](https://boshen3d.gumroad.com/l/ubtppt)** — the production
  layer: multi-part bed packing with collision guarantees, batch scheduling
  across multiple printers, slicer time/cost estimation, and TPMS lattice
  generation (gyroid/diamond) with measured-vs-target density reporting.

Every tool ships with the source and was tested against a 22-case adversarial
suite (corrupt files, empty geometry, garbage input) before release.

## License

MIT — use it, fork it, sell prints made with it.
