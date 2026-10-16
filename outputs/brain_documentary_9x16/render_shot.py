#!/usr/bin/env python3
"""Render a 3s vertical (9:16) 'living' cinematic shot from a single keyframe.

Motion + light design:
  * slow eased camera push-in (1.00 -> 1.14) with a subtle upward tilt,
  * traveling neural bloom (low-frequency spatial mask x smooth temporal noise)
    so blue filaments and orange pulses glow in different regions at different times,
  * randomized electrical-pulse flashes anchored on real bright filament hotspots
    detected in the source image (they scale/pan correctly with the camera),
  * exposure breathing, film grain, lens vignette, gentle contrast grade.
"""
import os, sys, math, subprocess, shutil
import numpy as np
from PIL import Image, ImageFilter

SRC      = "/home/user/AI-Content-Studio/media/brain_lab_keyframe.png"
FRAMEDIR = "/tmp/frames"
OUT_W, OUT_H = 1080, 1920
FPS, DUR = 30, 3.0
NFRAMES  = int(round(FPS * DUR))
ZOOM_END = 1.14
SEED     = 20261016
FFMPEG   = "/tmp/venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"

os.makedirs(FRAMEDIR, exist_ok=True)
for f in os.listdir(FRAMEDIR):
    os.remove(os.path.join(FRAMEDIR, f))

rng = np.random.default_rng(SEED)


def smoothstep(u):
    return u * u * (3.0 - 2.0 * u)


# ---------------------------------------------------------------- source prep
src = Image.open(SRC).convert("RGB")
W, H = src.size
# crop to exact 9:16 (centre crop on the short axis)
if W / H > 9 / 16:
    cw, ch = int(round(H * 9 / 16)), H
else:
    cw, ch = W, int(round(W * 16 / 9)) - 1
left, top = (W - cw) // 2, (H - ch) // 2
base = src.crop((left, top, left + cw, top + ch))
# 2x working buffer: every output frame is a *downscale* => crisp, no soft upscale
BW, BH = cw * 2, ch * 2
base2 = base.resize((BW, BH), Image.LANCZOS).filter(
    ImageFilter.UnsharpMask(radius=2.0, percent=55, threshold=2))
base2_np = np.asarray(base2).astype(np.float32) / 255.0
print(f"source {W}x{H} -> crop {cw}x{ch} -> working {BW}x{BH}")

