#!/usr/bin/env python3
"""Generate one GeoJSON per network (station points) for GitHub's built-in map
rendering. Reads the authoritative StationXML per network and writes
geojson/<net>.geojson (a FeatureCollection of station Points).

Sources: scml/<net>.xml for the UoM + affiliated nets; external/du/all.xml for DU
(the SAA-Stations submodule). Uses station-level coordinates (channel-level coords
are zeroed in the SMP SCML — a known defect — but station coords are correct).

Usage:  python tools/make_geojson.py
"""
import os, json, glob, warnings
import obspy

warnings.filterwarnings("ignore")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def features(inv):
    out = []
    for net in inv:
        for sta in net:
            out.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [sta.longitude, sta.latitude, sta.elevation],
                },
                "properties": {
                    "network": net.code,
                    "station": sta.code,
                    "site": (sta.site.name if sta.site else "") or "",
                    "elevation_m": sta.elevation,
                    "start": str(sta.start_date)[:10] if sta.start_date else None,
                    "end": str(sta.end_date)[:10] if sta.end_date else None,
                },
            })
    return out

def main():
    outdir = os.path.join(REPO, "geojson")
    os.makedirs(outdir, exist_ok=True)

    sources = {}
    for p in sorted(glob.glob(os.path.join(REPO, "scml", "*.xml"))):
        sources[os.path.splitext(os.path.basename(p))[0]] = p
    du = os.path.join(REPO, "external", "du", "all.xml")
    if os.path.exists(du):
        sources["du"] = du

    total = 0
    for net, path in sorted(sources.items()):
        inv = obspy.read_inventory(path)
        feats = features(inv)
        out = os.path.join(outdir, f"{net}.geojson")
        with open(out, "w") as fh:
            json.dump({"type": "FeatureCollection", "features": feats}, fh, indent=2)
        print(f"{net}: {len(feats)} stations -> {os.path.relpath(out, REPO)}")
        total += len(feats)
    print(f"total {total} stations across {len(sources)} networks")

if __name__ == "__main__":
    main()
