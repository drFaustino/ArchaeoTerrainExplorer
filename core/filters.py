import numpy as np


def nan_mean_filter(arr, size=3):
    """
    Fast NaN-aware mean filter (replacement for scipy in simple cases).
    Suitable for small kernel smoothing (3–11 typical in DEM analysis).
    """
    if size <= 1:
        return arr

    pad = size // 2
    padded = np.pad(arr, pad, mode="edge")

    out = np.zeros_like(arr, dtype=float)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            window = padded[i:i+size, j:j+size]
            out[i, j] = np.nanmean(window)

    return out


def gaussian_like_filter(arr, sigma=1.0):
    """
    Lightweight approximation of Gaussian smoothing without scipy.
    Uses separable kernel approximation.
    """
    from math import exp, sqrt

    radius = int(3 * sigma)
    x = np.arange(-radius, radius + 1)
    kernel = np.array([exp(-(i**2) / (2 * sigma**2)) for i in x])
    kernel /= kernel.sum()

    def conv1d(mat, axis):
        return np.apply_along_axis(
            lambda m: np.convolve(m, kernel, mode="same"),
            axis,
            mat
        )

    return conv1d(conv1d(arr, axis=0), axis=1)


def multi_scale_lrm(arr, small=3, large=15):
    """
    Multi-scale Local Relief Model (LRM).
    Core archaeological enhancement filter.
    """
    small_f = nan_mean_filter(arr, small)
    large_f = nan_mean_filter(arr, large)

    return small_f - large_f


def edge_enhancement(arr):
    """
    Simple Laplacian edge detector for archaeological micro-relief.
    """
    kernel = np.array([
        [0, -1,  0],
        [-1, 4, -1],
        [0, -1,  0]
    ], dtype=float)

    pad = 1
    padded = np.pad(arr, pad, mode="edge")
    out = np.zeros_like(arr, dtype=float)

    for i in range(arr.shape[0]):
        for j in range(arr.shape[1]):
            window = padded[i:i+3, j:j+3]
            out[i, j] = np.nansum(window * kernel)

    return out


def anisotropic_smoothing(arr, iterations=2):
    """
    Very lightweight anisotropic-like smoothing (edge-preserving).
    Not full Perona-Malik, but stable for DEM preprocessing.
    """
    out = arr.copy()

    for _ in range(iterations):
        north = np.roll(out, -1, axis=0)
        south = np.roll(out, 1, axis=0)
        east = np.roll(out, -1, axis=1)
        west = np.roll(out, 1, axis=1)

        out = (out + north + south + east + west) / 5.0

    return out