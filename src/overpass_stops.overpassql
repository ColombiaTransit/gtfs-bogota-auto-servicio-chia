[out:json][timeout:120];

// Area: Portal Suba / Portal Norte (south) to Cajicá (north), Cota (west) to Yerbabuena (east)
(
  node["highway"="bus_stop"](4.735,-74.115,4.925,-73.990);
  node["public_transport"~"^(platform|stop_position)$"]["bus"="yes"](4.735,-74.115,4.925,-73.990);
  way["public_transport"="platform"]["bus"="yes"](4.735,-74.115,4.925,-73.990);
  node["amenity"="bus_station"](4.735,-74.115,4.925,-73.990);
  way["amenity"="bus_station"](4.735,-74.115,4.925,-73.990);
)->.stops;

// Bus route relations that may be operated by Auto Servicio Chía
(
  relation["type"="route"]["route"="bus"]["operator"~"Ch[ií]a|Auto ?Servicio",i](4.735,-74.115,4.925,-73.990);
  relation["type"="route"]["route"="bus"]["network"~"Ch[ií]a",i](4.735,-74.115,4.925,-73.990);
  relation["type"="route"]["route"="bus"]["name"~"Ch[ií]a",i](4.735,-74.115,4.925,-73.990);
)->.routes;

.stops out center tags;
.routes out tags;
node(r.routes:"stop")->.rstops;
node(r.routes:"platform")->.rplat;
(.rstops; .rplat;);
out tags;
.routes out skel;
