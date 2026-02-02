# University of Melbourne Seismic Data

Purpose of This Repository

This GitHub repository is not the authoritative source for seismic metadata.
Instead, it functions as a public mirror of metadata that is curated, validated, and maintained elsewhere.

The definitive metadata for the University of Melbourne Seismic Network is managed through Gempa SMP:

🔗 https://smp.gempa.de
🔗 https://smp.gempa.de/dansand/uom_seismic_metadata

Gempa SMP provides the workflow for editing, validating, and exporting metadata, but the platform only supports downloading in SeisComP Markup Language (SCML) format. Because operational use often requires additional file formats—such as FDSN StationXML, deployment-organised inventories, and other derived representations—the GitHub repository serves the following purposes:

What this repository is for

* A unified location to store exported SCML and FDSN StationXML files
* A place to host metadata in multiple derived configurations, such as deployment-based or network-specific bundles
* A convenient location for downstream workflows, scripts, CI processes, or automated metadata consumers
* A public mirror, not an editable upstream source

What this repository is not for
* It is not where authoritative metadata is modified
* It is not a replacement for the Gempa SMP curation workflow
* Any edits made here would be overwritten by future exports and should therefore not be treated as canonical

## Links UOM Network(s)

- https://www.fdsn.org/networks/detail/VW/
- https://www.fdsn.org/networks/detail/VX/
- https://www.fdsn.org/networks/detail/Z1/

## Affiliated Network(s) 

### DU Network

- https://www.fdsn.org/networks/detail/DU/
- https://www.fdsn.org/networks/detail/AU/
- https://www.fdsn.org/networks/detail/OZ/     

## SmartSolo nodes

# SmartSolo / SoloLite metadata notes (working draft)

We are still in the process of finalising metadata practices for SmartSolo nodes.

The **SoloLite software** is capable of exporting **FDSN StationXML** directly. The azimuths in the exported XML are **reversed relative to the conventional E/N/Z station configuration**, but conistent with teh Sensor Polarity. This behaviour is documented in the AusPASS wiki and reflects the internal orientation conventions used by SmartSolo hardware/software.

Separately, we have experimented with generating SmartSolo metadata via **GEMPA SMP**, using **NRL-derived response information** for SmartSolo nodes. At the time of writing, the metadata produced via this route is **not fully consistent** with the StationXML exported directly by SoloLite.

However, importing SoloLite-generated StationXML into **GEMPA SMP** introduces further complications. Although the XML is formally valid and can be converted into SeisComP inventory, the SMP web interface often reports that **no sensor is available**, which prevents straightforward editing or updating of channel information. 

In summary:
- SoloLite StationXML is internally consistent and vendor-supported, but uses non-standard orientation conventions.
- NRL/SMP-based SmartSolo metadata is currently inconsistent with SoloLite output.
- SMP is not well suited to editing externally generated SmartSolo StationXML without recreating sensor/datalogger objects inside SMP.
- A workflow based on **SoloLite XML → scripted normalisation → direct import into SeisComP** is likely the most reliable short-term solution.

These issues require further exploration, particularly if long-term SMP-based editing or strict NRL alignment is desired.

