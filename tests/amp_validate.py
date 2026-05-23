#!/usr/bin/env python3
"""Amplitude validation of a harvested instrument template.

Corrects the BEST test waveforms to ground velocity using:
  - generated StationXML  (our gecko_g1_cmg6t template, via tools/generate.py)
  - the bundled BEST.xml   (sparse 3-stage reference)
  - the Seismosphere SUD   (independent system, via sudspy) -- if available
and compares peak ground velocity. If the template is physically right, the
generated-template result should match the independent SUD reference and the
local BEST.xml within a few percent (in the flat 1-20 Hz band of the CMG-6T).

Uses output='VEL' with water_level=60 to avoid the DISP/water_level pitfall the
notebook documents.
"""
import os, sys, warnings
import numpy as np
import obspy
from obspy import read, read_inventory

warnings.filterwarnings("ignore")
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEST = os.path.join(REPO, "tests", "test_amplitude_src")
MSEED = os.path.join(TEST, "2026-05-09 0800_BEST.ms", "mszip.16222778378020441172.ms")
LOCAL = os.path.join(TEST, "2026-05-09 0800_BEST.ms", "BEST.xml")
SUD = os.path.join(TEST, "20260509_0812.all.seismosphere.v.sud")
GEN = os.environ.get("GEN_XML", "/tmp/gen_vw.xml")

PRE_FILT = (0.05, 0.1, 80.0, 100.0)
WL = 60
NET, STA = "VW", "BEST"

def ztrace(st):
    z = st.select(component="Z") or st.select(component="V")
    return z.merge(method=1, fill_value=0)[0]

def isens(inv, cha):
    for n in inv:
        for s in n:
            for c in s:
                if n.code == NET and s.code == STA and c.code == cha and c.response \
                        and c.response.instrument_sensitivity:
                    sv = c.response.instrument_sensitivity
                    return sv.value, sv.frequency, len(c.response.response_stages)
    return None

def vel_peak(tr, inv):
    t = tr.copy()
    t.remove_response(inventory=inv, output="VEL", water_level=WL,
                      pre_filt=PRE_FILT, zero_mean=True, taper=True)
    return float(np.abs(t.data).max())

def vel_peak_band(tr, inv, fmin=1.0, fmax=20.0):
    t = tr.copy()
    t.detrend("linear")
    t.taper(max_percentage=0.05, type="cosine")
    t.filter("bandpass", freqmin=fmin, freqmax=fmax, corners=4, zerophase=True)
    t.remove_response(inventory=inv, output="VEL", water_level=WL)
    return float(np.abs(t.data).max())

def Habs(inv, cha, freqs):
    for n in inv:
        for s in n:
            for c in s:
                if n.code == NET and s.code == STA and c.code == cha:   # BEST only
                    return np.abs(c.response.get_evalresp_response_for_frequencies(freqs, output="VEL"))
    return None

tr_ms = ztrace(read(MSEED))
inv_gen = read_inventory(GEN)
inv_local = read_inventory(LOCAL)

print(f"mseed Z: {tr_ms.id}  {tr_ms.stats.npts} pts @ {tr_ms.stats.sampling_rate} Hz")
print("\nOverall sensitivity  VW.BEST.CHZ  (value @ freq, n_stages):")
print(f"  generated(template): {isens(inv_gen,   'CHZ')}")
print(f"  local BEST.xml     : {isens(inv_local, 'CHZ')}")

print("\nPeak ground velocity (m/s), BROADBAND (pre_filt 0.05-0.1-80-100):")
v_gen = vel_peak(tr_ms, inv_gen)
v_loc = vel_peak(tr_ms, inv_local)
print(f"  generated(template): {v_gen:.6e}")
print(f"  local BEST.xml     : {v_loc:.6e}")
print(f"  ratio gen/local    : {v_gen / v_loc:.4f}")

print("\nPeak ground velocity (m/s), 1-20 Hz magnitude band:")
b_gen = vel_peak_band(tr_ms, inv_gen)
b_loc = vel_peak_band(tr_ms, inv_local)
print(f"  generated(template): {b_gen:.6e}")
print(f"  local BEST.xml     : {b_loc:.6e}")
print(f"  ratio gen/local    : {b_gen / b_loc:.4f}")

freqs = np.logspace(-1, 2, 400)
Hg, Hl = Habs(inv_gen, "CHZ", freqs), Habs(inv_local, "CHZ", freqs)
band = (freqs >= 1) & (freqs <= 20)
r = Hg[band] / Hl[band]
print(f"\n|H(f)| gen/local in 1-20 Hz: mean={r.mean():.4f} min={r.min():.4f} max={r.max():.4f}")

# Independent SUD reference (Seismosphere) via sudspy, if importable
try:
    sys.path.insert(0, "/Users/DSAND/projects/SubSurfObs/sudspy")
    import sudspy
    tr_sud = ztrace(sudspy.read_suds_stream(SUD, default_location="00"))
    inv_sud = sudspy.read_suds_inv(SUD, default_location="00")
    print(f"\nSUD ref Z: {tr_sud.id}  {tr_sud.stats.npts} pts @ {tr_sud.stats.sampling_rate} Hz")
    print(f"  SUD sensitivity: {isens(inv_sud, tr_sud.stats.channel)}")
    print(f"  raw peak counts  mseed={np.abs(tr_ms.data).max():.6g}  sud={np.abs(tr_sud.data).max():.6g}")
    v_sud = vel_peak(tr_sud, inv_sud)
    print(f"  SUD peak ground vel (sud inv): {v_sud:.6e}")
    print(f"  ratio gen(mseed)/sud(sud)    : {v_gen / v_sud:.4f}")
except Exception as e:
    print(f"\nSUD reference unavailable ({e!r}); skipped independent cross-check.")
