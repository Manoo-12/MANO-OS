use core::sync::atomic::{AtomicU64, Ordering};
use spin::Mutex;
use x86_64::instructions::interrupts;

/// Interrupt-masked spinlock preventing ISR-vs-task deadlock on single-core x86-64.
pub struct IrqGuardLock<T> {
    inner: Mutex<T>,
    acquisitions: AtomicU64,
}

impl<T> IrqGuardLock<T> {
    pub const fn new(value: T) -> Self {
        Self {
            inner: Mutex::new(value),
            acquisitions: AtomicU64::new(0),
        }
    }

    pub fn with_lock<R>(&self, f: impl FnOnce(&mut T) -> R) -> R {
        interrupts::without_interrupts(|| {
            let mut guard = self.inner.lock();
            self.acquisitions.fetch_add(1, Ordering::Relaxed);
            f(&mut guard)
        })
    }

    pub fn lock_count(&self) -> u64 {
        self.acquisitions.load(Ordering::Relaxed)
    }
}
