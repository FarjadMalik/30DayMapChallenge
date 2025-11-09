import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import rasterio
from rasterio.transform import Affine
import cv2
from tkinter import Tk, filedialog

class MapGeoreferencer:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image = Image.open(image_path)
        self.image_points = []
        self.world_points = []
        self.fig, self.ax = plt.subplots()
        self.ax.imshow(self.image)
        self.cid = self.fig.canvas.mpl_connect('button_press_event', self.onclick)
        self.num_points = 0
        self.max_points = 0

    def onclick(self, event):
        if event.inaxes != self.ax:
            return
        if len(self.image_points) < self.max_points:
            self.image_points.append([event.xdata, event.ydata])
            self.ax.plot(event.xdata, event.ydata, 'ro')
            self.fig.canvas.draw()
            print(f"Selected image point: {event.xdata:.2f}, {event.ydata:.2f}")

    def select_points(self, n_points):
        self.max_points = n_points
        print(f"Please click {n_points} points on the image.")
        plt.show()
        return np.array(self.image_points)

    def input_world_points(self, n_points):
        print(f"Enter the corresponding world coordinates (lon, lat) for each point:")
        for i in range(n_points):
            coords = input(f"Point {i+1} (format: lon,lat): ")
            lon, lat = map(float, coords.strip().split(','))
            self.world_points.append([lon, lat])
        return np.array(self.world_points)


def compute_affine_transform(image_points, world_points):
    """
    Compute 2D affine transform using first 3 points.
    """
    assert image_points.shape[0] >= 3, "At least 3 points required."
    matrix = cv2.getAffineTransform(np.float32(image_points[:3]), np.float32(world_points[:3]))
    return matrix

def compute_homography(image_points, world_points):
    """
    Compute homography using at least 4 points.
    """
    assert image_points.shape[0] >= 4, "At least 4 points required."
    matrix, _ = cv2.findHomography(np.float32(image_points), np.float32(world_points))
    return matrix

def georeference_image(image_path, matrix, out_path, method='affine'):
    img = Image.open(image_path)
    img_arr = np.array(img)
    rows, cols = img_arr.shape[:2]

    if method == 'affine':
        transformed = cv2.warpAffine(img_arr, matrix, (cols, rows))
        a, b, c = matrix[0]
        d, e, f = matrix[1]
        transform = Affine(a, b, c, d, e, f)
    else:  # homography
        transformed = cv2.warpPerspective(img_arr, matrix, (cols, rows))
        # Approximate affine transform from homography for rasterio
        transform = Affine.identity()  # you can refine this if needed

    with rasterio.open(
        out_path,
        'w',
        driver='GTiff',
        height=transformed.shape[0],
        width=transformed.shape[1],
        count=3 if transformed.ndim == 3 else 1,
        dtype=transformed.dtype,
        crs='EPSG:4326',
        transform=transform
    ) as dst:
        if transformed.ndim == 3:
            for i in range(3):
                dst.write(transformed[:, :, i], i + 1)
        else:
            dst.write(transformed, 1)
    print(f"Georeferenced image saved as: {out_path}")


# Launch file dialog to select an image
root = Tk()
root.withdraw()
image_file = filedialog.askopenfilename(title="Select Analog Map Image")
root.destroy()

georef = MapGeoreferencer(image_file)

# Step 1: Pick points interactively
n_points = int(input("How many points do you want to select? (min 3 for affine, 4+ for homography): "))
image_pts = georef.select_points(n_points)

# Step 2: Input corresponding world coordinates
world_pts = georef.input_world_points(n_points)

# Step 3: Compute transformation
if n_points >= 4:
    matrix = compute_homography(image_pts, world_pts)
    method = 'homography'
else:
    matrix = compute_affine_transform(image_pts, world_pts)
    method = 'affine'

# Step 4: Save georeferenced image
out_file = image_file.replace(".png", "_geo.tif")
georeference_image(image_file, matrix, out_file, method)