# --------------------------------------------------- hotspot detection (nodes)
small = np.asarray(base.convert("L").resize((cw // 4, ch // 4), Image.BILINEAR)).astype(np.float32)
lum = small / 255.0
# local maxima via shifted comparisons (no scipy needed)
mx = np.maximum.reduce([
    lum, np.roll(lum, 1, 0), np.roll(lum, -1, 0), np.roll(lum, 1, 1), np.roll(lum, -1, 1),
    np.roll(np.roll(lum, 1, 0), 1, 1), np.roll(np.roll(lum, 1, 0), -1, 1),
    np.roll(np.roll(lum, -1, 0), 1, 1), np.roll(np.roll(lum, -1, 0), -1, 1)])
cand = np.argwhere((lum >= mx - 1e-6) & (lum > 0.55))
vals = lum[cand[:, 0], cand[:, 1]]
order = np.argsort(-vals)
hot = []                                    # normalized coords in working buffer
MIN_D = max(cw // 12, 8)
for i in order:
    y, x = cand[i]
    if all((x - hx) ** 2 + (y - hy) ** 2 > (MIN_D / 4) ** 2 for hx, hy in hot):
        hot.append((x, y))
    if len(hot) >= 16:
        break
hot = [(hx * 4 / BW, hy * 4 / BH) for hx, hy in hot]      # normalise (small was /4)
print(f"electrical hotspots detected: {len(hot)}")

# flash schedule on those hotspots: amplitude, birth time, decay, colour
flashes = []
for hx, hy in hot:
    for _ in range(int(rng.integers(1, 4))):
        t0 = float(rng.uniform(-0.25, DUR - 0.1))
        flashes.append(dict(
            x=hx, y=hy,
            t0=t0,
            tau=float(rng.uniform(0.10, 0.30)),          # fast electrical decay
            amp=float(rng.uniform(0.16, 0.55)),
            rad=float(rng.uniform(0.045, 0.115)),        # fraction of frame height
            warm=float(rng.random())))                   # 0 = blue, 1 = orange

# traveling bloom masks: coarse fields interpolated over time
FIELD = (10, 18)                                   # (rows, cols)
KEYS = [rng.random(FIELD).astype(np.float32) for _ in range(NFRAMES // 6 + 3)]


def field_at(t):
    p = t * (len(KEYS) - 1) / DUR
    i, f = int(p), p - int(p)
    f = smoothstep(f)
    a, b = KEYS[min(i, len(KEYS) - 1)], KEYS[min(i + 1, len(KEYS) - 1)]
    return Image.fromarray(((a * (1 - f) + b * f) * 255).astype(np.uint8), "L").resize(
        (OUT_W, OUT_H), Image.BICUBIC)


# fixed lens vignette (a lens effect: stays with the frame, not the image)
yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
r = np.sqrt(((xx - OUT_W / 2) / (OUT_W / 2)) ** 2 + ((yy - OUT_H / 2) / (OUT_H / 2)) ** 2)
VIG = (1.0 - 0.30 * np.clip(r / 1.18, 0, 1) ** 2.3)[..., None].astype(np.float32)
EDGE = np.clip(np.abs(r / 1.42), 0, 1) ** 3 * 0.035        # slight channel split at frame edge
CHROMA = (1 - EDGE, np.ones_like(EDGE), 1 + EDGE)

# exposure breathing curve (documentary-camera feel, very subtle)
def exposure(t):
    return (1.0
            + 0.016 * math.sin(2 * math.pi * 0.55 * t)
            + 0.010 * math.sin(2 * math.pi * 1.7 * t + 1.1)
            + 0.006 * math.sin(2 * math.pi * 4.3 * t + 2.7))


CY0, CY1 = 0.515, 0.480          # gentle upward tilt as we push in
CX0, CX1 = 0.500, 0.504


def blob(cy, cx, sigma, shape):
    h, w = shape
    y0, y1 = max(0, int(cy - 3 * sigma)), min(h, int(cy + 3 * sigma) + 1)
    x0, x1 = max(0, int(cx - 3 * sigma)), min(w, int(cx + 3 * sigma) + 1)
    if y1 <= y0 or x1 <= x0:
        return None, (0, 0)
    gy = np.arange(y0, y1, dtype=np.float32)[:, None] - cy
    gx = np.arange(x0, x1, dtype=np.float32)[None, :] - cx
    g = np.exp(-(gy * gy + gx * gx) / (2.0 * sigma * sigma)).astype(np.float32)
    return g, (y0, x0)


print("rendering", NFRAMES, "frames ...")
for i in range(NFRAMES):
    t = i / FPS
    u = smoothstep(i / max(NFRAMES - 1, 1))
    z = 1.0 + (ZOOM_END - 1.0) * u

    win_w, win_h = BW / z, BH / z
    cx, cy = (CX0 + (CX1 - CX0) * u) * BW, (CY0 + (CY1 - CY0) * u) * BH
    x0, y0 = cx - win_w / 2, cy - win_h / 2
    # integer crop in the 2x buffer, LANCZOS down to output => sub-pixel smooth
    ix, iy = int(round(x0)), int(round(y0))
    ix = max(0, min(ix, BW - int(round(win_w))))
    iy = max(0, min(iy, BH - int(round(win_h))))
    win = base2.crop((ix, iy, ix + int(round(win_w)), iy + int(round(win_h))))
    frame = win.resize((OUT_W, OUT_H), Image.LANCZOS)

    img = np.asarray(frame).astype(np.float32) / 255.0

    # --- neural bloom: bright filaments bleed light, modulated by traveling field
    lum_f = img.max(axis=2)
    bp = np.clip((lum_f - 0.52) / 0.48, 0, 1) ** 1.4
    bp_img = Image.fromarray((bp * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(radius=1.6))
    bp_np = np.asarray(bp_img).astype(np.float32) / 255.0
    bp_np = bp_np * (0.35 + 1.15 * np.asarray(field_at(t)).astype(np.float32) / 255.0)
    bloom = bp_np[..., None] * np.array([0.42, 0.78, 1.00], dtype=np.float32) * 0.42  # cool bleed
    # warm spike bloom (orange pulses follow the hottest cores)
    core = np.clip((lum_f - 0.80) / 0.20, 0, 1) ** 2.0
    core_img = Image.fromarray((core * 255).astype(np.uint8), "L").filter(
        ImageFilter.GaussianBlur(radius=3.2))
    core_np = np.asarray(core_img).astype(np.float32) / 255.0
    bloom += core_np[..., None] * np.array([1.00, 0.55, 0.16], dtype=np.float32) * 0.55
    img = 1.0 - (1.0 - img) * (1.0 - np.clip(bloom, 0, 1) * 0.85)      # screen blend

    # --- electrical flashes anchored on real filament nodes (pan/zoom aware)
    for f in flashes:
        dt = t - f["t0"]
        if dt <= 0 or dt > 6 * f["tau"]:
            continue
        rise = min(1.0, dt / (0.25 * f["tau"]))
        inten = f["amp"] * rise * math.exp(-dt / f["tau"])
        inten *= 0.75 + 0.25 * math.sin(2 * math.pi * 14.0 * dt)      # electric flicker
        in_x = (f["x"] * BW - ix) / win_w
        in_y = (f["y"] * BH - iy) / win_h
        if not (-0.2 < in_x < 1.2 and -0.2 < in_y < 1.2):
            continue
        sigma = f["rad"] * OUT_H * z * 0.55
        g, (gy, gx) = blob(in_y * OUT_H, in_x * OUT_W, sigma, (OUT_H, OUT_W))
        if g is None:
            continue
        col = np.array([0.55, 0.85, 1.0]) * (1 - f["warm"]) + np.array([1.0, 0.62, 0.25]) * f["warm"]
        patch = img[gy:gy + g.shape[0], gx:gx + g.shape[1]]
        add = (g * inten * 1.35)[..., None] * col.astype(np.float32)
        img[gy:gy + g.shape[0], gx:gx + g.shape[1]] = 1.0 - (1.0 - patch) * (1.0 - np.clip(add, 0, 1))

    # --- grade: exposure breathing, contrast S-curve, warm/cool balance, vignette
    img *= exposure(t)
    img = np.clip(img, 0, 1)
    img = img * 1.045 - 0.022
    th = 0.52 + 0.018 * math.sin(2 * math.pi * 0.31 * t)
    img = np.clip(img, 0, 1)
    img = np.clip((img - th) * 1.085 + th, 0, 1)
    shade = (1.0 - np.clip(img.mean(axis=2, keepdims=True), 0, 1)) ** 2
    img = np.clip(img * (1 + shade * np.array([-0.010, 0.002, 0.030], np.float32)), 0, 1)  # teal shadows
    hilite = np.clip(img.mean(axis=2, keepdims=True) - 0.6, 0, 1) / 0.4
    img = np.clip(img * (1 + hilite * np.array([0.022, 0.004, -0.020], np.float32)), 0, 1)  # warm highlights
    img *= VIG
    img *= np.stack([CHROMA[0], CHROMA[1], CHROMA[2]], axis=-1)

    # --- film grain (luma-weighted so shadows stay alive without mushing midtones)
    g1 = rng.normal(0, 1.0, (OUT_H, OUT_W, 1)).astype(np.float32)
    g1 += 0.5 * rng.normal(0, 1.0, (OUT_H, OUT_W, 1)).astype(np.float32)
    img += g1 * (0.0125 - 0.005 * np.clip(img.mean(axis=2, keepdims=True), 0, 1))

    out = Image.fromarray((np.clip(img, 0, 1) * 255.0 + 0.5).astype(np.uint8), "RGB")
    out = out.filter(ImageFilter.UnsharpMask(radius=1.1, percent=48, threshold=3))
    out.save(f"{FRAMEDIR}/f_{i:04d}.png")
    if i % 15 == 0 or i == NFRAMES - 1:
        print(f"  frame {i + 1}/{NFRAMES}  t={t:.2f}s  zoom={z:.3f}", flush=True)

print("encoding ...")
os.makedirs("/home/user/AI-Content-Studio/outputs/brain_documentary_9x16", exist_ok=True)
OUT = "/home/user/AI-Content-Studio/outputs/brain_documentary_9x16/brain_documentary_9x16.mp4"
cmd = [FFMPEG, "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", f"{FRAMEDIR}/f_%04d.png",
       "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-profile:v", "high", "-level", "4.2",
       "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", "-an", OUT]
subprocess.run(cmd, check=True, capture_output=True)
print("done ->", OUT, round(os.path.getsize(OUT) / 1e6, 2), "MB")
