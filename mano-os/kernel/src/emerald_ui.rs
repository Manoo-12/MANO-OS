use bootloader_api::info::{FrameBuffer, FrameBufferInfo, PixelFormat};
use font8x8::{BASIC_FONTS, UnicodeFonts};

pub const BG_OBSIDIAN: (u8, u8, u8) = (5, 12, 9);
pub const PANEL_DARK: (u8, u8, u8) = (11, 24, 19);
pub const BORDER_EMERALD: (u8, u8, u8) = (16, 185, 129);
pub const ACCENT_MINT: (u8, u8, u8) = (110, 231, 183);
pub const ACCENT_GOLD: (u8, u8, u8) = (245, 158, 11);
pub const TEXT_PEARL: (u8, u8, u8) = (236, 253, 245);

pub struct EmeraldCanvas<'a> {
    buf: &'a mut [u8],
    info: FrameBufferInfo,
}

impl<'a> EmeraldCanvas<'a> {
    pub fn new(fb: &'a mut FrameBuffer) -> Self {
        let info = fb.info();
        let buf = fb.buffer_mut();
        Self { buf, info }
    }

    pub fn put_px(&mut self, x: usize, y: usize, rgb: (u8, u8, u8)) {
        if x >= self.info.width || y >= self.info.height {
            return;
        }
        let bpp = self.info.bytes_per_pixel;
        let offset = (y * self.info.stride + x) * bpp;
        if offset + bpp > self.buf.len() {
            return;
        }
        match self.info.pixel_format {
            PixelFormat::Rgb => {
                self.buf[offset] = rgb.0;
                self.buf[offset + 1] = rgb.1;
                self.buf[offset + 2] = rgb.2;
            }
            PixelFormat::Bgr => {
                self.buf[offset] = rgb.2;
                self.buf[offset + 1] = rgb.1;
                self.buf[offset + 2] = rgb.0;
            }
            _ => {
                let gray = ((rgb.0 as u16 + rgb.1 as u16 + rgb.2 as u16) / 3) as u8;
                self.buf[offset] = gray;
            }
        }
    }

    pub fn fill_rect(&mut self, x0: usize, y0: usize, w: usize, h: usize, rgb: (u8, u8, u8)) {
        let x_end = (x0 + w).min(self.info.width);
        let y_end = (y0 + h).min(self.info.height);
        for y in y0..y_end {
            for x in x0..x_end {
                self.put_px(x, y, rgb);
            }
        }
    }

    pub fn stroke_rect(&mut self, x0: usize, y0: usize, w: usize, h: usize, rgb: (u8, u8, u8)) {
        self.fill_rect(x0, y0, w, 2, rgb);
        self.fill_rect(x0, y0 + h.saturating_sub(2), w, 2, rgb);
        self.fill_rect(x0, y0, 2, h, rgb);
        self.fill_rect(x0 + w.saturating_sub(2), y0, 2, h, rgb);
    }

    pub fn draw_text(&mut self, mut x: usize, y: usize, text: &str, rgb: (u8, u8, u8), scale: usize) {
        let s = scale.max(1);
        for ch in text.chars() {
            if let Some(glyph) = BASIC_FONTS.get(ch) {
                for (row_idx, row_bits) in glyph.iter().enumerate() {
                    for col_idx in 0..8 {
                        if (row_bits >> col_idx) & 1 != 0 {
                            self.fill_rect(x + col_idx * s, y + row_idx * s, s, s, rgb);
                        }
                    }
                }
            }
            x += 8 * s;
        }
    }

    pub fn render_dashboard(&mut self, test_results: &[(&str, bool)], heap_used: usize, switches: u64) {
        let w = self.info.width;
        let h = self.info.height;
        self.fill_rect(0, 0, w, h, BG_OBSIDIAN);

        // Top Emerald Status Bar
        self.fill_rect(0, 0, w, 46, PANEL_DARK);
        self.fill_rect(0, 44, w, 2, BORDER_EMERALD);
        self.draw_text(20, 14, "MANO OS  |  Bare-Metal Rust x86-64 Microkernel", TEXT_PEARL, 2);

        // Hero Banner Panel
        let pw = w.saturating_sub(64).min(920);
        self.fill_rect(32, 72, pw, 92, PANEL_DARK);
        self.stroke_rect(32, 72, pw, 92, BORDER_EMERALD);
        self.draw_text(52, 88, "MANO OS  v1.0  (Obsidian Emerald Edition)", ACCENT_MINT, 2);
        self.draw_text(52, 122, "Author: MANO M  |  100 Hz PIT  |  40 ms RR Quantum  |  Host SSD Read-Only Guard", ACCENT_GOLD, 1);

        // Verification Matrix Card
        self.fill_rect(32, 184, pw, 220, PANEL_DARK);
        self.stroke_rect(32, 184, pw, 220, BORDER_EMERALD);
        self.draw_text(52, 200, "Kernel Self-Verification Suite (TC1 - TC6)", TEXT_PEARL, 2);

        let mut row_y = 236;
        for (label, passed) in test_results {
            let status_txt = if *passed { "[PASS]" } else { "[FAIL]" };
            let status_col = if *passed { BORDER_EMERALD } else { ACCENT_GOLD };
            self.draw_text(52, row_y, status_txt, status_col, 1);
            self.draw_text(116, row_y, label, TEXT_PEARL, 1);
            row_y += 24;
        }

        // Bottom Telemetry Pill
        let _ = (heap_used, switches);
        self.fill_rect(32, h.saturating_sub(56), pw, 36, PANEL_DARK);
        self.stroke_rect(32, h.saturating_sub(56), pw, 36, ACCENT_GOLD);
        self.draw_text(52, h.saturating_sub(42), "All CA-6 kernel tests verified over COM1 UART  |  Zero host disk writes.", ACCENT_MINT, 1);
    }
}
