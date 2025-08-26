# WiGLE Unified GUI

A Tk/Ttk desktop app for searching WiGLE’s Wi-Fi, Bluetooth, and Cellular datasets, with an optional map/bounding-box helper, “Detailed Query” drill-downs, MCC/MNC lookup, and one-click CSV/KML/JSON exports.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Install](#install)
- [Run](#run)
- [Credentials](#credentials)
- [Using the Tabs](#using-the-tabs)
  - [Basic Tabs](#basic-tabs-wi-fi--bluetooth--cell)
  - [Detail Tabs](#detail-tabs)
  - [MCC-MNC Lookup](#mcc-mnc-lookup)
- [Map & Location](#map--location)
- [Exports](#exports)
- [Troubleshooting](#troubleshooting)
- [License](#license)

## Features
- Tabs for **BT Basic**, **Wi-Fi Basic**, **Cell Basic**, **BT Detail**, **WiFi/Cell Detail**, and **MCC-MNC Lookup**.
- Right-click context menu on Basic results:
  - Copy MAC/ID, Copy Name, Copy Lat/Lon
  - **Detailed Query** → jumps to the appropriate detail tab and pre-fills fields
- Optional map with BBox drawing, “Use View as BBox”, and geocode **Go to location**.
- Exports:
  - **Full CSV** and **KML** generated from **raw JSON** (not just the visible table)
  - Optional **JSON** (merged); if JSON export is **off**, temporary page JSONs are auto-cleaned
- `searchAfter` pagination support and **Submitted** URL logging in the Status pane.
- MCC/MNC lookup with CSV export.

## Requirements
- **Python 3.8+**
- A working Tk runtime (Linux: `sudo apt install python3-tk`)
- Third-party packages listed in `requirements.txt`

## Install
```bash
# (Recommended) virtual environment
python3 -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
