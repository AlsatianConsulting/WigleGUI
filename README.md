# WiGLE GUI Tool

A cross‑platform **Tkinter** app for searching WiGLE (Wi‑Fi, Bluetooth, and Cellular), visualizing results on a map (with a draw‑your‑own bounding box), and exporting **JSON‑driven CSV/KML**. Includes right‑click context menus, “send to detail” shortcuts, batch detail runs from a text file, and an MCC/MNC lookup.

> **Why this matters:** All exports are generated from the **raw JSON** responses (not the UI table), so your CSV headers and KML attributes reflect the **full dataset** across paginated pages.

---

## Table of Contents

- [Features](#features)
- [Screens & Tabs](#screens--tabs)
  - [Wi‑Fi Basic](#wi-fi-basic)
  - [Bluetooth Basic](#bluetooth-basic)
  - [Cell Basic](#cell-basic)
  - [Wi‑Fi/Cell Detail](#wi-ficell-detail)
  - [Bluetooth Detail](#bluetooth-detail)
  - [MCC/MNC Lookup](#mccmnc-lookup)
  - [Settings](#settings)
- [Installation](#installation)
- [Getting WiGLE API Credentials](#getting-wigle-api-credentials)
- [Running the App](#running-the-app)
- [Using the Map & Bounding Boxes](#using-the-map--bounding-boxes)
- [Exports (JSON → CSV/KML)](#exports-json--csvkml)
  - [File/Folder Naming](#filefolder-naming)
- [Batch Detail Runs](#batch-detail-runs)
- [Tips, Limits, and Troubleshooting](#tips-limits-and-troubleshooting)
- [Screenshots](#screenshots)
- [FAQ](#faq)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **Wi‑Fi / Bluetooth / Cell** basic searches with form fields, country dropdowns, and **map bounding‑box** tools.
- **Right‑click context menu** on results: copy ID/Name/Lat/Lon, or “**Send to Detail**” (auto‑fills detail tab).
- **Detail tabs** for Wi‑Fi/Cell and Bluetooth with **batch file** processing (`Browse…` to load a text file).
- **Exports from raw JSON**:
  - Toggle **JSON / CSV / KML** independently.
  - CSV headers are the **union** of all keys across pages.
  - KML includes **ExtendedData** attributes for all keys.
- **Automatic pagination** using `searchAfter` (when supported by the WiGLE endpoint).
- **Per‑run output folders** with clean, consistent filenames.
- **MCC/MNC lookup** with normalization and CSV export.
- **Credential manager** (Settings → WiGLE Credentials) stores your API username/token in a local JSON file.
- **Dark‑mode friendly** layout and status pane.

---

## Screens & Tabs

### Wi‑Fi Basic
- Form inputs for SSID/BSSID filters, country, and optional bounding box (map).
- Results table with right‑click copy and “Send to Detail” to pre‑fill the **Wi‑Fi/Cell Detail** tab.
- Export toggles (JSON/CSV/KML) affect this tab’s searches.

### Bluetooth Basic
- Search for Bluetooth devices by name/MAC (and country if supported).
- Right‑click results to copy values or “Send to Detail” (Bluetooth Detail tab).

### Cell Basic
- Search cellular towers/operators with MCC/MNC filters and **country** limit.
- Supports `searchAfter` pagination when available.
- Right‑click → copy → send to detail.

### Wi‑Fi/Cell Detail
- Single or **batch** detail lookups.
- **Browse…** to import a text file of IDs (e.g., BSSIDs, network IDs) and run them sequentially.
- Per‑run folder creation; all exports pulled from **JSON**, not the UI table.

### Bluetooth Detail
- Single or **batch** Bluetooth detail lookups.
- Mirrors the behavior of the Wi‑Fi/Cell Detail tab for batch processing and exports.

### MCC/MNC Lookup
- Enter MCC or MCC/MNC (wildcards supported where relevant).
- Normalizes common formats (e.g., `mccmnc` vs `mcc-mnc`) and exports results to CSV.

### Settings
- **WiGLE Credentials**: store API username and token into `~/.wigle_gui/credentials.json`.
- **Export Options**: toggle JSON, CSV, KML behavior (e.g., keep JSON pages, remove after CSV/KML, etc.).
- **Paths**: choose default output directory.

---

## Installation

> Works on **Windows**, **macOS**, and **Linux** with Python **3.10+**.

1. **Clone** this repository:
   ```bash
   git clone https://github.com/<your-org>/<your-repo>.git
   cd <your-repo>
   ```

2. **Create & activate a virtualenv** (recommended):
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS/Linux
   source .venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **OS notes**:
   - **Windows:** no extra steps typically required.
   - **macOS:** if you see SSL/cert errors with Tkinter/requests, run the “Install Certificates.command” that ships with python.org builds, or `pip install certifi`.
   - **Linux (Debian/Ubuntu):** ensure Tk is available:
     ```bash
     sudo apt-get update
     sudo apt-get install -y python3-tk
     ```

---

## Getting WiGLE API Credentials

1. Log into your WiGLE account and generate an API token.
2. In the app, open **Settings → WiGLE Credentials**.
3. Enter your **username** and **API token**; they’re stored locally at:
   ```
   ~/.wigle_gui/credentials.json
   ```
   > You can edit or delete this file anytime.

---

## Running the App

```bash
python wigleGUI.py
```

- The main window opens in **dark‑mode friendly** colors.
- Pick a tab, set filters, draw a **bounding box** if needed, and click **Search**.
- Watch the **Status** pane for progress, page counts, and export info.

---

## Using the Map & Bounding Boxes

- **Pan/Zoom** the map to your area of interest.
- Use the **draw rectangle** tool to set the bounding box.
- The app will apply the rectangle’s **min/max lat/lon** to supported searches.
- Clear or redraw the box to adjust your search area.

---

## Exports (JSON → CSV/KML)

- Enable **JSON**, **CSV**, and/or **KML** via the export toggles (top/right or Settings).
- The app always works from the **raw JSON pages**:
  - **CSV**: builds a **union** of keys across all pages so no fields are lost.
  - **KML**: puts all key/value pairs into **ExtendedData** (click a placemark to view attributes).
- JSON pages can be **kept** for auditing or **removed** automatically after CSV/KML generation (your choice in Settings).

### File/Folder Naming

Each run creates a clearly‑named output folder with a unique token:

```
<output-root>/
  wifi-basic-<timestamp-or-id>/
    wifi-basic-<id>-page_1.json
    wifi-basic-<id>-page_2.json
    wifi-basic-<id>.csv
    wifi-basic-<id>.kml
```

The same convention is used for **bluetooth-basic**, **cell-basic**, and the **detail** tabs.

---

## Batch Detail Runs

- In **Wi‑Fi/Cell Detail** or **Bluetooth Detail**, click **Browse…** to select a text file.
- Provide one identifier **per line** (e.g., BSSID, network ID, BT MAC).
- The app runs them sequentially, writes per‑run exports, and shows a final summary dialog (e.g., “Created X CSVs / Y KMLs”).
- The selected file path is displayed under the input to make it obvious which batch is running.

**Batch file example**:
```
aa:bb:cc:dd:ee:ff
11:22:33:44:55:66
77:88:99:aa:bb:cc
```

---

## Tips, Limits, and Troubleshooting

- **Rate limits**: WiGLE enforces request limits—use bounding boxes and filters to scope queries.
- **Zero results**:
  - Check your filters (country, tech type, bbox).
  - Try a larger bounding box or fewer filters.
- **Pagination**: The app uses `searchAfter` (when available) to pull all pages automatically.
- **Map tiles**: If tiles don’t load, verify you have internet access or a permissive network.
- **CSV headers**: Because headers are the **union** of keys across pages, expect many columns for rich datasets.
- **KML size**: Large runs → large KMLs. Consider filtering or splitting searches.
- **macOS SSL**: If you see `certificate verify failed`, run the **Install Certificates.command** (bundled with python.org installs) or install `certifi`.

---
## Screenshots
**Bluetooth Basic**
<img width="3964" height="2496" alt="bt-basic" src="https://github.com/user-attachments/assets/03a7b90f-4371-4a5f-87cd-c4d3b8728639" />

**Wifi Basic**
<img width="3964" height="2496" alt="wifi-basic" src="https://github.com/user-attachments/assets/97cb667b-2059-4217-b62a-23e179a5fc4b" />

**Cell Basic**
<img width="3964" height="2496" alt="cell-basic" src="https://github.com/user-attachments/assets/eb08c7bc-5ca2-4f7c-bb70-a05d15335715" />

**BT Detail**
<img width="3964" height="2496" alt="bt-detail" src="https://github.com/user-attachments/assets/0cd06a0c-be1e-44bb-b86e-dd9b3e4c9ac5" />

**Wifi/Cell Detail**
<img width="3964" height="2496" alt="wifi-cell-details" src="https://github.com/user-attachments/assets/9ddd3382-0510-4554-9083-5fd10028a392" />

**MCC-MNC Detail**
<img width="3964" height="2496" alt="MCC-MNC" src="https://github.com/user-attachments/assets/ff91440e-e187-4ae5-9b45-96a095380a19" />

---

## FAQ

**Q: Where are my WiGLE credentials stored?**  
A: In a local JSON file at `~/.wigle_gui/credentials.json`. You can edit or delete it anytime.

**Q: Why export from JSON instead of the table I see on screen?**  
A: The UI table may truncate or omit fields. Exporting from raw JSON guarantees you capture **all** available fields from each page, which become CSV columns and KML attributes.

**Q: Can I keep the JSON pages for auditing?**  
A: Yes. In **Settings**, enable “Keep JSON pages after export”. Otherwise, pages are deleted after CSV/KML are generated.

**Q: How do batch runs work?**  
A: Prepare a text file with one ID per line (BSSID, network ID, or BT MAC). Use **Browse…** on the Detail tab to select it. The app iterates through each, exporting JSON/CSV/KML per run and shows a final count dialog.

**Q: I’m seeing newline characters (`\\n`) in the Status pane—what gives?**  
A: The Status pane shows raw progress strings. Exports are unaffected. If you prefer cleaner status text, reduce verbosity in Settings or clear between runs; we trim common newline artifacts in recent builds.

**Q: Will this exceed WiGLE rate limits?**  
A: It tries to be polite, but large batch/detail jobs can hit limits. Use country/bounding box filters and consider pausing between runs if needed.

**Q: Does the map work offline?**  
A: Map tiles require internet. You can still run searches and exports without tiles, but drawing a bbox needs the map to be visible.

**Q: My KML won’t open in Google Earth—file is huge.**  
A: Very large datasets produce very large KMLs. Try filtering more narrowly or splitting the run.

---

## Contributing

Issues and PRs are welcome! Please include:
- OS and Python version
- Steps to reproduce (inputs, tab, filters)
- Logs from the Status pane (copy/paste) and any stack traces

---

## License
 Apache-2.0
