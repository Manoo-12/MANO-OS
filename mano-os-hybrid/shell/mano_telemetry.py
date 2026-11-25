#!/usr/bin/env python3
"""
MANO OS — Obsidian & Emerald Live System Telemetry Dashboard (GTK3)
Engineered by MANO M.
Distinct card-grid dashboard showing live kernel, RAM, Wi-Fi drivers/firmware,
NetworkManager state, snapd daemon, and PCI hardware.
"""

import gi
gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
from gi.repository import Gtk, Gdk, GLib

import os
import subprocess


TELEM_CSS = b"""
window, .telem-root {
    background-color: #060C0A;
    color: #ECFDF5;
    font-family: "DejaVu Sans", "Liberation Sans", sans-serif;
}
.telem-hdr {
    font-size: 18px;
    font-weight: 800;
    color: #34D399;
}
.telem-sub {
    font-size: 11px;
    color: #A7F3D0;
}
.kpi-card {
    background-color: #0C1A15;
    border: 1px solid #163A2D;
    border-top: 3px solid #10B981;
    border-radius: 10px;
    padding: 10px 14px;
}
.kpi-card-gold {
    background-color: #0C1A15;
    border: 1px solid #3B2F12;
    border-top: 3px solid #F59E0B;
    border-radius: 10px;
    padding: 10px 14px;
}
.kpi-label {
    font-size: 10px;
    font-weight: 700;
    color: #6EE7B7;
}
.kpi-val {
    font-size: 14px;
    font-weight: 800;
    color: #FFFFFF;
}
.detail-card {
    background-color: #0A1511;
    border: 1px solid #15382B;
    border-radius: 10px;
    padding: 12px 14px;
}
.mono-out {
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 11px;
    color: #D1FAE5;
}
"""


def run_out(cmd):
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT, timeout=4).strip()
    except Exception as exc:
        return f"(unavailable: {exc})"


class ManoTelemetry(Gtk.Window):
    def __init__(self):
        super().__init__(title="MANO OS — Live System Telemetry")
        self.set_default_size(740, 520)
        self.set_position(Gtk.WindowPosition.CENTER)

        prov = Gtk.CssProvider()
        prov.load_from_data(TELEM_CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), prov, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)
        root.get_style_context().add_class("telem-root")
        self.add(root)

        hdr = Gtk.Label(label="◆ MANO OS  •  Hardware & Kernel Telemetry")
        hdr.set_xalign(0.0)
        hdr.get_style_context().add_class("telem-hdr")
        root.pack_start(hdr, False, False, 0)

        sub = Gtk.Label(label="Engineered by MANO M  •  Live Read-Only RAM Session (Internal Disk Protected)")
        sub.set_xalign(0.0)
        sub.get_style_context().add_class("telem-sub")
        root.pack_start(sub, False, False, 0)

        # 4 KPI summary cards row
        kpi_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        kpi_row.set_homogeneous(True)
        self.kpi_kernel = self._make_kpi(kpi_row, "KERNEL", "...", False)
        self.kpi_ram = self._make_kpi(kpi_row, "MEMORY USED", "...", False)
        self.kpi_fw = self._make_kpi(kpi_row, "WI-FI FIRMWARE", "...", True)
        self.kpi_snap = self._make_kpi(kpi_row, "SNAP STORE", "...", True)
        root.pack_start(kpi_row, False, False, 0)

        # Live details scroll box
        scroll = Gtk.ScrolledWindow()
        scroll.set_vexpand(True)
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        card.get_style_context().add_class("detail-card")
        self.details_lbl = Gtk.Label()
        self.details_lbl.set_xalign(0.0)
        self.details_lbl.set_yalign(0.0)
        self.details_lbl.set_selectable(True)
        self.details_lbl.get_style_context().add_class("mono-out")
        card.pack_start(self.details_lbl, True, True, 0)
        scroll.add(card)
        root.pack_start(scroll, True, True, 0)

        self.connect("destroy", Gtk.main_quit)
        self.refresh()
        GLib.timeout_add_seconds(3, self.refresh)
        self.show_all()

    def _make_kpi(self, parent, title, initial, gold=False):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.get_style_context().add_class("kpi-card-gold" if gold else "kpi-card")
        tl = Gtk.Label(label=title)
        tl.set_xalign(0.0)
        tl.get_style_context().add_class("kpi-label")
        vl = Gtk.Label(label=initial)
        vl.set_xalign(0.0)
        vl.get_style_context().add_class("kpi-val")
        box.pack_start(tl, False, False, 0)
        box.pack_start(vl, False, False, 0)
        parent.pack_start(box, True, True, 0)
        return vl

    def refresh(self):
        uname = run_out(["uname", "-r"])
        mem_full = run_out(["free", "-h"])
        ram_short = "N/A"
        for ln in mem_full.splitlines():
            if ln.startswith("Mem:"):
                p = ln.split()
                if len(p) >= 3:
                    ram_short = f"{p[2]} / {p[1]}"

        fw_rtl = os.path.exists("/lib/firmware/rtw88/rtw8821c_fw.bin")
        fw_iwl = any(f.startswith("iwlwifi") for f in os.listdir("/lib/firmware")) if os.path.isdir("/lib/firmware") else False
        fw_txt = "Universal OK" if (fw_rtl and fw_iwl) else ("RTL8821CE OK" if fw_rtl else "Check FW")

        snap_state = run_out(["systemctl", "is-active", "snapd.socket"])
        nm = run_out(["nmcli", "dev", "status"])
        ip = run_out(["ip", "-br", "addr"])
        pci = run_out(["bash", "-c", "lspci | grep -iE 'network|wireless|ethernet|realtek|intel|vga|audio' || true"])
        host = run_out(["hostname"])

        self.kpi_kernel.set_text(f"Linux {uname.split('-')[0]}")
        self.kpi_ram.set_text(ram_short)
        self.kpi_fw.set_text(fw_txt)
        self.kpi_snap.set_text("ACTIVE" if snap_state == "active" else snap_state.upper())

        details = (
            f"OS / Hostname   : MANO OS 1.0  ({host})\n"
            f"Kernel Release  : {uname}\n"
            f"Wi-Fi Firmware  : Realtek RTL8821CE [{'PRESENT' if fw_rtl else 'MISSING'}] • Intel iwlwifi [{'PRESENT' if fw_iwl else 'MISSING'}]\n"
            f"Snapd Daemon    : {snap_state}\n\n"
            f"=== MEMORY ===\n{mem_full}\n\n"
            f"=== NETWORK INTERFACES (NetworkManager) ===\n{nm}\n\n"
            f"=== ACTIVE IP ADDRESSES ===\n{ip}\n\n"
            f"=== DETECTED PCI HARDWARE ===\n{pci}\n"
        )
        self.details_lbl.set_text(details)
        return True


if __name__ == "__main__":
    ManoTelemetry()
    Gtk.main()
