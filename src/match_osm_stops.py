"""Match OSM bus stops (Overpass export) to the route shapes.

Usage: python3 src/match_osm_stops.py path/to/overpass_export.json
Writes src/osm_stops.json: {shape_id: [[osm_id, name, lat, lon, dist_along_m], ...]}
"""
import json, math, os, sys

SP = os.path.dirname(os.path.abspath(__file__))
MAX_OFFSET = 25.0   # m, stop must be within this distance of the shape
MIN_GAP = 150.0     # m, drop stops closer than this to the previous kept stop / terminals
COSLAT = math.cos(math.radians(4.85))


def xy(lon, lat):
    return lon * 111320 * COSLAT, lat * 110574


def is_excluded(t, lat):
    net = (t.get("network", "") + " " + t.get("operator", "") + " " + t.get("name", "")).lower()
    # Bogotá SITP/TransMilenio stops: not used by these intermunicipal buses
    return lat < 4.79 or "sitp" in net or "transmilenio" in net


def load_stops(path):
    out = []
    for e in json.load(open(path))["elements"]:
        if e["type"] not in ("node", "way"):
            continue
        t = e.get("tags", {})
        lat = e.get("lat", e.get("center", {}).get("lat"))
        lon = e.get("lon", e.get("center", {}).get("lon"))
        if lat is None or t.get("amenity") == "bus_station" or is_excluded(t, lat):
            continue
        out.append({"id": f"{e['type'][0]}{e['id']}", "name": t.get("name", ""), "lat": lat, "lon": lon,
                    "platform": t.get("public_transport") != "stop_position"})
    return out


def match(shape, stops):
    P = [xy(*p) for p in shape]
    cum = [0.0]
    for i in range(1, len(P)):
        cum.append(cum[-1] + math.dist(P[i - 1], P[i]))
    res = []
    for s in stops:
        q = xy(s["lon"], s["lat"])
        best = None
        for i in range(1, len(P)):
            (ax, ay), (bx, by) = P[i - 1], P[i]
            dx, dy = bx - ax, by - ay
            L2 = dx * dx + dy * dy
            u = 0 if L2 == 0 else max(0, min(1, ((q[0] - ax) * dx + (q[1] - ay) * dy) / L2))
            px, py = ax + u * dx, ay + u * dy
            off = math.hypot(q[0] - px, q[1] - py)
            if off <= MAX_OFFSET and (best is None or off < best[0]):
                side = dx * (q[1] - ay) - dy * (q[0] - ax)  # >0 left, <0 right
                best = (off, cum[i - 1] + u * math.sqrt(L2), side)
        if best is None:
            continue
        off, along, side = best
        # Colombia drives on the right: platforms must be on the right-hand side
        if s["platform"] and off > 4 and side > 0:
            continue
        res.append([s["id"], s["name"], s["lat"], s["lon"], round(along)])
    res.sort(key=lambda r: r[4])
    kept, last = [], MIN_GAP * -1 + 0
    total = cum[-1]
    for r in res:
        if r[4] < MIN_GAP or r[4] > total - MIN_GAP:
            continue  # too close to a terminal
        if kept and r[4] - kept[-1][4] < MIN_GAP:
            continue
        kept.append(r)
    return kept


if __name__ == "__main__":
    stops = load_stops(sys.argv[1])
    shapes = {}
    for k, v in json.load(open(os.path.join(SP, "shapes.json"))).items():
        shapes[k] = v
    for k, v in json.load(open(os.path.join(SP, "intermunicipal_shapes.json"))).items():
        shapes["I_" + k] = v["pts"]
    out = {k: match(v, stops) for k, v in shapes.items()}
    json.dump(out, open(os.path.join(SP, "osm_stops.json"), "w"), ensure_ascii=False, indent=0)
    print(len(stops), "candidate stops")
    for k, v in out.items():
        print(f"{k:32s} {len(v):3d}  " + ", ".join((r[1] or r[0]) for r in v)[:110])
