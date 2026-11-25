use core::alloc::{GlobalAlloc, Layout};
use core::cell::UnsafeCell;
use core::ptr::null_mut;
use core::sync::atomic::{AtomicUsize, Ordering};

pub const ARENA_BYTES: usize = 128 * 1024;

#[repr(C, align(16))]
pub struct BumpArena {
    storage: UnsafeCell<[u8; ARENA_BYTES]>,
    cursor: AtomicUsize,
    allocations: AtomicUsize,
}

unsafe impl Sync for BumpArena {}

impl BumpArena {
    pub const fn new() -> Self {
        Self {
            storage: UnsafeCell::new([0; ARENA_BYTES]),
            cursor: AtomicUsize::new(0),
            allocations: AtomicUsize::new(0),
        }
    }

    pub fn used_bytes(&self) -> usize {
        self.cursor.load(Ordering::Relaxed)
    }

    pub fn allocation_count(&self) -> usize {
        self.allocations.load(Ordering::Relaxed)
    }
}

unsafe impl GlobalAlloc for BumpArena {
    unsafe fn alloc(&self, layout: Layout) -> *mut u8 {
        let align = layout.align().max(1);
        let size = layout.size();
        loop {
            let cur = self.cursor.load(Ordering::Relaxed);
            let aligned = (cur + align - 1) & !(align - 1);
            let next = match aligned.checked_add(size) {
                Some(n) if n <= ARENA_BYTES => n,
                _ => return null_mut(),
            };
            if self
                .cursor
                .compare_exchange_weak(cur, next, Ordering::SeqCst, Ordering::Relaxed)
                .is_ok()
            {
                self.allocations.fetch_add(1, Ordering::Relaxed);
                let base = self.storage.get() as *mut u8;
                return unsafe { base.add(aligned) };
            }
        }
    }

    unsafe fn dealloc(&self, _ptr: *mut u8, _layout: Layout) {
        // Monotonic educational bump arena (deterministic O(1) allocation).
    }
}

#[global_allocator]
pub static KERNEL_ARENA: BumpArena = BumpArena::new();
