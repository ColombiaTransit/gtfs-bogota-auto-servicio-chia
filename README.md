# GTFS – Auto Servicio Chía (servicio urbano)

Unofficial GTFS feed for the bus routes of **Auto Servicio Chía Ltda.** in Chía, Cundinamarca (Colombia): urban routes within Chía and intermunicipal routes to Bogotá (Portal 170, Suba, Guaymaral), Cota and Cajicá.

- Download: [`gtfs.zip`](gtfs.zip) (the unzipped files are in [`gtfs/`](gtfs/))
- 24 routes (17 urban, 7 intermunicipal), 24 stops, 50 trip patterns (outbound and return), frequency-based timetable
- Valid from 2026-11-01 to 2027-10-31

## Sources

| Data | Source |
|---|---|
| Urban routes: first/last departure, headway, fares | https://autoserviciochia.com/urbano-2/ |
| Urban route geometry (shapes) | GeoJSON layers of the route map at http://autoserviciochia.com/mapas-chia/index.html |
| Intermunicipal routes: first/last departure, headway, fares | https://autoserviciochia.com/intermunicipal/ |
| Intermunicipal terminal locations | [OpenStreetMap](https://www.openstreetmap.org/) (Nominatim / Overpass) |
| Intermunicipal route geometry and running times | [GraphHopper Routing API](https://docs.graphhopper.com/#tag/Routing-API) on OpenStreetMap data |

The urban map layers consist of loose segments per direction. These were chained into one continuous line per direction, simplified with Douglas–Peucker (6 m tolerance) and rounded to 5 decimals. The result is in [`src/shapes.json`](src/shapes.json).

The intermunicipal website publishes no map, so each route was routed terminal-to-terminal with GraphHopper (8 m simplification). The result is in [`src/intermunicipal_shapes.json`](src/intermunicipal_shapes.json) and can be regenerated with [`src/fetch_intermunicipal.py`](src/fetch_intermunicipal.py).

## Assumptions and limitations

### Intermunicipal routes

- **Shapes** are the fastest road route between the terminals, not necessarily the exact path the buses take.
- **Running times** are GraphHopper's free-flow time × 1.5 to account for traffic and boarding.
- **Headways** given as a range use the midpoint (2–3 min → 2.5 min, 3–4 min → 3.5 min); "approx. 10 min" is modelled as 10 min.
- **Terminals**:
  - *Portal 170* → TransMilenio Portal Norte (Autopista Norte, Calle 174).
  - *Terminal Suba* → TransMilenio Portal Suba.
  - *Terminal Cota* → the bus station "Terminal Urbano" in Cota (OSM).
  - *Cajicá* → no terminal in OSM; the Parque Principal is used.
  - *Guaymaral* → the website lists "Terminal Guaymaral → Guaymaral"; modelled as Chía ↔ Guaymaral with an approximate stop on the Autopista Norte.
- Only the two terminals are included as stops; no intermediate stops are published.

### Urban routes

- **Stops**: the website publishes no stop locations. Each trip therefore has only two stops: *Terminal Urbano Chía* and the route's terminus (the end of the outbound shape).
- **Running times**: estimated from shape length at 15 km/h.
- **Timetable**: modelled with `frequencies.txt` (`exact_times=0`). Outbound trips follow the first/last departure from the website; return trips use the same window shifted by the running time.
- **Service days**: not stated on the website; daily service is assumed.
- **Route to map-layer mapping** where the names differ:
  - *Chilacos* → layer "Colombia y Viceversa"
  - *Las Juntas* (destination "Variante") → layer "Variante La Caro y Viceversa"
  - *Centro Chía*: the website gives Despacho Guaymaral as origin; the map shows the route from the Terminal Urbano, which is what the feed uses.
- *Cerca de Piedra / 20 de Julio* has two variants, alternating every 10 minutes each (combined headway 5 min).
- The map layers "BalsaCapilla" and "Fusca" have no timetable on the website and are not included.

## Regenerating

```bash
python3 src/build.py
```

This writes `gtfs/*.txt` and `gtfs.zip`. Parameters (headways, times, fares, speed, traffic factor) are in `src/build.py`.

To refresh the intermunicipal shapes (requires a [GraphHopper API key](https://www.graphhopper.com/), or `GH_URL` pointing at your own GraphHopper server):

```bash
GH_KEY=your-key python3 src/fetch_intermunicipal.py
python3 src/build.py
```

## Disclaimer

This feed is not an official publication of Auto Servicio Chía Ltda. Data is derived from their public website and may be incomplete or out of date.
