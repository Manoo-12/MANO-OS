use crate::gdt::DOUBLE_FAULT_IST_IDX;
use crate::uart_println;
use core::sync::atomic::{AtomicU64, Ordering};
use pic8259::ChainedPics;
use spin::{Lazy, Mutex};
use x86_64::instructions::port::Port;
use x86_64::structures::idt::{InterruptDescriptorTable, InterruptStackFrame, PageFaultErrorCode};

pub const PIC_1_OFFSET: u8 = 32;
pub const PIC_2_OFFSET: u8 = PIC_1_OFFSET + 8;

#[derive(Debug, Clone, Copy)]
#[repr(u8)]
pub enum IrqVector {
    Timer = PIC_1_OFFSET,
    Keyboard = PIC_1_OFFSET + 1,
}

pub static PICS: Mutex<ChainedPics> =
    Mutex::new(unsafe { ChainedPics::new(PIC_1_OFFSET, PIC_2_OFFSET) });

pub static PIT_TICKS: AtomicU64 = AtomicU64::new(0);

static IDT: Lazy<InterruptDescriptorTable> = Lazy::new(|| {
    let mut idt = InterruptDescriptorTable::new();
    idt.breakpoint.set_handler_fn(breakpoint_handler);
    unsafe {
        idt.double_fault
            .set_handler_fn(double_fault_handler)
            .set_stack_index(DOUBLE_FAULT_IST_IDX);
    }
    idt.page_fault.set_handler_fn(page_fault_handler);
    idt[IrqVector::Timer as u8].set_handler_fn(timer_irq_handler);
    idt[IrqVector::Keyboard as u8].set_handler_fn(keyboard_irq_handler);
    idt
});

pub fn init_interrupts() {
    IDT.load();
    unsafe {
        PICS.lock().initialize();
        // Program 8253/8254 PIT Channel 0 to ~100 Hz (1193182 / 11932)
        let divisor: u16 = 11932;
        Port::<u8>::new(0x43).write(0x36);
        Port::<u8>::new(0x40).write((divisor & 0xFF) as u8);
        Port::<u8>::new(0x40).write((divisor >> 8) as u8);
    }
}

extern "x86-interrupt" fn breakpoint_handler(frame: InterruptStackFrame) {
    uart_println!("[MANO-IRQ] Breakpoint @ {:#x}", frame.instruction_pointer.as_u64());
}

extern "x86-interrupt" fn double_fault_handler(frame: InterruptStackFrame, code: u64) -> ! {
    uart_println!("[MANO-FAULT] DOUBLE FAULT (code={}) @ {:#?}", code, frame);
    loop {
        x86_64::instructions::hlt();
    }
}

extern "x86-interrupt" fn page_fault_handler(
    frame: InterruptStackFrame,
    error_code: PageFaultErrorCode,
) {
    uart_println!("[MANO-FAULT] PAGE FAULT ({:?}) @ {:#?}", error_code, frame);
    loop {
        x86_64::instructions::hlt();
    }
}

extern "x86-interrupt" fn timer_irq_handler(_frame: InterruptStackFrame) {
    PIT_TICKS.fetch_add(1, Ordering::Relaxed);
    unsafe {
        PICS.lock().notify_end_of_interrupt(IrqVector::Timer as u8);
    }
}

extern "x86-interrupt" fn keyboard_irq_handler(_frame: InterruptStackFrame) {
    unsafe {
        let _scancode: u8 = Port::<u8>::new(0x60).read();
        PICS.lock().notify_end_of_interrupt(IrqVector::Keyboard as u8);
    }
}
