
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wigleGUI.py — Unified WiGLE GUI (with context menus + Detailed Query)

What's new in this update
- Right‑click on **any Basic** results table opens a context menu:
    • Copy MAC/ID
    • Copy Name
    • Copy Lat,Lon
    • Detailed Query  ← jumps to the appropriate detail tab and pre-fills fields
      - BT Basic → BT Detail (netid)
      - Wifi Basic → WiFi/Cell Detail (netid/bssid)
      - Cell Basic → WiFi/Cell Detail (operator, lac, cid) parsed from ID "OP_LAC_CID"
- Country dropdowns stay **blank** by default and are cleared by **Clear Params / Clear All**.
- Previous fixes retained (bbox indentation, etc.).
"""

import os
import re
import json
import time
import threading
from datetime import datetime
from pathlib import Path

import tkinter as tk
import tkinter.font as tkfont
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText

# Optional map widget
try:
    from tkintermapview import TkinterMapView
except Exception:
    TkinterMapView = None

import requests

APP_NAME = "WiGLE Unified GUI"
STORE_DIR = Path.home() / ".wigle_gui"
STORE_DIR.mkdir(parents=True, exist_ok=True)
CRED_PATH = STORE_DIR / "credentials.json"

OSM_TILE_URL = "https://a.tile.openstreetmap.org/{z}/{x}/{y}.png"
SAT_TILE_URL = "http://mt0.google.com/vt/lyrs=y&hl=en&x={x}&y={y}&z={z}"

HEADERS = {"User-Agent": "WiGLE-GUI/Unified/1.0 (+local)"}

ENDPOINTS = {
    "wifi_search":       "https://api.wigle.net/api/v2/network/search",
    "bt_search":         "https://api.wigle.net/api/v2/bluetooth/search",
    "cell_search":       "https://api.wigle.net/api/v2/cell/search",
    "network_detail":    "https://api.wigle.net/api/v2/network/detail",
    "mccmnc":            "https://api.wigle.net/api/v2/cell/mccMnc",
    "bt_detail":         "https://api.wigle.net/api/v2/bluetooth/detail",
}

# ---------------------- Utils ----------------------

def xml_escape(text):
    try:
        s = str(text)
    except Exception:
        s = ""
    return (s.replace("&", "&amp;").replace("<", "&lt;")
             .replace(">", "&gt;").replace('"', "&quot;").replace("'", "&apos;"))

def safe_json_dump(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

# ---------------------- Credentials & API client ----------------------

class CredentialManager:
    def __init__(self, path=CRED_PATH):
        self.path = Path(path)
        self.user = ""
        self.token = ""
        self.load()

    def load(self):
        try:
            data = json.load(open(self.path, "r", encoding="utf-8"))
            self.user = data.get("username", "") or ""
            self.token = data.get("token", "") or ""
        except Exception:
            self.user = ""
            self.token = ""

    def save(self, username, token):
        self.user = username or ""
        self.token = token or ""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            json.dump({"username": self.user, "token": self.token}, open(self.path, "w", encoding="utf-8"))
        except Exception as e:
            messagebox.showwarning("Credentials", f"Failed to save credentials: {e}")

    def ready(self):
        return bool(self.user and self.token)

class ApiClient:
    def __init__(self, cred: CredentialManager):
        self.cred = cred
        self._session = None

    @property
    def session(self):
        if self._session is None:
            s = requests.Session()
            from requests.adapters import HTTPAdapter
            adapter = HTTPAdapter(pool_connections=32, pool_maxsize=64, max_retries=2)
            s.mount("https://", adapter)
            s.mount("http://", adapter)
            s.headers.update(HEADERS)
            if self.cred.ready():
                s.auth = (self.cred.user, self.cred.token)
            self._session = s
        else:
            if self.cred.ready():
                self._session.auth = (self.cred.user, self.cred.token)
        return self._session

# ---------------------- Country data ----------------------
COUNTRY_LIST = [
    ("Afghanistan","AF"),("Åland Islands","AX"),("Albania","AL"),("Algeria","DZ"),("American Samoa","AS"),
    ("Andorra","AD"),("Angola","AO"),("Anguilla","AI"),("Antarctica","AQ"),("Antigua and Barbuda","AG"),
    ("Argentina","AR"),("Armenia","AM"),("Aruba","AW"),("Australia","AU"),("Austria","AT"),
    ("Azerbaijan","AZ"),("Bahamas","BS"),("Bahrain","BH"),("Bangladesh","BD"),("Barbados","BB"),
    ("Belarus","BY"),("Belgium","BE"),("Belize","BZ"),("Benin","BJ"),("Bermuda","BM"),
    ("Bhutan","BT"),("Bolivia","BO"),("Bonaire, Sint Eustatius and Saba","BQ"),("Bosnia and Herzegovina","BA"),
    ("Botswana","BW"),("Bouvet Island","BV"),("Brazil","BR"),("British Indian Ocean Territory","IO"),
    ("Brunei Darussalam","BN"),("Bulgaria","BG"),("Burkina Faso","BF"),("Burundi","BI"),
    ("Cabo Verde","CV"),("Cambodia","KH"),("Cameroon","CM"),("Canada","CA"),("Cayman Islands","KY"),
    ("Central African Republic","CF"),("Chad","TD"),("Chile","CL"),("China","CN"),("Christmas Island","CX"),
    ("Cocos (Keeling) Islands","CC"),("Colombia","CO"),("Comoros","KM"),("Congo","CG"),
    ("Congo, Democratic Republic of the","CD"),("Cook Islands","CK"),("Costa Rica","CR"),("Côte d’Ivoire","CI"),
    ("Croatia","HR"),("Cuba","CU"),("Curaçao","CW"),("Cyprus","CY"),("Czechia","CZ"),
    ("Denmark","DK"),("Djibouti","DJ"),("Dominica","DM"),("Dominican Republic","DO"),
    ("Ecuador","EC"),("Egypt","EG"),("El Salvador","SV"),("Equatorial Guinea","GQ"),("Eritrea","ER"),
    ("Estonia","EE"),("Eswatini","SZ"),("Ethiopia","ET"),("Falkland Islands (Malvinas)","FK"),("Faroe Islands","FO"),
    ("Fiji","FJ"),("Finland","FI"),("France","FR"),("French Guiana","GF"),("French Polynesia","PF"),
    ("French Southern Territories","TF"),("Gabon","GA"),("Gambia","GM"),("Georgia","GE"),("Germany","DE"),
    ("Ghana","GH"),("Gibraltar","GI"),("Greece","GR"),("Greenland","GL"),("Grenada","GD"),
    ("Guadeloupe","GP"),("Guam","GU"),("Guatemala","GT"),("Guernsey","GG"),("Guinea","GN"),
    ("Guinea-Bissau","GW"),("Guyana","GY"),("Haiti","HT"),("Heard Island and McDonald Islands","HM"),("Holy See","VA"),
    ("Honduras","HN"),("Hong Kong","HK"),("Hungary","HU"),("Iceland","IS"),("India","IN"),
    ("Indonesia","ID"),("Iran, Islamic Republic of","IR"),("Iraq","IQ"),("Ireland","IE"),("Isle of Man","IM"),
    ("Israel","IL"),("Italy","IT"),("Jamaica","JM"),("Japan","JP"),("Jersey","JE"),("Jordan","JO"),
    ("Kazakhstan","KZ"),("Kenya","KE"),("Kiribati","KI"),("Korea, Democratic People's Republic of","KP"),
    ("Korea, Republic of","KR"),("Kuwait","KW"),("Kyrgyzstan","KG"),("Lao People's Democratic Republic","LA"),
    ("Latvia","LV"),("Lebanon","LB"),("Lesotho","LS"),("Liberia","LR"),("Libya","LY"),
    ("Liechtenstein","LI"),("Lithuania","LT"),("Luxembourg","LU"),("Macao","MO"),("Madagascar","MG"),
    ("Malawi","MW"),("Malaysia","MY"),("Maldives","MV"),("Mali","ML"),("Malta","MT"),("Marshall Islands","MH"),
    ("Martinique","MQ"),("Mauritania","MR"),("Mauritius","MU"),("Mayotte","YT"),("Mexico","MX"),
    ("Micronesia, Federated States of","FM"),("Moldova, Republic of","MD"),("Monaco","MC"),("Mongolia","MN"),
    ("Montenegro","ME"),("Montserrat","MS"),("Morocco","MA"),("Mozambique","MZ"),("Myanmar","MM"),
    ("Namibia","NA"),("Nauru","NR"),("Nepal","NP"),("Netherlands","NL"),("New Caledonia","NC"),("New Zealand","NZ"),
    ("Nicaragua","NI"),("Niger","NE"),("Nigeria","NG"),("Niue","NU"),("Norfolk Island","NF"),
    ("North Macedonia","MK"),("Northern Mariana Islands","MP"),("Norway","NO"),("Oman","OM"),
    ("Pakistan","PK"),("Palau","PW"),("Palestine, State of","PS"),("Panama","PA"),("Papua New Guinea","PG"),
    ("Paraguay","PY"),("Peru","PE"),("Philippines","PH"),("Pitcairn","PN"),("Poland","PL"),("Portugal","PT"),
    ("Puerto Rico","PR"),("Qatar","QA"),("Réunion","RE"),("Romania","RO"),("Russian Federation","RU"),
    ("Rwanda","RW"),("Saint Barthélemy","BL"),("Saint Helena, Ascension and Tristan da Cunha","SH"),
    ("Saint Kitts and Nevis","KN"),("Saint Lucia","LC"),("Saint Martin (French part)","MF"),("Saint Pierre and Miquelon","PM"),
    ("Saint Vincent and the Grenadines","VC"),("Samoa","WS"),("San Marino","SM"),("Sao Tome and Principe","ST"),
    ("Saudi Arabia","SA"),("Senegal","SN"),("Serbia","RS"),("Seychelles","SC"),("Sierra Leone","SL"),
    ("Singapore","SG"),("Sint Maarten (Dutch part)","SX"),("Slovakia","SK"),("Slovenia","SI"),
    ("Solomon Islands","SB"),("Somalia","SO"),("South Africa","ZA"),("South Georgia and the South Sandwich Islands","GS"),
    ("South Sudan","SS"),("Spain","ES"),("Sri Lanka","LK"),("Sudan","SD"),("Suriname","SR"),("Svalbard and Jan Mayen","SJ"),
    ("Sweden","SE"),("Switzerland","CH"),("Syrian Arab Republic","SY"),("Taiwan, Province of China","TW"),
    ("Tajikistan","TJ"),("Tanzania, United Republic of","TZ"),("Thailand","TH"),("Timor-Leste","TL"),
    ("Togo","TG"),("Tokelau","TK"),("Tonga","TO"),("Trinidad and Tobago","TT"),("Tunisia","TN"),
    ("Turkey","TR"),("Turkmenistan","TM"),("Turks and Caicos Islands","TC"),("Tuvalu","TV"),
    ("Uganda","UG"),("Ukraine","UA"),("United Arab Emirates","AE"),("United Kingdom of Great Britain and Northern Ireland","GB"),
    ("United States of America","US"),("United States Minor Outlying Islands","UM"),("Uruguay","UY"),
    ("Uzbekistan","UZ"),("Vanuatu","VU"),("Venezuela (Bolivarian Republic of)","VE"),("Viet Nam","VN"),
    ("Virgin Islands (British)","VG"),("Virgin Islands (U.S.)","VI"),("Wallis and Futuna","WF"),("Western Sahara","EH"),
    ("Yemen","YE"),("Zambia","ZM"),("Zimbabwe","ZW")
]

def build_country_display_list():
    items = [f"{name} ({code})" for (name, code) in COUNTRY_LIST]
    items.sort(key=lambda s: s.lower())
    return items

def country_display_to_code(display: str) -> str:
    m = re.search(r"\(([A-Z]{2})\)\s*$", display or "")
    return m.group(1) if m else ""

# ---------------------- Base tab classes ----------------------

class BaseTab(ttk.Frame):
    def __init__(self, master, api: ApiClient, app=None):
        super().__init__(master)
        self.api = api
        self.app = app
        self.stop_event = threading.Event()
        self.search_thread = None
        self.csv_selected = False
        self.kml_selected = False
        self.json_selected = False
        self.output_dir = None
        self.run_tag = None

        self._img_red = tk.PhotoImage(width=12, height=12); self._img_red.put("#cc0000", to=(0,0,12,12))
        self._img_green = tk.PhotoImage(width=12, height=12); self._img_green.put("#00aa00", to=(0,0,12,12))

    def _toggle_btn(self, btn, flag_name):
        val = not getattr(self, flag_name)
        setattr(self, flag_name, val)
        try:
            btn.configure(image=(self._img_green if val else self._img_red))
        except Exception:
            pass

    def _ask_parent_outdir(self, prefix):
        parent = filedialog.askdirectory(title="Select Parent Folder for Exports")
        if not parent:
            return None, None
        epoch = int(time.time())
        tag = f"{prefix}-{epoch}"
        outdir = Path(parent) / tag
        outdir.mkdir(parents=True, exist_ok=True)
        return outdir, tag

    def _log(self, text):
        pass

# -------- Basic Search Tab --------

class BasicSearchTab(BaseTab):
    def clear_results(self):
        try:
            self.status.delete('1.0', 'end')
        except Exception:
            pass
        try:
            for iid in self.table.get_children():
                self.table.delete(iid)
        except Exception:
            pass
        self.page_files.clear()

    DEFAULT_CENTER = (20.0, 0.0)
    DEFAULT_ZOOM = 2

    def __init__(self, master, api: ApiClient, app, title="Search"):
        super().__init__(master, api, app)

        main = ttk.Frame(self, padding=0)
        main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # LEFT
        left = ttk.Frame(main)
        left.grid(row=0, column=0, sticky="nsw")
        left.rowconfigure(2, weight=1)

        param_frame = ttk.LabelFrame(left, text="Search Parameters", padding=6)
        param_frame.grid(row=0, column=0, sticky="ew", padx=4, pady=4)
        self.entries = {}
        for i, key in enumerate(self.param_fields):
            row = i // 2
            col = (i % 2) * 2
            ttk.Label(param_frame, text=f"{key}:").grid(row=row, column=col, sticky="e", padx=(0,6), pady=2)
            if key in ("lastupdt","firsttime","lasttime"):
                rowf = ttk.Frame(param_frame); rowf.grid(row=row, column=col+1, sticky="w")
                ent = ttk.Entry(rowf, width=26); ent.pack(side="left")
                ttk.Button(rowf, text="Pick", width=6, command=lambda k=key: self._pick_date_into(k)).pack(side="left", padx=(6,0))
            elif key == "country" and hasattr(self, "country_values"):
                ent = ttk.Combobox(param_frame, values=self.country_values, state="readonly", width=32)
                ent.grid(row=row, column=col+1, sticky="w")
                ent.set("")
            else:
                ent = ttk.Entry(param_frame, width=32)
                ent.grid(row=row, column=col+1, sticky="w")
            self.entries[key] = ent
        param_frame.columnconfigure(1, weight=1)
        param_frame.columnconfigure(3, weight=1)

        ctrl = ttk.Frame(left)
        ctrl.grid(row=1, column=0, sticky="w", padx=4)
        ttk.Button(ctrl, text="Search", command=self.start_search).pack(side="left")
        ttk.Button(ctrl, text="Stop", command=self.stop_search).pack(side="left", padx=(6,0))
        ttk.Button(ctrl, text="Clear Params", command=self.clear_parameters).pack(side="left", padx=(6,0))
        ttk.Button(ctrl, text="Clear All", command=self.clear_all).pack(side="left", padx=(6,12))

        self.btn_csv = ttk.Button(ctrl, text="Export Full CSV", compound="left",
                                  image=self._img_red, command=lambda: self._toggle_btn(self.btn_csv, "csv_selected"))
        self.btn_csv.pack(side="left")
        self.btn_kml = ttk.Button(ctrl, text="Export KML", compound="left",
                                  image=self._img_red, command=lambda: self._toggle_btn(self.btn_kml, "kml_selected"))
        self.btn_kml.pack(side="left", padx=(6,0))
        self.btn_json = ttk.Button(ctrl, text="Export JSON", compound="left",
                                   image=self._img_red, command=lambda: self._toggle_btn(self.btn_json, "json_selected"))
        self.btn_json.pack(side="left", padx=(6,0))

        self.status = ScrolledText(left, width=60, height=10)
        self.status.grid(row=2, column=0, sticky="nsew", padx=4, pady=6)

        # RIGHT
        right = ttk.Frame(main)
        right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        right.rowconfigure(2, weight=1)

        map_box = ttk.LabelFrame(right, text="Map Bounding Box")
        map_box.grid(row=0, column=0, sticky="nsew", padx=4, pady=(4,2))
        map_box.columnconfigure(0, weight=1)
        map_box.rowconfigure(1, weight=1)

        map_ctrl = ttk.Frame(map_box)
        map_ctrl.grid(row=0, column=0, sticky="w")
        self.btn_view = ttk.Button(map_ctrl, text="Satellite View", command=self._toggle_view)
        self.btn_view.pack(side="left")
        self.btn_bbox = ttk.Button(map_ctrl, text="BBox", command=self._toggle_bbox)
        self.btn_bbox.pack(side="left", padx=(6,0))
        ttk.Button(map_ctrl, text="Use View as BBox", command=self._use_view_bbox).pack(side="left", padx=(6,0))
        ttk.Button(map_ctrl, text="Clear BBox", command=self._clear_bbox).pack(side="left", padx=(6,0))

        if TkinterMapView is None:
            self.map_widget = ttk.Label(map_box, text="Install tkintermapview to enable the map.", anchor="center")
        else:
            self.map_widget = TkinterMapView(map_box, corner_radius=0)
            self.map_widget.set_tile_server(OSM_TILE_URL)
            self.map_widget.set_position(*self.DEFAULT_CENTER)
            self.map_widget.set_zoom(self.DEFAULT_ZOOM)
            try:
                self.map_widget.add_left_click_map_command(self._on_map_click)
            except Exception:
                pass
        self.map_widget.grid(row=1, column=0, sticky="nsew")

        loc = ttk.Frame(right)
        loc.grid(row=1, column=0, sticky="ew", padx=4)
        ttk.Label(loc, text="Location:").pack(side="left")
        self.loc_entry = ttk.Entry(loc, width=64)
        self.loc_entry.pack(side="left")
        self.loc_entry.bind("<Return>", lambda e: self._go_location())
        ttk.Button(loc, text="Go", command=self._go_location).pack(side="left", padx=(6,0))

        tbl_box = ttk.LabelFrame(right, text="Results")
        tbl_box.grid(row=2, column=0, sticky="nsew", padx=4, pady=(2,4))
        tbl_box.columnconfigure(0, weight=1)
        tbl_box.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(tbl_box, columns=[k for k,_ in self.table_cols], show="headings")
        for key, head in self.table_cols:
            self.table.heading(key, text=head)
            self.table.column(key, width=120, anchor="w", stretch=True)
        self.table.grid(row=0, column=0, sticky="nsew")

        # Context menu for table
        self.copy_mac_label = getattr(self, "copy_mac_label", "Copy ID")
        self._send_target = getattr(self, "_send_target", None)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label=self.copy_mac_label, command=self._copy_mac_id)
        self.menu.add_command(label="Copy Name", command=self._copy_name)
        self.menu.add_command(label="Copy Lat,Lon", command=self._copy_latlon)
        if self._send_target:
            self.menu.add_separator()
            self.menu.add_command(label="Detailed Query", command=self._send_to_advanced)
        self.table.bind("<Button-3>", self._on_right_click)  # Right-click

        # bbox state
        self._sat = False
        self._bbox_on = False
        self._bbox_start = None
        self._bbox_poly = None

        # run state
        self.page_files = []

    # ----- helpers -----

    def _log(self, text):
        s = str(text).replace("\\r\\n", "\n").replace("\\n", "\n")
        if not s.endswith("\n"):
            s += "\n"
        self.status.insert("end", s)
        self.status.see("end")

    def _pick_date_into(self, key):
        val = self._pick_date_dialog()
        if val:
            self.entries[key].delete(0, "end")
            self.entries[key].insert(0, val)

    def _pick_date_dialog(self):
        today = datetime.today()
        y, m, d = today.year, today.month, today.day
        top = tk.Toplevel(self)
        top.title("Select Date")
        frm = ttk.Frame(top, padding=8); frm.grid(row=0, column=0)
        ttk.Label(frm, text="Year").grid(row=0, column=0)
        yv = tk.IntVar(value=y); ttk.Spinbox(frm, from_=1970, to=2100, width=6, textvariable=yv).grid(row=0, column=1)
        ttk.Label(frm, text="Month").grid(row=1, column=0)
        mv = tk.IntVar(value=m); ttk.Spinbox(frm, from_=1, to=12, width=4, textvariable=mv).grid(row=1, column=1)
        ttk.Label(frm, text="Day").grid(row=2, column=0)
        dv = tk.IntVar(value=d); ttk.Spinbox(frm, from_=1, to=31, width=4, textvariable=dv).grid(row=2, column=1)
        out = {"val": None}
        def ok():
            try:
                datetime(yv.get(), mv.get(), dv.get())
            except ValueError:
                messagebox.showerror("Date", "Invalid date")
                return
            out["val"] = f"{yv.get():04d}{mv.get():02d}{dv.get():02d}000000"
            top.destroy()
        ttk.Button(frm, text="OK", command=ok).grid(row=3, column=0, columnspan=2, pady=6)
        top.grab_set(); self.wait_window(top)
        return out["val"]

    def _toggle_view(self):
        if TkinterMapView is None: return
        if self._sat:
            self.map_widget.set_tile_server(OSM_TILE_URL); self.btn_view.config(text="Satellite View")
        else:
            self.map_widget.set_tile_server(SAT_TILE_URL); self.btn_view.config(text="Map View")
        self._sat = not self._sat

    def _toggle_bbox(self):
        self._bbox_on = not self._bbox_on
        self.btn_bbox.config(text=("BBox (ON)" if self._bbox_on else "BBox"))

    def _clear_bbox(self):
        try:
            if self._bbox_poly: self._bbox_poly.delete()
        except Exception:
            pass
        self._bbox_poly = None
        self._bbox_start = None
        self._bbox_on = False
        self.btn_bbox.config(text="BBox")
        for k in ("latrange1","latrange2","longrange1","longrange2"):
            if k in self.entries:
                self.entries[k].delete(0, "end")
        self._log("BBox cleared.")

    def _use_view_bbox(self):
        if TkinterMapView is None: return
        lat_min = lon_min = lat_max = lon_max = None
        if hasattr(self.map_widget, "get_bounds"):
            try:
                (lat_min, lon_min), (lat_max, lon_max) = self.map_widget.get_bounds()
            except Exception:
                pass
        if lat_min is None:
            try:
                center_lat, center_lon = self.map_widget.get_position()
                z = getattr(self.map_widget, "zoom", self.DEFAULT_ZOOM)
                w = getattr(self.map_widget, "width", 800); h = getattr(self.map_widget, "height", 600)
                def lon_to_x(lon, z): return (lon + 180.0) / 360.0 * (256 * (2**z))
                def lat_to_y(lat, z):
                    import math as _m
                    s = max(min(_m.sin(_m.radians(lat)), 0.9999), -0.9999)
                    return (0.5 - _m.log((1+s)/(1-s))/(4*_m.pi)) * (256 * (2**z))
                def x_to_lon(x, z): return x / (256 * (2**z)) * 360.0 - 180.0
                def y_to_lat(y, z):
                    import math as _m
                    n = _m.pi - 2.0 * _m.pi * y / (256 * (2**z))
                    return _m.degrees(_m.atan(0.5*(_m.exp(n)-_m.exp(-n))))
                cx, cy = lon_to_x(center_lon, z), lat_to_y(center_lat, z)
                half_w, half_h = w/2, h/2
                lon_min, lon_max = x_to_lon(cx-half_w, z), x_to_lon(cx+half_w, z)
                lat_min, lat_max = y_to_lat(cy+half_h, z), y_to_lat(cy-half_h, z)
            except Exception:
                messagebox.showerror("BBox", "Unable to compute bounds")
                return
        for k, v in {"latrange1":lat_min, "latrange2":lat_max, "longrange1":lon_min, "longrange2":lon_max}.items():
            if k in self.entries:
                self.entries[k].delete(0, "end")
                self.entries[k].insert(0, f"{v:.6f}")
        try:
            if self._bbox_poly: self._bbox_poly.delete()
        except Exception:
            pass
        try:
            pts = [(lat_min, lon_min), (lat_min, lon_max), (lat_max, lon_max), (lat_max, lon_min)]
            self._bbox_poly = self.map_widget.set_polygon(pts, outline_color="blue", fill_color=None, border_width=2)
        except Exception:
            self._bbox_poly = None
        self._log("BBox set from current map view.")

    def _on_map_click(self, coords):
        if not self._bbox_on:
            return
        try:
            lat, lon = coords
        except Exception:
            return
        if self._bbox_start is None:
            self._bbox_start = (lat, lon)
            self._log("BBox: first corner set. Click opposite corner.")
            return
        lat1, lon1 = self._bbox_start; lat2, lon2 = lat, lon
        lat_min, lat_max = sorted((lat1, lat2)); lon_min, lon_max = sorted((lon1, lon2))
        try:
            if self._bbox_poly: self._bbox_poly.delete()
        except Exception:
            pass
        try:
            pts = [(lat_min, lon_min), (lat_min, lon_max), (lat_max, lon_max), (lat_max, lon_min)]
            self._bbox_poly = self.map_widget.set_polygon(pts, outline_color="blue", fill_color=None, border_width=2)
        except Exception:
            self._bbox_poly = None
        for k, v in {"latrange1":lat_min, "latrange2":lat_max, "longrange1":lon_min, "longrange2":lon_max}.items():
            if k in self.entries:
                self.entries[k].delete(0, "end")
                self.entries[k].insert(0, f"{v:.6f}")
        self._log("BBox set from map clicks. Exiting draw mode.")
        self._bbox_on = False
        self.btn_bbox.config(text="BBox")
        self._bbox_start = None

    def _go_location(self):
        q = (self.loc_entry.get() or "").strip()
        if not q:
            return
        m = re.match(r"^\s*([+-]?\d+(?:\.\d+)?)\s*[, ]\s*([+-]?\d+(?:\.\d+)?)\s*$", q)
        latlon = None
        if m:
            latlon = (float(m.group(1)), float(m.group(2)))
        else:
            try:
                r = requests.get("https://nominatim.openstreetmap.org/search",
                                 params={"q": q, "format":"json", "limit":1},
                                 headers={"User-Agent": HEADERS["User-Agent"]},
                                 timeout=15)
                r.raise_for_status()
                arr = r.json()
                if arr:
                    latlon = (float(arr[0]["lat"]), float(arr[0]["lon"]))
            except Exception as e:
                self._log(f"Nominatim error: {e}")
        if latlon and TkinterMapView is not None:
            lat, lon = latlon
            self.map_widget.set_position(lat, lon)
            self.map_widget.set_zoom(15)
            self._log(f"Slewed to {lat:.6f}, {lon:.6f}")

    # ----- Right-click menu handlers -----

    def _on_right_click(self, event):
        # select row under cursor
        iid = self.table.identify_row(event.y)
        if iid:
            self.table.selection_set(iid)
            try:
                self.menu.tk_popup(event.x_root, event.y_root)
            finally:
                self.menu.grab_release()

    def _get_selected_values(self):
        sel = self.table.selection()
        if not sel:
            return None
        vals = self.table.item(sel[0], "values")
        if not vals or len(vals) < 5:
            return None
        # Column order for all basic tabs: [id/netid, name, lastupdt/gentype, lat, lon]
        return {
            "id": vals[0],
            "name": vals[1],
            "lat": vals[3],
            "lon": vals[4],
        }

    def _copy_mac_id(self):
        v = self._get_selected_values()
        if not v: return
        try:
            self.clipboard_clear()
            self.clipboard_append(v["id"])
            self._log(f"Copied: {v['id']}")
        except Exception:
            pass

    def _copy_name(self):
        v = self._get_selected_values()
        if not v: return
        try:
            self.clipboard_clear()
            self.clipboard_append(v["name"] or "")
            self._log(f"Copied: {v['name']}")
        except Exception:
            pass

    def _copy_latlon(self):
        v = self._get_selected_values()
        if not v: return
        txt = f"{v['lat']},{v['lon']}"
        try:
            self.clipboard_clear()
            self.clipboard_append(txt)
            self._log(f"Copied: {txt}")
        except Exception:
            pass

    def _send_to_advanced(self):
        v = self._get_selected_values()
        if not v or not self._send_target or not self.app:
            return
        target = self._send_target
        # Show/ensure target tab exists
        self.app.show(target)
        detail = self.app.frames.get(target)
        if not detail:
            return
        # Populate according to source tab
        try:
            if target == "BT Detail":
                # BT: netid only
                ent = detail.entries.get("netid")
                if ent is not None:
                    ent.delete(0, "end"); ent.insert(0, v["id"])
            else:
                # WiFi/Cell Detail
                if getattr(self, "is_cell_basic", False):
                    # Parse operator/lac/cid from id "OP_LAC_CID"
                    parts = (v["id"] or "").split("_")
                    if len(parts) >= 1 and detail.entries.get("operator") is not None:
                        e = detail.entries["operator"]; e.delete(0, "end"); e.insert(0, parts[0])
                    if len(parts) >= 2 and detail.entries.get("lac") is not None:
                        e = detail.entries["lac"]; e.delete(0, "end"); e.insert(0, parts[1])
                    if len(parts) >= 3 and detail.entries.get("cid") is not None:
                        e = detail.entries["cid"]; e.delete(0, "end"); e.insert(0, parts[2])
                else:
                    # WiFi: netid/bssid to netid
                    ent = detail.entries.get("netid")
                    if ent is not None:
                        ent.delete(0, "end"); ent.insert(0, v["id"])
        except Exception:
            pass

    # ----- search flow -----

    def clear_parameters(self):
        for k, w in self.entries.items():
            try:
                if isinstance(w, ttk.Combobox) and k == "country":
                    w.set("")
                else:
                    w.delete(0, "end")
            except Exception:
                pass

    def clear_all(self):
        self.clear_parameters()
        try:
            self.status.delete("1.0", "end")
        except Exception:
            pass
        try:
            for iid in self.table.get_children():
                self.table.delete(iid)
        except Exception:
            pass
        self.page_files.clear()

    def stop_search(self):
        if self.search_thread and self.search_thread.is_alive():
            self.stop_event.set()

    def _collect_params(self):
        p = {}
        for k, w in self.entries.items():
            try:
                if isinstance(w, ttk.Combobox) and k == "country":
                    disp = w.get().strip()
                    code = country_display_to_code(disp)
                    if code:
                        p[k] = code
                else:
                    v = w.get().strip()
                    if v:
                        p[k] = v
            except Exception:
                pass
        return p

    def start_search(self):
        if not self.api.cred.ready():
            messagebox.showinfo("WiGLE Credentials", "Please set WiGLE credentials in Settings → WiGLE Credentials…")
            return
        if self.search_thread and self.search_thread.is_alive():
            return
        params = self._collect_params()

        outdir, tag = self._ask_parent_outdir(self.save_prefix)
        if not outdir:
            return
        self.output_dir = Path(outdir)
        self.run_tag = tag

        self.clear_results()
        self._log(f"Output folder: {self.output_dir}")

        def worker():
            session = self.api.session
            try:
                r0 = session.get(self.endpoint, params={**params, "resultsPerPage": params.get("resultsPerPage", 1)}, timeout=30)
                r0.raise_for_status()
                count = r0.json().get("totalResults", "unknown")
                self._log(f"Total in DB: {count}")
            except Exception as e:
                self._log(f"Count check failed: {e}")

            local = dict(params)
            page = 1
            total = 0
            self.stop_event.clear()

            # Log the submitted URL (initial request params)
            try:
                _req = requests.Request("GET", self.endpoint, params=local).prepare()
                self._log(f"Submitted: {_req.url}")
            except Exception as _e:
                self._log(f"Submitted (could not build full URL): {self.endpoint} with params {local}")
            while not self.stop_event.is_set():
                try:
                    resp = session.get(self.endpoint, params=local, timeout=60)
                    resp.raise_for_status()
                except Exception as e:
                    self._log(f"Request failed: {e}")
                    break
                data = {}
                try:
                    data = resp.json()
                except Exception:
                    pass
                results = data.get("results", [])
                if not results:
                    break

                page_path = self.output_dir / f"{self.save_prefix}-{self.run_tag}-page_{page}.json"
                try:
                    safe_json_dump(page_path, results)
                    self._log(f"Page {page}: {len(results)} results saved: {page_path}")
                    self.page_files.append(str(page_path))
                except Exception as e:
                    self._log(f"Failed to write page {page}: {e}")

                for r in results:
                    try:
                        vals = self.row_from_result(r)
                        self.table.insert("", "end", values=vals)
                    except Exception:
                        pass
                total += len(results)

                sa = data.get("search_after") or data.get("searchAfter")
                if not sa:
                    break
                local["searchAfter"] = sa
                page += 1
            self._log(f"Search complete: {total} results")

            try:
                if self.csv_selected: self._export_csv()
                if self.kml_selected: self._export_kml()
            finally:
                if not self.json_selected:
                    removed = 0
                    for p in list(self.page_files):
                        try:
                            os.remove(p)
                            removed += 1
                        except Exception:
                            pass
                    self.page_files.clear()
                    self._log(f"Cleaned {removed} temporary JSON file(s).")

        self.search_thread = threading.Thread(target=worker, daemon=True)
        self.search_thread.start()

    def _gather_pages(self):
        return [str(self.output_dir / Path(p).name) for p in self.page_files if os.path.exists(p)]

    def _export_csv(self):
        files = self._gather_pages()
        if not files:
            self._log("No JSON pages to export CSV.")
            return
        headers, seen = [], set()
        rows = []
        for fp in files:
            try:
                data = json.load(open(fp, "r", encoding="utf-8"))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data]
            for e in items:
                if isinstance(e, dict):
                    for k in e.keys():
                        if k not in seen:
                            headers.append(k); seen.add(k)
                    rows.append(e)
        if not headers:
            self._log("CSV export: no headers.")
            return
        csv_path = self.output_dir / f"{self.save_prefix}-{self.run_tag}.csv"
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(headers)
            for e in rows:
                w.writerow([ (json.dumps(v, ensure_ascii=False, separators=(",", ":")) if isinstance(v,(dict,list)) else v) for v in (e.get(k,"") for k in headers) ])
        self._log(f"Full CSV exported: {csv_path}")

    def _export_kml(self):
        files = self._gather_pages()
        if not files:
            self._log("No JSON pages to export KML.")
            return
        parts = ['<?xml version="1.0" encoding="UTF-8"?>','<kml xmlns="http://www.opengis.net/kml/2.2">','<Document>']
        any_point = False
        for fp in files:
            try:
                data = json.load(open(fp, "r", encoding="utf-8"))
            except Exception:
                continue
            items = data if isinstance(data, list) else [data]
            for e in items:
                lat = e.get("trilat") or e.get("lat") or e.get("latitude")
                lon = e.get("trilong") or e.get("lon") or e.get("longitude")
                if lat in (None, "") or lon in (None, ""):
                    continue
                any_point = True
                name = e.get("ssid") or e.get("name") or e.get("netid") or e.get("id") or ""
                parts.append(f"<Placemark><name>{xml_escape(name)}</name>")
                parts.append("<ExtendedData>")
                for k, v in e.items():
                    if isinstance(v, (dict, list)):
                        try:
                            v = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
                        except Exception:
                            v = str(v)
                    parts.append(f'<Data name="{xml_escape(k)}"><value>{xml_escape(v)}</value></Data>')
                parts.append("</ExtendedData>")
                parts.append(f"<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>")
        parts.append("</Document></kml>")
        if not any_point:
            self._log("KML export: no points with lat/lon.")
            return
        kml_path = self.output_dir / f"{self.save_prefix}-{self.run_tag}.kml"
        with open(kml_path, "w", encoding="utf-8") as f:
            f.write("".join(parts))
        self._log(f"KML exported: {kml_path}")

# -------- Specific Basic Tabs --------

class WifiBasicTab(BasicSearchTab):
    def __init__(self, master, api, app):
        self.endpoint = ENDPOINTS["wifi_search"]
        self.save_prefix = "wifi-basic"
        self.param_fields = [
            "onlymine","notmine",
            "latrange1","latrange2","longrange1","longrange2",
            "closestLat","closestLong",
            "lastupdt","firsttime","lasttime",
            "startTransID","endTransID",
            "encryption","freenet","paynet",
            "netid","ssid","ssidlike",
            "minQoS","variance",
            "rcoisMinimum","rcoisMaximum",
            "channel","frequency",
            "houseNumber","road","city","region","postalCode","country",
            "resultsPerPage","searchAfter"
        ]
        self.table_cols = [("netid","BSSID"),("ssid","SSID"),("lastupdt","Last Updated"),("trilat","Lat"),("trilong","Lon")]
        self.country_values = build_country_display_list()
        self.copy_mac_label = "Copy MAC"
        self._send_target = "WiFi/Cell Detail"
        super().__init__(master, api, app, title="Wi‑Fi Basic")

    def row_from_result(self, r):
        return (r.get("netid",""), r.get("ssid",""), r.get("lastupdt",""), r.get("trilat",""), r.get("trilong",""))

class BtBasicTab(BasicSearchTab):
    def __init__(self, master, api, app):
        self.endpoint = ENDPOINTS["bt_search"]
        self.save_prefix = "bt-basic"
        self.param_fields = [
            "onlymine","notmine",
            "latrange1","latrange2","longrange1","longrange2",
            "closestLat","closestLong",
            "lastupdt","firsttime","lasttime",
            "startTransID","endTransID",
            "netid","name","namelike",
            "minQoS","variance",
            "houseNumber","road","city","region","postalCode","country",
            "resultsPerPage","searchAfter"
        ]
        self.table_cols = [("netid","BTID"),("name","Name"),("lastupdt","Last Updated"),("trilat","Lat"),("trilong","Lon")]
        self.country_values = build_country_display_list()
        self.copy_mac_label = "Copy MAC"
        self._send_target = "BT Detail"
        super().__init__(master, api, app, title="BT Basic")

    def row_from_result(self, r):
        return (r.get("netid",""), r.get("name","") or r.get("ssid",""), r.get("lastupdt",""), r.get("trilat",""), r.get("trilong",""))

class CellBasicTab(BasicSearchTab):
    def __init__(self, master, api, app):
        self.endpoint = ENDPOINTS["cell_search"]
        self.save_prefix = "cell-basic"
        self.param_fields = [
            "onlymine","notmine",
            "latrange1","latrange2","longrange1","longrange2",
            "closestLat","closestLong",
            "lastupdt","firsttime","lasttime",
            "startTransID","endTransID",
            "ssid","ssidlike",
            "cell_op","cell_net","cell_id",
            "showGsm","showCdma","showLte","showWcdma","showNr",
            "minQoS","variance",
            "houseNumber","road","city","region","postalCode","country",
            "resultsPerPage","searchAfter"
        ]
        self.table_cols = [("id","ID"),("ssid","Name"),("gentype","GenType"),("trilat","Lat"),("trilong","Lon")]
        self.country_values = build_country_display_list()
        self.copy_mac_label = "Copy ID"
        self._send_target = "WiFi/Cell Detail"
        self.is_cell_basic = True
        super().__init__(master, api, app, title="Cell Basic")

    def row_from_result(self, r):
        return (r.get("id",""), r.get("ssid",""), r.get("gentype",""), r.get("trilat",""), r.get("trilong",""))

# -------- Detail Tabs --------

class BaseDetailTab(BaseTab):
    def __init__(self, master, api: ApiClient, app, label="Detail", include_extra=False):
        super().__init__(master, api, app)
        self.endpoint = ENDPOINTS["network_detail"]
        self.basename = None
        self.page_files = []
        self.merged_json = None
        self.csv_done = False
        self.kml_done = False

        main = ttk.Frame(self); main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0, minsize=420)
        main.columnconfigure(1, weight=1)

        # LEFT
        left = ttk.Frame(main); left.grid(row=0, column=0, sticky="nsw")
        lf = ttk.LabelFrame(left, text=f"{label} Parameters", padding=6); lf.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        lf.columnconfigure(1, weight=1)
        self.entries = {}

        ttk.Label(lf, text="netid:").grid(row=0, column=0, sticky="e", padx=(0,6))
        self.entries["netid"] = ttk.Entry(lf, width=28); self.entries["netid"].grid(row=0, column=1, sticky="ew")

        brow = ttk.Frame(lf); brow.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(2,6))
        brow.columnconfigure(1, weight=1)
        self.batch_var = tk.StringVar(value="")
        ttk.Label(brow, text="Batch file:").grid(row=0, column=0, sticky="e", padx=(0,6))
        ttk.Entry(brow, textvariable=self.batch_var, state="readonly").grid(row=0, column=1, sticky="ew")
        ttk.Button(brow, text="Browse…", command=self._browse_batch).grid(row=0, column=2, padx=(6,0))

        rowi = 2
        self.extra_keys = []
        if include_extra:
            for key, tip in (("operator","GSM/LTE/WCDMA/NR Operator ID"),
                             ("lac","Location Area Code"),
                             ("cid","Cell ID / NIR"),
                             ("type","Type (WIFI/BT/LTE/NR/...)"),
                             ("system","CDMA System ID"),
                             ("network","CDMA Network ID"),
                             ("basestation","CDMA Base Station ID")):
                ttk.Label(lf, text=f"{key}:").grid(row=rowi, column=0, sticky="e", padx=(0,6))
                ent = ttk.Entry(lf, width=28); ent.grid(row=rowi, column=1, sticky="ew")
                self.entries[key] = ent
                self.extra_keys.append(key)
                rowi += 1

        btns = ttk.Frame(left); btns.grid(row=1, column=0, sticky="w", padx=6, pady=(0,6))
        ttk.Button(btns, text="Search", command=self.start_search).pack(side="left")
        ttk.Button(btns, text="Clear Params", command=self.clear_parameters).pack(side="left", padx=(6,0))
        ttk.Button(btns, text="Clear All", command=self.clear_all).pack(side="left", padx=(6,12))

        self.btn_csv = ttk.Button(btns, text="Export Full CSV", compound="left",
                                  image=self._img_red, command=lambda: self._toggle_btn(self.btn_csv, "csv_selected"))
        self.btn_csv.pack(side="left")
        self.btn_kml = ttk.Button(btns, text="Export KML", compound="left",
                                  image=self._img_red, command=lambda: self._toggle_btn(self.btn_kml, "kml_selected"))
        self.btn_kml.pack(side="left", padx=(6,0))
        self.btn_json = ttk.Button(btns, text="Export JSON", compound="left",
                                   image=self._img_red, command=lambda: self._toggle_btn(self.btn_json, "json_selected"))
        self.btn_json.pack(side="left", padx=(6,0))

        self.status = ScrolledText(left, width=58, height=14); self.status.grid(row=2, column=0, sticky="ew", padx=6)

        right = ttk.Frame(main); right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1); right.rowconfigure(0, weight=1)
        st = ttk.Style(self)
        base = tkfont.nametofont("TkDefaultFont")
        normal = tkfont.Font(family=base.cget("family"), size=9, weight="normal")
        st.configure("Results.TLabelframe.Label", font=normal)
        st.configure("Res.Treeview", rowheight=18, font=normal)
        st.configure("Res.Treeview.Heading", font=normal, padding=(2,2))

        box = ttk.LabelFrame(right, text="Results", padding=0, style="Results.TLabelframe")
        box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        box.columnconfigure(0, weight=1); box.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(box, columns=("id","name","lat","lon","updated"), show="headings", style="Res.Treeview")
        for c,h in (("id","Device ID"),("name","Name"),("lat","Latitude"),("lon","Longitude"),("updated","Date Updated")):
            self.table.heading(c, text=h); self.table.column(c, width=120, anchor="w", stretch=True)
        self.table.grid(row=0, column=0, sticky="nsew")

    def _log(self, text):
        s = str(text)
        if not s.endswith("\n"):
            s += "\n"
        self.status.insert("end", s)
        self.status.see("end")

    def _browse_batch(self):
        p = filedialog.askopenfilename(title="Select text file with IDs (one per line)",
                                       filetypes=[("Text files","*.txt *.list *.csv *.tsv"),("All files","*.*")])
        if p:
            self.batch_var.set(p)

    def clear_parameters(self):
        for k,e in self.entries.items():
            try:
                e.delete(0, "end")
            except Exception:
                pass
        self.batch_var.set("")

    def clear_all(self):
        self.clear_parameters()
        try:
            self.status.delete("1.0","end")
        except Exception:
            pass
        try:
            for iid in self.table.get_children():
                self.table.delete(iid)
        except Exception:
            pass
        self.page_files.clear(); self.merged_json=None; self.basename=None
        self.csv_done=False; self.kml_done=False
        self.csv_selected=False; self.kml_selected=False; self.json_selected=False
        for b in (self.btn_csv, self.btn_kml, self.btn_json):
            try:
                b.configure(image=self._img_red)
            except Exception:
                pass

    def _points_from_entry(self, entry):
        pts = []
        locs = entry.get("locationData") or entry.get("locations") or []
        if isinstance(locs, dict): locs = [locs]
        for p in (locs if isinstance(locs, list) else []):
            lat = p.get("lat") or p.get("latitude")
            lon = p.get("lon") or p.get("longitude")
            if lat in (None, "") or lon in (None, ""):
                continue
            when = p.get("time") or p.get("lasttime") or p.get("lastupdt") or entry.get("lastupdt")
            pts.append((f"{float(lat):.6f}", f"{float(lon):.6f}", str(when or "")))
        return pts

    def _device_id(self, entry):
        if entry.get("netid"): return entry.get("netid")
        parts = []
        for k in ("operator","lac","cid","system","network","basestation"):
            v = entry.get(k)
            if v not in (None,""):
                parts.append(f"{k}={v}")
        return ";".join(parts) or "(unknown)"

    def start_search(self):
        if not self.api.cred.ready():
            messagebox.showinfo("WiGLE Credentials", "Please set WiGLE credentials in Settings → WiGLE Credentials…")
            return
        if self.search_thread and self.search_thread.is_alive():
            return

        batch = (self.batch_var.get() or "").strip()
        if batch:
            self._run_batch(batch)
        else:
            self._run_single()

    def _run_single(self):
        params = {}
        for k,e in self.entries.items():
            v = (e.get() or "").strip()
            if v:
                params[k] = v

        parent = filedialog.askdirectory(title="Select Parent Folder for Exports")
        if not parent:
            return
        epoch = int(time.time())
        outdir = Path(parent) / f"detail-{epoch}"
        outdir.mkdir(parents=True, exist_ok=True)
        self.output_dir = outdir

        base = params.get("netid") or "_".join([f"{k}-{params[k]}" for k in ("operator","lac","cid","system","network","basestation") if k in params]) or "detail"
        self.basename = re.sub(r"[^A-Za-z0-9_-]+", "_", base.replace(":",""))

        from urllib.parse import urlencode
        self.status.delete("1.0","end")
        self._log(f"Detail submitted: {ENDPOINTS['network_detail']}?{urlencode(params)}")
        self._log(f"Output folder: {self.output_dir}")

        def worker():
            self._do_detail(params, auto_export=True)
        self.search_thread = threading.Thread(target=worker, daemon=True); self.search_thread.start()

    def _run_batch(self, path):
        try:
            ids = [ln.strip() for ln in open(path,"r",encoding="utf-8") if ln.strip() and not ln.strip().startswith("#")]
        except Exception as ex:
            messagebox.showerror("Batch", f"Failed to read batch file: {ex}")
            return
        if not ids:
            messagebox.showinfo("Batch", "The batch file appears to be empty.")
            return
        parent = filedialog.askdirectory(title="Select Parent Folder for Exports (batch)")
        if not parent:
            return
        epoch = int(time.time())
        outdir = Path(parent) / f"detail-{epoch}"
        outdir.mkdir(parents=True, exist_ok=True)
        self.output_dir = outdir
        self._log(f"Batch file: {path}")
        self._log(f"Output folder: {self.output_dir}")

        def worker():
            csv_ct = kml_ct = 0
            for i, nid in enumerate(ids, start=1):
                self.page_files.clear(); self.merged_json=None; self.basename=None
                self.csv_done=False; self.kml_done=False
                self.status.insert("end", "\n" + "="*64 + "\n"); self.status.insert("end", f"[{i}/{len(ids)}] NETID: {nid}\n"); self.status.insert("end", "="*64 + "\n"); self.status.see("end")
                params = {}
                for k,e in self.entries.items():
                    if k == "netid":
                        continue
                    v = (e.get() or "").strip()
                    if v:
                        params[k] = v
                params["netid"] = nid
                self._do_detail(params, auto_export=True)
                if self.csv_done: csv_ct += 1
                if self.kml_done: kml_ct += 1
            messagebox.showinfo("Batch complete", f"Created {csv_ct} CSV(s) and {kml_ct} KML(s).")
        self.search_thread = threading.Thread(target=worker, daemon=True); self.search_thread.start()

    def _do_detail(self, params, auto_export=False):
        s = self.api.session
        # Log the fully prepared submitted URL
        try:
            _prep = requests.Request('GET', self.endpoint, params=params).prepare()
            self._log(f'Submitted: {_prep.url}')
        except Exception as _e:
            self._log(f'Submitted: {self.endpoint} with params {params}')
        try:
            r = s.get(self.endpoint, params=params, timeout=60); r.raise_for_status()
        except Exception as e:
            self._log(f"Detail request failed: {e}")
            return
        data = r.json()
        results = data.get("results") or ([data.get("result")] if data.get("result") else [])
        if not results:
            self._log("No results.")
            return

        base = params.get("netid") or "_".join([f"{k}-{params[k]}" for k in ("operator","lac","cid","system","network","basestation") if k in params]) or "detail"
        self.basename = re.sub(r"[^A-Za-z0-9_-]+","_", base.replace(":",""))
        page_path = self.output_dir / f"{self.basename}-page_1.json"
        try:
            safe_json_dump(page_path, results)
            self.page_files = [str(page_path)]
            self._log(f"Saved RAW detail JSON page: {page_path}")
        except Exception as ex:
            self._log(f"Failed to write RAW JSON page: {ex}")

        if self.json_selected and self.page_files:
            try:
                merged = self.output_dir / f"{self.basename}.json"
                allr = []
                for p in self.page_files:
                    d = json.load(open(p,"r",encoding="utf-8"))
                    allr.extend(d if isinstance(d,list) else [d])
                safe_json_dump(merged, allr)
                for p in list(self.page_files):
                    try: os.remove(p)
                    except Exception: pass
                self.page_files.clear(); self.merged_json = str(merged)
                self._log(f"Merged RAW JSON saved: {merged}")
            except Exception as ex:
                self._log(f"Failed to merge RAW JSON pages: {ex}")

        for e in results:
            device_id = self._device_id(e)
            name = e.get("ssid") or e.get("name") or e.get("operator") or ""
            for lat, lon, when in self._points_from_entry(e):
                self.table.insert("", "end", values=(device_id, name, lat, lon, when))

        if auto_export:
            if self.csv_selected: self.export_full_csv()
            if self.kml_selected: self.export_kml()
            if (not self.json_selected) and self.page_files:
                removed = 0
                for p in list(self.page_files):
                    try:
                        os.remove(p); removed += 1
                    except Exception:
                        pass
                self.page_files.clear(); self._log(f"RAW JSON pages removed: {removed} files from {self.output_dir}")

    def _raw_files(self):
        if self.merged_json and os.path.isfile(self.merged_json): return [self.merged_json]
        files = []
        for fn in os.listdir(self.output_dir):
            if fn.startswith(self.basename) and fn.endswith(".json"):
                files.append(str(self.output_dir / fn))
        page_like = [p for p in files if "-page_" in os.path.basename(p)]
        return page_like or files

    def _flatten_entry_point(self, entry, point):
        row = {}
        if isinstance(entry, dict):
            for k, v in entry.items():
                if k in ("locationData","locations"): continue
                if isinstance(v, (str,int,float,bool)) or v is None: row[k] = v
                else:
                    try: row[k] = json.dumps(v, ensure_ascii=False, separators=(",", ":"))
                    except Exception: row[k] = str(v)
        if isinstance(point, dict):
            for k, v in point.items(): row[k] = v
        return row

    def _rows_from_full_json(self):
        files = self._raw_files(); rows=[]; header=[]; seen=set()
        def push(k):
            if k not in seen: seen.add(k); header.append(k)
        for p in files:
            try: data = json.load(open(p,"r",encoding="utf-8"))
            except Exception: continue
            entries = data if isinstance(data, list) else data.get("results", [])
            for e in entries:
                locs = e.get("locationData") or e.get("locations") or []
                if isinstance(locs, dict): locs = [locs]
                if not locs:
                    row = self._flatten_entry_point(e, {}); [push(k) for k in row.keys()]; rows.append(row); continue
                for pt in (locs if isinstance(locs, list) else []):
                    row = self._flatten_entry_point(e, pt if isinstance(pt, dict) else {})
                    lat = row.get("lat", row.get("latitude")); lon = row.get("lon", row.get("longitude"))
                    if lat in (None,"") or lon in (None,""): continue
                    [push(k) for k in row.keys()]; rows.append(row)
        return rows, header

    def export_full_csv(self):
        if not self.output_dir or not self.basename:
            messagebox.showinfo("Export Full CSV", "Run a search first.")
            return
        rows, header = self._rows_from_full_json()
        if not rows:
            messagebox.showinfo("Export Full CSV", "No rows to export from raw JSON.")
            return
        csv_path = self.output_dir / f"{self.basename}.csv"
        import csv
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(header)
            for r in rows: w.writerow([r.get(k,"") for k in header])
        self.csv_done=True; self._log(f"Full CSV exported: {csv_path}")

    def export_kml(self):
        if not self.output_dir or not self.basename:
            messagebox.showinfo("Export KML", "Run a search first.")
            return
        rows, header = self._rows_from_full_json()
        any_point=False; parts=['<?xml version="1.0" encoding="UTF-8"?>','<kml xmlns="http://www.opengis.net/kml/2.2">','<Document>']
        for r in rows:
            lat = r.get("lat") or r.get("latitude"); lon = r.get("lon") or r.get("longitude")
            if lat in (None,"") or lon in (None,""): continue
            any_point=True
            name = r.get("ssid") or r.get("name") or r.get("netid") or ""
            parts.append(f"<Placemark><name>{xml_escape(name)}</name>")
            parts.append("<ExtendedData>")
            for k in header:
                v = r.get(k,"")
                parts.append(f'<Data name="{xml_escape(k)}"><value>{xml_escape(v)}</value></Data>')
            parts.append("</ExtendedData>")
            parts.append(f"<Point><coordinates>{lon},{lat},0</coordinates></Point></Placemark>")
        parts.append("</Document></kml>")
        if not any_point:
            messagebox.showinfo("Export KML", "No points with lat/lon to write.")
            return
        kml_path = self.output_dir / f"{self.basename}.kml"
        with open(kml_path, "w", encoding="utf-8") as f: f.write("".join(parts))
        self.kml_done=True; self._log(f"KML exported: {kml_path}")

class BtDetailTab(BaseDetailTab):
    def __init__(self, master, api, app):
        super().__init__(master, api, app, label="BT Detail", include_extra=False)
        self.endpoint = ENDPOINTS["bt_detail"]
class WifiCellDetailTab(BaseDetailTab):
    def __init__(self, master, api, app):
        super().__init__(master, api, app, label="WiFi/Cell Detail", include_extra=True)

# -------- MCC/MNC Tab --------

class MccMncTab(BaseTab):
    def __init__(self, master, api, app):
        super().__init__(master, api, app)
        main = ttk.Frame(self); main.pack(fill="both", expand=True)
        main.columnconfigure(0, weight=0, minsize=360); main.columnconfigure(1, weight=1); main.rowconfigure(0, weight=1)

        left = ttk.Frame(main); left.grid(row=0, column=0, sticky="nsw")
        param = ttk.LabelFrame(left, text="MCC/MNC Parameters", padding=6); param.grid(row=0, column=0, sticky="ew", padx=6, pady=6)
        param.columnconfigure(1, weight=1)
        self.entries = {}
        ttk.Label(param, text="MCC:").grid(row=0, column=0, sticky="e", padx=(0,6)); self.entries["mcc"] = ttk.Entry(param, width=18); self.entries["mcc"].grid(row=0, column=1, sticky="ew")
        ttk.Label(param, text="MNC:").grid(row=1, column=0, sticky="e", padx=(0,6)); self.entries["mnc"] = ttk.Entry(param, width=18); self.entries["mnc"].grid(row=1, column=1, sticky="ew")

        btns = ttk.Frame(left); btns.grid(row=1, column=0, sticky="w", padx=6, pady=(0,6))
        ttk.Button(btns, text="Search", command=self.start_search).pack(side="left")
        ttk.Button(btns, text="Clear", command=self.clear_all).pack(side="left", padx=(6,0))
        ttk.Button(btns, text="Export Results CSV", command=self.export_csv).pack(side="left", padx=(12,0))

        self.status = ScrolledText(left, width=50, height=10); self.status.grid(row=2, column=0, sticky="ew", padx=6)

        right = ttk.Frame(main); right.grid(row=0, column=1, sticky="nsew")
        right.columnconfigure(0, weight=1); right.rowconfigure(0, weight=1)
        box = ttk.LabelFrame(right, text="Results", padding=0); box.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        box.columnconfigure(0, weight=1); box.rowconfigure(0, weight=1)
        self.table = ttk.Treeview(box, columns=("country","brand","operator","bands","notes"), show="headings")
        for c,h in (("country","Country"),("brand","Brand"),("operator","Operator"),("bands","Bands"),("notes","Notes")):
            self.table.heading(c, text=h); self.table.column(c, width=120, anchor="w", stretch=True)
        self.table.grid(row=0, column=0, sticky="nsew")

        self._raw_rows = []

    def _log(self, text):
        s = str(text)
        if not s.endswith("\n"):
            s += "\n"
        self.status.insert("end", s); self.status.see("end")

    def clear_all(self):
        for e in self.entries.values():
            try: e.delete(0, "end")
            except Exception: pass
        try: self.status.delete("1.0","end")
        except Exception: pass
        try:
            for iid in self.table.get_children(): self.table.delete(iid)
        except Exception: pass
        self._raw_rows = []

    def start_search(self):
        if not self.api.cred.ready():
            messagebox.showinfo("WiGLE Credentials", "Please set WiGLE credentials in Settings → WiGLE Credentials…")
            return
        mcc = (self.entries["mcc"].get() or "").strip()
        mnc = (self.entries["mnc"].get() or "").strip()
        if not (mcc or mnc):
            messagebox.showinfo("MCC/MNC", "Enter at least an MCC or an MCC + MNC.")
            return
        self.clear_all()
        self._log(f"GET {ENDPOINTS['mccmnc']}?mcc={mcc}&mnc={mnc}")

        def _extract_records(data, qp):
            if isinstance(data, dict):
                if isinstance(data.get("results"), list): return [r for r in data["results"] if isinstance(r, dict)]
                if isinstance(data.get("result"), dict):  return [data["result"]]
                recs = []
                if qp.get("mcc") and qp.get("mnc"):
                    mm = data.get(qp["mcc"])
                    if isinstance(mm, dict) and isinstance(mm.get(qp["mnc"]), dict):
                        return [mm[qp["mnc"]]]
                for _mcc, m in data.items():
                    if isinstance(m, dict):
                        for _mnc, rec in m.items():
                            if isinstance(rec, dict): recs.append(rec)
                return recs
            elif isinstance(data, list):
                return [r for r in data if isinstance(r, dict)]
            return []

        s = self.api.session
        def try_get(qp):
            r = s.get(ENDPOINTS["mccmnc"], params=qp, timeout=30)
            if r.status_code != 200:
                try:
                    j = r.json()
                    err = j.get("message") or j.get("error") or j
                except Exception:
                    err = r.text[:400]
                raise requests.HTTPError(f"{r.status_code} – {err}")
            return _extract_records(r.json(), qp)

        try:
            res = try_get({"mcc": mcc, "mnc": mnc} if mcc else {})
            self._log(f"HTTP 200 – {len(res)} result(s)")
        except Exception as e:
            self._log(f"Primary request failed: {e}")
            res = []

        if not res and mcc and mnc:
            attempts = [{"mccmnc": f"{mcc}{mnc}"}]
            if mnc.isdigit():
                attempts += [{"mccmnc": f"{mcc}{mnc.zfill(2)}"}, {"mccmnc": f"{mcc}{mnc.zfill(3)}"}]
            for qp in attempts:
                try:
                    self._log(f"Retrying with {qp}")
                    res = try_get(qp)
                    self._log(f"HTTP 200 – {len(res)} result(s)")
                    if res:
                        break
                except Exception as e2:
                    self._log(f"Retry failed: {e2}")
        if not res:
            self._log("No results.")
            return

        self._raw_rows = []
        for r in res:
            country_name = r.get("countryName") or r.get("country") or ""
            country_code = r.get("countryCode") or r.get("cc") or ""
            country_display = f"{country_name} ({country_code})" if (country_name and country_code) else (country_name or country_code)
            row = {
                "country": country_display,
                "brand": r.get("brand",""),
                "operator": r.get("operator",""),
                "bands": r.get("bands",""),
                "notes": r.get("notes",""),
            }
            self._raw_rows.append(row)
            self.table.insert("", "end", values=(row["country"], row["brand"], row["operator"], row["bands"], row["notes"]))

    def export_csv(self):
        if not self._raw_rows:
            messagebox.showinfo("Export CSV", "No rows to export.")
            return
        p = filedialog.asksaveasfilename(title="Save Results CSV As", defaultextension=".csv", filetypes=[("CSV","*.csv")])
        if not p:
            return
        import csv
        with open(p, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["Country","Brand","Operator","Bands","Notes"])
            for r in self._raw_rows: w.writerow([r["country"], r["brand"], r["operator"], r["bands"], r["notes"]])
        messagebox.showinfo("Export CSV", f"CSV exported to {p}")

# ---------------------- App shell with left-side 'tabs' ----------------------

class LeftTabsApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1400x900")

        self.cred = CredentialManager()
        self.api = ApiClient(self.cred)

        menubar = tk.Menu(self)
        m_settings = tk.Menu(menubar, tearoff=0)
        m_settings.add_command(label="WiGLE Credentials…", command=self._ask_creds)
        menubar.add_cascade(label="Settings", menu=m_settings)
        self.config(menu=menubar)

        root = ttk.Frame(self); root.pack(fill="both", expand=True)
        root.columnconfigure(1, weight=1); root.rowconfigure(0, weight=1)

        self.btns = ttk.Frame(root); self.btns.grid(row=0, column=0, sticky="nsw")
        self.btns.columnconfigure(0, weight=1)

        self.content = ttk.Frame(root); self.content.grid(row=0, column=1, sticky="nsew")
        self.content.columnconfigure(0, weight=1); self.content.rowconfigure(0, weight=1)

        self.tabs = {
            "BT Basic":          lambda: BtBasicTab(self.content, self.api, self),
            "Wifi Basic":        lambda: WifiBasicTab(self.content, self.api, self),
            "Cell Basic":        lambda: CellBasicTab(self.content, self.api, self),
            "BT Detail":         lambda: BtDetailTab(self.content, self.api, self),
            "WiFi/Cell Detail":  lambda: WifiCellDetailTab(self.content, self.api, self),
            "MCC-MNC Lookup":    lambda: MccMncTab(self.content, self.api, self),
        }
        self.frames = {}
        self._current = None

        for i, (label, factory) in enumerate(self.tabs.items()):
            b = ttk.Button(self.btns, text=label, command=lambda L=label: self.show(L), width=18)
            b.grid(row=i, column=0, sticky="ew", padx=6, pady=(6 if i==0 else 3, 3))

        self.show("BT Basic")
        self.after(300, self._nudge_creds_if_empty)

    def _nudge_creds_if_empty(self):
        if not self.cred.ready():
            messagebox.showinfo("WiGLE Credentials", "Tip: set your WiGLE credentials (Settings → WiGLE Credentials…)")

    def _ask_creds(self):
        top = tk.Toplevel(self); top.title("WiGLE Credentials")
        frm = ttk.Frame(top, padding=12); frm.grid(row=0, column=0)
        ttk.Label(frm, text="WiGLE Username / API Name:").grid(row=0, column=0, sticky="e", padx=(0,8), pady=4)
        ttk.Label(frm, text="WiGLE API Token (password):").grid(row=1, column=0, sticky="e", padx=(0,8), pady=4)
        uvar = tk.StringVar(value=self.cred.user); pvar = tk.StringVar(value=self.cred.token)
        uent = ttk.Entry(frm, textvariable=uvar, width=40); uent.grid(row=0, column=1, sticky="w")
        pent = ttk.Entry(frm, textvariable=pvar, width=40, show="•"); pent.grid(row=1, column=1, sticky="w")
        def save_close():
            self.cred.save(uvar.get().strip(), pvar.get().strip())
            if self.api._session is not None:
                self.api._session.auth = (self.cred.user, self.cred.token)
            top.destroy()
        ttk.Button(frm, text="Save", command=save_close).grid(row=2, column=0, columnspan=2, pady=(12,0))
        top.grab_set(); self.wait_window(top)

    def show(self, label):
        if self._current is not None:
            self._current.pack_forget()
        if label not in self.frames:
            self.frames[label] = self.tabs[label]()
        f = self.frames[label]
        f.pack(fill="both", expand=True)
        self._current = f

if __name__ == "__main__":
    LeftTabsApp().mainloop()