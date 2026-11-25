#![no_std]
#![no_main]
#![feature(abi_x86_interrupt)]

extern crate alloc;

mod emerald_ui;
mod gdt;
mod heap;
mod idt;
mod lock;
mod sched;
mod self_test;
mod uart;

use bootloader_api::{BootInfo, BootloaderConfig, entry_point};
use core::panic::PanicInfo;
use emerald_ui::EmeraldCanvas;
use heap::KERNEL_ARENA;

pub static BOOTLOADER_CONFIG: BootloaderConfig = {
    let mut cfg = BootloaderConfig::new_default();
    cfg.mappings.physical_memory = Some(bootloader_api::config::Mapping::Dynamic);
    cfg
};

entry_point!(mano_kernel_entry, config = &BOOTLOADER_CONFIG);

fn mano_kernel_entry(boot_info: &'static mut BootInfo) -> ! {
    uart::init_uart();
    uart_println!("\n=== MANO OS v1.0 (Obsidian Emerald) — Booting x86-64 Rust Microkernel ===");
    uart_println!("Author: MANO M | Mode: Freestanding #![no_std] | Host Disk: Read-Only Protected");

    gdt::init_gdt();
    uart_println!("[BOOT] GDT & TSS (IST0 Double-Fault Stack) loaded.");

    idt::init_interrupts();
    uart_println!("[BOOT] 256-entry IDT, 8259 PIC (32..47), and 100 Hz PIT initialized.");

    let summary = self_test::run_all_tests();

    // Seed live runtime scheduler with baseline system workers
    sched::SCHEDULER.with_lock(|eng| {
        eng.enqueue_task(1, "IdleMonitor", 10_000);
        eng.enqueue_task(2, "TelemetrySync", 10_000);
    });

    if let Some(fb) = boot_info.framebuffer.as_mut() {
        let mut canvas = EmeraldCanvas::new(fb);
        canvas.render_dashboard(&summary.cases, KERNEL_ARENA.used_bytes(), summary.total_switches);
        uart_println!("[GUI ] Rendered MANO OS Obsidian-Emerald GOP Dashboard.");
    }

    x86_64::instructions::interrupts::enable();
    uart_println!("[READY] MANO OS Microkernel running with hardware interrupts enabled.");

    loop {
        x86_64::instructions::hlt();
    }
}

#[panic_handler]
fn panic(info: &PanicInfo) -> ! {
    uart_println!("[MANO-PANIC] {}", info);
    loop {
        x86_64::instructions::hlt();
    }
}
