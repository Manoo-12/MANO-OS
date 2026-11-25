#!/usr/bin/env python3
"""
MANO OS — Obsidian & Emerald Desktop Shell (GTK3)
Engineered by MANO M.

Distinct Architecture (macOS / GNOME Nebula Style):
- Full-width Top Frosted Glass Status Bar (Brand Menu, Live Clock Pill, Wi-Fi, Battery, Power)
- Centered Floating Bottom Glass App Dock with Custom Color-Coded Icon Tiles
- Top-Left MANO App Launcher Drawer
- Top-Right Live Wi-Fi Control Center backed directly by NetworkManager (nmcli)
- Animated Fullscreen MANO OS Welcome Splash
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib, Pango

import glob
import os
import signal
import subprocess
import threading
import time
from datetime import datetime


MANO_SHELL_CSS = b"""
window, .mano-surface {
    background-color: #060D0A;
    color: #ECFDF5;
    font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
}
button {
    background-image: none;
    box-shadow: none;
    text-shadow: none;
}

/* === Top Frosted Glass Bar === */
.topbar {
    background-color: #07120E;
    border-bottom: 1px solid #163D2F;
}
.brand-pill {
    background-color: #059669;
    border: 1px solid #34D399;
    border-radius: 14px;
    padding: 3px 13px;
    color: #FFFFFF;
    font-size: 12px;
    font-weight: 800;
}
.brand-pill:hover {
    background-color: #10B981;
}
.ws-pill {
    background-color: #0C1F18;
    border: 1px solid #184233;
    border-radius: 12px;
    padding: 3px 11px;
    color: #6EE7B7;
    font-size: 11px;
    font-weight: 600;
}
.clock-pill {
    background-color: #0C1E17;
    border: 1px solid #1A4837;
    border-radius: 14px;
    padding: 3px 16px;
    color: #ECFDF5;
    font-size: 12px;
    font-weight: 700;
}
.tray-pill {
    background-color: #0D1F18;
    border: 1px solid #1B4636;
    border-radius: 14px;
    padding: 3px 11px;
    color: #D1FAE5;
    font-size: 11px;
    font-weight: 700;
}
.tray-pill:hover {
    background-color: #133126;
    border-color: #10B981;
    color: #FFFFFF;
}
.power-pill {
    background-color: #1E1315;
    border: 1px solid #7F1D1D;
    border-radius: 14px;
    padding: 3px 10px;
    color: #FCA5A5;
    font-size: 12px;
    font-weight: 800;
}
.power-pill:hover {
    background-color: #991B1B;
    color: #FFFFFF;
}

