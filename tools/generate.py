#!/usr/bin/env python3
"""Minimal StationXML generator (proof of concept).

Reads the single-source-of-truth under source/ and expands it to FDSN StationXML:
  source/stations/<net>.yaml   station identity + ordered epochs (instrument + sample_rate)
  source/instruments/*.yaml    (recorder + gain + sensor) templates
  source/responses/*.xml       pinned, validated responses (one per instrument+rate)

Channels are expanded from the instrument's components with standard ZNE az/dip; the
SEED band letter is derived from sample_rate (Gecko convention). The response is grafted
from the pinned response file. Nothing about the response is hand-built here.

Usage:  python tools/generate.py <net> <out.xml>
"""
import sys, os, copy, warnings
import yaml
import obspy
from obspy.core.inventory import Inventory, Network, Station

warnings.filterwarnings("ignore")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SEED band letter from sample rate — Gecko convention (rate only, no sensor distinction)
def band_letter(sr):
    if sr >= 1000: return "F"
    if sr >= 250:  return "C"
    if sr >= 80:   return "H"
    raise ValueError(f"unhandled sample_rate {sr}")

# standard ZNE orientation (azimuth, dip)
ORIENT = {"Z": (0.0, -90.0), "N": (0.0, 0.0), "E": (90.0, 0.0)}

def _load_yaml(path):
    with open(path) as fh:
        return yaml.safe_load(fh)

def _instruments():
    d = {}
    idir = os.path.join(REPO, "source", "instruments")
    for fn in os.listdir(idir):
        if fn.endswith(".yaml"):
            d[fn[:-5]] = _load_yaml(os.path.join(idir, fn))
    return d

INSTR = _instruments()
_proto_cache = {}

def _proto_channel(instr_name, rate):
    """The harvested response-channel for a given instrument + rate (cached)."""
    key = (instr_name, int(rate))
    if key not in _proto_cache:
        ref = INSTR[instr_name]["response_ref"].replace("{rate}", str(int(rate)))
        inv = obspy.read_inventory(os.path.join(REPO, "source", ref))
        _proto_cache[key] = inv[0][0][0]
    return _proto_cache[key]

def _utc(v):
    return None if v in (None, "null") else obspy.UTCDateTime(str(v))

def build_station(code, sdef):
    st = Station(code=code, latitude=sdef["latitude"], longitude=sdef["longitude"],
                 elevation=sdef["elevation"])
    starts, ends = [], []
    for ep in sdef["epochs"]:
        inst = INSTR[ep["instrument"]]
        rate = float(ep["sample_rate"])
        band = band_letter(rate)
        proto = _proto_channel(ep["instrument"], rate)
        start, end = _utc(ep["start"]), _utc(ep["end"])
        starts.append(start); ends.append(end)
        for comp in inst["components"]:
            az, dip = ORIENT[comp]
            ch = copy.deepcopy(proto)
            ch.code = band + inst["instrument_code"] + comp
            ch.location_code = str(inst.get("location", "00"))
            ch.latitude = sdef["latitude"]; ch.longitude = sdef["longitude"]
            ch.elevation = sdef["elevation"]; ch.depth = float(sdef.get("depth", 0.0))
            ch.azimuth, ch.dip = az, dip
            ch.sample_rate = rate
            ch.start_date, ch.end_date = start, end
            st.channels.append(ch)
    st.start_date = min(starts)
    st.end_date = None if any(e is None for e in ends) else max(ends)
    return st

def build_network(net_code):
    sdefs = _load_yaml(os.path.join(REPO, "source", "stations", f"{net_code}.yaml"))
    net = Network(code=net_code.upper())
    for code, sdef in sdefs.items():
        net.stations.append(build_station(code, sdef))
    return Inventory(networks=[net], source="uom_seismic_metadata/tools/generate.py")

if __name__ == "__main__":
    net = sys.argv[1] if len(sys.argv) > 1 else "vw"
    out = sys.argv[2] if len(sys.argv) > 2 else f"/tmp/gen_{net}.xml"
    inv = build_network(net)
    inv.write(out, format="STATIONXML")
    n = sum(len(s) for nw in inv for s in nw)
    print(f"generated {net}: {len(inv[0])} stations, {n} channels -> {out}")
