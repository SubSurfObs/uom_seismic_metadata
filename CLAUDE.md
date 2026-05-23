# UoM seismic metadata — Claude Code working file

Purpose: this repo is the GitHub **mirror** of the Gempa-SMP-curated station
inventory for the University of Melbourne seismic network. The metadata stored
here is pulled onto the SeisComP servers and imported, so this file gives the
metadata agent the context it needs about those servers and how metadata flows
onto them. The **twin repo `seiscomp_server_uom`** owns server operations and
config (bindings, archiving, fdsnws, monitoring, dev/prod sync); this repo owns
the metadata itself.

## What this repo is

- A **public mirror**, not the authoritative source. Authoritative metadata is
  curated in **Gempa SMP** (`https://smp.gempa.de/dansand/uom_seismic_metadata`).
  Edits made directly in this repo get overwritten by the next SMP export — do
  not treat them as canonical.
- SMP only exports **SCML**; this repo additionally stores FDSN StationXML and
  derived/deployment bundles for downstream use.
- GitHub: `https://github.com/SubSurfObs/uom_seismic_metadata`.

### Layout
- `scml/<net>.xml` — SCML exports from SMP (au, du, oz, s1, vw, vx, z1).
- `fdsnxml/<net>.xml` — FDSN StationXML (same networks).
- `deployment_based/` — deployment-organised bundles (e.g. apollo_bay, woods_point).
- `tests/` — validation work (amplitude-comparison notebook + sample miniSEED).
- `README.md`, `Gempa-smp.md` — purpose and SMP-workflow notes.

### Networks
VW, VX, Z1 (UoM); DU, AU, OZ (affiliated); S1. Currently **loaded on the
servers**: au, du, vw, vx, z1 (oz/s1 exist here but aren't imported yet).

### Metadata gotchas (correctness matters here)
- **SCML vs FDSN for archiving:** importing DU from the **fdsn** form produced
  working local archiving; the **scml** form did not. Prefer the **fdsnxml**
  form for stations that must archive until this is understood.
- **SmartSolo azimuths:** StationXML exported directly by SoloLite has azimuths
  **reversed** relative to conventional E/N/Z (consistent with the sensor
  polarity). SMP/NRL-derived SmartSolo metadata is **not yet fully consistent**
  with the SoloLite export. Unresolved — see `README.md`.

## The servers (where this metadata lands)

| Role | Hostname | SeisComP root |
|---|---|---|
| Dev | seismology-dev1.its.unimelb.edu.au | /opt/seiscomp |
| Prod | seismology-prod1.its.unimelb.edu.au | /opt/seiscomp |

- VPN (domain `its`) required; SSH as user `seiscomp`; both are older boxes that
  need `HostKeyAlgorithms +ssh-rsa` / `PubkeyAcceptedAlgorithms +ssh-rsa`.
- **Dev = testing, prod = production** (prod's archive is the canonical record).
  Always apply on dev first, verify, then prod. **Do not open a live shell on
  prod without explicit authorization.**

## Where SeisComP and its components are installed

- `SEISCOMP_ROOT=/opt/seiscomp` on both servers. (Note: the env is **not**
  loaded in a non-interactive SSH shell — use full paths like
  `/opt/seiscomp/bin/seiscomp`, or `bash -l`.)
- **Binaries:** `/opt/seiscomp/bin/` — `seiscomp`, `import_inv`, `scinv`,
  `slinktool`, `scart`, `scardac`, etc.
- **Config:** `/opt/seiscomp/etc/` — `global.cfg` + `scmaster.cfg` (MariaDB
  connection), module configs (`seedlink.cfg`, `slarchive.cfg`, `fdsnws.cfg`),
  `key/` (per-station bindings — owned by the server repo), and
  **`inventory/`** (the loaded per-network XMLs this repo feeds).
- **Runtime/generated:** `/opt/seiscomp/var/lib/` (e.g. seedlink `chain0.xml`);
  logs in `/opt/seiscomp/var/log/`.
- **Database:** MariaDB (Ubuntu's MySQL). After `import_inv` + `update-config`,
  inventory objects live in the DB; `fdsnws` and `scardac` read from there.
- **Modules:** scmaster, seedlink, slarchive, fdsnws.
- **Archive:** `/opt/seiscomp_archive_local` (live SDS; on prod rsynced daily to
  long-term), `/mnt/seiscomp_archive` (long-term CIFS, canonical — prod only).
- Python is system-wide (PEP 668): install deps via apt, not pip.

## How metadata flows from here onto a server

1. Edit in **Gempa SMP** (authoritative) → export SCML.
2. Commit/push to this repo (add the fdsnxml / derived forms too).
3. On the server the repo is a **git clone at `/home/seiscomp/uom_seismic_metadata`**
   — `git pull` to fetch the new commit.
4. Import + apply (prefer the fdsnxml form):
   ```bash
   cd /home/seiscomp/uom_seismic_metadata
   seiscomp exec import_inv fdsnxml fdsnxml/<net>.xml
   seiscomp exec scinv ls
   seiscomp update-config
   ```
   To swap a source cleanly, move the old file aside in
   `/opt/seiscomp/etc/inventory/` and re-run `update-config` (otherwise
   `scinv ls` keeps listing the stale file).
5. The loaded inventory lands in **`/opt/seiscomp/etc/inventory/<net>.xml`**.
   fdsnws then serves those channels — but **archiving also needs a populated
   key file** under `/opt/seiscomp/etc/key/`, which is the **server repo's**
   responsibility, not this one.

## Where this is heading (sync automation — future)

Target: change in Gempa SMP → commit here → **auto-pull onto dev** → import +
verify (scinv parses cleanly, the station actually archives) → on success,
**propagate to prod** (pull + import, or a one-shot dev→prod inventory sync).
The server-side mechanics (pull / import / verify / propagate command) will live
in **`seiscomp_server_uom`**; this repo's job is to keep the exported metadata
correct and committed. Coordinate across the two repos at the import step.

## How to work with the user

- Prefers concrete, paste-ready shell commands over abstract description.
- Ground recommendations in observed system state, not priors — the user has
  years on this stack and will catch generic SeisComP advice. On pushback,
  update reasoning rather than doubling down.
- One step at a time; a single clear next step beats a five-step block.
- Dev first, verify, then prod; prod live-shell only with explicit OK.
