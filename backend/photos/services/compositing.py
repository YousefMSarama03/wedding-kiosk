from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

from PIL import Image, ImageChops, ImageDraw, ImageEnhance, ImageFilter, ImageStat


@dataclass(frozen=True)
class LightDirection:
    """
    Simple 2D light direction in image space.

    dx > 0 means light comes from the right (shadow goes left).
    dy > 0 means light comes from the bottom (shadow goes up).
    """

    dx: float
    dy: float


def _luminance(im: Image.Image) -> Image.Image:
    return im.convert("RGB").convert("L")


def estimate_light_direction(background_rgb: Image.Image) -> LightDirection:
    """
    Heuristic light-direction estimator using coarse luminance asymmetry.
    This is intentionally lightweight (Pillow-only) and robust for typical event photos.
    """
    bg = background_rgb.convert("RGB")
    # Downscale for speed and noise robustness.
    w, h = bg.size
    sample_w = max(64, min(320, w // 6))
    sample_h = max(64, min(320, h // 6))
    small = bg.resize((sample_w, sample_h), Image.Resampling.BILINEAR)
    lum = _luminance(small)
    px = lum.tobytes()

    # Compute mean luminance in left/right and top/bottom halves.
    def _mean(xs: range, ys: range) -> float:
        total = 0
        n = 0
        for y in ys:
            row = y * sample_w
            for x in xs:
                total += px[row + x]
                n += 1
        return total / max(1, n)

    left = _mean(range(0, sample_w // 2), range(0, sample_h))
    right = _mean(range(sample_w // 2, sample_w), range(0, sample_h))
    top = _mean(range(0, sample_w), range(0, sample_h // 2))
    bottom = _mean(range(0, sample_w), range(sample_h // 2, sample_h))

    # Light tends to come from the brighter side.
    dx = 1.0 if right > left else -1.0
    dy = 1.0 if bottom > top else -1.0
    return LightDirection(dx=dx, dy=dy)


def _compute_cdf(hist: Iterable[int]) -> list[float]:
    cdf: list[float] = []
    total = float(sum(hist)) or 1.0
    run = 0.0
    for v in hist:
        run += float(v)
        cdf.append(run / total)
    return cdf


def _masked_mean_luma(im_rgb: Image.Image, mask: Image.Image) -> float:
    """Mean luminance (0–255) over pixels with mask > 8."""
    gray = im_rgb.convert("L")
    gp = gray.tobytes()
    mp = mask.tobytes()
    total = 0.0
    n = 0
    for i, a in enumerate(mp):
        if a > 8:
            total += gp[i]
            n += 1
    return total / max(1, n)


def _mean_luma(im_rgb: Image.Image) -> float:
    gray = im_rgb.convert("L")
    px = gray.tobytes()
    return sum(px) / max(1, len(px))


def _clamp_gains(gr: float, gg: float, gb: float, lo: float = 0.58, hi: float = 1.72) -> tuple[float, float, float]:
    return (max(lo, min(hi, gr)), max(lo, min(hi, gg)), max(lo, min(hi, gb)))


def _match_masked_luminance(
    fg_rgb: Image.Image,
    fg_mask: Image.Image,
    target_luma: float,
    *,
    strength: float = 0.62,
) -> Image.Image:
    """
    Scale overall brightness so masked foreground mean luminance moves toward ``target_luma``.
    """
    cur = _masked_mean_luma(fg_rgb, fg_mask)
    if cur <= 1e-3 or target_luma <= 1e-3:
        return fg_rgb
    ratio = target_luma / cur
    ratio = max(0.65, min(1.45, ratio))
    # Blend toward neutral (1.0) so we don't fight the color pass too aggressively.
    adj = 1.0 + (ratio - 1.0) * max(0.0, min(1.0, strength))
    return ImageEnhance.Brightness(fg_rgb).enhance(adj)


def _match_saturation_to_reference(fg_rgb: Image.Image, ref_rgb: Image.Image, strength: float = 0.35) -> Image.Image:
    """Gently align saturation with the background crop for a more unified, photographic look."""
    # Pillow: convert to HSV not built-in; approximate via Color enhancer vs reference colorfulness.
    def _sat_proxy(im: Image.Image) -> float:
        stat = ImageStat.Stat(im.convert("RGB"))
        # Std of RGB channels as a simple "spread" proxy.
        return sum(stat.stddev) / 3.0

    fg_s = max(1e-6, _sat_proxy(fg_rgb))
    ref_s = max(1e-6, _sat_proxy(ref_rgb))
    t = ref_s / fg_s
    t = max(0.82, min(1.18, t))
    enhanced = ImageEnhance.Color(fg_rgb).enhance(1.0 + (t - 1.0) * strength)
    return enhanced


def _refine_alpha_edges(alpha: Image.Image) -> Image.Image:
    """
    Tighten semi-transparent fringe from segmentation and re-anti-alias the boundary.
    """
    a = alpha.convert("L")
    # Suppress thin bright halos outside the subject.
    cleaned = a.filter(ImageFilter.MinFilter(size=3))
    a = Image.blend(a, cleaned, 0.45)
    # Smooth transitions slightly for a more photographic matte (sub-pixel edge).
    a = a.filter(ImageFilter.GaussianBlur(radius=0.65))
    return a


def _histogram_match_channel(src: Image.Image, ref: Image.Image) -> Image.Image:
    """
    1D histogram matching for a single 8-bit channel using CDF mapping.
    """
    src_hist = src.histogram()
    ref_hist = ref.histogram()
    src_cdf = _compute_cdf(src_hist)
    ref_cdf = _compute_cdf(ref_hist)

    # Build LUT: for each src value find closest ref value by CDF.
    lut = [0] * 256
    j = 0
    for i in range(256):
        si = src_cdf[i]
        while j < 255 and ref_cdf[j] < si:
            j += 1
        lut[i] = j
    return src.point(lut)


def match_foreground_to_background(
    fg_rgba: Image.Image,
    bg_rgb: Image.Image,
    *,
    bg_sample_box: tuple[int, int, int, int],
    strength: float = 0.7,
) -> Image.Image:
    """
    Match foreground brightness/color to a background sample region.

    Steps:
    - Gain-based white balance / temperature-tint approximation (per-channel mean match)
    - Gentle histogram matching per channel (controlled by strength)
    """
    fg = fg_rgba.convert("RGBA")
    bg = bg_rgb.convert("RGB")
    bg_crop = bg.crop(bg_sample_box).convert("RGB")

    fg_rgb = fg.convert("RGB")
    fg_mask = fg.split()[-1]

    # Use masked mean for fg.
    def _masked_mean_rgb(im_rgb: Image.Image, mask: Image.Image) -> tuple[float, float, float]:
        r, g, b = im_rgb.split()
        m = mask
        rp = r.tobytes()
        gp = g.tobytes()
        bp = b.tobytes()
        mp = m.tobytes()
        n = 0
        sr = sg = sb = 0.0
        for i, a in enumerate(mp):
            if a > 8:
                n += 1
                sr += rp[i]
                sg += gp[i]
                sb += bp[i]
        if n == 0:
            return (128.0, 128.0, 128.0)
        return (sr / n, sg / n, sb / n)

    def _mean_rgb(im_rgb: Image.Image) -> tuple[float, float, float]:
        r, g, b = im_rgb.split()
        rp = r.tobytes()
        gp = g.tobytes()
        bp = b.tobytes()
        n = len(rp) or 1
        return (sum(rp) / n, sum(gp) / n, sum(bp) / n)

    fg_mean = _masked_mean_rgb(fg_rgb, fg_mask)
    bg_mean = _mean_rgb(bg_crop)

    # Temperature/tint approximation: per-channel gains to match means.
    gains = []
    for fm, bm in zip(fg_mean, bg_mean):
        if fm <= 1e-6:
            gains.append(1.0)
        else:
            gains.append(bm / fm)
    gr, gg, gb = _clamp_gains(*gains)

    def _apply_gains(im: Image.Image) -> Image.Image:
        r, g, b = im.split()
        r = r.point(lambda v: max(0, min(255, int(round(v * gr)))))
        g = g.point(lambda v: max(0, min(255, int(round(v * gg)))))
        b = b.point(lambda v: max(0, min(255, int(round(v * gb)))))
        return Image.merge("RGB", (r, g, b))

    fg_balanced = _apply_gains(fg_rgb)

    # Histogram match each channel against background crop.
    fr, fg_ch, fb = fg_balanced.split()
    br, bg_ch, bb = bg_crop.split()
    mr = _histogram_match_channel(fr, br)
    mg = _histogram_match_channel(fg_ch, bg_ch)
    mb = _histogram_match_channel(fb, bb)
    fg_matched = Image.merge("RGB", (mr, mg, mb))

    # Blend with strength so we don't over-fit and create odd colors.
    blended = Image.blend(fg_balanced, fg_matched, max(0.0, min(1.0, strength)))
    # Exposure: align mean luminance of the subject with the local background lighting.
    target_l = _mean_luma(bg_crop)
    blended = _match_masked_luminance(blended, fg_mask, target_l, strength=0.68)
    # Slightly stronger local color harmony (still identity-safe; applied only to pasted cutout).
    blended = _match_saturation_to_reference(blended, bg_crop, strength=0.42)
    out = Image.merge("RGBA", (*blended.split(), fg_mask))
    return out


def render_soft_shadow(
    fg_alpha: Image.Image,
    *,
    light: LightDirection,
    floor_y: int,
    softness: float = 18.0,
    opacity: float = 0.35,
    squash: float = 0.28,
    shear: float = 0.35,
    max_offset_px: int = 120,
) -> Image.Image:
    """
    Create a soft, photorealistic ground shadow from a foreground alpha mask.
    Returns an RGBA image (same size as fg_alpha) containing only the shadow.
    """
    a = fg_alpha.convert("L")
    w, h = a.size

    # Start as black shadow with alpha derived from mask.
    shadow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    shadow.putalpha(a.point(lambda v: int(v * opacity)))

    # Squash shadow vertically around floor plane.
    sy = max(0.10, min(0.60, squash))
    new_h = max(1, int(round(h * sy)))
    squashed = shadow.resize((w, new_h), Image.Resampling.BILINEAR)

    # Place it near the floor (default: anchor at floor_y).
    base = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    y0 = max(0, min(h - new_h, floor_y - new_h + 2))
    base.alpha_composite(squashed, (0, y0))

    # Shear away from the light direction.
    dx = -1.0 if light.dx > 0 else 1.0  # shadow goes opposite the light
    offset = int(round(max_offset_px * abs(dx)))
    shear_x = (shear * dx)
    # Affine: x' = x + shear_x * y + tx
    # PIL expects (a, b, c, d, e, f): x' = a*x + b*y + c; y' = d*x + e*y + f
    affine = (1, shear_x, offset if dx > 0 else 0, 0, 1, 0)
    sheared = base.transform((w, h), Image.Transform.AFFINE, affine, resample=Image.Resampling.BILINEAR)

    # Blur for softness.
    blur_radius = max(2.0, min(40.0, float(softness)))
    soft = sheared.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Fade with distance from floor (strongest near contact).
    fade = Image.new("L", (w, h), 0)
    for y in range(h):
        # 1 near floor, 0 far away above.
        t = 1.0 - max(0.0, min(1.0, (floor_y - y) / max(1.0, h * 0.35)))
        fade.putpixel((0, y), int(round(255 * t)))
    fade = fade.resize((w, h), Image.Resampling.NEAREST)
    fade = fade.filter(ImageFilter.GaussianBlur(radius=6))
    # Apply fade to alpha.
    r, g, b, alpha = soft.split()
    alpha = ImageChops.multiply(alpha, fade)
    out = Image.merge("RGBA", (r, g, b, alpha))
    return out


def _env_truthy(name: str, default: bool = True) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in ("true", "1", "yes", "on")


def _eff(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _subject_edge_mask(alpha: Image.Image) -> Image.Image:
    """Narrow rim along the silhouette (inside + just outside) for bounce light."""
    a = alpha.convert("L")
    outer = a
    for _ in range(4):
        outer = outer.filter(ImageFilter.MaxFilter(3))
    inner = a.filter(ImageFilter.MinFilter(3))
    rim = ImageChops.subtract(outer, inner)
    return rim.filter(ImageFilter.GaussianBlur(radius=1.15))


def _warm_bounce_tint_from_bg(bg_rgb: Image.Image, box: tuple[int, int, int, int]) -> tuple[int, int, int]:
    crop = bg_rgb.crop(box).convert("RGB").filter(ImageFilter.GaussianBlur(radius=14))
    r, g, b = tuple(int(round(ImageStat.Stat(crop).mean[i])) for i in range(3))
    # Gentle warm lift (bounce reads slightly amber vs. raw gray-card balance).
    return (min(255, r + 8), min(255, g + 4), max(0, b - 6))


def _screen_masked_rgb(base: Image.Image, light_rgb: Image.Image, strength_l: Image.Image) -> Image.Image:
    br, bg, bb = base.convert("RGB").split()
    lr, lg, lb = light_rgb.convert("RGB").split()
    st = strength_l.convert("L")

    def pair(bch: Image.Image, lch: Image.Image) -> Image.Image:
        bp, lp, sp = bch.tobytes(), lch.tobytes(), st.tobytes()
        out = bytearray(len(bp))
        for i in range(len(bp)):
            b, l, t = bp[i], lp[i], sp[i] / 255.0
            screened = round(255.0 - (255.0 - b) * (255.0 - l) / 255.0)
            out[i] = max(0, min(255, round(b + t * (screened - b))))
        return Image.frombytes("L", bch.size, bytes(out))

    return Image.merge("RGB", (pair(br, lr), pair(bg, lg), pair(bb, lb)))


def apply_light_warm_edge_bounce(
    canvas_rgb: Image.Image,
    subject_mask: Image.Image,
    bounce_rgb: tuple[int, int, int],
    *,
    strength_0_1: float,
) -> Image.Image:
    """Very subtle warm screen on subject edges only (background-derived bounce)."""
    edge = _subject_edge_mask(subject_mask)
    cap = max(4, min(72, int(round(strength_0_1 * 220))))
    edge_w = edge.point(lambda z, c=cap: max(0, min(255, int(round(z * c / 255.0)))))
    fill = Image.new("RGB", canvas_rgb.size, bounce_rgb)
    return _screen_masked_rgb(canvas_rgb, fill, edge_w)


def _grain_residual_std(im_rgb: Image.Image, *, blur_r: float = 1.05) -> float:
    lum = im_rgb.convert("L")
    smooth = lum.filter(ImageFilter.GaussianBlur(radius=blur_r))
    return float(ImageStat.Stat(ImageChops.difference(lum, smooth)).stddev[0])


def _add_matched_grain_masked(
    rgb: Image.Image,
    mask_l: Image.Image,
    target_std: float,
) -> Image.Image:
    """Film grain matched to venue micro-contrast; applied only where ``mask_l`` > 0."""
    mask = mask_l.convert("L")
    bw, bh = rgb.size
    tgt = max(4.5, float(target_std))
    cur = max(4.5, _grain_residual_std(rgb))
    scale = max(0.55, min(2.2, tgt / cur)) * _eff("KEEPSAKE_FILM_GRAIN_SCALE", 1.0)
    k_base = _eff("KEEPSAKE_FILM_GRAIN_STRENGTH", 18.0) / 220.0
    k = max(0.04, min(0.38, k_base * scale))

    tw = max(64, bw // 12)
    th = max(64, bh // 12)
    noise = Image.frombytes("L", (tw, th), os.urandom(tw * th)).resize((bw, bh), Image.Resampling.BILINEAR)
    noise = noise.filter(ImageFilter.GaussianBlur(radius=0.45))
    adj = noise.point(lambda px: max(-48, min(48, int(round((px - 128) * k)))))
    m_soft = mask.filter(ImageFilter.GaussianBlur(radius=0.85))
    r, g, b = rgb.split()
    nr = ImageChops.add(r, adj)
    ng = ImageChops.add(g, adj)
    nb = ImageChops.add(b, adj)
    merged = Image.merge("RGB", (nr, ng, nb))
    return Image.composite(merged, rgb, m_soft)


def _band_mass_center(
    alpha: Image.Image,
    y0: int,
    y1: int,
    x0: int,
    x1: int,
) -> tuple[float, float, float] | None:
    """Returns (cx, cy, total_alpha) in alpha coords, or None if empty."""
    a = alpha.crop((x0, y0, x1, y1)).convert("L")
    w, h = a.size
    px = memoryview(a.tobytes())
    sx = sy = sw = 0.0
    for yy in range(h):
        row = yy * w
        for xx in range(w):
            v = px[row + xx]
            if v > 12:
                sx += (x0 + xx) * v
                sy += (y0 + yy) * v
                sw += v
    if sw < 800:
        return None
    return (sx / sw, sy / sw, sw)


def render_ambient_contact_shadows_multi(
    fg_alpha: Image.Image,
    *,
    tint: tuple[int, int, int] = (26, 22, 34),
    foot_max_alpha: float = 0.24,
    hand_max_alpha: float = 0.14,
) -> Image.Image:
    """
    Small ambient contact darkening under feet / stance and under hands so the figure reads grounded.
    """
    a = fg_alpha.convert("L")
    w, h = a.size
    rr, rg, rb = tint
    acc = Image.new("RGBA", (w, h), (0, 0, 0, 0))

    def _blob(cx: float, cy: float, rx: int, ry: int, peak: float) -> None:
        cx_i, cy_i = int(round(cx)), int(round(cy))
        rx = max(10, rx)
        ry = max(6, ry)
        ell = Image.new("L", (w, h), 0)
        ed = ImageDraw.Draw(ell)
        ed.ellipse((cx_i - rx, cy_i - ry, cx_i + rx, cy_i + ry), fill=min(255, int(round(peak * 420))))
        ell = ell.filter(ImageFilter.GaussianBlur(radius=max(2.0, ry / 2.8)))
        layer = Image.merge("RGBA", (Image.new("L", (w, h), rr), Image.new("L", (w, h), rg), Image.new("L", (w, h), rb), ell))
        acc.alpha_composite(layer)

    # --- Legs / floor placement: bottom band + left/right foot split ---
    y_floor0 = max(0, int(h * 0.82))
    y_floor1 = h
    mid_x = w // 2
    left = _band_mass_center(a, y_floor0, y_floor1, 0, mid_x)
    right = _band_mass_center(a, y_floor0, y_floor1, mid_x, w)
    center = _band_mass_center(a, y_floor0, y_floor1, 0, w)

    if center:
        foot_y = min(h - 4, int(round(center[1] + 6)))
    elif left and right:
        foot_y = min(h - 4, int(round((left[1] + right[1]) * 0.5 + 6)))
    else:
        foot_y = h - 4
    span = max(int(w * 0.14), 28)

    if left and right and abs(left[0] - right[0]) > w * 0.08:
        _blob(left[0], foot_y, int(span * 0.95), max(8, int(h * 0.035)), foot_max_alpha * 0.92)
        _blob(right[0], foot_y, int(span * 0.95), max(8, int(h * 0.035)), foot_max_alpha * 0.92)
    elif center:
        _blob(center[0], foot_y, int(span * 1.35), max(9, int(h * 0.042)), foot_max_alpha)

    # Wide shallow “stance” grounding under both feet region
    if center:
        _blob(center[0], min(h - 2, foot_y + max(4, h // 55)), int(w * 0.36), max(7, int(h * 0.028)), foot_max_alpha * 0.45)

    # --- Hands: side pockets in mid-upper body (typical arm hang) ---
    y_h0 = max(0, int(h * 0.34))
    y_h1 = min(h, int(h * 0.62))
    qw = max(1, w // 4)
    hl = _band_mass_center(a, y_h0, y_h1, 0, qw + 8)
    hr = _band_mass_center(a, y_h0, y_h1, w - qw - 8, w)
    hand_rx = max(11, int(w * 0.065))
    hand_ry = max(7, int(h * 0.04))
    if hl and hl[2] > 1200:
        _blob(hl[0], hl[1] + hand_ry * 0.35, hand_rx, hand_ry, hand_max_alpha)
    if hr and hr[2] > 1200:
        _blob(hr[0], hr[1] + hand_ry * 0.35, hand_rx, hand_ry, hand_max_alpha)

    return acc


def compose_guest_on_background(
    *,
    guest_rgba: Image.Image,
    background_rgb: Image.Image,
    position: tuple[int, int],
    max_size: tuple[int, int] | None,
    enable_color_match: bool = True,
    enable_shadow: bool = True,
) -> Image.Image:
    """
    Deterministic compositing: color match, shadow, optional warm edge bounce, multi-point
    ambient contact (feet / stance / hands), and film grain on the individual only.

    Env (all optional): ``KEEPSAKE_WARM_EDGE_BOUNCE``, ``KEEPSAKE_WARM_BOUNCE_STRENGTH`` (0–1,
    default ~0.10 very light), ``KEEPSAKE_AMBIENT_CONTACT_SHADOW``, ``KEEPSAKE_FILM_GRAIN_INDIVIDUAL``,
    ``KEEPSAKE_FILM_GRAIN_SCALE``, ``KEEPSAKE_FILM_GRAIN_STRENGTH``.
    """
    bg = background_rgb.convert("RGB")
    fg = guest_rgba.convert("RGBA")
    r0, g0, b0, a0 = fg.split()
    fg = Image.merge("RGBA", (r0, g0, b0, _refine_alpha_edges(a0)))

    # Resize guest if needed.
    if max_size is not None:
        max_w, max_h = max_size
        w, h = fg.size
        scale = min(1.0, max_w / max(1, w), max_h / max(1, h))
        if scale < 1.0:
            nw = max(1, int(round(w * scale)))
            nh = max(1, int(round(h * scale)))
            fg = fg.resize((nw, nh), Image.Resampling.LANCZOS)

    x, y = position
    fg_w, fg_h = fg.size
    bg_w, bg_h = bg.size
    x = max(-fg_w + 1, min(bg_w - 1, x))
    y = max(-fg_h + 1, min(bg_h - 1, y))

    # Background sample region around where the subject will be placed.
    pad = int(round(max(fg_w, fg_h) * 0.25))
    sx0 = max(0, x - pad)
    sy0 = max(0, y - pad)
    sx1 = min(bg_w, x + fg_w + pad)
    sy1 = min(bg_h, y + fg_h + pad)
    sample_box = (sx0, sy0, sx1, sy1)

    warm_bounce = _env_truthy("KEEPSAKE_WARM_EDGE_BOUNCE", True)
    ambient_contact = _env_truthy("KEEPSAKE_AMBIENT_CONTACT_SHADOW", True)
    grain_individual = _env_truthy("KEEPSAKE_FILM_GRAIN_INDIVIDUAL", True)

    if enable_color_match:
        fg = match_foreground_to_background(fg, bg, bg_sample_box=sample_box, strength=0.78)
        # Slightly reduce “cutout” harshness by matching micro-contrast to the venue photo.
        fg_rgb = fg.convert("RGB")
        ref_contrast = ImageStat.Stat(bg.crop(sample_box).convert("RGB")).stddev
        ref_avg = sum(ref_contrast) / max(1, len(ref_contrast))
        subj_contrast = sum(ImageStat.Stat(fg_rgb).stddev) / 3.0
        if ref_avg > 1e-3 and subj_contrast > 1e-3:
            c_ratio = max(0.92, min(1.08, ref_avg / subj_contrast))
            fg_rgb = ImageEnhance.Contrast(fg_rgb).enhance(1.0 + (c_ratio - 1.0) * 0.55)
        else:
            fg_rgb = ImageEnhance.Contrast(fg_rgb).enhance(0.985)
        fg = Image.merge("RGBA", (*fg_rgb.split(), fg.split()[-1]))

    out = bg.convert("RGBA")

    alpha = fg.split()[-1]
    if enable_shadow:
        light = estimate_light_direction(bg)
        floor_y = min(bg_h - 1, y + fg_h - 1)
        shadow = render_soft_shadow(alpha, light=light, floor_y=floor_y)
        out.alpha_composite(shadow, (x, y))
    if ambient_contact:
        contacts = render_ambient_contact_shadows_multi(
            alpha,
            foot_max_alpha=float(_eff("KEEPSAKE_CONTACT_FEET_ALPHA", 0.22)),
            hand_max_alpha=float(_eff("KEEPSAKE_CONTACT_HANDS_ALPHA", 0.12)),
        )
        out.alpha_composite(contacts, (x, y))

    out.alpha_composite(fg, (x, y))
    rgb = out.convert("RGB")

    mask_full = Image.new("L", (bg_w, bg_h), 0)
    mask_full.paste(fg.split()[-1], (x, y))

    if warm_bounce:
        bounce_rgb = _warm_bounce_tint_from_bg(bg, sample_box)
        strength = max(0.04, min(0.28, _eff("KEEPSAKE_WARM_BOUNCE_STRENGTH", 0.10)))
        rgb = apply_light_warm_edge_bounce(rgb, mask_full, bounce_rgb, strength_0_1=strength)

    if grain_individual:
        ref_std = _grain_residual_std(bg.crop(sample_box).convert("RGB"))
        rgb = _add_matched_grain_masked(rgb, mask_full, ref_std)

    return rgb

