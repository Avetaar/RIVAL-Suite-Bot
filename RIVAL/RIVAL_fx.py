import os
import RIVAL_config as CFG
FX_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fx_cache")
_BG = (15, 15, 18)
_COLORS = {
    "chat": (59, 130, 246),
    "image": (34, 197, 94),
    "tts": (249, 115, 22),
    "music": (168, 85, 247),
    "coder": (20, 184, 166),
    "status": (239, 68, 68),
    "models": (234, 179, 8),
    "main": (59, 130, 246),
}
def _spinner(color, frames=14, size=132):
    from PIL import Image, ImageDraw
    out = []
    cx = cy = size // 2
    r = int(size * 0.40)
    for i in range(frames):
        img = Image.new("RGB", (size, size), _BG)
        d = ImageDraw.Draw(img)
        for seg in range(3):
            a0 = (i * 12 + seg * 96) % 360
            d.arc([cx - r, cy - r, cx + r, cy + r],
                  start=a0, end=a0 + 52, fill=color, width=9)
        m = 11
        d.ellipse([cx - m, cy - m, cx + m, cy + m], fill=(color[0] // 2, color[1] // 2, color[2] // 2))
        out.append(img)
    return out
def _typing(frames=8, size=150, color=(148, 163, 184)):
    from PIL import Image, ImageDraw
    out = []
    h = size // 2
    for i in range(frames):
        img = Image.new("RGB", (size, h), _BG)
        d = ImageDraw.Draw(img)
        cy = h // 2
        for j in range(3):
            x = size // 2 + (j - 1) * 36
            act = (i + j) % 3
            rad = 10 + (5 if act == 0 else (2 if act == 1 else 0))
            dy = 4 if act == 0 else 0
            col = (min(255, color[0] + 40), min(255, color[1] + 40), min(255, color[2] + 40))
            d.ellipse([x - rad, cy - rad - dy, x + rad, cy + rad - dy], fill=col)
        out.append(img)
    return out
def _save_gif(frames, path, duration=180):
    frames[0].save(path, save_all=True, append_images=frames[1:],
                   duration=duration, loop=0, optimize=True, disposal=2)
def build_all() -> dict:
    os.makedirs(FX_DIR, exist_ok=True)
    paths = {}
    for kind, color in _COLORS.items():
        f = os.path.join(FX_DIR, f"loader_{kind}.gif")
        if not os.path.exists(f):
            _save_gif(_spinner(color), f)
        paths["loader_" + kind] = f
    t = os.path.join(FX_DIR, "typing.gif")
    if not os.path.exists(t):
        _save_gif(_typing(), t, duration=160)
    paths["typing"] = t
    return paths
def path_for(kind: str) -> str | None:
    p = os.path.join(FX_DIR, f"loader_{kind}.gif")
    if not os.path.exists(p):
        try:
            build_all()
        except Exception:
            p = os.path.join(FX_DIR, "loader_main.gif")
    return p if os.path.exists(p) else None
def all_paths() -> dict:
    return build_all()
