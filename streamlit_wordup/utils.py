import os
import re
from PIL import Image, ImageOps, ImageEnhance

def ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def safe_join(*parts):
    clean = [p for p in parts if p and str(p).strip() != ""]
    path = os.path.join(*clean)
    return os.path.normpath(path)

def upscale_to_4k_canvas(img):
    target_w, target_h = 3840, 2160
    src_w, src_h = img.size
    scale = min(target_w / src_w, target_h / src_h)
    new_w, new_h = max(1, int(src_w * scale)), max(1, int(src_h * scale))
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
    x = (target_w - new_w) // 2
    y = (target_h - new_h) // 2
    canvas.paste(resized, (x, y), resized if resized.mode == "RGBA" else None)
    return canvas

def clean_text(text, removals, use_regex=False, ignore_case=True):
    if not text or not removals:
        return text or "", 0
    flags = re.IGNORECASE if ignore_case else 0
    removed_total = 0
    out = text
    if use_regex:
        for pat in removals:
            if pat.strip() == "":
                continue
            compiled = re.compile(pat, flags)
            out, n = compiled.subn("", out)
            removed_total += n
    else:
        for token in removals:
            tok = token if token is not None else ""
            if tok == "":
                continue
            if ignore_case:
                pattern = re.compile(re.escape(tok), flags)
                out, n = pattern.subn("", out)
                removed_total += n
            else:
                n = out.count(tok)
                out = out.replace(tok, "")
                removed_total += n
    return out, removed_total

def _hex_to_rgba(color_hex):
    color_hex = color_hex.strip().lstrip("#")
    if len(color_hex) == 3:
        color_hex = "".join([c*2 for c in color_hex])
    r = int(color_hex[0:2], 16)
    g = int(color_hex[2:4], 16)
    b = int(color_hex[4:6], 16)
    return (r, g, b, 255)

def recolor_image(img, tint_hex="#FF00FF", strength=0.35):
    """Blend a solid tint over the image. Strength between 0 and 1."""
    strength = max(0.0, min(1.0, float(strength)))
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    tint_rgba = _hex_to_rgba(tint_hex)
    overlay = Image.new("RGBA", img.size, tint_rgba)
    # Blend: img*(1-strength) + overlay*strength
    blended = Image.blend(img, overlay, strength)
    # Small contrast boost to keep edges alive
    enhancer = ImageEnhance.Contrast(blended)
    return enhancer.enhance(1.05)

def add_background(img, bg_hex="#000000"):
    """Composite the RGBA image onto a solid background color."""
    if img.mode != "RGBA":
        img = img.convert("RGBA")
    bg = Image.new("RGBA", img.size, _hex_to_rgba(bg_hex))
    bg.paste(img, (0, 0), img)
    return bg
