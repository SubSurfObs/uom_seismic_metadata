# uom_seismic_metadata

Purpose of This Repository

This GitHub repository is not the authoritative source for seismic metadata.
Instead, it functions as a public mirror of metadata that is curated, validated, and maintained elsewhere.

The definitive metadata for the University of Melbourne Seismic Network is managed through Gempa SMP:

🔗 https://smp.gempa.de
🔗 https://smp.gempa.de/dansand/uom_seismic_metadata

Gempa SMP provides the workflow for editing, validating, and exporting metadata, but the platform only supports downloading in SeisComP Markup Language (SCML) format. Because operational use often requires additional file formats—such as FDSN StationXML, deployment-organised inventories, and other derived representations—the GitHub repository serves the following purposes:

What this repository is for
	•	A unified location to store exported SCML and FDSN StationXML files
	•	A place to host metadata in multiple derived configurations, such as deployment-based or network-specific bundles
	•	A convenient location for downstream workflows, scripts, CI processes, or automated metadata consumers
	•	A public mirror, not an editable upstream source

What this repository is not for
	•	It is not where authoritative metadata is modified
	•	It is not a replacement for the Gempa SMP curation workflow
	•	Any edits made here would be overwritten by future exports and should therefore not be treated as canonical

# UOM Network(s) Overview

## VW Network

- **Type:** Primary, permanent long-term network  
- **Description:** University of Melbourne seismic network deployed primarily across Victoria for regional monitoring.  
- **Operated By:** University of Melbourne, Australia  
- **FDSN Network Registry:** https://www.fdsn.org/networks/detail/VW/  

---

## VX Network

- **Type:** Temporary network (aftershock arrays and short-duration deployments)  
- **Description:** University of Melbourne temporary deployments, including aftershock arrays and short-term monitoring experiments.  
- **Operated By:** University of Melbourne, Australia  
- **FDSN Network Registry:** https://www.fdsn.org/networks/detail/VX/  

---



---

## Z1 Network

- **Type:** Temporary borehole monitoring network  
- **Description:** Otway CO₂ Borehole Monitoring Network — borehole geophones, borehole tiltmeters, and additional surface nodal seismometers installed to assist in monitoring the Otway Stage 4 field program.  
- **Operated By:** University of Melbourne, Australia  
- **FDSN Network Registry:** https://www.fdsn.org/networks/detail/Z1/  

---

# Affiliated Network(s) Overview


## DU Network

- **Type:** Regional permanent network  
- **Description:** Stations operated by Seismological Association of Australia (SAA), archived on UoM FDSNWS 
- **Operated By:** Seismological Association of Australia (SAA)  
- **FDSN Network Registry:** https://www.fdsn.org/networks/detail/DU/  



## AU Network (selected stations)

- **Type:** National permanent network (selected collaborative stations)  
- **Description:** Metadata for a small number of Australian National Seismograph Network (ANSN) stations used in collaborative deployments (e.g. following the 2021 Woods Point Earthquake).  
- **Operated By:** Geoscience Australia  
- **FDSN Network Registry:** https://www.fdsn.org/networks/detail/AU/  

## OZ Network

- **Type:** Permanent network (selected collaborative stations)  
- **Operated By:** Seismology Research Centre
---
