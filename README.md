# WiGLE Unified GUI — Complete Documentation

A Tk/Ttk desktop app for searching **WiGLE**’s Wi-Fi, Bluetooth, and Cellular datasets — with an optional map + bounding-box helper, “Detailed Query” drill-downs, MCC/MNC lookup, and one-click CSV/KML/JSON exports.

> **Why this tool?**
> Quickly pivot from broad, map-bounded searches to per-device detail, then export clean CSV/KML generated from the **raw JSON** responses (not just what’s on screen). Designed for repeatable workflows and batch runs.

---

## Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
  - [requirements.txt](#requirementstxt)
- [Install](#install)
- [Run](#run)
- [Credentials](#credentials)
- [How to Use](#how-to-use)
  - [Wi-Fi Basic](#wi-fi-basic)
  - [Bluetooth Basic](#bluetooth-basic)
  - [Cellular Basic](#cellular-basic)
  - [WiFi/Cell Detail](#wificell-detail)
  - [Bluetooth Detail](#bluetooth-detail)
  - [MCC–MNC Lookup](#mccmnclookup)
- [Map & Bounding Box](#map--bounding-box)
- [Exporting Data](#exporting-data)
- [Status & Logging](#status--logging)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [Security & Privacy](#security--privacy)
- [License](#license)
- [Changelog](#changelog)
- [Credits](#credits)
- [Appendix: GitHub Wiki Pages (Ready-to-Copy)](#appendix-github-wiki-pages-ready-to-copy)

---

## Features

- **Tabbed UI** for:
  - **Wi-Fi Basic**, **Bluetooth Basic**, **Cellular Basic**
  - **WiFi/Cell Detail** and **Bluetooth Detail** (single or **Batch** from a text file)
  - **MCC–MNC Lookup**
- **Context menu** on Basic search results:
  - Copy MAC/ID, Copy Name, Copy Lat/Lon
  - **Detailed Query** → jumps to the right *Detail* tab and pre-fills fields
- **Optional Map**:
  - Draw **BBox** (fills `latrange1/2`, `longrange1/2`)
  - **Use View as BBox**, **Clear BBox**
  - **Go to Location** via `lat,lon` or a place search (OSM/Nominatim)
  - OSM / Satellite tiles
- **Smart Exports** (per tab):
  - **Full CSV** and **KML** created from the **raw JSON** pages
  - Optional **JSON** (merged where applicable)
  - If JSON export is **off**, temporary page JSONs are cleaned after export
- **Pagination**:
  - Automatic `searchAfter` until all pages are fetched
- **Transparent logging**:
  - Status pane shows **Submitted** URL, per-page saves, **Total in DB**, and **Search complete**

---

## Screenshots

> _Add your own screenshots here (optional)._
> Suggested images:
>
> - `docs/img/main.png` — Main window (tabs visible)
> - `docs/img/map_bbox.png` — Map with bounding box + “Use View as BBox”
> - `docs/img/detail.png` — Detail tab after right-click → Detailed Query
> - `docs/img/exports.png` — Export toggles and resulting files

---

## Requirements

- **Python 3.8+**
- A working **Tk** runtime (Linux: `sudo apt install python3-tk`)
- Third-party packages listed in **`requirements.txt`**

### requirements.txt

```txt
# Core
requests>=2.31.0,<3

# Optional map widget (safe to remove if you don’t want map features)
tkintermapview==1.29
pillow>=10.0.0

# Pin to avoid occasional build/metadata hiccups pulled via tkintermapview -> geocoder
geocoder==1.38.1
pyperclip==1.8.2
```

> **Disable the map**: If you prefer not to install GUI map deps, remove/comment the last four lines above and reinstall.

---

## Install

```bash
# 1) Create & activate a virtual environment
python3 -m venv .venv
# Windows:
# .venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# 2) Install dependencies
pip install -r requirements.txt
```

> **Linux note**: If you see Tk errors, install Tk: `sudo apt install python3-tk`.

---

## Run

```bash
python wigleGUI.py
```

- The application opens on **BT Basic**.
- If credentials aren’t set yet, you’ll be prompted to add them (see next section).

---

## Credentials

The app uses WiGLE’s API:

1. Open **`Settings → WiGLE Credentials…`**
2. Enter:
   - **WiGLE Username / API Name**
   - **WiGLE API Token** (password)
3. Credentials are stored locally at:
   - **`~/.wigle_gui/credentials.json`**

> You can update these at any time via the same menu.

---

## How to Use

Below is a high-level user guide. For a step-by-step guide per tab (with more screenshots), see the project Wiki or the wiki pages included in this zip.

### Wi-Fi Basic

- **Endpoint**: `network/search`
- **Typical fields**:
  Ownership (`onlymine`, `notmine`), time windows (`firsttime`, `lasttime`, `lastupdt`), network filters (`netid`/BSSID, `ssid`, `ssidlike`), encryption flags, location (`latrange1/2`, `longrange1/2`, or `closestLat/closestLong`), address components, pagination (`resultsPerPage`, `searchAfter`), etc.
- **Country** combobox starts **blank**. Use **Clear Params/All** to reset.
- **Results columns**: **BSSID**, **SSID**, **Last Updated**, **Lat**, **Lon**
- **Right-click** any row → Copy actions or **Detailed Query** (opens WiFi/Cell Detail with fields pre-filled).

### Bluetooth Basic

- **Endpoint**: `bluetooth/search`
- **Fields**: Similar to Wi-Fi (location + time windows + pagination) plus BT-specific (`netid`, `name`, `namelike`).
- **Results columns**: **BTID**, **Name**, **Last Updated**, **Lat**, **Lon**
- Right-click → **Detailed Query** (opens **Bluetooth Detail**).

### Cellular Basic

- **Endpoint**: `cell/search`
- **Fields**: `cell_op` (operator), `cell_net`, `cell_id`, and generation flags (`showGsm`, `showCdma`, `showLte`, `showWcdma`, `showNr`), plus generic location/time/pagination fields.
- **Results columns**: **ID** (`OP_LAC_CID`), **Name**, **GenType**, **Lat**, **Lon**
- Right-click → **Detailed Query** (opens **WiFi/Cell Detail** and auto-fills `operator`, `lac`, `cid`).

### WiFi/Cell Detail

- **Wi-Fi** detail by **`netid`** (BSSID).
- **Cell** detail by **`operator` / `lac` / `cid`** (also supports `system`, `network`, `basestation`).
- **Batch mode**: Provide a text file (one ID per line). Each runs as its own detail request.
- **Exports**: CSV/KML from merged/raw JSON; optional JSON kept if you enable **Export JSON**.

### Bluetooth Detail

- Provide a **BT `netid`** (or right-click → **Detailed Query** from Bluetooth Basic).
- **Batch mode** supported (text file, one `netid` per line).
- **Exports** behave like WiFi/Cell Detail.

### MCC–MNC Lookup

- **Endpoint**: `cell/mccMnc`
- Enter **MCC** and/or **MNC**; see **Country**, **Brand**, **Operator**, **Bands**, **Notes**.
- Click **Export Results CSV** to save the table.

---

## Map & Bounding Box

> The map is optional — the rest of the app works without it.

- **BBox**:
  - Click **BBox**, then click two corners on the map; the app fills `latrange1/2` and `longrange1/2`.
  - **Use View as BBox** converts the current viewport into the four range fields.
  - **Clear BBox** resets range fields and removes the shape.
- **Go to Location**:
  - Enter `lat,lon` (e.g., `37.7749,-122.4194`) **or** a place name/address (geocoded via OSM Nominatim).
  - The map pans/zooms to the result.
- **Tiles**: OSM and Satellite views available.

---

## Exporting Data

Exports are **per tab** and controlled via toggle buttons:

- **Full CSV** and **KML** are generated from the **raw JSON** pages (not just the visible table).
- **Export JSON**:
  - **ON** → keeps (or merges) the JSON pages.
  - **OFF** → the app **cleans** temporary page JSONs after CSV/KML are created.

### Detail Exports (flattened)

- **CSV** flattens each entry’s `locationData/locations`, adding lat/lon/time.
- **KML** writes a Placemark per location point.

### Filenames (convention)

- **Basic**: `wifi-basic-<runTag>.csv/.kml` (similar for BT/Cell)
- **Detail**: `<basename>.csv/.kml` + optional `<basename>.json`

---

## Status & Logging

The **Status** pane records:

- **Submitted:** full request URL (useful for auditing/replays)
- Per-page saves: `Page N: X results saved: …/page_N.json`
- **Total in DB** (when present in API response)
- **Search complete** (with counts)
- **Temporary JSON pages removed:** count & path when cleanup occurs

> Use this area to confirm parameters, pagination progress, and where files were written.

---

## Troubleshooting

- **Map not visible**
  Install the map deps: `pip install tkintermapview pillow geocoder pyperclip`
  (Linux may also need Tk: `sudo apt install python3-tk`.)
- **401 / auth errors**
  Re-enter credentials at **Settings → WiGLE Credentials…** (username/API name + API token).
- **Empty CSV/KML**
  Ensure your results actually contain coordinates; recheck BBox/country/time filters.
- **“Where did the JSON files go?”**
  If **Export JSON** is **off**, temporary page JSONs are **deleted** after CSV/KML are written.
- **No results but you expect some**
  Verify **country** (starts blank), date windows, BBox, and pagination (`resultsPerPage`/`searchAfter`).

---

## FAQ

**Q: Do I need the map?**
A: No. The app runs fine without it. You can still type lat/long ranges directly.

**Q: Are exports only what I see on screen?**
A: No. CSV/KML are generated from the **raw JSON** results collected during the run.

**Q: Can I run multiple IDs at once for Detail queries?**
A: Yes. Use **Batch** with a text file (one ID per line).

**Q: Where are credentials stored?**
A: `~/.wigle_gui/credentials.json` on your machine.

---

## Roadmap

- CLI wrapper for headless batch runs
- Saved search presets per tab
- Export profiles (choose columns / KML styles)
- Map marker clustering and per-result tooltips

> File an issue with your priorities; PRs welcome!

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feat/your-idea`
3. Commit: `git commit -m "Add awesome thing"`
4. Push: `git push origin feat/your-idea`
5. Open a Pull Request

Please keep UI strings and filenames consistent with existing conventions.

---

## Security & Privacy

- Your WiGLE credentials are stored locally in `~/.wigle_gui/credentials.json`.
  Treat this file like a password; do not commit it to version control.
- Respect WiGLE’s Terms of Service and rate limits.
- If sharing exports, review them for sensitive location data.

---

## License

**MIT** — see `LICENSE` (or replace with your preferred license).

---

## Changelog

- **v0.1.0** – Initial public release

---

## Credits

- Built with Python, Tk/Ttk, and optionally `tkintermapview` for mapping.
- Thanks to the WiGLE community for their datasets and API.