/* === Centered Floating Bottom Dock === */
.dock-capsule {
    background-color: #081510;
    border: 1px solid #1D533F;
    border-radius: 18px;
    padding: 7px 14px;
}
.dock-item {
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 12px;
    padding: 4px 8px;
    color: #D1FAE5;
}
.dock-item:hover {
    background-color: #112A21;
    border-color: #10B981;
}
.dock-glyph {
    border-radius: 10px;
    padding: 6px 10px;
    font-size: 16px;
    font-weight: 800;
    color: #FFFFFF;
}
.tile-browser { background-color: #0284C7; border: 1px solid #38BDF8; }
.tile-youtube { background-color: #DC2626; border: 1px solid #F87171; }
.tile-store   { background-color: #D97706; border: 1px solid #FBBF24; }
.tile-wifi    { background-color: #059669; border: 1px solid #34D399; }
.tile-files   { background-color: #B45309; border: 1px solid #F59E0B; }
.tile-term    { background-color: #1E293B; border: 1px solid #34D399; }
.tile-telem   { background-color: #0F766E; border: 1px solid #2DD4BF; }
.dock-lbl {
    font-size: 10px;
    font-weight: 700;
    color: #A7F3D0;
}

/* === Drop-Down Glass Panels === */
.glass-panel {
    background-color: #091611;
    border: 1px solid #10B981;
    border-radius: 14px;
}
.panel-hdr {
    padding: 12px 16px 10px 16px;
    border-bottom: 1px solid #163A2D;
}
.panel-title {
    font-size: 15px;
    font-weight: 800;
    color: #ECFDF5;
}
.panel-sub {
    font-size: 11px;
    color: #6EE7B7;
}
.panel-footer {
    background-color: #060F0C;
    border-top: 1px solid #163A2D;
    padding: 10px 14px;
}
.wifi-row {
    background-color: #0D1E18;
    border: 1px solid #16382C;
    border-radius: 10px;
    padding: 10px 12px;
    margin: 4px 10px;
}
.wifi-row:hover {
    background-color: #132C23;
    border-color: #10B981;
}
.wifi-row-active {
    background-color: #0D2920;
    border: 1px solid #34D399;
    border-left: 4px solid #10B981;
    border-radius: 10px;
    padding: 11px 12px;
    margin: 4px 10px;
}
.ssid-lbl {
    font-size: 13px;
    font-weight: 700;
    color: #F0FDF4;
}
.meta-lbl {
    font-size: 11px;
    color: #6EE7B7;
}
.gold-lbl {
    font-size: 11px;
    font-weight: 700;
    color: #FBBF24;
}
.pw-entry {
    background-color: #050C09;
    color: #ECFDF5;
    border: 1px solid #1E4E3D;
    border-bottom: 2px solid #10B981;
    border-radius: 7px;
    padding: 6px 10px;
    font-size: 12px;
}
.btn-primary {
    background-color: #059669;
    color: #FFFFFF;
    border: 1px solid #34D399;
    border-radius: 8px;
    padding: 6px 14px;
    font-size: 12px;
    font-weight: 700;
}
.btn-primary:hover {
    background-color: #10B981;
}
.btn-ghost {
    background-color: #10241C;
    color: #D1FAE5;
    border: 1px solid #1D4939;
    border-radius: 8px;
    padding: 5px 12px;
    font-size: 11px;
    font-weight: 600;
}
.btn-ghost:hover {
    background-color: #17352A;
    color: #FFFFFF;
}
.drawer-tile {
    background-color: #0D1F18;
    border: 1px solid #183E30;
    border-radius: 12px;
    padding: 12px 10px;
    color: #ECFDF5;
    font-size: 12px;
    font-weight: 700;
}
.drawer-tile:hover {
    background-color: #123025;
    border-color: #10B981;
}

/* === Welcome Splash === */
.splash-bg {
    background-color: #040A08;
}
.splash-emblem {
    font-size: 56px;
    color: #10B981;
}
.splash-title {
    font-size: 44px;
    font-weight: 800;
    color: #ECFDF5;
}
.splash-tagline {
    font-size: 16px;
    font-weight: 600;
    color: #F59E0B;
}
.splash-sub {
    font-size: 12px;
    color: #6EE7B7;
}
progressbar trough {
    background-color: #0E221B;
    border: 1px solid #1C4A39;
    border-radius: 6px;
    min-height: 8px;
}
progressbar progress {
    background-color: #10B981;
    border-radius: 6px;
    min-height: 8px;
}
"""


def run_cmd(cmd, timeout=12):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:
        return 1, "", str(exc)


def spawn_app(cmd_list):
    try:
        subprocess.Popen(cmd_list, start_new_session=True)
    except Exception:
        pass


def get_screen_size():
    screen = Gdk.Screen.get_default()
    if screen:
        return screen.get_width(), screen.get_height()
    return 1280, 800


def read_battery_text():
    bats = sorted(glob.glob("/sys/class/power_supply/BAT*"))
    if not bats:
        return "⚡ AC"
    try:
        cap = open(os.path.join(bats[0], "capacity")).read().strip()
        st = open(os.path.join(bats[0], "status")).read().strip()
        icon = "⚡" if st in ("Charging", "Full") else "●"
        return f"{icon} {cap}%"
    except Exception:
        return "⚡ AC"


def read_active_network_summary():
    rc, out, _ = run_cmd(["nmcli", "-t", "-f", "TYPE,STATE,CONNECTION", "dev", "status"], timeout=4)
    if rc != 0:
        return "((•)) Wi-Fi", "Disconnected", None
    wifi_conn = None
    eth_conn = None
    has_wifi_hw = False
    for ln in out.splitlines():
        parts = ln.split(":")
        if len(parts) < 3:
            continue
        dev_type, state, conn = parts[0], parts[1], parts[2]
        if dev_type == "wifi":
            has_wifi_hw = True
            if state == "connected" and conn:
                wifi_conn = conn
        elif dev_type == "ethernet" and state == "connected" and conn:
            eth_conn = conn
    if wifi_conn:
        short = wifi_conn if len(wifi_conn) <= 16 else wifi_conn[:15] + "…"
        return f"((•)) {short}", f"Connected to Wi-Fi: {wifi_conn}", wifi_conn
    if eth_conn:
        return "◉ Wired", f"Connected (Ethernet: {eth_conn})", None
    if has_wifi_hw:
        return "((•)) Wi-Fi", "Wi-Fi Ready — Select a Network", None
    return "◉ Network", "No Wi-Fi Adapter Detected", None


def list_wifi_networks():
    rc, out, _ = run_cmd(
        ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY,BARS", "dev", "wifi", "list"],
        timeout=8,
    )
    if rc != 0:
        return []
    seen = {}
    for ln in out.splitlines():
        # Split safely from right since SSID may contain escaped colons
        parts = ln.replace("\\:", "::ESC::").split(":")
        if len(parts) < 5:
            continue
        in_use = parts[0].strip() == "*"
        ssid = parts[1].replace("::ESC::", ":").strip()
        if not ssid:
            continue
        try:
            sig = int(parts[2])
        except ValueError:
            sig = 0
        sec = parts[3].strip() or "Open"
        bars = parts[4].strip() or "▂▄▆"
        prev = seen.get(ssid)
        if prev is None or in_use or sig > prev["signal"]:
            seen[ssid] = {
                "ssid": ssid,
                "in_use": in_use or (prev["in_use"] if prev else False),
                "signal": max(sig, prev["signal"]) if prev else sig,
                "security": sec,
                "bars": bars,
            }
    return sorted(seen.values(), key=lambda x: (not x["in_use"], -x["signal"]))


class WelcomeSplash(Gtk.Window):
    def __init__(self, on_done):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.on_done = on_done
        self.set_decorated(False)
        self.set_keep_above(True)
        self.fullscreen()
        self.get_style_context().add_class("splash-bg")

        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        outer.set_halign(Gtk.Align.CENTER)
        outer.set_valign(Gtk.Align.CENTER)
        self.add(outer)

        emb = Gtk.Label(label="◆")
        emb.get_style_context().add_class("splash-emblem")
        outer.pack_start(emb, False, False, 0)

        title = Gtk.Label(label="MANO OS")
        title.get_style_context().add_class("splash-title")
        outer.pack_start(title, False, False, 0)

        tag = Gtk.Label(label="Crafted by MANO M.  •  Obsidian Emerald Edition")
        tag.get_style_context().add_class("splash-tagline")
        outer.pack_start(tag, False, False, 0)

        self.pbar = Gtk.ProgressBar()
        self.pbar.set_size_request(360, 10)
        self.pbar.set_margin_top(16)
        outer.pack_start(self.pbar, False, False, 0)

        self.stage_lbl = Gtk.Label(label="Starting Linux 6.1 LTS • Universal Wi-Fi • Canonical snapd...")
        self.stage_lbl.get_style_context().add_class("splash-sub")
        outer.pack_start(self.stage_lbl, False, False, 4)

        self.connect("button-press-event", lambda *_: self.finish())
        self.step = 0
        self.done_flag = False
        self.show_all()
        GLib.timeout_add(75, self._tick)

    def _tick(self):
        if self.done_flag:
            return False
        self.step += 1
        frac = min(1.0, self.step / 30.0)
        self.pbar.set_fraction(frac)
        if self.step == 10:
            self.stage_lbl.set_text("Initializing NetworkManager & Realtek/Intel/Atheros Wi-Fi...")
        elif self.step == 20:
            self.stage_lbl.set_text("Launching MANO Emerald Desktop & Snap Store...")
        if self.step >= 32:
            self.finish()
            return False
        return True

    def finish(self):
        if self.done_flag:
            return
        self.done_flag = True
        self.hide()
        self.destroy()
        if self.on_done:
            self.on_done()


class WifiControlCenter(Gtk.Window):
    def __init__(self, on_status_changed):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.on_status_changed = on_status_changed
        self.set_title("MANO Wi-Fi Control Center")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_size_request(380, 500)

        self.selected_ssid = None
        self.networks = []
        self.connecting = False

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.get_style_context().add_class("glass-panel")
        self.add(box)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        hdr.get_style_context().add_class("panel-hdr")
        hleft = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        htitle = Gtk.Label(label="((•)) MANO Wi-Fi Control Center")
        htitle.set_xalign(0.0)
        htitle.get_style_context().add_class("panel-title")
        self.status_sub = Gtk.Label(label="Scanning nearby wireless networks...")
        self.status_sub.set_xalign(0.0)
        self.status_sub.get_style_context().add_class("panel-sub")
        hleft.pack_start(htitle, False, False, 0)
        hleft.pack_start(self.status_sub, False, False, 0)
        hdr.pack_start(hleft, True, True, 0)

        self.radio_switch = Gtk.Switch()
        self.radio_switch.set_valign(Gtk.Align.CENTER)
        self.radio_switch.set_active(True)
        self.radio_switch.connect("state-set", self.on_toggle_radio)
        hdr.pack_end(self.radio_switch, False, False, 0)
        box.pack_start(hdr, False, False, 0)

        # Action toolbar
        act = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        act.set_margin_top(8)
        act.set_margin_bottom(6)
        act.set_margin_start(12)
        act.set_margin_end(12)
        rescan_btn = Gtk.Button(label="↻ Rescan Wi-Fi")
        rescan_btn.get_style_context().add_class("btn-ghost")
        rescan_btn.connect("clicked", lambda *_: self.refresh_async(rescan=True))
        act.pack_start(rescan_btn, False, False, 0)

        close_btn = Gtk.Button(label="✕ Close")
        close_btn.get_style_context().add_class("btn-ghost")
        close_btn.connect("clicked", lambda *_: self.hide())
        act.pack_end(close_btn, False, False, 0)
        box.pack_start(act, False, False, 0)

        # Message banner
        self.msg_lbl = Gtk.Label(label="")
        self.msg_lbl.set_xalign(0.0)
        self.msg_lbl.set_line_wrap(True)
        self.msg_lbl.set_margin_start(14)
        self.msg_lbl.set_margin_end(14)
        self.msg_lbl.get_style_context().add_class("gold-lbl")
        box.pack_start(self.msg_lbl, False, False, 2)

        # Scrollable networks list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_vexpand(True)
        self.list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        scroll.add(self.list_box)
        box.pack_start(scroll, True, True, 0)

        # Footer
        ftr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ftr.get_style_context().add_class("panel-footer")
        self.ip_lbl = Gtk.Label(label="NetworkManager (nmcli) • Live Hardware")
        self.ip_lbl.set_xalign(0.0)
        self.ip_lbl.get_style_context().add_class("meta-lbl")
        ftr.pack_start(self.ip_lbl, True, True, 0)
        box.pack_end(ftr, False, False, 0)

        self.connect("key-press-event", self._on_key)

    def _on_key(self, _w, ev):
        if ev.keyval == Gdk.KEY_Escape:
            self.hide()
            return True
        return False

    def toggle(self):
        if self.get_visible():
            self.hide()
        else:
            sw, _ = get_screen_size()
            self.move(max(10, sw - 392), 44)
            self.show_all()
            self.present()
            self.refresh_async(rescan=True)

    def on_toggle_radio(self, _sw, state):
        mode = "on" if state else "off"
        threading.Thread(target=lambda: (run_cmd(["nmcli", "radio", "wifi", mode]), self.refresh_async(rescan=state)), daemon=True).start()
        return False

    def refresh_async(self, rescan=False):
        def worker():
            if rescan:
                run_cmd(["nmcli", "dev", "wifi", "rescan"], timeout=8)
            _, summary, _ = read_active_network_summary()
            nets = list_wifi_networks()
            _, ip_out, _ = run_cmd(["hostname", "-I"], timeout=3)
            ip_short = ip_out.split()[0] if ip_out else "No IP"
            GLib.idle_add(self._apply_refresh, summary, nets, ip_short)

        threading.Thread(target=worker, daemon=True).start()

    def _apply_refresh(self, summary, nets, ip_short):
        self.status_sub.set_text(summary)
        self.ip_lbl.set_text(f"IP: {ip_short}  •  NetworkManager Active")
        self.networks = nets
        self._render_list()
        if self.on_status_changed:
            self.on_status_changed()

    def _render_list(self):
        for c in self.list_box.get_children():
            self.list_box.remove(c)

        if not self.networks:
            info = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            info.get_style_context().add_class("wifi-row")
            l1 = Gtk.Label(label="No wireless access points visible right now")
            l1.set_xalign(0.0)
            l1.get_style_context().add_class("ssid-lbl")
            l2 = Gtk.Label(
                label=(
                    "• On a physical laptop: Realtek, Intel, Qualcomm & Broadcom Wi-Fi\n"
                    "  networks appear automatically here — click any SSID to enter password.\n"
                    "• Inside Oracle VirtualBox: NAT Ethernet is active for Google, YouTube & Snap Store."
                )
            )
            l2.set_xalign(0.0)
            l2.set_line_wrap(True)
            l2.get_style_context().add_class("meta-lbl")
            info.pack_start(l1, False, False, 0)
            info.pack_start(l2, False, False, 0)
            self.list_box.pack_start(info, False, False, 4)
            self.list_box.show_all()
            return

        for net in self.networks:
            ssid = net["ssid"]
            is_sel = (self.selected_ssid == ssid)
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
            card.get_style_context().add_class("wifi-row-active" if (net["in_use"] or is_sel) else "wifi-row")

            top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            btn_area = Gtk.Button()
            btn_area.set_relief(Gtk.ReliefStyle.NONE)
            lbl_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            t1 = Gtk.Label(label=f"{'✓ ' if net['in_use'] else ''}{ssid}")
            t1.set_xalign(0.0)
            t1.get_style_context().add_class("ssid-lbl")
            sec_str = "Secured" if net["security"] != "Open" else "Open"
            t2 = Gtk.Label(label=f"{net['bars']}  {net['signal']}%  •  {sec_str}" + ("  •  Connected" if net["in_use"] else ""))
            t2.set_xalign(0.0)
            t2.get_style_context().add_class("meta-lbl")
            lbl_box.pack_start(t1, False, False, 0)
            lbl_box.pack_start(t2, False, False, 0)
            btn_area.add(lbl_box)
            btn_area.connect("clicked", self.on_select_ssid, ssid)
            top.pack_start(btn_area, True, True, 0)
            card.pack_start(top, False, False, 0)

            if is_sel:
                if net["in_use"]:
                    row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
                    dbtn = Gtk.Button(label="Disconnect")
                    dbtn.get_style_context().add_class("btn-ghost")
                    dbtn.connect("clicked", self.on_disconnect, ssid)
                    fbtn = Gtk.Button(label="Forget")
                    fbtn.get_style_context().add_class("btn-ghost")
                    fbtn.connect("clicked", self.on_forget, ssid)
                    row.pack_start(dbtn, False, False, 0)
                    row.pack_start(fbtn, False, False, 0)
                    card.pack_start(row, False, False, 2)
                else:
                    pw_entry = None
                    if net["security"] != "Open":
                        pw_entry = Gtk.Entry()
                        pw_entry.set_visibility(False)
                        pw_entry.set_placeholder_text("Enter Wi-Fi password...")
                        pw_entry.get_style_context().add_class("pw-entry")
                        pw_entry.connect("activate", lambda *_, s=ssid, e=pw_entry: self.on_connect(s, e.get_text()))
                        card.pack_start(pw_entry, False, False, 2)

                        chk = Gtk.CheckButton(label="Show password")
                        chk.connect("toggled", lambda b, e=pw_entry: e.set_visibility(b.get_active()))
                        card.pack_start(chk, False, False, 0)

                    cbtn = Gtk.Button(label="Connect")
                    cbtn.get_style_context().add_class("btn-primary")
                    cbtn.connect("clicked", lambda *_, s=ssid, e=pw_entry: self.on_connect(s, e.get_text() if e else ""))
                    card.pack_start(cbtn, False, False, 2)

            self.list_box.pack_start(card, False, False, 0)

        self.list_box.show_all()

    def on_select_ssid(self, _btn, ssid):
        self.selected_ssid = None if self.selected_ssid == ssid else ssid
        self._render_list()

    def on_connect(self, ssid, password):
        if self.connecting:
            return
        self.connecting = True
        self.msg_lbl.set_text(f"Connecting to '{ssid}'...")

        def worker():
            cmd = ["nmcli", "dev", "wifi", "connect", ssid]
            if password:
                cmd += ["password", password]
            rc, out, err = run_cmd(cmd, timeout=25)
            self.connecting = False
            if rc == 0:
                GLib.idle_add(self.msg_lbl.set_text, f"✓ Connected to {ssid}!")
                self.selected_ssid = None
            else:
                reason = (err or out or "Authentication failed").splitlines()[-1]
                GLib.idle_add(self.msg_lbl.set_text, f"✗ {reason}")
            self.refresh_async(rescan=False)

        threading.Thread(target=worker, daemon=True).start()

    def on_disconnect(self, _btn, ssid):
        def worker():
            run_cmd(["nmcli", "con", "down", ssid], timeout=10)
            GLib.idle_add(self.msg_lbl.set_text, f"Disconnected from {ssid}")
            self.refresh_async(rescan=False)
        threading.Thread(target=worker, daemon=True).start()

    def on_forget(self, _btn, ssid):
        def worker():
            run_cmd(["nmcli", "con", "delete", ssid], timeout=10)
            GLib.idle_add(self.msg_lbl.set_text, f"Forgot saved network '{ssid}'")
            self.refresh_async(rescan=False)
        threading.Thread(target=worker, daemon=True).start()


class AppDrawer(Gtk.Window):
    def __init__(self, wifi_panel):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.wifi_panel = wifi_panel
        self.set_title("MANO OS App Drawer")
        self.set_decorated(False)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.set_resizable(False)
        self.set_size_request(360, 410)

        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        box.get_style_context().add_class("glass-panel")
        self.add(box)

        hdr = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        hdr.get_style_context().add_class("panel-hdr")
        t1 = Gtk.Label(label="◆ MANO OS  •  Applications")
        t1.set_xalign(0.0)
        t1.get_style_context().add_class("panel-title")
        t2 = Gtk.Label(label="Engineered by MANO M  •  Obsidian Emerald Live")
        t2.set_xalign(0.0)
        t2.get_style_context().add_class("panel-sub")
        hdr.pack_start(t1, False, False, 0)
        hdr.pack_start(t2, False, False, 0)
        box.pack_start(hdr, False, False, 0)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(10)
        grid.set_margin_top(14)
        grid.set_margin_bottom(14)
        grid.set_margin_start(14)
        grid.set_margin_end(14)
        grid.set_column_homogeneous(True)

        apps = [
            ("◎ Chromium Web", lambda: spawn_app(["chromium", "--no-first-run", "https://www.google.com"])),
            ("▶ YouTube", lambda: spawn_app(["chromium", "--no-first-run", "https://www.youtube.com"])),
            ("⊞ MANO Snap Store", lambda: spawn_app(["python3", "/opt/mano/mano_store.py"])),
            ("((•)) Wi-Fi Control", lambda: self.wifi_panel.toggle()),
            ("☰ File Manager", lambda: spawn_app(["pcmanfm"])),
            (">_ Terminal", lambda: spawn_app(["lxterminal"])),
            ("⚡ System Telemetry", lambda: spawn_app(["python3", "/opt/mano/mano_telemetry.py"])),
            ("★ Offline Dino", lambda: spawn_app(["chromium", "--no-first-run", "chrome://dino"])),
        ]
        for idx, (label, action) in enumerate(apps):
            b = Gtk.Button(label=label)
            b.get_style_context().add_class("drawer-tile")
            b.connect("clicked", lambda *_, fn=action: (self.hide(), fn()))
            grid.attach(b, idx % 2, idx // 2, 1, 1)

        box.pack_start(grid, True, True, 0)

        ftr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        ftr.get_style_context().add_class("panel-footer")
        rb = Gtk.Button(label="↻ Reboot")
        rb.get_style_context().add_class("btn-ghost")
        rb.connect("clicked", lambda *_: spawn_app(["sudo", "reboot"]))
        po = Gtk.Button(label="PWR Off")
        po.get_style_context().add_class("power-pill")
        po.connect("clicked", lambda *_: spawn_app(["sudo", "poweroff"]))
        ftr.pack_start(rb, False, False, 0)
        ftr.pack_end(po, False, False, 0)
        box.pack_end(ftr, False, False, 0)

        self.connect("key-press-event", lambda _w, ev: (self.hide(), True)[1] if ev.keyval == Gdk.KEY_Escape else False)

    def toggle(self):
        if self.get_visible():
            self.hide()
        else:
            self.move(10, 44)
            self.show_all()
            self.present()


class TopStatusBar(Gtk.Window):
    def __init__(self, drawer, wifi_panel):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.drawer = drawer
        self.wifi_panel = wifi_panel
        self.set_title("MANO Top Bar")
        self.set_decorated(False)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.stick()

        sw, _ = get_screen_size()
        self.set_default_size(sw, 38)
        self.set_size_request(sw, 38)
        self.move(0, 0)

        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bar.set_margin_start(10)
        bar.set_margin_end(10)
        bar.set_margin_top(4)
        bar.set_margin_bottom(4)
        bar.get_style_context().add_class("topbar")
        self.add(bar)

        # Left: MANO OS Brand Menu + Workspace badge
        brand_btn = Gtk.Button(label="◆ MANO OS")
        brand_btn.get_style_context().add_class("brand-pill")
        brand_btn.connect("clicked", lambda *_: self.drawer.toggle())
        bar.pack_start(brand_btn, False, False, 0)

        ws_lbl = Gtk.Label(label="Emerald Live  •  MANO M")
        ws_lbl.get_style_context().add_class("ws-pill")
        bar.pack_start(ws_lbl, False, False, 2)

        # Center: Live Date & Clock Pill
        self.clock_lbl = Gtk.Label(label="")
        self.clock_lbl.get_style_context().add_class("clock-pill")
        bar.set_center_widget(self.clock_lbl)

        # Right: Power + Battery + Live Wi-Fi Pill
        pwr_btn = Gtk.Button(label="PWR")
        pwr_btn.set_tooltip_text("Power / Reboot Menu")
        pwr_btn.get_style_context().add_class("power-pill")
        pwr_btn.connect("clicked", lambda *_: self.drawer.toggle())
        bar.pack_end(pwr_btn, False, False, 0)

        self.bat_lbl = Gtk.Label(label=read_battery_text())
        self.bat_lbl.get_style_context().add_class("tray-pill")
        bar.pack_end(self.bat_lbl, False, False, 0)

        self.wifi_btn = Gtk.Button(label="((•)) Wi-Fi")
        self.wifi_btn.get_style_context().add_class("tray-pill")
        self.wifi_btn.connect("clicked", lambda *_: self.wifi_panel.toggle())
        bar.pack_end(self.wifi_btn, False, False, 0)

        self.connect("realize", self._reserve_top_strut)
        self.update_clock()
        self.update_status()
        GLib.timeout_add_seconds(5, self.update_clock)
        GLib.timeout_add_seconds(6, self.update_status)

    def _reserve_top_strut(self, *_):
        try:
            win = self.get_window()
            sw, _ = get_screen_size()
            if win:
                Gdk.property_change(
                    win,
                    Gdk.Atom.intern("_NET_WM_STRUT_PARTIAL", False),
                    Gdk.Atom.intern("CARDINAL", False),
                    32,
                    Gdk.PropMode.REPLACE,
                    [0, 0, 38, 0, 0, 0, 0, 0, 0, sw - 1, 0, 0],
                )
        except Exception:
            pass

    def update_clock(self):
        self.clock_lbl.set_text(datetime.now().strftime("%a, %b %d  •  %I:%M %p"))
        return True

    def update_status(self):
        def worker():
            pill, _, _ = read_active_network_summary()
            bat = read_battery_text()
            GLib.idle_add(self.wifi_btn.set_label, pill)
            GLib.idle_add(self.bat_lbl.set_text, bat)
        threading.Thread(target=worker, daemon=True).start()
        return True


class FloatingDock(Gtk.Window):
    def __init__(self, wifi_panel, drawer):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.set_title("MANO Floating Dock")
        self.set_decorated(False)
        self.set_type_hint(Gdk.WindowTypeHint.DOCK)
        self.set_keep_above(True)
        self.set_skip_taskbar_hint(True)
        self.stick()

        capsule = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        capsule.get_style_context().add_class("dock-capsule")
        self.add(capsule)

        dock_items = [
            ("◎", "Browser", "tile-browser", lambda: spawn_app(["chromium", "--no-first-run", "https://www.google.com"])),
            ("▶", "YouTube", "tile-youtube", lambda: spawn_app(["chromium", "--no-first-run", "https://www.youtube.com"])),
            ("⊞", "Snap Store", "tile-store", lambda: spawn_app(["python3", "/opt/mano/mano_store.py"])),
            ("((•))", "Wi-Fi", "tile-wifi", lambda: wifi_panel.toggle()),
            ("☰", "Files", "tile-files", lambda: spawn_app(["pcmanfm"])),
            (">_", "Terminal", "tile-term", lambda: spawn_app(["lxterminal"])),
            ("⚡", "Telemetry", "tile-telem", lambda: spawn_app(["python3", "/opt/mano/mano_telemetry.py"])),
        ]

        for glyph, name, tile_cls, action in dock_items:
            btn = Gtk.Button()
            btn.get_style_context().add_class("dock-item")
            col = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            ico = Gtk.Label(label=glyph)
            ico.set_size_request(44, 34)
            ico.get_style_context().add_class("dock-glyph")
            ico.get_style_context().add_class(tile_cls)
            lbl = Gtk.Label(label=name)
            lbl.get_style_context().add_class("dock-lbl")
            col.pack_start(ico, False, False, 0)
            col.pack_start(lbl, False, False, 0)
            btn.add(col)
            btn.connect("clicked", lambda *_, fn=action: fn())
            capsule.pack_start(btn, False, False, 0)

        self._last_pos = None
        self.connect("size-allocate", self._center_bottom)

    def _center_bottom(self, _w, alloc):
        sw, sh = get_screen_size()
        x = max(0, (sw - alloc.width) // 2)
        y = max(44, sh - alloc.height - 14)
        if self._last_pos != (x, y):
            self._last_pos = (x, y)
            self.move(x, y)


def main():
    prov = Gtk.CssProvider()
    prov.load_from_data(MANO_SHELL_CSS)
    Gtk.StyleContext.add_provider_for_screen(
        Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )

    topbar_ref = [None]
    wifi_panel = WifiControlCenter(lambda: topbar_ref[0].update_status() if topbar_ref[0] else None)
    drawer = AppDrawer(wifi_panel)
    topbar = TopStatusBar(drawer, wifi_panel)
    topbar_ref[0] = topbar
    dock = FloatingDock(wifi_panel, drawer)

    # Allow Openbox hotkeys (F4 Wi-Fi, F7 App Drawer) via POSIX signals
    signal.signal(signal.SIGUSR1, lambda *_: GLib.idle_add(wifi_panel.toggle))
    signal.signal(signal.SIGUSR2, lambda *_: GLib.idle_add(drawer.toggle))
    with open("/tmp/mano_shell.pid", "w") as f:
        f.write(str(os.getpid()))

    def show_desktop():
        topbar.show_all()
        dock.show_all()

    WelcomeSplash(on_done=show_desktop)
    Gtk.main()


if __name__ == "__main__":
    main()
