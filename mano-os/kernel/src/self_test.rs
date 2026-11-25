extern crate alloc;

use alloc::vec::Vec;
use crate::heap::KERNEL_ARENA;
use crate::lock::IrqGuardLock;
use crate::sched::{DEFAULT_QUANTUM_TICKS, RoundRobinEngine};
use crate::uart_println;

/// Internal storage write-lock policy: refuses any write targeting host internal SSD.
pub fn host_write_allowed(is_internal_ssd: bool) -> bool {
    !is_internal_ssd
}

pub struct VerificationSummary {
    pub cases: [(&'static str, bool); 6],
    pub total_switches: u64,
}

pub fn run_all_tests() -> VerificationSummary {
    uart_println!("========================================================");
    uart_println!("  MANO OS Bare-Metal Kernel Verification Suite (TC1-TC6)");
    uart_println!("========================================================");

    // TC1: Heap Arena Allocation & Integrity
    let mut probe: Vec<u64> = Vec::with_capacity(64);
    for i in 0..64u64 {
        probe.push(i * i);
    }
    let tc1 = probe.len() == 64 && probe[12] == 144 && KERNEL_ARENA.used_bytes() >= 512;
    uart_println!("[TC1] Heap Arena Allocator (used={} B): {}", KERNEL_ARENA.used_bytes(), if tc1 { "PASS" } else { "FAIL" });

    // TC2: 2-Task Round-Robin Fairness (40 ms quantum = 4 ticks)
    let mut eng2 = RoundRobinEngine::new(DEFAULT_QUANTUM_TICKS);
    eng2.enqueue_task(1, "Worker-A", 12);
    eng2.enqueue_task(2, "Worker-B", 12);
    for _ in 0..24 {
        eng2.on_timer_tick();
    }
    let tc2 = eng2.task_ticks(1) == 12 && eng2.task_ticks(2) == 12 && eng2.switches() >= 5;
    uart_println!("[TC2] 2-Task RR Fairness (switches={}): {}", eng2.switches(), if tc2 { "PASS" } else { "FAIL" });

    // TC3: 4-Task Circular Ready Queue Rotation
    let mut eng4 = RoundRobinEngine::new(DEFAULT_QUANTUM_TICKS);
    for id in 1..=4 {
        eng4.enqueue_task(id, "Worker", 8);
    }
    for _ in 0..32 {
        eng4.on_timer_tick();
    }
    let tc3 = (1..=4).all(|id| eng4.task_ticks(id) == 8);
    uart_println!("[TC3] 4-Task Circular Rotation (switches={}): {}", eng4.switches(), if tc3 { "PASS" } else { "FAIL" });

    // TC4: Boundary Test — Minimum Quantum = 1 Tick
    let mut eng_q1 = RoundRobinEngine::new(1);
    eng_q1.enqueue_task(10, "Fast-A", 5);
    eng_q1.enqueue_task(20, "Fast-B", 5);
    let mut trace = [0u32; 10];
    for slot in trace.iter_mut() {
        *slot = eng_q1.on_timer_tick().unwrap_or(0);
    }
    let tc4 = trace == [10, 20, 10, 20, 10, 20, 10, 20, 10, 20];
    uart_println!("[TC4] Boundary Quantum=1 Preemption: {}", if tc4 { "PASS" } else { "FAIL" });

    // TC5: Stress Test — 1,000 Lock Acquisitions + 1,000 Scheduler Ticks
    let shared = IrqGuardLock::new(0u64);
    for _ in 0..1000 {
        shared.with_lock(|v| *v += 1);
    }
    let mut eng_stress = RoundRobinEngine::new(2);
    for id in 1..=4 {
        eng_stress.enqueue_task(id, "Stress", 250);
    }
    for _ in 0..1000 {
        eng_stress.on_timer_tick();
    }
    let tc5 = shared.lock_count() == 1000 && eng_stress.ticks() == 1000 && eng_stress.switches() >= 490;
    uart_println!(
        "[TC5] 1,000-Cycle Spinlock & Scheduler Stress (switches={}): {}",
        eng_stress.switches(),
        if tc5 { "PASS" } else { "FAIL" }
    );

    // TC6: Host Internal SSD Zero-Write Protection & Determinism
    let blocked_internal = !host_write_allowed(true);
    let allowed_usb = host_write_allowed(false);
    let mut det_a = RoundRobinEngine::new(4);
    let mut det_b = RoundRobinEngine::new(4);
    for id in 1..=3 {
        det_a.enqueue_task(id, "Det", 12);
        det_b.enqueue_task(id, "Det", 12);
    }
    let mut match_all = true;
    for _ in 0..36 {
        if det_a.on_timer_tick() != det_b.on_timer_tick() {
            match_all = false;
        }
    }
    let tc6 = blocked_internal && allowed_usb && match_all;
    uart_println!("[TC6] Host Zero-Write Guard & Deterministic Repeatability: {}", if tc6 { "PASS" } else { "FAIL" });

    let total_switches = eng2.switches() + eng4.switches() + eng_q1.switches() + eng_stress.switches();
    VerificationSummary {
        cases: [
            ("TC1: 128 KB Bump Arena Heap Allocator", tc1),
            ("TC2: 2-Task Preemptive Round-Robin (40 ms Quantum)", tc2),
            ("TC3: 4-Task Circular Ready Queue Fairness", tc3),
            ("TC4: Quantum=1 Strict Alternating Boundary", tc4),
            ("TC5: 1,000-Cycle IrqGuardLock & Scheduler Stress", tc5),
            ("TC6: Internal SSD Zero-Write Lock & Repeatability", tc6),
        ],
        total_switches,
    }
}
