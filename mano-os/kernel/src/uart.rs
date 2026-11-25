use core::fmt;
use spin::Mutex;
use x86_64::instructions::interrupts;
use x86_64::instructions::port::Port;

const COM1_BASE: u16 = 0x3F8;

pub struct UartPort {
    base: u16,
    ready: bool,
}

impl UartPort {
    const fn new(base: u16) -> Self {
        Self { base, ready: false }
    }

    pub fn init(&mut self) {
        if self.ready {
            return;
        }
        unsafe {
            Port::<u8>::new(self.base + 1).write(0x00);
            Port::<u8>::new(self.base + 3).write(0x80);
            Port::<u8>::new(self.base).write(0x03);
            Port::<u8>::new(self.base + 1).write(0x00);
            Port::<u8>::new(self.base + 3).write(0x03);
            Port::<u8>::new(self.base + 2).write(0xC7);
            Port::<u8>::new(self.base + 4).write(0x0B);
        }
        self.ready = true;
    }

    fn write_byte(&mut self, byte: u8) {
        if !self.ready {
            self.init();
        }
        unsafe {
            let mut lsr = Port::<u8>::new(self.base + 5);
            let mut spins = 0u32;
            while (lsr.read() & 0x20) == 0 && spins < 10_000 {
                spins += 1;
                core::hint::spin_loop();
            }
            Port::<u8>::new(self.base).write(byte);
        }
    }
}

impl fmt::Write for UartPort {
    fn write_str(&mut self, s: &str) -> fmt::Result {
        for b in s.bytes() {
            if b == b'\n' {
                self.write_byte(b'\r');
            }
            self.write_byte(b);
        }
        Ok(())
    }
}

pub static COM1: Mutex<UartPort> = Mutex::new(UartPort::new(COM1_BASE));

pub fn init_uart() {
    interrupts::without_interrupts(|| {
        COM1.lock().init();
    });
}

#[doc(hidden)]
pub fn _emit(args: fmt::Arguments<'_>) {
    use fmt::Write;
    interrupts::without_interrupts(|| {
        let mut guard = COM1.lock();
        let _ = guard.write_fmt(args);
    });
}

#[macro_export]
macro_rules! uart_print {
    ($($arg:tt)*) => {
        $crate::uart::_emit(format_args!($($arg)*))
    };
}

#[macro_export]
macro_rules! uart_println {
    () => {
        $crate::uart_print!("\n")
    };
    ($($arg:tt)*) => {
        $crate::uart_print!("{}\n", format_args!($($arg)*))
    };
}
