import numpy as np

def slope(arr, res):
    dzdx = (arr[:, 2:] - arr[:, :-2]) / (2 * res)
    dzdy = (arr[2:, :] - arr[:-2, :]) / (2 * res)

    dzdx = dzdx[1:-1, :]
    dzdy = dzdy[:, 1:-1]

    return np.sqrt(dzdx**2 + dzdy**2)


def curvature(arr, res):
    zxx = (arr[:, 2:] - 2 * arr[:, 1:-1] + arr[:, :-2]) / (res**2)
    zyy = (arr[2:, :] - 2 * arr[1:-1, :] + arr[:-2, :]) / (res**2)

    return zxx[1:-1, :] + zyy[:, 1:-1]


def lrm(arr, small=3, large=15):
    from scipy.ndimage import uniform_filter
    return uniform_filter(arr, small) - uniform_filter(arr, large)