import numpy as np

def raster_block_to_array(block):
    """QGIS 4 safe raster extraction"""
    w = block.width()
    h = block.height()

    arr = np.zeros((h, w), dtype=float)

    for y in range(h):
        for x in range(w):
            arr[y, x] = block.value(y, x)

    return arr