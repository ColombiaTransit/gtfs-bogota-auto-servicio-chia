import json, csv, math, os, zipfile, sys

SP = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SP)
OUT = os.path.join(ROOT, "gtfs")
os.makedirs(OUT, exist_ok=True)
shapes = json.load(open(os.path.join(SP, "shapes.json")))

SPEED_KMH = 15.0  # aangenomen gemiddelde stadsbussnelheid incl. haltes

def dist(a, b):
    x = (a[0] - b[0]) * 111320 * math.cos(math.radians(4.86))
    y = (a[1] - b[1]) * 110574
    return math.hypot(x, y)

def length(pts):
    return sum(dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))

def hms(m):
    return f"{m // 60:02d}:{m % 60:02d}:00"

def tmin(s):
    h, m = s.split(":")
    return int(h) * 60 + int(m)

# route_id, naam bestemming, layer, start, eind, headway (min), tarief, origin-naam
ROUTES = [
    ("PEA", "Peaje", ["p1_11_peaje_project"], "04:55", "20:00", 3, 2000),
    ("CHI", "Av. Chilacos", ["p1_09_colombia_project"], "05:30", "21:00", 5, 2000),
    ("CDP", "Cerca de Piedra / 20 de Julio", ["p1_05_cerca_de_piedra_projec", "p2_02_20_de_julio_project"], "05:20", "20:30", 5, 2000),
    ("JUN", "Las Juntas (Variante)", ["p4_01_variantelacaro40_proje"], "05:30", "18:00", 30, 2000),
    ("ALE", "Alejandría", ["p1_13_alejandria_project"], "05:30", "19:00", 30, 2000),
    ("FAG", "Fagua", ["p1_08_fagua_project"], "04:47", "21:17", 10, 2000),
    ("GUA", "Guanatá", ["p2_04_guanata_project"], "05:45", "19:30", 15, 2000),
    ("SIN", "Sindamanoy", ["p2_01_sindamanoy_project"], "05:25", "18:10", 30, 2000),
    ("BOJ", "Bojacá", ["p1_06_bojaca_project"], "05:15", "21:30", 5, 2000),
    ("FON", "Fonquetá", ["p1_03_fonqueta_project"], "05:45", "20:30", 10, 2000),
    ("TIQ", "Tiquiza", ["p1_04_tiquiza_project"], "05:07", "19:57", 10, 2000),
    ("BAL", "La Balsa", ["p1_02_la_balsa_project"], "05:45", "20:00", 10, 2000),
    ("SAM", "Samaria", ["p1_01_samaria_project"], "05:00", "21:15", 10, 2000),
    ("CAR", "La Caro", ["p1_10_la_caro_project"], "05:30", "19:00", 30, 2000),
    ("YER", "Yerbabuena", ["p3_01_yerbabuena_project"], "05:20", "20:00", 30, 2400),
    ("CEN", "Centro Chía", ["p1_12_centrochia_project"], "05:20", "20:30", 3, 2000),
    ("BOS", "El Bosque", ["p1_07_el_bosque_project"], "05:30", "18:00", 60, 2000),
]
TERMINI_NAMES = {
    "p1_05_cerca_de_piedra_projec": "Cerca de Piedra",
    "p2_02_20_de_julio_project": "20 de Julio",
}

def w(name, header, rows):
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as f:
        c = csv.writer(f)
        c.writerow(header)
        c.writerows(rows)

agency = [["ASCH", "Auto Servicio Chía Ltda.", "https://autoserviciochia.com/", "America/Bogota", "es", "+57 310 569 4983"]]

# Terminal Urbano: gemiddelde van begin ida / eind regreso
starts = [shapes[f"{L}_0"][0] for r in ROUTES for L in r[2]] + [shapes[f"{L}_1"][-1] for r in ROUTES for L in r[2]]
T = [sum(p[0] for p in starts) / len(starts), sum(p[1] for p in starts) / len(starts)]
stops = [["TERMINAL", "Terminal Urbano Chía", f"{T[1]:.6f}", f"{T[0]:.6f}", "0", ""]]
routes, trips, stop_times, freqs, shape_rows, fare_rules = [], [], [], [], [], []
fares = {}
report = []

