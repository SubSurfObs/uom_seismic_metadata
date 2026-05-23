#!/usr/bin/env python3
"""A4 reverse-map: reconstruct source/ from a (Gempa-pulled) SCML and diff it against
the current source/stations/<net>.yaml, so a Gempa-originated change can be folded back
into the single source of truth.

Instrument recognition is derived from the instrument templates themselves
(recorder.model + preamp_gain + sensor.model), so there is no separate lookup table:
add a template and ingest recognises that combo automatically.

DRY-RUN by design: prints a change report and writes the reconstructed YAML to
/tmp/<net>.from_scml.yaml for review. It does NOT modify source/.

Usage:  python tools/ingest_scml.py <scml_file> <net>
"""
import sys, os, re, warnings
import yaml
import obspy

warnings.filterwarnings("ignore")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_instruments():
    d = {}
    idir = os.path.join(REPO, "source", "instruments")
    for fn in os.listdir(idir):
        if fn.endswith(".yaml"):
            with open(os.path.join(idir, fn)) as fh:
                d[fn[:-5]] = yaml.safe_load(fh)
    return d

def ikey(recorder_model, gain, sensor_model):
    return (str(recorder_model).lower(), str(gain), str(sensor_model).lower())

def build_recognition(instruments):
    rec = {}
    for name, inst in instruments.items():
        r, s = inst["recorder"], inst["sensor"]
        rec[ikey(r.get("model"), r.get("preamp_gain", "-"), s.get("model"))] = name
    return rec

def parse_desc(desc):
    """'Guralp; CMG-6T; ...' -> {make, model, gain?}."""
    if not desc:
        return {}
    parts = [p.strip() for p in desc.split(";")]
    out = {"make": parts[0] if parts else None,
           "model": parts[1] if len(parts) > 1 else (parts[0] if parts else None)}
    m = re.search(r"Preamp_Gain\s+(\d+)", desc)
    if m:
        out["gain"] = int(m.group(1))
    return out

def chan_instrument(c, rec):
    s = parse_desc(getattr(c.sensor, "description", None))
    d = parse_desc(getattr(c.data_logger, "description", None))
    key = ikey(d.get("model"), d.get("gain", "-"), s.get("model"))
    return rec.get(key), key

def reconstruct(inv, net_code, rec):
    out, unknown = {}, {}
    for net in inv:
        if net.code != net_code.upper():
            continue
        for sta in net:
            eps = {}
            for c in sta:
                name, key = chan_instrument(c, rec)
                if name is None:
                    unknown[key] = unknown.get(key, 0) + 1
                rate = int(round(c.sample_rate)) if c.sample_rate else None
                start = str(c.start_date)[:10] if c.start_date else None
                end = str(c.end_date)[:10] if c.end_date else None
                eps[(name or "UNKNOWN", rate, start, end)] = True
            ep_list = [{"start": s, "end": e, "instrument": n, "sample_rate": r}
                       for (n, r, s, e) in sorted(eps, key=lambda x: (x[2] or "", x[1] or 0))]
            out[sta.code] = {"network": net.code,
                             "latitude": round(sta.latitude, 6),
                             "longitude": round(sta.longitude, 6),
                             "elevation": float(sta.elevation),
                             "epochs": ep_list}
    return out, unknown

def norm_epochs(eplist):
    return sorted((str(e.get("instrument")), e.get("sample_rate"),
                   (str(e.get("start"))[:10] if e.get("start") else None),
                   (str(e.get("end"))[:10] if e.get("end") else None)) for e in eplist)

def main(scml, net):
    inv = obspy.read_inventory(scml)
    rec = build_recognition(load_instruments())
    recon, unknown = reconstruct(inv, net, rec)

    src_path = os.path.join(REPO, "source", "stations", f"{net}.yaml")
    existing = {}
    if os.path.exists(src_path):
        with open(src_path) as fh:
            existing = yaml.safe_load(fh) or {}

    print(f"=== A4 reverse-map: {net.upper()} from {os.path.basename(scml)} ===")
    print(f"SCML stations: {len(recon)}   source stations: {len(existing)}\n")

    new, changed, match = [], [], []
    for code, r in recon.items():
        if code not in existing:
            new.append(code); continue
        e = existing[code]
        diffs = []
        for f in ("latitude", "longitude", "elevation"):
            if abs(float(e.get(f, 0)) - float(r[f])) > 1e-4:
                diffs.append(f"{f} {e.get(f)}!={r[f]}")
        if norm_epochs(e.get("epochs", [])) != norm_epochs(r["epochs"]):
            diffs.append(f"epochs {norm_epochs(e.get('epochs', []))} != {norm_epochs(r['epochs'])}")
        (changed if diffs else match).append((code, diffs))

    print(f"MATCH   ({len(match)}): {', '.join(c for c, _ in match) or '-'}")
    print(f"CHANGED ({len(changed)}):")
    for c, d in changed:
        print(f"   {c}: " + "; ".join(d))
    print(f"NEW in SCML, not in source ({len(new)}): {', '.join(sorted(new)) or '-'}")
    only = [c for c in existing if c not in recon]
    print(f"ONLY in source, not in SCML ({len(only)}): {', '.join(sorted(only)) or '-'}")
    if unknown:
        print("\nUNKNOWN instruments (need a template before ingest can map them):")
        for k, n in sorted(unknown.items()):
            print(f"   {k}  x{n} channels")

    outp = f"/tmp/{net}.from_scml.yaml"
    with open(outp, "w") as fh:
        yaml.safe_dump(recon, fh, sort_keys=True, default_flow_style=False)
    print(f"\nreconstructed source written to {outp} (review only; source/ NOT modified)")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
