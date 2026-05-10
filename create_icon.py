"""
SHelper — Генератор иконки
Создаёт assets/icon.ico в стиле сайта проекта (чёрный + зелёный)
"""

import os
import struct
import zlib

def create_icon():
    os.makedirs("assets", exist_ok=True)

    sizes = [256, 128, 64, 48, 32, 16]
    png_images = []

    for size in sizes:
        png_data = _make_png(size)
        png_images.append(png_data)

    _write_ico("assets/icon.ico", sizes, png_images)
    print("[+] Иконка создана: assets/icon.ico")


def _make_png(size: int) -> bytes:
    """Рисует иконку SHelper: тёмный фон, зелёный щит, буква S"""
    pixels = []
    cx, cy = size / 2, size / 2
    r_outer = size * 0.44
    r_inner = size * 0.30

    for y in range(size):
        row = []
        for x in range(size):
            nx = (x - cx) / r_outer
            ny = (y - cy) / r_outer

            # Фон
            bg = (11, 11, 11, 255)

            # Щит (шестиугольник / форма щита)
            in_shield = _in_shield(nx, ny)

            # Внешнее свечение
            glow = _shield_glow(nx, ny, r_outer, x, y, cx, cy, size)

            if in_shield:
                # Градиент внутри щита: тёмно-зелёный
                t  = (ny + 1) / 2
                gr = int(20  + t * 10)
                gg = int(30  + t * 20)
                gb = int(25  + t * 10)
                base = (gr, gg, gb, 255)

                # Граница щита (обводка)
                border = _shield_border(nx, ny)
                if border > 0:
                    br = int(0   * border + gr * (1 - border))
                    bg2 = int(200 * border + gg * (1 - border))
                    bb = int(120 * border + gb * (1 - border))
                    pixel = (br, bg2, bb, 255)
                else:
                    pixel = base
            elif glow > 0:
                # Внешнее мягкое свечение
                gl = int(0   * glow)
                gg2 = int(80 * glow)
                gb2 = int(50 * glow)
                a  = int(180 * glow)
                pixel = (gl, gg2, gb2, a)
            else:
                pixel = bg

            # Буква "S" поверх щита
            if in_shield:
                s_alpha = _draw_s(x, y, size)
                if s_alpha > 0:
                    sr = int(0   * s_alpha + pixel[0] * (1 - s_alpha))
                    sg = int(255 * s_alpha + pixel[1] * (1 - s_alpha))
                    sb = int(136 * s_alpha + pixel[2] * (1 - s_alpha))
                    pixel = (sr, sg, sb, 255)

            row.append(pixel)
        pixels.append(row)

    return _encode_png(pixels, size)


def _in_shield(nx: float, ny: float) -> bool:
    """Форма щита: закруглённый шестиугольник, снизу острый"""
    if ny > 0.85 - abs(nx) * 0.9:
        return False
    if ny < -0.95:
        return False
    if abs(nx) > 0.80 + ny * 0.05:
        return False
    # Верхние углы срезаны
    if ny < -0.60 and abs(nx) > 0.70 + ny * 0.15:
        return False
    return True


def _shield_border(nx: float, ny: float) -> float:
    """Яркость обводки щита"""
    edge = max(
        abs(nx) - 0.72,
        ny - 0.78,
        -ny - 0.88,
    )
    t = 1.0 - min(1.0, max(0.0, (0.10 - edge) / 0.10))
    return t if t > 0.05 else 0.0


def _shield_glow(nx, ny, r_outer, x, y, cx, cy, size):
    dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
    outer_r = r_outer * 1.08
    glow_w  = r_outer * 0.18
    if outer_r < dist < outer_r + glow_w:
        t = 1.0 - (dist - outer_r) / glow_w
        return t * 0.4
    return 0.0


def _draw_s(x: int, y: int, size: int) -> float:
    """Рисует букву S в центре щита, возвращает alpha [0..1]"""
    s = size
    # Нормализованные координаты центра буквы
    lw = max(1, s // 20)     # толщина линии
    ch = s * 0.42            # высота буквы
    cw = s * 0.28            # ширина буквы
    cx = s / 2
    cy = s / 2

    rx = x - cx
    ry = y - cy

    # S состоит из двух полудуг и перемычки
    # Верхняя дуга (центр чуть выше центра)
    top_cy = -ch * 0.25
    bot_cy = ch * 0.25
    arc_r  = cw * 0.48
    arc_rinner = arc_r - lw * 1.5

    alpha = 0.0

    # Верхняя дуга (правая ориентация)
    dx = rx - 0 
    dy = ry - top_cy
    dist = (dx**2 + dy**2) ** 0.5
    if arc_rinner < dist < arc_r + lw:
        # Только правая половина верхней дуги
        if ry < cy - cy + top_cy + arc_r * 0.1:
            alpha = max(alpha, _smooth(dist, arc_rinner, arc_r + lw))

    # Нижняя дуга (левая ориентация)
    dx2 = rx - 0
    dy2 = ry - bot_cy
    dist2 = (dx2**2 + dy2**2) ** 0.5
    if arc_rinner < dist2 < arc_r + lw:
        if ry > cy - cy + bot_cy - arc_r * 0.1:
            alpha = max(alpha, _smooth(dist2, arc_rinner, arc_r + lw))

    # Средняя перемычка (горизонтальная полоса)
    if abs(ry) < lw * 1.2 and abs(rx) < cw * 0.52:
        alpha = max(alpha, 0.9)

    return min(1.0, alpha)


def _smooth(v: float, lo: float, hi: float) -> float:
    if v <= lo or v >= hi:
        return 0.0
    t = (v - lo) / (hi - lo)
    # Параболическая яркость (ярче в центре)
    return 1.0 - abs(2 * t - 1)


def _encode_png(pixels, size: int) -> bytes:
    """Кодирует пиксели RGBA в PNG вручную"""
    def chunk(name: bytes, data: bytes) -> bytes:
        c = name + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)

    # IHDR
    ihdr_data = struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)
    # Цветовой тип 6 = RGBA
    ihdr_data = struct.pack(">II", size, size) + bytes([8, 6, 0, 0, 0])

    raw = bytearray()
    for row in pixels:
        raw.append(0)  # filter type None
        for (r, g, b, a) in row:
            raw += bytes([r, g, b, a])

    compressed = zlib.compress(bytes(raw), 9)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", ihdr_data)
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    return png


def _write_ico(path: str, sizes: list, png_list: list):
    """Записывает ICO-файл с несколькими PNG-изображениями"""
    n = len(sizes)
    # ICO header: RESERVED(2) + TYPE(2) + COUNT(2)
    header = struct.pack("<HHH", 0, 1, n)

    # Directory entries (16 bytes each)
    data_offset = 6 + n * 16
    dir_entries = b""
    image_data  = b""

    for i, (size, png) in enumerate(zip(sizes, png_list)):
        w = 0 if size == 256 else size
        h = 0 if size == 256 else size
        dir_entries += struct.pack(
            "<BBBBHHII",
            w, h,          # width, height (0 = 256)
            0,             # color count (0 = >256)
            0,             # reserved
            1,             # color planes
            32,            # bits per pixel
            len(png),      # size of image data
            data_offset + len(image_data)  # offset to image data
        )
        image_data += png

    with open(path, "wb") as f:
        f.write(header + dir_entries + image_data)


if __name__ == "__main__":
    create_icon()
