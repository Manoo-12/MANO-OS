# MANO OS — System Architecture

**Project:** MANO OS v1.0 (*Obsidian Emerald Edition*)  
**Author:** MANO M (`USN: 25BTLCL004`, GitHub: `Manoo-12`)  
**Course:** Operating Systems (`25PCCS201`) — CA-6 Micro-OS Engineering Project  

---

## 1. Dual-Edition Architecture

MANO OS separates low-level bare-metal OS mechanism design from full portable laptop hardware usability via two clean, self-contained editions:

1. **Edition 1 — Bare-Metal Rust Microkernel (`mano-os/`)**
   - Freestanding `#![no_std]` x86-64 Rust kernel built with `bootloader 0.11` (dual UEFI + Legacy BIOS disk images).
   - Implements custom 64-bit GDT & TSS with dedicated IST0 double-fault stack (`gdt.rs`).
   - Implements 256-entry IDT, chained 8259 PIC (`vectors 32..47`), and 100 Hz PIT hardware timer (`idt.rs`).
   - Implements interrupt-masked spinlock synchronization (`IrqGuardLock<T>` in `lock.rs`) preventing ISR/task deadlocks.
   - Implements a deterministic 128 KB aligned `BumpArena` kernel heap allocator (`heap.rs`).
   - Implements a circular-ring preemptive Round-Robin scheduler (`RoundRobinEngine`, 40 ms / 4-tick quantum in `sched.rs`).
   - Renders an Obsidian-Emerald GOP framebuffer dashboard (`emerald_ui.rs`) and runs automated verification suite `TC1`–`TC6` (`self_test.rs`) over COM1 UART (`uart.rs`).

2. **Edition 2 — Universal Portable Live OS (`mano-os-hybrid/`)**
   - Boots directly from a FAT32 USB pendrive using Microsoft-signed UEFI Secure Boot (`shimx64.efi` → `grubx64.efi`) and standard hybrid ISO (`grub-mkrescue`) on both UEFI and Legacy BIOS laptops.
   - Uses signed Linux 6.1 LTS + universal Wi-Fi/GPU/audio firmware (`Realtek RTL8821CE`, `Intel iwlwifi`, `Qualcomm/Atheros`, `Broadcom`, `AMD`, `Intel SOF`).
   - Runs the custom **Obsidian & Emerald Green** GTK3 desktop environment (`mano_shell.py`): Top Frosted Glass Status Bar, Centered Floating App Dock, Top-Left App Drawer, Top-Right Live `nmcli` Wi-Fi Control Center, animated welcome splash, native GTK3 **`MANO Snap Store`** backed by real Canonical `snapd` (`mano_store.py`), live **`MANO System Telemetry`** (`mano_telemetry.py`), and fully sandboxed **Chromium** (Google & YouTube).
   - Runs strictly in read-only RAM Live mode (`boot=live`) — zero modifications to the host laptop's internal NVMe/SATA SSD.

---

## 2. Module Map (`mano-os/kernel/src/`)

| Module | Role | Key Mechanisms |
| :--- | :--- | :--- |
| `main.rs` | Kernel entry point | Bootloader handoff, init sequence, GOP dashboard, `sti`/`hlt` idle loop |
| `uart.rs` | Serial telemetry | COM1 (`0x3F8`) 115200-baud UART with interrupt-masked mutex |
| `gdt.rs` | Segmentation & TSS | 64-bit GDT (`CS`/`DS`/`TSS`), 20 KB IST0 Double-Fault stack |
| `idt.rs` | Interrupts & Timer | 256-entry IDT, 8259 PIC remapping, 100 Hz PIT (`0x43`/`0x40`) |
| `heap.rs` | Memory allocator | 128 KB atomic aligned `BumpArena` `#[global_allocator]` |
| `lock.rs` | Synchronization | `IrqGuardLock<T>` (`without_interrupts` + `spin::Mutex` + counter) |
| `sched.rs` | CPU Scheduler | `TaskDescriptor`, 16-slot circular `RunRing`, 40 ms RR preemption |
| `emerald_ui.rs` | Framebuffer UI | Obsidian-Emerald RGB/BGR GOP renderer (`font8x8`) |
| `self_test.rs` | Verification | Automated `TC1`–`TC6` suite + internal SSD zero-write guard policy |
