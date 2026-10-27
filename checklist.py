#!/usr/bin/env python3
"""stl-precheck: a 5-point pre-print sanity check for STL/OBJ/PLY meshes.

Free and open source. Checks: watertightness, normal consistency & volume
sign, scale sanity, overhang fraction, degenerate faces.

Requires: pip install trimesh numpy

Usage:
  python checklist.py part.stl
  python checklist.py part.stl --json
"""
import argparse
import json
import sys

try:
    import numpy as np
    import trimesh
    from trimesh.repair import fill_holes, fix_normals, fix_winding
except Exception as e:  # pragma: no cover
    sys.exit("Install dependencies first:\n  pip install trimesh numpy\n"
             f"(detail: {e})")


def load_mesh(path):
    import os
    if not os.path.exists(path):
        sys.exit(f"File not found: {path}")
    try:
        m = trimesh.load(path, process=False, force="mesh")
    except Exception as e:
        sys.exit(f"Could not parse {path}: {e}\n(Supported: STL/OBJ/PLY/GLB)")
    if isinstance(m, trimesh.Scene):
        geos = [g for g in m.geometry.values() if isinstance(g, trimesh.Trimesh)]
        m = trimesh.util.concatenate(geos) if geos else None
    if m is None or len(m.vertices) == 0 or len(m.faces) == 0:
        sys.exit("No triangle geometry found (file empty, corrupt, or faceless).")
    m.merge_vertices()  # STL is a triangle soup; without this every STL reads "not watertight"
    return m


def check_watertight(m):
    ok = bool(m.is_watertight)
    fixable = False
    if not ok:
        probe = m.copy()
        for _ in range(3):
            if probe.is_watertight:
                break
            fill_holes(probe)
            probe.merge_vertices()
            probe.remove_unreferenced_vertices()
        fixable = bool(probe.is_watertight)
    return {
        "check": "watertight",
        "ok": ok,
        "detail": "closed surface" if ok else (
            "open boundaries; auto-closing looks possible" if fixable
            else "open boundaries; simple hole-filling will NOT close it"),
    }


def check_normals(m):
    fix_winding(m)
    fix_normals(m, multibody=True)
    pos = bool(m.volume > 0)
    return {
        "check": "normals_and_volume",
        "ok": pos,
        "detail": ("normals consistent, volume positive" if pos
                   else "volume is negative — mesh is inside-out; invert before slicing"),
    }


def check_scale(m):
    bbox = np.asarray(m.bounds[1]) - np.asarray(m.bounds[0])
    biggest = float(bbox.max()) if len(bbox) else 0.0
    sane = 1.0 <= biggest <= 500.0
    return {
        "check": "scale_sanity",
        "ok": sane,
        "detail": f"bbox mm = {[round(float(v), 2) for v in bbox]}"
                  + ("" if sane else " — suspicious for a typical FDM part; check units"),
    }


def check_overhang(m, limit_deg=45.0, warn_frac=0.03):
    # Only faces that point DOWNWARD beyond the limit need support; vertical
    # walls print fine unsupported. Faces at the very bottom are assumed to
    # sit on the bed and are excluded too.
    up = np.array([0, 0, 1.0])
    nz = m.face_normals[:, 2]
    centers_z = m.triangles.mean(axis=1)[:, 2]
    bed_z = float(m.bounds[0][2]) + 1e-3 * max(1.0, float(m.bounds[1][2] - m.bounds[0][2]) / 100.0)
    off_bed = centers_z > bed_z
    needs = (nz < -np.cos(np.radians(limit_deg))) & off_bed
    total = float(m.area_faces.sum()) or 1.0
    frac = float(m.area_faces[needs].sum()) / total
    ok = frac <= warn_frac
    return {
        "check": "overhang_fraction",
        "ok": ok,
        "detail": f"{frac:.1%} of surface is downward-facing beyond {limit_deg:.0f} deg (walls and bed face excluded)"
                  + (" — fine unsupported" if ok else " — rotate or add supports"),
    }


def check_degenerate(m):
    zero = int(np.isclose(m.area_faces, 0.0).sum())
    ok = zero == 0
    return {
        "check": "degenerate_faces",
        "ok": ok,
        "detail": (f"{zero} zero-area faces" if not ok else "no zero-area faces")
                  + ("" if ok else " — clean before slicing"),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="5-point pre-print mesh check")
    ap.add_argument("input", help="STL/OBJ/PLY/GLB file")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    args = ap.parse_args(argv)

    m = load_mesh(args.input)
    results = [
        check_watertight(m),
        check_normals(m),
        check_scale(m),
        check_overhang(m),
        check_degenerate(m),
    ]
    verdict = "PASS" if all(r["ok"] for r in results) else "ATTENTION NEEDED"
    out = {"file": args.input, "verdict": verdict, "checks": results,
           "tip": "Run the fixed mesh through your slicer's preview before a long print."}
    if args.json:
        print(json.dumps(out, indent=2))
    else:
        print(f"== {args.input}: {verdict} ==")
        for r in results:
            print(f"[{'ok ' if r['ok'] else '!!'}] {r['check']}: {r['detail']}")
        print(out["tip"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
