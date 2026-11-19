"""Haalt de CBS-tabellen 84903NED, 86054NED en 86331NED op via de OData-API (opendata.cbs.nl) en schrijft
per tabel de eigenschappen, de dimensies en de landelijke rijen als json in de opgegeven map."""
import json
import os
import sys
import urllib.parse
import urllib.request

map_uit = sys.argv[1]
os.makedirs(map_uit, exist_ok=True)
BASIS = "https://opendata.cbs.nl/ODataApi/odata/{tabel}/{deel}?$format=json"


def haal(tabel, deel, filt=None):
    url = BASIS.format(tabel=tabel, deel=deel)
    if filt:
        url += "&$filter=" + urllib.parse.quote(filt)
    rijen = []
    while url:
        with urllib.request.urlopen(url, timeout=120) as r:
            d = json.load(r)
        rijen += d["value"]
        url = d.get("odata.nextLink")
    return rijen


for tabel in ["84903NED", "86054NED", "86331NED"]:
    props = haal(tabel, "DataProperties")
    with open(os.path.join(map_uit, f"{tabel}_props.json"), "w", encoding="utf-8") as f:
        json.dump(props, f, ensure_ascii=False, indent=1)
    dims = [p["Key"] for p in props if p.get("Type") in ("Dimension", "GeoDimension", "TimeDimension")]
    for dim in dims:
        waarden = haal(tabel, dim)
        with open(os.path.join(map_uit, f"{tabel}_{dim}.json"), "w", encoding="utf-8") as f:
            json.dump(waarden, f, ensure_ascii=False, indent=1)
    geo = [p["Key"] for p in props if p.get("Type") == "GeoDimension"]
    filt = f"{geo[0]} eq 'NL01  '" if geo else None
    data = haal(tabel, "TypedDataSet", filt)
    with open(os.path.join(map_uit, f"{tabel}_data_NL.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(tabel, len(props), dims, len(data))
