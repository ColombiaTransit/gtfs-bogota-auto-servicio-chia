# GTFS – Auto Servicio Chía (servicio urbano)

Unofficial GTFS feed for the urban bus routes of **Auto Servicio Chía Ltda.** in Chía, Cundinamarca (Colombia).

- Download: [`gtfs.zip`](gtfs.zip) (the unzipped files are in [`gtfs/`](gtfs/))
- 17 routes, 19 stops, 36 trip patterns (outbound and return), frequency-based timetable
- Valid from 2026-11-01 to 2027-10-31

## Sources

| Data | Source |
|---|---|
| Routes, first/last departure, headway, fares | https://autoserviciochia.com/urbano-2/ |
| Route geometry (shapes) | GeoJSON layers of the route map at http://autoserviciochia.com/mapas-chia/index.html |

The map layers consist of loose segments per direction. These were chained into one continuous line per direction, simplified with Douglas–Peucker (6 m tolerance) and rounded to 5 decimals. The result is in [`src/shapes.json`](src/shapes.json).

## Assumptions and limitations

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

This writes `gtfs/*.txt` and `gtfs.zip`. Parameters (headways, times, fares, speed) are at the top of `src/build.py`.

## Disclaimer

This feed is not an official publication of Auto Servicio Chía Ltda. Data is derived from their public website and may be incomplete or out of date.
