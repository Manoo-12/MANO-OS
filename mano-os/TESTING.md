# MANO OS — Verification & Testing Guide

**Author:** MANO M  
**Hypervisor Policy:** Oracle VirtualBox (UEFI) — Zero QEMU  

---

## 1. Bare-Metal Rust Microkernel Verification (`TC1`–`TC6`)

On every boot, `mano_kernel` executes `self_test::run_all_tests()` and logs deterministic pass/fail telemetry to COM1 serial UART as well as the Obsidian-Emerald GOP dashboard:

| Test ID | Verification Target | Pass Criterion |
| :---: | :--- | :--- |
| **TC1** | 128 KB Bump Arena Heap Allocator | Allocates 64-element `Vec<u64>`, verifies `probe[12] == 144` and `used_bytes >= 512` |
| **TC2** | 2-Task Round-Robin Fairness (40 ms quantum) | Both tasks consume exact equal share (12 ticks each) with ≥ 5 preemptive switches |
| **TC3** | 4-Task Circular Ready Queue Rotation | All 4 tasks complete 8 ticks each in FIFO ring rotation without starvation |
| **TC4** | Boundary Test (`quantum = 1` tick) | Strict per-tick alternation trace `[10, 20, 10, 20, 10, 20, 10, 20, 10, 20]` |
| **TC5** | Stress Test (1,000 Locks + 1,000 Ticks) | 1,000 `IrqGuardLock` cycles + 1,000 RR ticks (≥ 490 switches) with zero deadlock |
| **TC6** | Host SSD Zero-Write Guard & Repeatability | Blocks internal SSD writes, allows portable USB target, 100% bit-identical repeat run |

---

## 2. Universal Hybrid Live OS Verification (Oracle VirtualBox UEFI)

Run `mano-os-hybrid/scripts/test_vbox_mano.ps1` to boot the exact FAT32 Microsoft-signed UEFI USB disk image (`mano_usb_test.img`) in Oracle VirtualBox (2 GB RAM, 2 vCPUs, UEFI firmware, NAT internet) and automatically capture 6 live verification screens:

1. `mano_01_desktop.png` — Clean Obsidian-Emerald desktop with Top Glass Bar, Centered Floating Dock, and procedural Aurora wallpaper.
2. `mano_02_snap_store.png` — Live **`MANO Snap Store`** showing `snapd ACTIVE` and live Canonical Snap catalog (`F6`).
3. `mano_03_wifi_panel.png` — Top-right **`MANO Wi-Fi Control Center`** backed by `NetworkManager` / `nmcli` (`F4`).
4. `mano_04_telemetry.png` — **`MANO System Telemetry`** showing Linux 6.1 LTS, RAM usage, universal Wi-Fi firmware status, `snapd` daemon, and PCI devices (`F5`).
5. `mano_05_google.png` — Sandboxed **Chromium** loading live `https://www.google.com` with zero `--no-sandbox` banner (`F3`).
6. `mano_06_youtube.png` — Sandboxed **Chromium** loading live `https://www.youtube.com`.
