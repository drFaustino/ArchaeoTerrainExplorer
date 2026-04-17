import numpy as np

def hillshade(dem, azimuth_deg=315.0, altitude_deg=45.0, res=1.0, z_factor=1.0):
    dem = np.asarray(dem, dtype=float)
    az = np.deg2rad(azimuth_deg)
    alt = np.deg2rad(altitude_deg)

    gy, gx = np.gradient(dem * z_factor, res, res)

    slope = np.arctan(np.hypot(gx, gy))
    aspect = np.arctan2(-gx, gy)
    aspect = np.where(aspect < 0, 2 * np.pi + aspect, aspect)

    hs = (np.sin(alt) * np.cos(slope) +
          np.cos(alt) * np.sin(slope) * np.cos(az - aspect))

    hs = np.clip(hs, 0, 1)
    return (hs * 255).astype(np.uint8)


def openness(dem, radius=5, positive=True):
    dem = np.asarray(dem, dtype=float)
    h, w = dem.shape
    out = np.zeros_like(dem, dtype=float)

    dirs = [(0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    for y in range(h):
        for x in range(w):
            z0 = dem[y, x]
            angles = []
            for dy, dx in dirs:
                for r in range(1, radius + 1):
                    yy = y + dy * r
                    xx = x + dx * r
                    if 0 <= yy < h and 0 <= xx < w:
                        dz = dem[yy, xx] - z0
                        dist = np.hypot(dx * r, dy * r)
                        angles.append(np.arctan2(dz, dist))
            if not angles:
                out[y, x] = 0
                continue
            angles = np.array(angles)
            if positive:
                out[y, x] = np.degrees(np.mean(angles[angles > 0])) if np.any(angles > 0) else 0
            else:
                out[y, x] = np.degrees(np.mean(angles[angles < 0])) if np.any(angles < 0) else 0

    a = np.nan_to_num(out)
    vmin, vmax = np.percentile(a, 2), np.percentile(a, 98)
    if vmax == vmin:
        vmax = vmin + 1
    a = np.clip(a, vmin, vmax)
    return ((a - vmin) / (vmax - vmin) * 255).astype(np.uint8)


def sky_view_factor(dem, radius=5):
    dem = np.asarray(dem, dtype=float)
    h, w = dem.shape
    out = np.zeros_like(dem, dtype=float)

    dirs = [(0, 1), (1, 1), (1, 0), (1, -1),
            (0, -1), (-1, -1), (-1, 0), (-1, 1)]

    for y in range(h):
        for x in range(w):
            z0 = dem[y, x]
            max_angles = []
            for dy, dx in dirs:
                max_ang = -np.inf
                for r in range(1, radius + 1):
                    yy = y + dy * r
                    xx = x + dx * r
                    if 0 <= yy < h and 0 <= xx < w:
                        dz = dem[yy, xx] - z0
                        dist = np.hypot(dx * r, dy * r)
                        ang = np.arctan2(dz, dist)
                        if ang > max_ang:
                            max_ang = ang
                if max_ang > -np.inf:
                    max_angles.append(max_ang)
            if not max_angles:
                out[y, x] = 1.0
                continue
            max_angles = np.array(max_angles)
            svf = np.mean(np.cos(max_angles))
            out[y, x] = svf

    out = np.clip(out, 0, 1)
    return (out * 255).astype(np.uint8)


def msrm(dem, small=3, large=15, n_scales=3):
    """
    MSRM multi‑scala configurabile:
    - small: raggio minimo
    - large: raggio massimo
    - n_scales: numero di scale intermedie
    """
    dem = np.asarray(dem, dtype=float)
    h, w = dem.shape
    out = np.zeros_like(dem, dtype=float)

    if n_scales < 1:
        n_scales = 1
    if large < small:
        large = small

    scales = np.linspace(small, large, n_scales).astype(int)
    scales = np.unique(scales)

    for r in scales:
        pad = r
        padded = np.pad(dem, pad, mode="edge")
        local = np.zeros_like(dem, dtype=float)
        for y in range(h):
            for x in range(w):
                yy = y + pad
                xx = x + pad
                win = padded[yy - r:yy + r + 1, xx - r:xx + r + 1]
                local[y, x] = dem[y, x] - np.mean(win)
        out += local

    a = np.nan_to_num(out)
    vmin, vmax = np.percentile(a, 2), np.percentile(a, 98)
    if vmax == vmin:
        vmax = vmin + 1
    a = np.clip(a, vmin, vmax)
    return ((a - vmin) / (vmax - vmin) * 255).astype(np.uint8)

