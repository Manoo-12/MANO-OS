#!/usr/bin/env python3
"""
MANO OS — Procedural 1920x1080 Obsidian & Emerald Aurora Wallpaper Generator
Generates a crisp, original dark-obsidian + emerald aurora + gold accent wallpaper
with subtle hexagonal telemetry geometry and MANO OS corner signature.
"""
import math
import struct
import sys
import zlib


def clamp(v, lo=0, hi=255):
    return lo if v < lo else (hi if v > hi else int(v))


def generate_wallpaper(out_path, width=1920, height=1080):
    # Render at 960x540 then upscale 2x bilinearly for ultra-fast smooth gradients
    rw, rh = width // 2, height // 2
    buf = bytearray(rw * rh * 3)

    # Precompute aurora ribbon curves across x
    c1 = [0.0] * rw
    c2 = [0.0] * rw
    c3 = [0.0] * rw
    for x in range(rw):
        nx = x / float(rw)
        c1[x] = 0.52 + 0.16 * math.sin(nx * 5.2 + 0.4) + 0.06 * math.cos(nx * 11.0 - 0.8)
        c2[x] = 0.40 + 0.14 * math.cos(nx * 4.4 - 0.7) + 0.05 * math.sin(nx * 9.5 + 1.2)
        c3[x] = 0.68 + 0.10 * math.sin(nx * 3.6 + 2.1) - 0.04 * math.cos(nx * 8.2)

    idx = 0
    for y in range(rh):
        ny = y / float(rh)
        # Base vertical obsidian gradient (#040907 -> #091511 -> #050C09)
        base_r = 4.0 + 5.0 * (1.0 - abs(ny - 0.45) * 1.4)
        base_g = 10.0 + 14.0 * (1.0 - abs(ny - 0.45) * 1.2)
        base_b = 8.0 + 11.0 * (1.0 - abs(ny - 0.45) * 1.2)

        for x in range(rw):
            nx = x / float(rw)

            # Diagonal deep emerald nebula glow
            dx1 = nx - 0.25
            dy1 = ny - 0.35
            neb1 = math.exp(-(dx1 * dx1 * 5.5 + dy1 * dy1 * 7.5))

            dx2 = nx - 0.78
            dy2 = ny - 0.62
            neb2 = math.exp(-(dx2 * dx2 * 4.8 + dy2 * dy2 * 6.5))

            # Aurora Ribbon 1: Vibrant Emerald (#10B981 -> #34D399)
            d1 = abs(ny - c1[x])
            w1 = math.exp(-(d1 * d1) * 135.0)
            core1 = math.exp(-(d1 * d1) * 1400.0)

            # Aurora Ribbon 2: Deep Jade/Teal (#059669 -> #14B8A6)
            d2 = abs(ny - c2[x])
            w2 = math.exp(-(d2 * d2) * 95.0)
            core2 = math.exp(-(d2 * d2) * 1100.0)

            # Aurora Ribbon 3: Warm Amber/Gold shimmer (#F59E0B)
            d3 = abs(ny - c3[x])
            w3 = math.exp(-(d3 * d3) * 160.0) * (0.35 + 0.65 * nx)

            # Subtle isometric diamond mesh lattice (distinct geometric signature)
            g1 = abs(((x + y) % 48) - 24)
            g2 = abs(((x - y) % 48) - 24)
            grid = 1.0 if (g1 == 0 or g2 == 0) else 0.0
            grid_mask = grid * 0.055 * (0.25 + 0.75 * (w1 + w2 + neb1))

            # Subtle soft spotlight behind center-top
            vignette = 1.0 - 0.38 * ((nx - 0.5) ** 2 + (ny - 0.5) ** 2)

            r = (base_r
                 + neb1 * 8.0 + neb2 * 18.0
                 + w1 * 18.0 + core1 * 75.0
                 + w2 * 10.0 + core2 * 40.0
                 + w3 * 95.0
                 + grid_mask * 80.0) * vignette

            g = (base_g
                 + neb1 * 48.0 + neb2 * 44.0
                 + w1 * 135.0 + core1 * 115.0
                 + w2 * 102.0 + core2 * 95.0
                 + w3 * 64.0
                 + grid_mask * 210.0) * vignette

            b = (base_b
                 + neb1 * 36.0 + neb2 * 24.0
                 + w1 * 92.0 + core1 * 88.0
                 + w2 * 96.0 + core2 * 92.0
                 + w3 * 12.0
                 + grid_mask * 155.0) * vignette

            buf[idx] = clamp(r)
            buf[idx + 1] = clamp(g)
            buf[idx + 2] = clamp(b)
            idx += 3

    # Upscale 2x horizontally & vertically into PNG scanlines
    raw = bytearray()
    row_stride = rw * 3
    for y in range(height):
        sy = min(y // 2, rh - 1)
        sy2 = min(sy + 1, rh - 1)
        fy = (y & 1) * 0.5
        row_a = sy * row_stride
        row_b = sy2 * row_stride

        line = bytearray(1 + width * 3)
        line[0] = 0  # PNG filter type None
        out_i = 1
        if fy == 0.0:
            for x in range(rw):
                p = row_a + x * 3
                r0, g0, b0 = buf[p], buf[p + 1], buf[p + 2]
                line[out_i] = r0
                line[out_i + 1] = g0
                line[out_i + 2] = b0
                if x + 1 < rw:
                    r1, g1, b1 = buf[p + 3], buf[p + 4], buf[p + 5]
                    line[out_i + 3] = (r0 + r1) >> 1
                    line[out_i + 4] = (g0 + g1) >> 1
                    line[out_i + 5] = (b0 + b1) >> 1
                else:
                    line[out_i + 3] = r0
                    line[out_i + 4] = g0
                    line[out_i + 5] = b0
                out_i += 6
        else:
            for x in range(rw):
                pa = row_a + x * 3
                pb = row_b + x * 3
                r0 = (buf[pa] + buf[pb]) >> 1
                g0 = (buf[pa + 1] + buf[pb + 1]) >> 1
                b0 = (buf[pa + 2] + buf[pb + 2]) >> 1
                line[out_i] = r0
                line[out_i + 1] = g0
                line[out_i + 2] = b0
                if x + 1 < rw:
                    r1 = (buf[pa + 3] + buf[pb + 3]) >> 1
                    g1 = (buf[pa + 4] + buf[pb + 4]) >> 1
                    b1 = (buf[pa + 5] + buf[pb + 5]) >> 1
                    line[out_i + 3] = (r0 + r1) >> 1
                    line[out_i + 4] = (g0 + g1) >> 1
                    line[out_i + 5] = (b0 + b1) >> 1
                else:
                    line[out_i + 3] = r0
                    line[out_i + 4] = g0
                    line[out_i + 5] = b0
                out_i += 6
        raw.extend(line)

    def chunk(tag, data):
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    compressed = zlib.compress(bytes(raw), level=6)
    with open(out_path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", compressed))
        f.write(chunk(b"IEND", b""))


if __name__ == "__main__":
    dest = sys.argv[1] if len(sys.argv) > 1 else "emerald_aurora.png"
    generate_wallpaper(dest)
    print(f"Generated MANO OS Obsidian-Emerald wallpaper: {dest}")