for rid, dest, layers, st, en, hw, price in ROUTES:
    routes.append([rid, "ASCH", rid, f"Terminal Urbano – {dest}", 3, "", ""])
    fid = f"F{price}"
    fares[fid] = price
    fare_rules.append([fid, rid])
    n = len(layers)
    for li, L in enumerate(layers):
        ida, reg = shapes[f"{L}_0"], shapes[f"{L}_1"]
        sid = f"S_{rid}{li if n > 1 else ''}"
        tname = TERMINI_NAMES.get(L, dest)
        # eindhalte: midden tussen eind ida en begin regreso
        e = [(ida[-1][0] + reg[0][0]) / 2, (ida[-1][1] + reg[0][1]) / 2]
        stops.append([sid, tname, f"{e[1]:.6f}", f"{e[0]:.6f}", "0", ""])
        # varianten verdelen de frequentie: elk n*hw, verschoven met hw
        vhw = hw * n
        off = hw * li
        for d, (pts, a, b) in enumerate([(ida, "TERMINAL", sid), (reg, sid, "TERMINAL")]):
            shp = f"{rid}{li if n > 1 else ''}_{d}"
            cum = 0.0
            for i, p in enumerate(pts):
                if i:
                    cum += dist(pts[i - 1], p)
                shape_rows.append([shp, f"{p[1]:.5f}", f"{p[0]:.5f}", i + 1, f"{cum / 1000:.3f}"])
            km = cum / 1000
            tt = max(5, round(km / SPEED_KMH * 60))
            tid = f"{shp}_T"
            head = tname if d == 0 else "Terminal Urbano"
            trips.append([rid, "DIARIO", tid, head, d, shp])
            stop_times.append([tid, "00:00:00", "00:00:00", a, 1, "0.000", 0])
            stop_times.append([tid, hms(tt), hms(tt), b, 2, f"{km:.3f}", 0])
            # ida: vertrek vanaf Terminal volgens site; regreso: zelfde venster, verschoven met rijtijd
            s = tmin(st) + off + (0 if d == 0 else tt)
            e_ = tmin(en) + (0 if d == 0 else tt) + 1  # end_time exclusief
            freqs.append([tid, hms(s), hms(e_), vhw * 60, 0])
            report.append(f"{shp:8s} {km:5.1f} km  {tt:3d} min  {hms(s)}-{hms(e_ - 1)} elke {vhw} min")

w("agency.txt", ["agency_id", "agency_name", "agency_url", "agency_timezone", "agency_lang", "agency_phone"], agency)
w("stops.txt", ["stop_id", "stop_name", "stop_lat", "stop_lon", "location_type", "parent_station"], stops)
w("routes.txt", ["route_id", "agency_id", "route_short_name", "route_long_name", "route_type", "route_color", "route_text_color"], routes)
w("trips.txt", ["route_id", "service_id", "trip_id", "trip_headsign", "direction_id", "shape_id"], trips)
w("stop_times.txt", ["trip_id", "arrival_time", "departure_time", "stop_id", "stop_sequence", "shape_dist_traveled", "timepoint"], stop_times)
w("frequencies.txt", ["trip_id", "start_time", "end_time", "headway_secs", "exact_times"], freqs)
w("shapes.txt", ["shape_id", "shape_pt_lat", "shape_pt_lon", "shape_pt_sequence", "shape_dist_traveled"], shape_rows)
w("calendar.txt", ["service_id", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "start_date", "end_date"],
  [["DIARIO", 1, 1, 1, 1, 1, 1, 1, "20261101", "20271031"]])
w("fare_attributes.txt", ["fare_id", "price", "currency_type", "payment_method", "transfers", "agency_id"],
  [[f, p, "COP", 0, 0, "ASCH"] for f, p in fares.items()])
w("fare_rules.txt", ["fare_id", "route_id"], fare_rules)
w("feed_info.txt", ["feed_publisher_name", "feed_publisher_url", "feed_lang", "feed_start_date", "feed_end_date", "feed_version"],
  [["Afgeleid van autoserviciochia.com (niet officieel)", "https://autoserviciochia.com/urbano-2/", "es", "20261101", "20271031", "2026-10-31"]])

zp = os.path.join(ROOT, "gtfs.zip")
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(OUT)):
        z.write(os.path.join(OUT, fn), fn)
print("\n".join(report))
print(zp, len(stops), "stops", len(trips), "trips", len(shape_rows), "shape pts")
