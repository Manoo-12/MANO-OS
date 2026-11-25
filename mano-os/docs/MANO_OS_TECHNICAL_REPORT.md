# MANO OS — Custom x86-64 Rust Microkernel & Universal Portable Live OS
## Technical Engineering Report (CA-6)

- **Operating System:** **MANO OS v1.0** (*Obsidian Emerald Edition*)
- **Author:** MANO M (`GitHub: Manoo-12`)
- **USN:** `25BTLCL004`
- **Course:** Operating Systems (`25PCCS201`) — CA-6 Engineering Project
- **GitHub Repository:** https://github.com/Manoo-12/MANO-OS
- **Hugging Face Release:** https://huggingface.co/datasets/Manoo-12/MANO-OS-Releases
- **Hypervisor:** Oracle VirtualBox (UEFI — Zero QEMU)

---

## 1. Abstract

**MANO OS** is a dual-edition x86-64 operating system project designed to demonstrate foundational operating-system mechanisms directly in freestanding `#![no_std]` Rust while also providing a plug-and-play portable Live USB operating system capable of real laptop Wi-Fi connectivity, modern TLS 1.3 web browsing, YouTube playback, and live Canonical Snap Store package management.

1. **Edition 1 (`mano-os/`)** implements a clean, compact bare-metal x86-64 Rust microkernel booting on both UEFI GOP and Legacy BIOS via `bootloader 0.11`. It provides a custom 64-bit GDT/TSS with a dedicated IST0 double-fault stack, 256-entry IDT, chained 8259 PIC, 100 Hz PIT hardware timer, interrupt-masked `IrqGuardLock<T>` spinlocks, a 128 KB atomic `BumpArena` heap allocator, a circular-ring preemptive Round-Robin scheduler (40 ms / 4-tick quantum), an Obsidian-Emerald GOP framebuffer dashboard, and automated `TC1`–`TC6` verification over COM1 UART.
2. **Edition 2 (`mano-os-hybrid/`)** delivers a universal portable FAT32 Live USB and hybrid UEFI+BIOS ISO powered by signed Linux 6.1 LTS, Microsoft-signed UEFI Secure Boot (`shimx64.efi` → `grubx64.efi`), universal Wi-Fi/GPU/audio firmware (`Realtek`, `Intel`, `Qualcomm/Atheros`, `Broadcom`), a custom **Obsidian & Emerald Green** GTK3 desktop environment (Top Frosted Glass Status Bar + Centered Floating App Dock + procedural Emerald Aurora wallpaper), a live `NetworkManager` (`nmcli`) Wi-Fi Control Center, sandboxed Chromium, and the native GTK3 **`MANO Snap Store`** backed by real Canonical `snapd`.

---

## 2. Core Operating-System Mechanisms Implemented (`mano-os/`)

| Subsystem | Source Module | Implementation Highlights |
| :--- | :--- | :--- |
| **Privilege & Fault Isolation** | `gdt.rs` | 64-bit GDT (`CS`, `DS`, `TSS`) with dedicated 20 KB `IST0` stack preventing triple faults on double fault |
| **Interrupts & Hardware Timer** | `idt.rs` | 256-entry IDT, 8259 PIC remapping (`vectors 32..47`), 100 Hz PIT timer (`divisor = 11932`) |
| **Synchronization** | `lock.rs` | `IrqGuardLock<T>` masking CPU interrupts around `spin::Mutex` with atomic acquisition counters |
| **Dynamic Memory Allocation** | `heap.rs` | 128 KB 16-byte-aligned lock-free `BumpArena` implementing Rust `GlobalAlloc` |
| **Preemptive Scheduling** | `sched.rs` | `RoundRobinEngine` with 16-slot FIFO `RunRing`, 40 ms (`4`-tick) quantum, per-task tick accounting |
| **Graphics & Telemetry** | `emerald_ui.rs`, `uart.rs` | Obsidian-Emerald GOP framebuffer renderer (`font8x8`) + 115200-baud COM1 serial logger |
| **Verification Suite** | `self_test.rs` | Automated `TC1`–`TC6` unit, fairness, boundary (`quantum=1`), 1,000-cycle stress, and host zero-write tests |

---

## 3. Universal Portable Live OS Architecture (`mano-os-hybrid/`)

- **Secure Boot Ready:** Uses Debian's Microsoft-signed `shimx64.efi.signed` + `grubx64.efi.signed` + `mmx64.efi` on FAT32 so laptops boot straight from USB even with UEFI Secure Boot enabled.
- **Zero Host Disk Modification:** Runs in read-only Live RAM mode (`boot=live components`) without touching internal NVMe/SATA drives.
- **Distinct Obsidian-Emerald Desktop (`mano_shell.py`):**
  - Top Frosted Glass Status Bar (`◆ MANO OS` menu, live centered clock pill, live Wi-Fi status pill, battery & power controls).
  - Centered Floating Bottom Glass App Dock with color-coded icon tiles (Browser, YouTube, Snap Store, Wi-Fi, Files, Terminal, Telemetry).
  - Animated fullscreen **MANO OS** welcome splash and custom procedural 1920×1080 Obsidian-Emerald Aurora wallpaper (`mano_wallpaper.py`).
- **Live Wi-Fi Control Center:** Backed directly by `NetworkManager` (`nmcli`), supporting wireless radio toggling, live SSID scanning, WPA2/WPA3 password authentication with show/hide toggle, disconnect, and forget.
- **Native Canonical Snap Store (`mano_store.py`):** Left-rail category navigation + live `snap find`, `snap install`, `snap list`, `snap remove`, and `/snap/bin` app launching powered by real `snapd`.
- **Live Telemetry (`mano_telemetry.py`):** Four KPI status cards (Kernel, Memory, Wi-Fi Firmware, Snapd) + live PCI, IP, and interface output.

---

## 4. Verification Summary

- **Bare-Metal Rust Microkernel (`mano-os/`):** Compiled cleanly with nightly Rust (`x86_64-unknown-none`), generating standalone bootable `mano-uefi.img` and `mano-bios.img` disk images with all 6 kernel self-tests (`TC1`–`TC6`) built in.
- **Universal Live OS (`mano-os-hybrid/`):** Booted end-to-end in **Oracle VirtualBox (UEFI)** from the exact FAT32 Microsoft-signed USB layout and visually verified across all 6 screens: Desktop, `MANO Snap Store` (`snapd ACTIVE`), `MANO Wi-Fi Control Center`, `MANO System Telemetry`, sandboxed Chromium on **Google**, and sandboxed Chromium on **YouTube**.
