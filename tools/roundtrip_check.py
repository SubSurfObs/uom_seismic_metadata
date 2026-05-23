#!/usr/bin/env python3
"""Round-trip / no-drift check.

Compares generated StationXML against the reference SCML for every station that appears
in BOTH, channel by channel. This is the seed of the CI "no-drift" guard: once source/
is complete, generated should match the committed inventory.

Usage:  python tools/roundtrip_check.py <generated.xml> <reference.xml>
"""
import sys, os, warnings
import obspy

warnings.filterwarnings("ignore")

FIELDS = ["sample_rate", "azimuth", "dip", "latitude", "longitude", "elevation", "depth"]

def channels_by_station(inv):
    out = {}
    for net in inv:
        for sta in net:
            out.setdefault(sta.code, {})
            for ch in sta:
                out[sta.code][(ch.location_code, ch.code)] = ch
    return out

def cmp_channel(oc, gc):
    diffs = []
    for f in FIELDS:
        ov, gv = getattr(oc, f, None), getattr(gc, f, None)
        if isinstance(ov, float) and isinstance(gv, float):
            if abs(ov - gv) > 1e-6:
                diffs.append(f"{f} {ov}!={gv}")
        elif ov != gv:
            diffs.append(f"{f} {ov}!={gv}")
    for f in ("start_date", "end_date"):
        if getattr(oc, f) != getattr(gc, f):
            diffs.append(f"{f} {getattr(oc, f)}!={getattr(gc, f)}")
    try:
        os_ = oc.response.instrument_sensitivity.value
        gs_ = gc.response.instrument_sensitivity.value
        if abs(os_ - gs_) / os_ > 1e-9:
            diffs.append(f"sensitivity {os_}!={gs_}")
        on, gn = len(oc.response.response_stages), len(gc.response.response_stages)
        if on != gn:
            diffs.append(f"n_stages {on}!={gn}")
    except Exception as e:
        diffs.append(f"response_error {e!r}")
    return diffs

def main(gen_path, ref_path):
    gen = channels_by_station(obspy.read_inventory(gen_path))
    ref = channels_by_station(obspy.read_inventory(ref_path))
    shared = sorted(set(gen) & set(ref))
    print(f"comparing {len(shared)} station(s): {', '.join(shared)}")
    ok = True
    for sta in shared:
        g, r = gen[sta], ref[sta]
        keys = sorted(set(g) | set(r))
        print(f"\n== {sta} (ref {len(r)} ch / gen {len(g)} ch) ==")
        for k in keys:
            if k not in r:
                print(f"  {k[0]}.{k[1]:4} EXTRA in generated"); ok = False; continue
            if k not in g:
                print(f"  {k[0]}.{k[1]:4} MISSING in generated"); ok = False; continue
            diffs = cmp_channel(r[k], g[k])
            if diffs:
                ok = False
                print(f"  {k[0]}.{k[1]:4} DIFF  " + "; ".join(diffs))
            else:
                print(f"  {k[0]}.{k[1]:4} OK")
    print("\nROUND-TRIP:", "PASS — generated matches reference" if ok else "DIFFERENCES FOUND")
    return 0 if ok else 1

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
