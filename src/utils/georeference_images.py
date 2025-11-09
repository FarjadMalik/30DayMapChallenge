import cv2
import rasterio
import numpy as np

from PIL import Image
from rasterio.transform import Affine

from src.utils.logger import get_logger


def compute_affine_transform(image_points, world_points):
    """
    Compute 2D affine transform from image pixel points to world coordinates.

    Parameters
    ----------
    image_points : ndarray
        Nx2 array of points on the image in pixels.
    world_points : ndarray
        Nx2 array of points in lon/lat coordinates.

    Returns
    -------
    matrix : ndarray
        2x3 affine transformation matrix.
    """
    assert image_points.shape[0] >= 3, "At least 3 points required."
    matrix = cv2.getAffineTransform(np.float32(image_points[:3]), np.float32(world_points[:3]))
    return matrix

def georeference_image(image_path, matrix, out_path):
    """
    Georeference a raster image using an affine transform.

    Parameters
    ----------
    image_path : str
        Path to analog map image.
    matrix : ndarray
        2x3 affine transformation matrix from compute_affine_transform.
    out_path : str
        Path to save georeferenced raster.
    """
    img = Image.open(image_path)
    img_arr = np.array(img)

    # Apply affine transform to image
    rows, cols = img_arr.shape[:2]
    transformed = cv2.warpAffine(img_arr, matrix, (cols, rows))

    # Extract affine coefficients for rasterio
    a, b, c = matrix[0]
    d, e, f = matrix[1]
    transform = Affine(a, b, c, d, e, f)

    # Save with rasterio
    with rasterio.open(
        out_path,
        'w',
        driver='GTiff',
        height=transformed.shape[0],
        width=transformed.shape[1],
        count=3 if transformed.ndim==3 else 1,
        dtype=transformed.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        if transformed.ndim == 3:
            for i in range(3):
                dst.write(transformed[:,:,i], i+1)
        else:
            dst.write(transformed, 1)

## You need at least 3 points for an affine transform (translation, scaling, rotation). 
# Points on the analog map (pixels)
# image_points = np.array([
#     [x1, y1],
#     [x2, y2],
#     [x3, y3]
# ])

# # Corresponding points in real-world coordinates (lon, lat)
# world_points = np.array([
#     [lon1, lat1],
#     [lon2, lat2],
#     [lon3, lat3]
# ])
# Tip: Use a tool like GIMP or ImageJ to get pixel coordinates on your analog map.

# # Pixel coordinates on the analog map
# image_points = np.array([
#     [100, 200],  # Example: top-left
#     [800, 220],  # top-right
#     [120, 900]   # bottom-left
# ])

# # Real-world coordinates in lon/lat
# world_points = np.array([
#     [68, 36],   # corresponds to top-left
#     [97, 36],   # top-right
#     [68, 6]     # bottom-left
# ])

# matrix = compute_affine_transform(image_points, world_points)
# georeference_image("british_india_map.png", matrix, "british_india_map_geo.tif")


# maps_info = [
#     {"path": "british_india_map_1850.png", "image_points": image_points, "world_points": world_points},
#     {"path": "british_india_map_1900.png", "image_points": image_points, "world_points": world_points},
# ]

# for info in maps_info:
#     matrix = compute_affine_transform(info["image_points"], info["world_points"])
#     out_path = info["path"].replace(".png", "_geo.tif")
#     georeference_image(info["path"], matrix, out_path)
