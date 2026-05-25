#!/usr/bin/env python3
"""Convert FDSN StationXML -> SeisComP XML (SCML) via SeisComP `fdsnxml2inv`.

ObsPy can't *write* SCML, so we shell out to a host that has SeisComP installed — by
default the dev server. The FDSN file is streamed to the host, converted in a temp dir,
and the SCML streamed back. Nothing is committed or changed on the host: it is used purely
as a conversion engine (distinct from the live `import_inv`, which is seiscomp_server_uom's
job). This is what lets generator/FDSN output also become the SCML the repo commits and the
user manually uploads to Gempa SMP.

Config (env-overridable, so a Mac SeisComP install or a host list can slot in later):
  SCML_HOST  (default seismology-dev1.its.unimelb.edu.au)
  SCML_USER  (default seiscomp)
  SCML_TOOL  (default "/opt/seiscomp/bin/seiscomp exec fdsnxml2inv")
Requires the `its` VPN + key-based SSH (older host needs +ssh-rsa).

Usage:
  python tools/to_scml.py fdsnxml/vw.xml                 # -> /tmp/vw.xml (safe default)
  python tools/to_scml.py external/du/all.xml -o scml/du.xml   # explicit output file (DU SCML for SMP)
SAFETY: default output is /tmp so a run can never silently overwrite the committed,
SMP-derived scml/ files. Writing into scml/ requires an explicit --outdir scml.
"""
import os, sys, argparse, subprocess

HOST = os.environ.get("SCML_HOST", "seismology-dev1.its.unimelb.edu.au")
USER = os.environ.get("SCML_USER", "seiscomp")
TOOL = os.environ.get("SCML_TOOL", "/opt/seiscomp/bin/seiscomp exec fdsnxml2inv")
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=20",
       "-o", "HostKeyAlgorithms=+ssh-rsa", "-o", "PubkeyAcceptedAlgorithms=+ssh-rsa",
       f"{USER}@{HOST}"]

REMOTE = ('t=$(mktemp); o=$(mktemp); cat > "$t"; '
          f'{TOOL} "$t" "$o" >/dev/null; rc=$?; '
          '[ "$rc" -eq 0 ] && cat "$o"; rm -f "$t" "$o"; exit "$rc"')

def convert(fdsn_path, scml_path):
    with open(fdsn_path, "rb") as fh:
        fdsn = fh.read()
    p = subprocess.run(SSH + [REMOTE], input=fdsn, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode(errors="replace"))
        raise SystemExit(f"fdsnxml2inv failed on {HOST} for {fdsn_path} (rc={p.returncode})")
    with open(scml_path, "wb") as fh:
        fh.write(p.stdout)
    return len(p.stdout)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("inputs", nargs="+")
    ap.add_argument("--outdir", default="/tmp",
                    help="output dir (default /tmp — pass --outdir scml to write into the repo)")
    ap.add_argument("-o", "--out", help="explicit output FILE (single input only); overrides --outdir")
    a = ap.parse_args()
    if a.out:
        if len(a.inputs) != 1:
            ap.error("--out takes exactly one input")
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        n = convert(a.inputs[0], a.out)
        print(f"{a.inputs[0]} -> {a.out}  ({n} bytes)")
        return
    os.makedirs(a.outdir, exist_ok=True)
    for fdsn in a.inputs:
        out = os.path.join(a.outdir, os.path.basename(fdsn))
        n = convert(fdsn, out)
        print(f"{fdsn} -> {out}  ({n} bytes)")

if __name__ == "__main__":
    main()
