#!/usr/bin/env python3
from PIL import Image
import sys

PDF_TEXT = (
    "OPERATION WRTHUG — Thousands of ASUS Routers Hijacked in Global Campaign — "
    "STRIKE by SecurityScorecard — China Nexus ORB — "
    "CVE-2023-41345 CVE-2023-41346 CVE-2023-41347 CVE-2023-41348 CVE-2024-12912 CVE-2025-2492 — "
    "AiCloud exploit on End-of-Life ASUS WRT routers — "
    "Self-signed TLS cert SHA1:1894a6800dff523894eba7f31cea8d05d51032b4 — "
    "100-year expiration April 2022 — CN=a OU=a O=a L=a ST=a C=aa — "
    "30-50% targeting Taiwan — SE Asia Russia Europe United States — "
    "50000 unique IPs compromised worldwide — "
    "AyySSHush connection — CVE-2023-39780 cmd injection — SSH port 53282 — "
    "Only 7 dual-compromised IPs — lighttpd 1.4.29 — Apache httpd 2.0 — "
    "4G-AC55U DSL-AC68U GT-AC5300 GT-AX11000 RT-AC1200HP RT-AC1300UHP — "
    "Operational Relay Box — LapDogs ORB — ViciousTrap — "
    "CISA KEV — Nth day vulns — Token module filtering — OS cmd injection — "
    "Improper auth control — Arbitrary cmd exec — SOHO routers under siege — "
    "Persistent backdoors via SSH — Multi-stage infections — "
    "No post-exploit patching — door left open — "
    "IOC 46.132.187.85 221.43.126.86 122.100.210.209 59.26.66.44 195.234.71.218 — "
    "State-sponsored espionage infrastructure global reach — "
    "Shields up 2025 — Update firmware — Replace EoL — Disable AiCloud — "
)

WIDTH = 160
HEIGHT = 38

raw = Image.open("/home/hakcer/strike_meridian_art/Untitled.png")
print(f"DEBUG: mode={raw.mode}, size={raw.size}", file=sys.stderr)

# Composite onto white background to handle alpha
if raw.mode == "RGBA":
    bg = Image.new("RGBA", raw.size, (255, 255, 255, 255))
    bg.paste(raw, mask=raw.split()[3])
    img = bg.convert("L")
elif raw.mode == "LA":
    bg = Image.new("LA", raw.size, (255, 255))
    bg.paste(raw, mask=raw.split()[1])
    img = bg.convert("L")
else:
    img = raw.convert("L")

img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

pixels = [img.getpixel((x, y)) for y in range(HEIGHT) for x in range(WIDTH)]
dark = sum(1 for p in pixels if p < 128)
light = sum(1 for p in pixels if p >= 128)
print(f"DEBUG: dark={dark}, light={light}, total={len(pixels)}", file=sys.stderr)

text_stream = (PDF_TEXT * ((dark // len(PDF_TEXT)) + 3))
char_idx = 0

lines = []
for y in range(HEIGHT):
    row = []
    for x in range(WIDTH):
        pixel = img.getpixel((x, y))
        if pixel < 128:
            ch = text_stream[char_idx]
            char_idx += 1
            row.append(ch)
        else:
            row.append(" ")
    lines.append("".join(row).rstrip())

output = "\n".join(lines)

with open("/home/hakcer/strike_meridian_art/wrthug_strike_ascii.txt", "w") as f:
    f.write(output)

print(output)
