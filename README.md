# WiGLE Unified GUI

A cross‑platform Python GUI for exploring the [WiGLE](https://wigle.net/) API. It combines your scripts into a single app with left‑side tabs, a map‑based bounding‑box tool, exports, and quick “Detailed Query” hand‑offs from basic searches to detail lookups.

> **Tabs**
> - **BT Basic**
> - **Wifi Basic**
> - **Cell Basic**
> - **BT Detail**
> - **WiFi/Cell Detail**
> - **MCC‑MNC Lookup**

---

## ✨ Features

- **WiGLE credentials manager** (Settings → *WiGLE Credentials…*). Credentials persist to `~/.wigle_gui/credentials.json` and are used across all tabs.
- **Basic searches** for Wi‑Fi, Bluetooth, and Cellular:
  - Optional **map bounding box** (drag two corners or use “Use View as BBox”).  
    *(Map requires `tkintermapview`; without it, the app still works and shows a helper message.)*
  - **Right‑click context menu** on results: **Copy MAC/ID**, **Copy Name**, **Copy Lat,Lon**, **Detailed Query**.
  - **Detailed Query** jumps to the related detail tab and pre‑fills fields:
    - BT Basic → **BT Detail** (`netid`)
    - Wifi Basic → **WiFi/Cell Detail** (`netid`/BSSID)
    - Cell Basic → **WiFi/Cell Detail** (`operator`, `lac`, `cid`) parsed from cell `ID` (`operator_lac_cid`)
  - **Country** drop‑downs show a full ISO‑3166 list as “Country Name (XX)”; only the **digraph (XX)** is sent.
  - **Submitted URL** is shown in the status pane.
  - **Parameters are preserved** between searches (only results/logs clear).
- **Detail tabs (BT Detail & WiFi/Cell Detail)**  
  - Accept a single `netid` (and for WiFi/Cell, optional `operator/lac/cid/...`).  
  - Batch mode (load a text file with one ID per line).  
  - **Submitted URL** shown in status. Parameters are preserved between runs.
- **MCC‑MNC Lookup** with CSV export.
- **Exports**: Full CSV, KML, and (optionally) merged JSON from raw API data (not from table cells).

---

## 🧰 Requirements

- **Python 3.8+**
- **Tkinter** (usually bundled with Python on Windows and macOS; on Linux install `python3-tk` package)
- **Pip packages**:
  - `requests`
  - `tkintermapview` *(optional, for the embedded map)*

> The app detects if `tkintermapview` is missing and falls back to a non‑map experience.

---

## 💻 Installation

### 1) Clone and enter the project
```bash
git clone https://github.com/AlsatianConsulting/WigleGUI.git
cd WigleGUI
```

### 2) (Recommended) Create and activate a virtual environment

**Linux / macOS**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies

**Option A: via requirements.txt**
```bash
pip install -r requirements.txt
```

**Option B: directly with pip**
```bash
pip install requests tkintermapview
```

> If you **don’t** want the map:  
> `pip install requests` (skip `tkintermapview`).

### OS‑specific notes

#### Linux
- Ensure Tk is installed:
  - Debian/Ubuntu: `sudo apt-get update && sudo apt-get install -y python3-tk`
  - Fedora: `sudo dnf install python3-tkinter`
  - Arch: `sudo pacman -S tk`
- If you use Wayland and see focus/copy issues, try running under XWayland: `GDK_BACKEND=x11 python wigleGUI.py`

#### Windows
- The official Python installer includes Tkinter by default.
- From PowerShell, use `py -3 -m pip install ...` to match your default Python.

#### macOS
- Python from **python.org** typically includes Tkinter.
- With **Homebrew** Python, you may need modern Tcl/Tk:
  ```bash
  brew install tcl-tk
  # Optional: make sure the headers/libs are found during builds
  echo 'export PATH="/usr/local/opt/tcl-tk/bin:$PATH"' >> ~/.zprofile
  echo 'export LDFLAGS="-L/usr/local/opt/tcl-tk/lib"' >> ~/.zprofile
  echo 'export CPPFLAGS="-I/usr/local/opt/tcl-tk/include"' >> ~/.zprofile
  source ~/.zprofile
  ```

---

## ▶️ Run the app

```bash
python wigleGUI.py
```

- First run: open **Settings → WiGLE Credentials…**, enter your **WiGLE Username** (API name) and **API Token**.  
  These are stored in `~/.wigle_gui/credentials.json`.

---

## 🕹️ Usage highlights

- **Left‑side tabs**: click to switch.
- **Map controls (Basic tabs)**:
  - **BBox** toggles click‑to‑draw (first corner → opposite corner).
  - **Use View as BBox** uses the current map viewport.
  - **Satellite View / Map View** toggles tiles.
- **Search lifecycle (Basic tabs)**:
  - Status shows **Total in DB**, **Submitted URL**, per‑page saves, and completion.
  - **Parameters stay put**. Use **Clear Params** to reset inputs or **Clear All** to also clear results/log.
- **Right‑click in results (Basic tabs)**:
  - **Copy MAC/ID**, **Copy Name**, **Copy Lat,Lon**
  - **Detailed Query**: jumps to matching detail tab and pre‑fills
- **Detail tabs**:
  - Single **netid** or **Batch** file (one ID per line).
  - Status shows the **Submitted URL**.
- **Exports**:
  - **Full CSV**: flat CSV built from the underlying raw JSON (including per‑point location data).
  - **KML**: placemarks for points that have `lat/lon`.
  - **JSON (optional)**: merged raw pages if you toggle the JSON export button.

---

## 🔐 Credentials & storage

- Saved at `~/.wigle_gui/credentials.json` as:
  ```json
  {"username": "<your-username>", "token": "<your-api-token>"}
  ```
- The app uses **HTTP Basic Auth** to call the WiGLE API.

> Treat your API token like a password. Don’t commit `~/.wigle_gui/` to version control.

---

## ❓ Troubleshooting

- **401 Unauthorized / 403**: check your WiGLE username/token and rate limits.
- **404 on BT Detail**: the Bluetooth `netid` doesn’t exist (or endpoint changed). BT detail uses `/api/v2/bluetooth/detail`.
- **Map doesn’t appear**: install `tkintermapview` or check network access for tiles; the app works without it.
- **Copy/Paste issues on Linux**: try `xclip`/`xsel` installed or run under XWayland (`GDK_BACKEND=x11`).

---

## 📦 Optional: build a standalone executable

> These steps are optional; running from source is recommended.

Using **PyInstaller**:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed wigleGUI.py
```
Your binary will be in `dist/`. On macOS, you may need additional flags for tcl/tk bundling.

---

## 📝 Requirements file example

If you want to ship a `requirements.txt`, this is a good starting point:
```
requests>=2.31.0
tkintermapview>=1.29
```
> `tkinter` ships with Python; it’s not installable via `pip`.

---

## ⚖️ License

Choose a license (e.g., MIT) and add it to `LICENSE` in the repo.

---

## 🙌 Acknowledgements

- [WiGLE](https://wigle.net/)
- [tkintermapview](https://github.com/TomSchimansky/TkinterMapView)
