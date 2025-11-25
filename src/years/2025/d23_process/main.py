import rasterio
import numpy as np
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt

from pathlib import Path
from rasterio.plot import plotting_extent
from matplotlib.patches import Patch
from pypalettes import load_cmap

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path
from src.utils.map_helpers import copernicus_lulc_flags


logger = get_logger(__name__)


def create_png(admin, 
               lulc_arr, lulc_transform, 
               dem_arr, dem_transform, 
               pop_arr, pop_transform, 
               output_path):
   """
   """
   # Prepare colormaps using pypalettes
   land_cmap = load_cmap("land", cmap_type="discrete")
   dem_cmap = load_cmap("BluGrn", cmap_type="continuous")
   pop_cmap = load_cmap("Mint", cmap_type="continuous")

   # Normalize DEM amd pop (no need for LULC because its classes)
   dem_min, dem_max = np.nanmin(dem_arr), np.nanmax(dem_arr)
   dem_norm = (dem_arr - dem_min) / (dem_max - dem_min)
   pop_min, pop_max = np.nanmin(pop_arr), np.nanmax(pop_arr)
   pop_norm = (pop_arr - pop_min) / (pop_max - pop_min)
   
   # Get extent for both images
   extent_dem = plotting_extent(dem_norm, dem_transform)
   extent_lc = plotting_extent(lulc_arr, lulc_transform)
   extent_pop = plotting_extent(pop_norm, pop_transform)

   # Build legend for landcover
   # Find unique values and their counts
   unique_vals, counts = np.unique(lulc_arr[~np.isnan(lulc_arr)], return_counts=True) 
   # Get top 5 
   sorted_idx = np.argsort(counts)[::-1]
   top_idx = sorted_idx[:5]
   top_classes = unique_vals[top_idx]
   top_counts = counts[top_idx]
   logger.debug(f"LULC Top Classes {top_classes} - {top_counts}"
                f"- {[copernicus_lulc_flags.get(str(x), 'Unknown') for x in top_classes]}")
   # Not using all classes as legend becomes too large
   # classes = np.unique(lulc_arr[~np.isnan(lulc_arr)]).astype(int)
   # logger.debug(f"LULC Classes {classes.max()} - {classes}")

   patches = []
   for cls in top_classes:
      # Determine a corresponding color — since the colormap is discrete
      color = land_cmap(cls/(unique_vals.max() + 1))
      patches.append(
         Patch(color=color, label=f"{copernicus_lulc_flags.get(str(cls), 'Unknown')}")
         )

   # create fig and axis
   fig, axes = plt.subplots(2, 2, figsize=(14, 12))
   axes = axes.flatten()

   for index, ax in enumerate(axes):
      if index == 0:
         admin_web = admin.to_crs(epsg=3857)
         ax = admin_web.plot(
            ax=ax,
            edgecolor="black",
            facecolor="none",
            linewidth=1
         )
         ctx.add_basemap(ax=ax, source=ctx.providers.OpenStreetMap.Mapnik)
         ax.set_title(
            "Region of Interest",
            fontsize=18,
            fontweight="bold",
            fontfamily="serif",
            )
      elif index == 1:
         # Plot image
         img_lc = ax.imshow(lulc_arr, cmap=land_cmap, extent=extent_lc, origin="upper")
         # Plot region boundary
         admin.plot(ax=ax,
                    edgecolor="black",
                    facecolor="none",
                    linewidth=1
                    )
         # Set axis title
         ax.set_title(
            "Land Use/Land Cover Classification",
            fontsize=18,
            fontweight="bold",
            fontfamily="serif",
            )
         # Add legend for LULC Classes 
         ax.legend(handles=patches,
                  title="Land Use/Cover Classes",
                  loc="upper left",)
                  # bbox_to_anchor=(1.05, 1))
      elif index == 2:  
         # Plot image
         img_dem = ax.imshow(dem_norm, cmap=dem_cmap, extent=extent_dem, origin="upper")
         # Plot region boundary
         admin.plot(ax=ax,
                    edgecolor="black",
                    facecolor="none",
                    linewidth=1
                    )
         # Set axis title
         ax.set_title(
            "Elevation - DEM (Norm)",
            fontsize=18,
            fontweight="bold",
            fontfamily="serif",
            )
         cbar_dem = fig.colorbar(img_dem, ax=ax, fraction=0.046, pad=0.04)
         cbar_dem.set_label("Elevation normalized (0–1)")
      else:
         # Plot image
         img_pop = ax.imshow(pop_norm, cmap=pop_cmap, extent=extent_pop, origin="upper")
         # Plot region boundary
         admin.plot(ax=ax,
                    edgecolor="black",
                    facecolor="none",
                    linewidth=1
                    )
         # Set axis title
         ax.set_title(
            "Population Density (Norm)",
            fontsize=18,
            fontweight="bold",
            fontfamily="serif",
            )
         cbar_pop = fig.colorbar(img_pop, ax=ax, fraction=0.046, pad=0.04)
         cbar_pop.set_label("Population Density normalized (0–1)")
      ax.set_axis_off()
   
   # Add title & legend
   fig.suptitle(
      "Pakistan Landscape Cartography: Landcover, Elevation & Population Density",
      fontsize=22, 
      fontweight="bold",
      fontfamily="serif"
      )

   # Save and close
   plt.tight_layout()
   fig.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   tif_fps = [
      "data/PAK_misc/copernicus_dem/copernicus_dem__PAK.tif",
      "data/PAK_misc/copernicus_lulc/copernicus_lulc__PAK.tif",
      "data/PAK_misc/pak_pop_2025_CN_100m_R2025A_v1.tif"
   ]   

   # Load the shapefile for boundaries or admin units
   shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
   admin_gdf = gpd.read_file(shapefile_path)
   admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

   # Read tif files and store
   lc_img = None
   dem_img = None
   lc_transform = None 
   dem_transform = None
   pop_img = None 
   pop_transform = None

   for f in tif_fps:
      with rasterio.open(f) as src:
         if f.__contains__('lulc'):
            lc_img = src.read(1)
            lc_transform = src.transform
            logger.debug(f"lulc crs - {src.crs}")
         elif f.__contains__('dem'):
            dem_img = src.read(1)
            dem_transform = src.transform
            logger.debug(f"dem crs - {src.crs}")
         elif f.__contains__('pop'):
            pop_crs = src.crs
            pop_img = src.read(1)
            pop_transform = src.transform
            logger.debug(f"pop crs - {src.crs}")
         else:
            raise ValueError(f"Check input tif files. Found - {f} which doesnt correspond with LU/LC or DEM")
         meta = src.meta.copy()
         nodata = meta.get("nodata", None)

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(admin=admin_gdf, 
              lulc_arr=lc_img, lulc_transform=lc_transform, 
              dem_arr=dem_img, dem_transform=dem_transform, 
              pop_arr=pop_img, pop_transform=pop_transform, 
              output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   filename = 'process_of_map'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
