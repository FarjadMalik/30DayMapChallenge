import rasterio
import numpy as np
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from pyfonts import load_font
from pypalettes import load_cmap
import matplotlib.patheffects as path_effects
from matplotlib.patches import Patch
from matplotlib_scalebar.scalebar import ScaleBar
from rasterio.mask import mask

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)

   
def create_png(admin, glaciers_gdf, rivers_gdf, raster_arr, raster_transform, output_path):
   """
   """
   if raster_arr.ndim != 3 or raster_arr.shape[0] == 3:
      raster_arr = np.transpose(raster_arr, (1, 2, 0))
      logger.debug(f"Img Raster shape - {raster_arr.shape}")
   elif raster_arr.ndim != 3 or raster_arr.shape[0] == 3:
       raise ValueError(f"Input Img arr must be a 3-band RGB array")
   
   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   # Normalize raster to 0–1 for display, preserving dynamic range
   raster_arr = raster_arr.astype("float32")
   raster_min, raster_max = np.min(raster_arr), np.max(raster_arr)
   if raster_max > 1.0 or raster_min < 0.0:
      raster_arr = (raster_arr - raster_min) / (raster_max - raster_min)

   # Load custom font and cmap
   cmap = load_cmap("Beach", cmap_type="continuous")

   # create fig and axis
   fig, ax = plt.subplots(figsize=(12, 10))

   # Plot raster with a perceptually uniform colormap as a background layer
   ax.imshow(raster_arr, origin="upper", 
             extent=(
               raster_transform.c,
               raster_transform.c + raster_transform.a * raster_arr.shape[1],
               raster_transform.f + raster_transform.e * raster_arr.shape[0],
               raster_transform.f
             ),
            cmap=cmap, 
            alpha=0.8, 
            interpolation="bicubic")

   # plot admin boundaries
   admin.plot(
      ax=ax,
      facecolor='none',
      edgecolor='black',
      linewidth=1.2,
      alpha=0.3,
      zorder=3
   )
   
   # plot glacier polygons with colors
   glaciers_gdf.plot(
      ax=ax,
      facecolor='#88ccee', # fill
      edgecolor='#88ccee', # outline
      linewidth=0.8,
      alpha=0.9,
      zorder=4,
      label="Glaciers"
   )

   # plot river lines with colors
   rivers_gdf.plot(
      ax=ax,
      color='#4477aa',
      linewidth=1,
      alpha=0.9,
      zorder=5,
      label="Rivers"
   )

   # Set limits and range from the center coordinates
   ax.set_xlim(center_lon - 9, center_lon + 9)
   ax.set_ylim(center_lat - 9, center_lat + 9)

   # Add title & legend
   ax.set_title(
      "Natural Earth Indus Basin Water (Glaciers, Rivers & Lakes)",
      fontsize=20,
      fontweight="bold",
      pad=20
   )

   # Define your color mapping for phases (for legend use, takes care of missing phases in the dataset)
   type_color_dict = {
      'Glacier': '#88ccee', 
      'River': '#4477aa',
   }
   legend_elements = []
   for type, color in type_color_dict.items():
      legend_elements.append(Patch(facecolor=color, edgecolor=color,
                                    label=f"{type}"))
   
   # Add legend
   ax.legend(
      handles=legend_elements,
      title="Artefacts",
      loc="upper left", # legend location
      facecolor="white",
      framealpha=0.8,
      edgecolor="gray",
      frameon=True
   )

   # Add scale bar (uses matplotlib-scalebar)
   scalebar = ScaleBar(
      raster_transform.a, units="m", location="lower left",
      pad=0.5, border_pad=0.5, color="black", frameon=True, box_alpha=0.5, rotation='horizontal-only'
   )
   ax.add_artist(scalebar)

   # Optional: add north arrow
   ax.annotate(
      "N",
      xy=(1.001, 0.7),
      xytext=(1.001, 0.6),
      arrowprops=dict(facecolor="black", width=5, headwidth=15),
      ha="center",
      va="center",
      fontsize=16,
      xycoords="axes fraction",
   )
   
   # Save and close
   ax.set_axis_off()
   plt.tight_layout()
   fig.savefig(output_path, dpi=300, bbox_inches="tight")
   plt.close(fig)

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for our area of interest
   hydrobasin_as_gdf = gpd.read_file("data/hybas_lake_as_lev01-12_v1c/hybas_lake_as_lev03_v1c.shp")
   hydrobasin_as_gdf = hydrobasin_as_gdf.loc[hydrobasin_as_gdf['HYBAS_ID']==4030033640,
                                             ['HYBAS_ID', 'SUB_AREA', 'geometry']]
   logger.debug(f"hydrobasin_as_gdf len - {len(hydrobasin_as_gdf)}")
   logger.debug(f"hydrobasin_as_gdf columns - {hydrobasin_as_gdf.columns}")

   # Load natural earth datasets 
   # Glaciers
   ne_glaciated_areas = gpd.read_file("data/ne_10m_glaciated_areas/ne_10m_glaciated_areas.shp")
   ne_glaciated_areas = ne_glaciated_areas[['name', 'scalerank', 'recnum', 'geometry']]
   # Clip glaciers to Basin boundary
   ne_glaciated_areas = gpd.clip(ne_glaciated_areas, hydrobasin_as_gdf, keep_geom_type=True)
   logger.debug(f"ne_glaciated_areas len - {len(ne_glaciated_areas)}")
   logger.debug(f"ne_glaciated_areas columns - {ne_glaciated_areas.columns}")
   # Rivers
   ne_rivers = gpd.read_file("data/ne_10m_rivers_lake_centerlines/ne_10m_rivers_lake_centerlines.shp")
   ne_rivers = ne_rivers[['name', 'name_ur', 'scalerank', 'rivernum', 'geometry']]
   # Clip rivers to Basin boundary
   ne_rivers = gpd.clip(ne_rivers, hydrobasin_as_gdf, keep_geom_type=True)
   logger.debug(f"ne_rivers len - {len(ne_rivers)}")
   logger.debug(f"ne_rivers columns - {ne_rivers.columns}")

   # Natural Earth 2 50M SR imagery
   fp_ne2_sr_tif = "data/NE2_50M_SR_W/NE2_50M_SR_W.tif"
   with rasterio.open("data/NE2_50M_SR_W/NE2_50M_SR_W.tif") as src:
      ne2_sr_img_crs = src.crs
      ne2_sr_img = src.read()
      meta = src.meta.copy()
      nodata = meta.get("nodata", None)

      # Clip raster to Basin boundary
      ne2_sr_img, ne2_transform = mask(src, hydrobasin_as_gdf.geometry, crop=True)

   logger.debug(f"ne2_sr_img crs - {ne2_sr_img_crs}")
   logger.debug(f"ne2_sr_img nodata - {nodata}")
   logger.debug(f"ne2_sr_img meta - {meta}")
   logger.debug(f"ne2_sr_img shape - {ne2_sr_img.shape}")  
   logger.debug(f"ne2_sr_img transform - {ne2_transform}") 

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(hydrobasin_as_gdf, 
              ne_glaciated_areas, ne_rivers, 
              ne2_sr_img, ne2_transform, 
              output_path=output_path)
   # create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # Download some natural earth dataset and play around
   # data/ne_10m_rivers_lake_centerlines/ne_10m_rivers_lake_centerlines.shp
   # Rivers of Africa or Asia + Glaciers, Land of the 7 rivers link it to Noah
   filename = 'natural_earth'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
