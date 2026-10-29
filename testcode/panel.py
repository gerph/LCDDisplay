#!/usr/bin/env python3
"""
Test pattern for the LCDDisplay module and a check of what the emulated panel shows.

    panel.py sprite <file>              write the test sprite (320 x 240, 16bpp 5:6:5)
    panel.py compare sprite <ppm>       check that the picture is the sprite
    panel.py compare black <ppm>        check that the picture is all black

The sprite has four coloured quadrants, a white border and a black diagonal line, so that
a mistake in the orientation, the colour order or the inversion shows as a mismatch.
"""

import struct
import sys

WIDTH = 320
HEIGHT = 240


def pixel(x, y):
    """The pixel at (x, y) as (red, green, blue) with 5, 6 and 5 bits."""
    if x < 2 or y < 2 or x >= WIDTH - 2 or y >= HEIGHT - 2:
        return (31, 63, 31)
    if abs(x - y * 4 // 3) < 2:
        return (0, 0, 0)
    if x < WIDTH // 2 and y < HEIGHT // 2:
        return (31, 0, 0)
    if x >= WIDTH // 2 and y < HEIGHT // 2:
        return (0, 63, 0)
    if x < WIDTH // 2:
        return (0, 0, 31)
    return (31, 63, 0)


def write_sprite(path):
    """
    Write a sprite file: the RISC OS 5 64K format (type 10) has red in bits 0 to 4, green in
    bits 5 to 10 and blue in bits 11 to 15.
    """
    data = bytearray()
    for y in range(HEIGHT):
        for x in range(WIDTH):
            red, green, blue = pixel(x, y)
            data += struct.pack('<H', red | (green << 5) | (blue << 11))
    size = 44 + len(data)
    header = struct.pack('<I12sIIIIIII', size, b'testpanel\0\0\0', WIDTH * 2 // 4 - 1, HEIGHT - 1,
                         0, 31, 44, 44, (10 << 27) | (90 << 14) | (90 << 1) | 1)
    with open(path, 'wb') as fh:
        fh.write(struct.pack('<III', 1, 16, 16 + size) + header + bytes(data))


def read_ppm(path):
    with open(path, 'rb') as fh:
        data = fh.read()
    magic, size, maxval, rest = data.split(b'\n', 3)
    width, height = [int(v) for v in size.split()]
    return width, height, rest


def expected(x, y):
    red, green, blue = pixel(x, y)
    return ((red << 3) | (red >> 2), (green << 2) | (green >> 4), (blue << 3) | (blue >> 2))


def compare(kind, path):
    width, height, rest = read_ppm(path)
    if (width, height) != (WIDTH, HEIGHT):
        print("The picture is %i by %i, not %i by %i" % (width, height, WIDTH, HEIGHT))
        return 1
    wrong = []
    for y in range(height):
        for x in range(width):
            got = tuple(rest[(y * width + x) * 3:(y * width + x) * 3 + 3])
            want = expected(x, y) if kind == 'sprite' else (0, 0, 0)
            if got != want:
                wrong.append((x, y, got, want))
    if wrong:
        print("%i pixels differ; the first is at (%i, %i): %r, expected %r" % ((len(wrong),) + wrong[0]))
        return 1
    print("The panel shows the %s" % ("sprite" if kind == 'sprite' else "black picture"))
    return 0


if __name__ == '__main__':
    if sys.argv[1] == 'sprite':
        write_sprite(sys.argv[2])
    else:
        sys.exit(compare(sys.argv[2], sys.argv[3]))
