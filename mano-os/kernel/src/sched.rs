use crate::lock::IrqGuardLock;

pub const MAX_TASKS: usize = 16;
pub const DEFAULT_QUANTUM_TICKS: u32 = 4; // 40 ms at 100 Hz PIT

#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum TaskPhase {
    Queued,
    Active,
    Yielded,
    Finished,
}

#[derive(Copy, Clone, Debug)]
pub struct TaskDescriptor {
    pub tid: u32,
    pub label: &'static str,
    pub phase: TaskPhase,
    pub ticks_consumed: u64,
    pub dispatch_count: u64,
    pub remaining_ticks: u32,
}

pub struct RoundRobinEngine {
    tasks: [Option<TaskDescriptor>; MAX_TASKS],
    ring: [usize; MAX_TASKS],
    head: usize,
    tail: usize,
    queued_len: usize,
    current_slot: Option<usize>,
    quantum_ticks: u32,
    slice_elapsed: u32,
    total_switches: u64,
    total_ticks: u64,
}

impl RoundRobinEngine {
    pub const fn new(quantum_ticks: u32) -> Self {
        Self {
            tasks: [None; MAX_TASKS],
            ring: [0; MAX_TASKS],
            head: 0,
            tail: 0,
            queued_len: 0,
            current_slot: None,
            quantum_ticks: if quantum_ticks == 0 { 1 } else { quantum_ticks },
            slice_elapsed: 0,
            total_switches: 0,
            total_ticks: 0,
        }
    }

    pub fn reset(&mut self, quantum_ticks: u32) {
        *self = Self::new(quantum_ticks);
    }

    pub fn enqueue_task(&mut self, tid: u32, label: &'static str, work_ticks: u32) -> bool {
        let Some(slot) = self.tasks.iter().position(|t| t.is_none()) else {
            return false;
        };
        self.tasks[slot] = Some(TaskDescriptor {
            tid,
            label,
            phase: TaskPhase::Queued,
            ticks_consumed: 0,
            dispatch_count: 0,
            remaining_ticks: work_ticks,
        });
        self.push_ring(slot);
        true
    }

    fn push_ring(&mut self, slot: usize) {
        if self.queued_len >= MAX_TASKS {
            return;
        }
        self.ring[self.tail] = slot;
        self.tail = (self.tail + 1) % MAX_TASKS;
        self.queued_len += 1;
    }

    fn pop_ring(&mut self) -> Option<usize> {
        if self.queued_len == 0 {
            return None;
        }
        let slot = self.ring[self.head];
        self.head = (self.head + 1) % MAX_TASKS;
        self.queued_len -= 1;
        Some(slot)
    }

    /// Advances the scheduler by one 10 ms PIT tick and returns the active TID.
    pub fn on_timer_tick(&mut self) -> Option<u32> {
        self.total_ticks += 1;

        if self.current_slot.is_none() {
            if let Some(next) = self.pop_ring() {
                self.current_slot = Some(next);
                self.slice_elapsed = 0;
                if let Some(t) = self.tasks[next].as_mut() {
                    t.phase = TaskPhase::Active;
                    t.dispatch_count += 1;
                }
            } else {
                return None;
            }
        }

        let slot = self.current_slot?;
        let active_tid;
        let finished;
        {
            let task = self.tasks[slot].as_mut()?;
            active_tid = task.tid;
            task.ticks_consumed += 1;
            self.slice_elapsed += 1;
            if task.remaining_ticks > 0 {
                task.remaining_ticks -= 1;
            }
            finished = task.remaining_ticks == 0;
            if finished {
                task.phase = TaskPhase::Finished;
            }
        }

        if finished {
            self.current_slot = None;
            self.slice_elapsed = 0;
            if let Some(next) = self.pop_ring() {
                self.current_slot = Some(next);
                self.total_switches += 1;
                if let Some(nt) = self.tasks[next].as_mut() {
                    nt.phase = TaskPhase::Active;
                    nt.dispatch_count += 1;
                }
            }
        } else if self.slice_elapsed >= self.quantum_ticks && self.queued_len > 0 {
            if let Some(cur) = self.tasks[slot].as_mut() {
                cur.phase = TaskPhase::Queued;
            }
            self.push_ring(slot);
            if let Some(next) = self.pop_ring() {
                self.current_slot = Some(next);
                self.slice_elapsed = 0;
                self.total_switches += 1;
                if let Some(nt) = self.tasks[next].as_mut() {
                    nt.phase = TaskPhase::Active;
                    nt.dispatch_count += 1;
                }
            }
        }

        Some(active_tid)
    }

    pub fn task_ticks(&self, tid: u32) -> u64 {
        self.tasks
            .iter()
            .flatten()
            .find(|t| t.tid == tid)
            .map(|t| t.ticks_consumed)
            .unwrap_or(0)
    }

    pub fn switches(&self) -> u64 {
        self.total_switches
    }

    pub fn ticks(&self) -> u64 {
        self.total_ticks
    }
}

pub static SCHEDULER: IrqGuardLock<RoundRobinEngine> =
    IrqGuardLock::new(RoundRobinEngine::new(DEFAULT_QUANTUM_TICKS));
