# GTFS – Auto Servicio Chía

Unofficial GTFS feed for the bus routes of **Auto Servicio Chía Ltda.** in Chía, Cundinamarca (Colombia): urban routes within Chía and intermunicipal routes to Bogotá (Portal 170, Suba, Guaymaral), Cota and Cajicá.

- Download: [`gtfs.zip`](gtfs.zip) (the unzipped files are in [`gtfs/`](gtfs/))
- 24 routes (17 urban, 7 intermunicipal), 43 stops, 50 trip patterns (outbound and return), frequency-based timetable
- Valid from 2026-11-01 to 2027-10-31

## Sources

| Data | Source |
|---|---|
| Urban routes: first/last departure, headway, fares | https://autoserviciochia.com/urbano-2/ |
| Urban route geometry (shapes) | GeoJSON layers of the route map at http://autoserviciochia.com/mapas-chia/index.html |
| Intermunicipal routes: first/last departure, headway, fares | https://autoserviciochia.com/intermunicipal/ |
| Intermunicipal terminal locations | [OpenStreetMap](https://www.openstreetmap.org/) (Nominatim / Overpass) |
| Intermunicipal route geometry and running times | [GraphHopper Routing API](https://docs.graphhopper.com/#tag/Routing-API) on OpenStreetMap data |
| Intermediate stops | OpenStreetMap bus stops via the [Overpass API](https://overpass-turbo.eu/) |

The urban map layers consist of loose segments per direction. These were chained into one continuous line per direction, simplified with Douglas–Peucker (6 m tolerance) and rounded to 5 decimals. The result is in [`src/shapes.json`](src/shapes.json).

The intermunicipal website publishes no map, so each route was routed terminal-to-terminal with GraphHopper (8 m simplification). The result is in [`src/intermunicipal_shapes.json`](src/intermunicipal_shapes.json) and can be regenerated with [`src/fetch_intermunicipal.py`](src/fetch_intermunicipal.py).

## Stops

The operator publishes no stop locations. Every trip has:

1. its two **terminals** (Terminal Urbano Chía and the route's other end), and
2. **intermediate stops from OpenStreetMap** where OSM has bus stops along the route.

### How OSM stops are matched

1. [`src/overpass_stops.overpassql`](src/overpass_stops.overpassql) exports all bus stops, platforms and bus stations in the area, plus any OSM bus route relations for the operator.
2. [`src/match_osm_stops.py`](src/match_osm_stops.py) matches them to every shape (both urban and intermunicipal). A stop is used when it:
   - lies within 25 m of the shape;
   - is on the right-hand side of the direction of travel (platforms more than 4 m from the line; stop positions on the road are accepted for both directions);
   - is at least 150 m from the previous stop and from either terminal.
3. Bogotá SITP and TransMilenio stops (and anything south of latitude 4.79) are excluded, because there is no evidence these buses use them; OSM contains no route relations for Auto Servicio Chía.
4. Most matched OSM stops have no `name` tag. Their GTFS names are in [`src/osm_stop_names.json`](src/osm_stop_names.json), built from the road and a nearby OSM landmark (e.g. *Autopista Norte – UNICOC*). Stop IDs are `OSM_<n|w><osm id>`, so each stop can be traced back to OSM.
5. Arrival times at intermediate stops are interpolated linearly by distance along the shape between the two terminals; only the terminals are marked as timepoints (`timepoint=1`).

The result is in [`src/osm_stops.json`](src/osm_stops.json).

### Coverage (OSM data of 2026-10-31)

19 OSM stops are used. Almost all of them are on the **Autopista Norte** between Chía and Bogotá, on the **Vía Chía–Cajicá** (Fontanar) and on the road towards **Yerbabuena / Sindamanoy**. Bus stops inside Chía itself are barely mapped in OSM, so:

| Routes | Intermediate stops per direction |
|---|---|
| 11 of 17 urban routes inside Chía | 0 |
| Peaje, Sindamanoy | 1–10 (Autopista Norte section only) |
| La Caro, Las Juntas, Yerbabuena, 20 de Julio | 1–3 |
| Chía – Portal 170, Cajicá – Portal 170 | 5–8 |
| Chía – Guaymaral | 0 outbound, 5 return |
| Chía – Cota, Chía – Cajicá, Chía – Suba, Cota – Suba | 0 |

Mapping bus stops in Chía in OpenStreetMap and re-running the steps below will directly improve this feed.

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

### Urban routes

- **Terminus stops**: placed at the end of the outbound shape.
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
```

To refresh the intermediate stops:

1. Run [`src/overpass_stops.overpassql`](src/overpass_stops.overpassql) on [overpass-turbo.eu](https://overpass-turbo.eu/) and export via *Export → Data → raw OSM data (JSON)*.
2. Match and rebuild:

   ```bash
   python3 src/match_osm_stops.py path/to/export.json   # writes src/osm_stops.json
   python3 src/build.py
   ```

3. Give newly matched unnamed stops a name in [`src/osm_stop_names.json`](src/osm_stop_names.json) (otherwise they are called *Parada &lt;osm id&gt;*).

## License and disclaimer

Stop locations, intermunicipal terminals and routed shapes are derived from OpenStreetMap data © OpenStreetMap contributors, available under the [ODbL](https://www.openstreetmap.org/copyright).

This feed is not an official publication of Auto Servicio Chía Ltda. Data is derived from their public website and OpenStreetMap and may be incomplete or out of date.
