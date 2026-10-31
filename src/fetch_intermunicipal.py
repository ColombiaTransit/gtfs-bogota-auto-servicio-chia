"""Regenerate src/intermunicipal_shapes.json by routing between the terminals with GraphHopper.

Uses the public GraphHopper Routing API by default (needs an API key from https://www.graphhopper.com/):

    GH_KEY=your-key python3 src/fetch_intermunicipal.py

Any compatible GraphHopper server can be used instead:

    GH_URL=https://your-server/route GH_PROFILE=bus python3 src/fetch_intermunicipal.py
"""
import json, math, os, urllib.parse, urllib.request

SP = os.path.dirname(os.path.abspath(__file__))
GH_URL = os.environ.get("GH_URL", "https://graphhopper.com/api/1/route")
GH_KEY = os.environ.get("GH_KEY", "")
GH_PROFILE = os.environ.get("GH_PROFILE", "car")

# Terminal coordinates (lat, lon), from OpenStreetMap
POINTS = {
    "CHIA": (4.858839, -74.063273),   # Terminal Urbano Chía
    "P170": (4.7545885, -74.0460432), # Portal Norte (TransMilenio, Calle 170/174)
    "COTA": (4.8123632, -74.0988734), # Terminal Urbano Cota
    "CAJ": (4.9172708, -74.0255304),  # Parque Principal Cajicá
    "SUBA": (4.7468966, -74.0942909), # Portal Suba (TransMilenio)
    "GUAY": (4.8075, -74.0447),       # Guaymaral, Autopista Norte (approximate)
}
ROUTES = [("CH170", "CHIA", "P170"), ("CHCOT", "CHIA", "COTA"), ("CHCAJ", "CHIA", "CAJ"),
          ("CHSUB", "CHIA", "SUBA"), ("CHGUA", "CHIA", "GUAY"), ("CAJ170", "CAJ", "P170"),
          ("COTSUB", "COTA", "SUBA")]


def dist(a, b):
    return math.hypot((a[0] - b[0]) * 111320 * 0.9964, (a[1] - b[1]) * 110574)


def simplify(pts, tol):
    if len(pts) < 3:
        return pts
    a, b = pts[0], pts[-1]
    ax, ay = (b[0] - a[0]) * 111320, (b[1] - a[1]) * 110574
    L = math.hypot(ax, ay)
    mx, ix = 0, 0
    for i in range(1, len(pts) - 1):
        px, py = (pts[i][0] - a[0]) * 111320, (pts[i][1] - a[1]) * 110574
        d = abs(ax * py - ay * px) / L if L else dist(pts[i], a)
        if d > mx:
            mx, ix = d, i
    if mx > tol:
        return simplify(pts[: ix + 1], tol)[:-1] + simplify(pts[ix:], tol)
    return [a, b]


def route(a, b):
    q = [("point", f"{a[0]},{a[1]}"), ("point", f"{b[0]},{b[1]}"), ("profile", GH_PROFILE),
         ("points_encoded", "false"), ("instructions", "false")]
    if GH_KEY:
        q.append(("key", GH_KEY))
    with urllib.request.urlopen(GH_URL + "?" + urllib.parse.urlencode(q), timeout=60) as r:
        return json.load(r)["paths"][0]


out = {}
for rid, a, b in ROUTES:
    for d, (x, y) in enumerate([(a, b), (b, a)]):
        p = route(POINTS[x], POINTS[y])
        pts = simplify([c[:2] for c in p["points"]["coordinates"]], 8)
        out[f"{rid}_{d}"] = {"km": round(p["distance"] / 1000, 2), "min": round(p["time"] / 60000),
                             "pts": [[round(c[0], 5), round(c[1], 5)] for c in pts]}
        print(rid, d, out[f"{rid}_{d}"]["km"], "km", out[f"{rid}_{d}"]["min"], "min")

json.dump(out, open(os.path.join(SP, "intermunicipal_shapes.json"), "w"), separators=(",", ":"))
