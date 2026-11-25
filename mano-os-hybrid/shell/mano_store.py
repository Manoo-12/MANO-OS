#!/usr/bin/env python3
"""
MANO OS — Native Obsidian-Emerald Graphical Snap Store (GTK3)
Engineered by MANO M.
Backed directly by real Canonical snapd (snap find, snap install, snap list, snap remove).
Distinct layout: Left Vertical Category Rail + Emerald Accent Header + Rich Package Cards + Live Console Drawer.
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import os
import subprocess
import threading


MANO_STORE_CSS = b"""
window, .mano-store-root {
    background-color: #060C0A;
    color: #ECFDF5;
    font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
}
button {
    background-image: none;
    box-shadow: none;
    text-shadow: none;
}
.top-banner {
    background-color: #091511;
    border-bottom: 1px solid #15382B;
    padding: 14px 18px;
}
.brand-title {
    font-size: 19px;
    font-weight: 800;
    color: #ECFDF5;
}
.brand-sub {
    font-size: 11px;
    color: #6EE7B7;
}
.pill-online {
    background-color: #064E3B;
    color: #34D399;
    border: 1px solid #10B981;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}
.pill-offline {
    background-color: #451A03;
    color: #FBBF24;
    border: 1px solid #F59E0B;
    border-radius: 14px;
    padding: 4px 12px;
    font-size: 11px;
    font-weight: 700;
}
.rail-box {
    background-color: #08120E;
    border-right: 1px solid #143328;
    padding: 12px 10px;
}
.rail-hdr {
    font-size: 10px;
    font-weight: 700;
    color: #6EE7B7;
    padding: 4px 8px 6px 8px;
}
.rail-btn {
    background-color: transparent;
    color: #A7F3D0;
    border: 1px solid transparent;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 12px;
    font-weight: 600;
}
.rail-btn:hover {
    background-color: #0F261E;
    color: #FFFFFF;
}
.rail-btn-active {
    background-color: #065F46;
    border-color: #10B981;
    color: #FFFFFF;
    font-weight: 700;
}
.search-bar {
    background-color: #0D1E18;
    color: #ECFDF5;
    border: 1px solid #1E4638;
    border-bottom: 2px solid #10B981;
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 13px;
}
.pkg-card {
    background-color: #0C1A15;
    border: 1px solid #17362B;
    border-radius: 10px;
    padding: 12px 14px;
    margin: 4px 12px;
}
.pkg-card:hover {
    background-color: #10241D;
    border-color: #10B981;
}
.pkg-title {
    font-size: 14px;
    font-weight: 700;
    color: #F0FDF4;
}
.pkg-meta {
    font-size: 11px;
    font-weight: 600;
    color: #34D399;
}
.pkg-summary {
    font-size: 12px;
    color: #A7F3D0;
}
.btn-emerald {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #10B981;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
}
.btn-emerald:hover {
    background-color: #10B981;
}
.btn-gold {
    background-color: #B45309;
    color: #FFFBEB;
    border: 1px solid #F59E0B;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
}
.btn-gold:hover {
    background-color: #D97706;
}
.btn-danger {
    background-color: #7F1D1D;
    color: #FEE2E2;
    border: 1px solid #EF4444;
    border-radius: 8px;
    padding: 6px 12px;
    font-size: 12px;
    font-weight: 700;
}
.btn-danger:hover {
    background-color: #991B1B;
}
.log-strip {
    background-color: #040907;
    border-top: 1px solid #15382B;
    padding: 8px 14px;
}
.log-mono {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 11px;
    color: #6EE7B7;
}
"""


CATEGORIES = [
    ("Featured", "editor"),
    ("Installed", "__installed__"),
    ("Browsers", "browser"),
    ("Developer", "code"),
    ("Media", "vlc"),
    ("Utilities", "calculator"),
    ("Games", "game"),
]

CURATED_FALLBACK = [
    ("hello-world", "6.4", "canonical*", "Canonical verification snap package"),
    ("vlc", "3.0.20", "videolan*", "Cross-platform multimedia player & streamer"),
    ("code", "stable", "vscode*", "Visual Studio Code editor (classic snap)"),
    ("firefox", "latest", "mozilla*", "Mozilla Firefox web browser"),
    ("gimp", "2.10", "snapcrafters", "GNU Image Manipulation Program"),
    ("htop", "3.3.0", "maxiberta", "Interactive terminal process & CPU viewer"),
    ("spotify", "latest", "spotify*", "Music and podcast streaming client"),
    ("telegram-desktop", "latest", "telegram*", "Fast cross-platform messaging client"),
]


def run_cmd(cmd, timeout=18):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def parse_snap_table(raw):
    rows = []
    lines = [ln for ln in raw.splitlines() if ln.strip()]
    if len(lines) <= 1:
        return rows
    for ln in lines[1:]:
        parts = ln.split(None, 4)
        if len(parts) >= 4:
            name = parts[0]
            ver = parts[1]
            pub = parts[2]
            summary = parts[4] if len(parts) >= 5 else (parts[3] if parts[3] != "-" else "Snap package")
            rows.append((name, ver, pub, summary))
    return rows


def get_installed_snaps():
    rc, out, _ = run_cmd(["snap", "list"], timeout=8)
    if rc != 0:
        return {}
    found = {}
    for ln in out.splitlines()[1:]:
        parts = ln.split()
        if len(parts) >= 2:
            found[parts[0]] = parts[1]
    return found


class ManoSnapStore(Gtk.Window):
    def __init__(self):
        super().__init__(title="MANO OS — Snap Store (Canonical snapd)")
        self.set_default_size(940, 620)
        self.set_position(Gtk.WindowPosition.CENTER)

        prov = Gtk.CssProvider()
        prov.load_from_data(MANO_STORE_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.installed = {}
        self.active_cat = "Featured"
        self.rail_buttons = {}
        self.busy = False

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        outer.get_style_context().add_class("mano-store-root")
        self.add(outer)

        # --- Top Brand Banner ---
        banner = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        banner.get_style_context().add_class("top-banner")
        outer.pack_start(banner, False, False, 0)

        tbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        t_lbl = Gtk.Label(label="◆ MANO Snap Store")
        t_lbl.set_xalign(0.0)
        t_lbl.get_style_context().add_class("brand-title")
        s_lbl = Gtk.Label(label="MANO OS Official Package Hub  •  Powered by Live Canonical snapd")
        s_lbl.set_xalign(0.0)
        s_lbl.get_style_context().add_class("brand-sub")
        tbox.pack_start(t_lbl, False, False, 0)
        tbox.pack_start(s_lbl, False, False, 0)
        banner.pack_start(tbox, True, True, 0)

        self.daemon_pill = Gtk.Label(label="● Checking snapd...")
        self.daemon_pill.get_style_context().add_class("pill-offline")
        banner.pack_end(self.daemon_pill, False, False, 0)

        refresh_btn = Gtk.Button(label="↻ Refresh")
        refresh_btn.get_style_context().add_class("btn-emerald")
        refresh_btn.connect("clicked", lambda *_: self.reload_current())
        banner.pack_end(refresh_btn, False, False, 0)

        # --- Body Split: Left Category Rail + Main Catalog ---
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        outer.pack_start(body, True, True, 0)

        rail = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        rail.set_size_request(185, -1)
        rail.get_style_context().add_class("rail-box")
        body.pack_start(rail, False, False, 0)

        rhdr = Gtk.Label(label="COLLECTIONS")
        rhdr.set_xalign(0.0)
        rhdr.get_style_context().add_class("rail-hdr")
        rail.pack_start(rhdr, False, False, 0)

        for label, query in CATEGORIES:
            b = Gtk.Button(label=label)
            b.set_halign(Gtk.Align.FILL)
            b.get_style_context().add_class("rail-btn")
            if label == self.active_cat:
                b.get_style_context().add_class("rail-btn-active")
            b.connect("clicked", self.on_select_category, label, query)
            rail.pack_start(b, False, False, 0)
            self.rail_buttons[label] = (b, query)

        # Main right pane
        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right.set_margin_top(12)
        right.set_margin_bottom(8)
        body.pack_start(right, True, True, 0)

        # Search row
        srow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        srow.set_margin_start(12)
        srow.set_margin_end(12)
        self.search_entry = Gtk.Entry()
        self.search_entry.set_placeholder_text("Search live Canonical Snap Store (e.g. vlc, firefox, htop, code, gimp)...")
        self.search_entry.get_style_context().add_class("search-bar")
        self.search_entry.connect("activate", self.on_search)
        srow.pack_start(self.search_entry, True, True, 0)

        sbtn = Gtk.Button(label="Search")
        sbtn.get_style_context().add_class("btn-emerald")
        sbtn.connect("clicked", self.on_search)
        srow.pack_start(sbtn, False, False, 0)
        right.pack_start(srow, False, False, 0)

        # Section status label
        self.count_lbl = Gtk.Label(label="Loading live Canonical Snap catalog...")
        self.count_lbl.set_xalign(0.0)
        self.count_lbl.set_margin_start(14)
        self.count_lbl.get_style_context().add_class("brand-sub")
        right.pack_start(self.count_lbl, False, False, 0)

        # Scrollable cards
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.cards_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        scroll.add(self.cards_box)
        right.pack_start(scroll, True, True, 0)

        # Bottom status log strip
        log_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        log_bar.get_style_context().add_class("log-strip")
        self.log_lbl = Gtk.Label(label="MANO Snap Store ready • Real Canonical snapd backend")
        self.log_lbl.set_xalign(0.0)
        self.log_lbl.set_ellipsize(3)
        self.log_lbl.get_style_context().add_class("log-mono")
        log_bar.pack_start(self.log_lbl, True, True, 0)
        outer.pack_end(log_bar, False, False, 0)

        self.connect("destroy", Gtk.main_quit)
        self.show_all()

        GLib.idle_add(self.bootstrap_store)

    def set_log(self, text):
        GLib.idle_add(self.log_lbl.set_text, text)

    def bootstrap_store(self):
        threading.Thread(target=self._check_daemon_and_load, daemon=True).start()
        return False

    def _check_daemon_and_load(self):
        rc, out, _ = run_cmd(["snap", "version"], timeout=6)
        snapd_ver = "unknown"
        active = False
        if rc == 0:
            for ln in out.splitlines():
                if ln.startswith("snapd"):
                    parts = ln.split()
                    if len(parts) >= 2 and parts[1] != "unavailable":
                        snapd_ver = parts[1]
                        active = True
        if not active:
            run_cmd(["sudo", "systemctl", "start", "snapd.socket", "snapd.service"], timeout=10)
            rc, out, _ = run_cmd(["snap", "version"], timeout=6)
            for ln in out.splitlines():
                if ln.startswith("snapd"):
                    parts = ln.split()
                    if len(parts) >= 2 and parts[1] != "unavailable":
                        snapd_ver = parts[1]
                        active = True

        def update_pill():
            ctx = self.daemon_pill.get_style_context()
            ctx.remove_class("pill-online")
            ctx.remove_class("pill-offline")
            if active:
                ctx.add_class("pill-online")
                self.daemon_pill.set_text(f"● snapd ACTIVE  v{snapd_ver}")
            else:
                ctx.add_class("pill-offline")
                self.daemon_pill.set_text("● snapd STARTING...")

        GLib.idle_add(update_pill)
        self._load_query("editor", "Featured")

    def on_select_category(self, _btn, label, query):
        self.active_cat = label
        for name, (b, _) in self.rail_buttons.items():
            ctx = b.get_style_context()
            if name == label:
                ctx.add_class("rail-btn-active")
            else:
                ctx.remove_class("rail-btn-active")
        self.search_entry.set_text("")
        threading.Thread(target=self._load_query, args=(query, label), daemon=True).start()

    def on_search(self, *_):
        q = self.search_entry.get_text().strip()
        if not q:
            self.reload_current()
            return
        threading.Thread(target=self._load_query, args=(q, f"Search: {q}"), daemon=True).start()

    def reload_current(self):
        _, query = self.rail_buttons.get(self.active_cat, (None, "editor"))
        q = self.search_entry.get_text().strip() or query
        title = f"Search: {q}" if self.search_entry.get_text().strip() else self.active_cat
        threading.Thread(target=self._load_query, args=(q, title), daemon=True).start()

    def _load_query(self, query, title):
        self.set_log(f"Querying Canonical Snap Store for '{title}'...")
        self.installed = get_installed_snaps()

        if query == "__installed__":
            rows = [(k, v, "installed", "Installed on this live MANO OS session") for k, v in sorted(self.installed.items())]
            status = f"Installed Snaps ({len(rows)} packages)"
        else:
            rc, out, err = run_cmd(["snap", "find", query], timeout=18)
            rows = parse_snap_table(out) if rc == 0 else []
            if rows:
                rows = rows[:24]
                status = f"{title} — {len(rows)} live packages from Canonical Snap Store"
            else:
                rows = CURATED_FALLBACK
                status = f"{title} — Offline curated catalog (connect Wi-Fi for live search)"

        GLib.idle_add(self._render_cards, rows, status)
        self.set_log(f"Ready • {status}")

    def _render_cards(self, rows, status):
        self.count_lbl.set_text(status)
        for child in self.cards_box.get_children():
            self.cards_box.remove(child)

        if not rows:
            empty = Gtk.Label(label="No packages installed yet. Pick a category or search above to install live snaps.")
            empty.set_margin_top(30)
            empty.get_style_context().add_class("pkg-summary")
            self.cards_box.pack_start(empty, False, False, 0)
            self.cards_box.show_all()
            return

        for name, ver, pub, summary in rows:
            card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            card.get_style_context().add_class("pkg-card")

            left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
            hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            nlbl = Gtk.Label(label=name)
            nlbl.set_xalign(0.0)
            nlbl.get_style_context().add_class("pkg-title")
            mlbl = Gtk.Label(label=f"v{ver}  •  {pub}")
            mlbl.set_xalign(0.0)
            mlbl.get_style_context().add_class("pkg-meta")
            hdr.pack_start(nlbl, False, False, 0)
            hdr.pack_start(mlbl, False, False, 0)

            dlbl = Gtk.Label(label=summary)
            dlbl.set_xalign(0.0)
            dlbl.set_line_wrap(True)
            dlbl.get_style_context().add_class("pkg-summary")

            left.pack_start(hdr, False, False, 0)
            left.pack_start(dlbl, False, False, 0)
            card.pack_start(left, True, True, 0)

            actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            actions.set_valign(Gtk.Align.CENTER)
            if name in self.installed:
                lbtn = Gtk.Button(label="▶ Launch")
                lbtn.get_style_context().add_class("btn-gold")
                lbtn.connect("clicked", self.on_launch_snap, name)
                rbtn = Gtk.Button(label="Remove")
                rbtn.get_style_context().add_class("btn-danger")
                rbtn.connect("clicked", self.on_remove_snap, name)
                actions.pack_start(lbtn, False, False, 0)
                actions.pack_start(rbtn, False, False, 0)
            else:
                ibtn = Gtk.Button(label="↓ Install")
                ibtn.get_style_context().add_class("btn-emerald")
                ibtn.connect("clicked", self.on_install_snap, name)
                actions.pack_start(ibtn, False, False, 0)

            card.pack_end(actions, False, False, 0)
            self.cards_box.pack_start(card, False, False, 0)

        self.cards_box.show_all()

    def on_install_snap(self, btn, name):
        if self.busy:
            return
        self.busy = True
        btn.set_sensitive(False)
        btn.set_label("Installing...")

        def worker():
            self.set_log(f"Running: sudo snap install {name} ...")
            rc, out, err = run_cmd(["sudo", "snap", "install", name], timeout=240)
            if rc != 0 and "--classic" in (err + out):
                self.set_log(f"Retrying with --classic: sudo snap install {name} --classic ...")
                rc, out, err = run_cmd(["sudo", "snap", "install", name, "--classic"], timeout=240)
            self.busy = False
            if rc == 0:
                self.set_log(f"✓ Installed '{name}' successfully via Canonical snapd!")
            else:
                msg = (err or out or "install failed").splitlines()[-1]
                self.set_log(f"✗ Failed installing '{name}': {msg}")
            self.reload_current()

        threading.Thread(target=worker, daemon=True).start()

    def on_remove_snap(self, btn, name):
        if self.busy:
            return
        self.busy = True
        btn.set_sensitive(False)
        btn.set_label("Removing...")

        def worker():
            self.set_log(f"Removing snap '{name}'...")
            rc, out, err = run_cmd(["sudo", "snap", "remove", name], timeout=120)
            self.busy = False
            if rc == 0:
                self.set_log(f"✓ Removed '{name}'.")
            else:
                self.set_log(f"✗ Could not remove '{name}': {(err or out)}")
            self.reload_current()

        threading.Thread(target=worker, daemon=True).start()

    def on_launch_snap(self, _btn, name):
        bin_path = f"/snap/bin/{name}"
        if os.path.exists(bin_path):
            subprocess.Popen([bin_path], start_new_session=True)
            self.set_log(f"Launched {bin_path}")
        else:
            subprocess.Popen(["lxterminal", "-e", f"bash -lc 'snap run {name}; echo; read -p \"Press Enter...\"'"], start_new_session=True)
            self.set_log(f"Launched snap run {name} in terminal")


if __name__ == "__main__":
    ManoSnapStore()
    Gtk.main()
