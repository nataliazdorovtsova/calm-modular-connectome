#!/usr/bin/env python3
"""
Derive the CALM community palette by computation, not by eye.

Community colours in this project are read in an ALL-PAIRS setting: in an
anatomical brain render any two communities can end up adjacent, so every pair
must be separable -- a much harder gate than the adjacent-only case that applies
to bars and stacks.

This script searches OKLCH space for N colours maximising the worst pairwise
distance under simulated protanopia and deuteranopia, subject to the same gates
the data-viz validator enforces:

    lightness band   L in [lo, hi] for the mode
    chroma floor     C >= 0.10          (below this a hue reads as grey)
    normal vision    worst pair dE >= 15 (hard gate)
    contrast         >= 3:1 vs surface preferred

It reuses the validator's own colour maths so the numbers agree exactly.

Usage:
    python3 design_palette.py            # light and dark searches, N=6
"""

import importlib.util
import itertools
import sys

VALIDATOR = ("/tmp/claude-7075/bundled-skills/2.1.263/"
             "0d33394c929680d4ed75d8808309012f/dataviz/scripts/validate_palette.py")

spec = importlib.util.spec_from_file_location("vp", VALIDATOR)
vp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(vp)

OKABE_ITO = {
    "orange":        "#E69F00",
    "sky blue":      "#56B4E9",
    "bluish green":  "#009E73",
    "yellow":        "#F0E442",
    "blue":          "#0072B2",
    "vermillion":    "#D55E00",
    "reddish purple": "#CC79A7",
}


def oklch_to_hex(L, C, H):
    """OKLCH -> sRGB hex, or None if out of gamut."""
    import math
    h = math.radians(H)
    a, b = C * math.cos(h), C * math.sin(h)
    l_ = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m_ = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s_ = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    r = +4.0767416621 * l_ - 3.3077115913 * m_ + 0.2309699292 * s_
    g = -1.2684380046 * l_ + 2.6097574011 * m_ - 0.3413193965 * s_
    bl = -0.0041960863 * l_ - 0.7034186147 * m_ + 1.7076147010 * s_
    out = []
    for c in (r, g, bl):
        if c < -0.001 or c > 1.001:
            return None
        out.append(max(0.0, min(1.0, c)))
    return "#" + "".join(f"{round(vp.lin2s(c) * 255):02x}" for c in out).upper()


def worst_cvd(colors):
    """Worst pairwise dE over all pairs under protan+deutan."""
    return min(min(vp.deltaE(x, y, "protan"), vp.deltaE(x, y, "deutan"))
               for x, y in itertools.combinations(colors, 2))


def worst_normal(colors):
    return min(vp.deltaE(x, y) for x, y in itertools.combinations(colors, 2))


def candidates(lo, hi, surface, min_contrast):
    """In-gamut colours inside the mode's band, meeting chroma + contrast."""
    out = []
    L = lo
    while L <= hi + 1e-9:
        for Ci in range(10, 33):
            C = Ci / 100
            for H in range(0, 360, 4):
                hx = oklch_to_hex(L, C, H)
                if hx is None:
                    continue
                _l, c = vp.oklch(hx)
                if c < 0.10:
                    continue
                if vp.contrast(hx, surface) < min_contrast:
                    continue
                out.append(hx)
        L += 0.03
    return sorted(set(out))


def search(n, lo, hi, surface, min_contrast, seed_from=None):
    """Greedy max-min, then swap refinement."""
    pool = candidates(lo, hi, surface, min_contrast)
    if not pool:
        return None, 0.0
    chosen = list(seed_from) if seed_from else [pool[0]]
    while len(chosen) < n:
        best, best_score = None, -1
        for cand in pool:
            if cand in chosen:
                continue
            score = min(min(vp.deltaE(cand, x, "protan"),
                            vp.deltaE(cand, x, "deutan")) for x in chosen)
            if score > best_score:
                best, best_score = cand, score
        chosen.append(best)
    # swap refinement
    improved = True
    while improved:
        improved = False
        for i in range(len(chosen)):
            base = worst_cvd(chosen)
            for cand in pool:
                if cand in chosen:
                    continue
                trial = list(chosen)
                trial[i] = cand
                if worst_normal(trial) < 15:
                    continue
                if worst_cvd(trial) > base:
                    chosen, base, improved = trial, worst_cvd(trial), True
    return chosen, worst_cvd(chosen)


def report(name, colors):
    print(f"\n{name}")
    print(f"   {','.join(colors)}")
    print(f"   worst CVD dE   : {worst_cvd(colors):.1f}")
    print(f"   worst normal dE: {worst_normal(colors):.1f}")
    for c in colors:
        L, C = vp.oklch(c)
        import math
        La, a, b = vp.lin2oklab(*vp.lin(c))
        H = math.degrees(math.atan2(b, a)) % 360
        print(f"     {c}  L={L:.3f} C={C:.3f} H={H:6.1f}")


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 6

    oi6 = [OKABE_ITO[k] for k in
           ("orange", "sky blue", "bluish green", "blue", "vermillion",
            "reddish purple")]
    report(f"Okabe-Ito {len(oi6)} (reference, light)", oi6)

    print("\n" + "=" * 60)
    print(f"SEARCH: light mode, n={n}, band 0.43-0.77, contrast >= 2.0")
    best, score = search(n, 0.43, 0.77, "#fcfcfb", 2.0)
    report(f"  best found (light, n={n})", best)

    print("\n" + "=" * 60)
    print(f"SEARCH: dark mode, n={n}, band 0.48-0.67, contrast >= 3.0")
    bestd, scored = search(n, 0.48, 0.67, "#1a1a19", 3.0)
    report(f"  best found (dark, n={n})", bestd)
