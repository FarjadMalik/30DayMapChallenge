import glob
import rasterio
import imageio
import numpy as np
import contextily as ctx
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt

from pathlib import Path
from typing import List, Dict, Tuple   
from rasterio.warp import transform_bounds

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def read_rasters(tif_files: List[str]) -> Tuple[np.ndarray, dict | None, rasterio.Affine | None]:
   """
   Read GeoTIFFs into a 3D numpy array (time, rows, cols). Reads only 1 band.
   Should have the similar transform and profiles
   
   Returns:
      img_arr (np.ndarray): shape (L, H, W) -> (Length of input tifs files, height, width)
      transform: the affince transform of rasters (read from the first file)
      meta: rasterio metadata (profile) of rasters (read from the first file)
   """
   img_arr = []
   meta = None
   transform = None

   for file in tif_files:
      with rasterio.open(file) as src:
         band = src.read(1)
         nodata = src.nodata
         if nodata is not None:  # If nodata is set, mask and replace
            mask = band == nodata 
            band[mask] = 0.0     # Replace nodata pixels with 0

         img_arr.append(band.astype(np.float32))


         if meta is None:
            meta = src.profile
            transform = src.transform
   
   data = np.stack(img_arr, axis=0)
   return data, meta, transform

def create_monthly_animation(dataset, meta, transform, output_path: str, 
                             cmap: str = 'Blues', duration: float = 0.5):
   """
   """
   imgs = []
   
   # compute bounds (left, bottom, right, top) and src crs
   src_crs = meta.get("crs", None)
   if src_crs is None:
      raise RuntimeError(f"Input Rasters have no CRS defined - {src_crs}")
   left, bottom = transform * (0, meta["height"])
   right, top = transform * (meta["width"], 0)

   vmin = np.nanmin(dataset)
   vmax = np.nanmax(dataset)
   norm = plt.Normalize(vmin=vmin,vmax=vmax)

   # for each time input create a separate img
   for t in range(dataset.shape[0]):
      fig = plt.figure(figsize=(8, 5))
      # Use a geographic projection
      ax = plt.axes(projection=ccrs.PlateCarree())
      ax.set_extent([left, right, bottom, top], crs=ccrs.PlateCarree())
      # Add basemap features (coastlines, borders)
      ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
      ax.add_feature(cfeature.BORDERS, linewidth=0.5)
      ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=0)
      # add our dataset to the map with the correct extent/transform
      im = ax.imshow(dataset[t, :, :],
                     cmap=cmap, 
                     norm=norm,
                     extent=(left, right, bottom, top),
                     origin="upper",
                     transform=ccrs.PlateCarree(),
                     zorder=1,
                     )
      # Beautify the map
      ax.set_title(f"Month {t+1}")
      ax.set_axis_off()
      cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
      cb.set_label("Percipitation")

      # save fig to a buffer list for animation
      fig.canvas.draw()
      # Use buffer_rgba (returns an RGBA buffer)
      buf = fig.canvas.renderer.buffer_rgba()
      # Convert to a NumPy array
      img_arr = np.asarray(buf, dtype=np.uint8)
      # img_arr will have shape (height, width, 4) because of RGBA
      # If you only need RGB, you can drop the alpha channel:
      # img_rgb = img_arr[:, :, :3]
      imgs.append(img_arr)

      plt.close(fig=fig)

   # save animation
   imageio.mimsave(f"{output_path}.gif", imgs, duration=duration, loop=0)

def create_seasonal_plots(dataset, meta, transform, output_path, cmap: str = 'Blues'):
   """
   """
   height, width = meta["height"], meta["width"]
   left, bottom = transform * (0, height)
   right, top = transform * (width, 0)
   extent = (left, right, bottom, top)

   vmin = min(np.nanmin(arr) for arr in dataset.values())
   vmax = max(np.nanmax(arr) for arr in dataset.values())
   norm = plt.Normalize(vmin=vmin, vmax=vmax)

   fig, axes = plt.subplots(2, 2, figsize=(12, 10), subplot_kw={"projection": ccrs.PlateCarree()})
   axes = axes.flatten()

   for ax, (season, arr) in zip(axes, dataset.items()):
      ax.set_extent([left, right, bottom, top], crs=ccrs.PlateCarree())
      ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
      ax.add_feature(cfeature.BORDERS, linewidth=0.5)
      ax.add_feature(cfeature.LAND, facecolor="lightgray", zorder=0)

      im = ax.imshow(
         arr,
         cmap=cmap,
         norm=norm,
         extent=extent,
         origin="upper",
         transform=ccrs.PlateCarree(),
         zorder=1,
      )
      ax.set_title(f"{season}")
      ax.axis("off")

   cb = fig.colorbar(im, ax=axes.tolist(), fraction=0.046, pad=0.04)
   cb.set_label("Average Percipitation")
   fig.savefig(f"{output_path}_seasonal.png", dpi=300, bbox_inches='tight')
   plt.close(fig)

def compute_seasonal_averages(data: np.ndarray) -> Dict[str, np.ndarray]:
    """
    Seasonal-average based on the 12 months
    """
    seasons = {
        "Winter (DJF)": [11, 0, 1],
        "Spring (MAM)": [2, 3, 4],
        "Summer (JJA)": [5, 6, 7],
        "Autumn (SON)": [8, 9, 10],
    }
    seasonal = {s: np.nanmean(data[idxs, :, :], axis=0) for s, idxs in seasons.items()}
    return seasonal

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # ClimateAfrica monthly precipitation dataset for 1990-2020 
   prec_files = glob.glob("data/Normal_1991-2020_monthly_tif_2.5m/Prec*")
   logger.debug(f"Prec files len - {len(prec_files)}")

   # Read rasters into an nd.arrary along with metadata
   data, meta, transform = read_rasters(tif_files=prec_files)

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   
   # monthly gif for visualization 
   create_monthly_animation(dataset=data, meta=meta, transform=transform, output_path=output_path)
   s_dataset = compute_seasonal_averages(data=data)
   # logger.debug(f"s_dataset - {[s_dataset[k].shape for k in s_dataset.keys()]}")
   create_seasonal_plots(dataset=s_dataset, meta=meta, transform=transform, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":                        
   filename = 'climateaf_monthly_percipitation_2020'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
