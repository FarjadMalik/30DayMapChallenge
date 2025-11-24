import folium
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_png(admin, dataset, output_path):
   """
   """
   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   # create fig and axis
   _, ax = plt.subplots(figsize=(12, 10))

   # plot admin boundaries
   admin.plot(
      ax=ax,
      color='white',
      edgecolor='black',
      linewidth=1
   )
   
   # plot polygons with colors
   dataset.plot(
      ax=ax,
      facecolor=dataset['color'], # fill
      edgecolor=dataset['color'], # outline
      # color='', # both fill and outline
      linewidth=1,
      alpha=0.7
   )
   # Set limits and range from the center coordinates
   ax.set_xlim(center_lon - 9, center_lon + 9)
   ax.set_ylim(center_lat - 9, center_lat + 9)

   # Add title & legend
   ax.set_title(
      "TITLE",
      fontsize=18,
      fontweight="bold",
      pad=20
   )

   # Define your color mapping for phases (for legend use, takes care of missing phases in the dataset)
   phase_color_dict = {
      1: '#fae61e', # Level 1
   }
   legend_elements = []
   for phase, color in phase_color_dict.items():
      legend_elements.append(Patch(facecolor=color, edgecolor=color,
                                    label=f"Level {phase}"))
   
   # Beautify, add legend and save
   ax.legend(
      handles=legend_elements,
      title="Legend Title",
      loc="upper left", # legend location
      frameon=True
   )
   ax.set_axis_off()
   # plt.tight_layout()
   plt.savefig(output_path, dpi=500, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for boundaries or admin units
   sudan_gdf = gpd.read_file("data/Sudan_misc/locality_polygon_mar20/Locality_Polygon_Mar20.shp")
   logger.debug(f"Sudan GDF CRS: {sudan_gdf.crs}")
   logger.debug(f"Sudan GDF Shape: {sudan_gdf.shape}")
   logger.debug(f"Sudan GDF Columns: {sudan_gdf.columns}")

   # sudan_gdf = sudan_gdf[['COUNTRY', 'NAME_1', 'geometry']]

   sudan_idp_df = pd.read_json("data/Sudan_misc/undp_internallydisplacedpeople.json")
   logger.debug(f"Sudan IDPs head - {sudan_idp_df.head()}")
   logger.debug(f"Sudan IDPs  Shape: {sudan_idp_df.shape}")
   logger.debug(f"Sudan IDPs  Columns: {sudan_idp_df.columns}")

   sudan_ref_df = pd.read_json("data/Sudan_misc/undp_selfrelocatedrefugees.json")
   logger.debug(f"Sudan Self Ref head - {sudan_ref_df.head()}")
   logger.debug(f"Sudan Self Ref  Shape: {sudan_ref_df.shape}")
   logger.debug(f"Sudan Self Ref  Columns: {sudan_ref_df.columns}")


   dfs = pd.read_excel("data/Sudan_misc/sudan_hrp_political_violence_events_and_fatalities_by_month-year_as-of-13nov2025.xlsx", sheet_name=None)
   logger.debug(f"File: sudan_hrp_political_violence_events_and_fatalities_by_month-year")
   for name, frame in dfs.items():
      logger.debug(f"Sheet: {name}")
      logger.debug(f"Head - {sudan_ref_df.head()}")
      logger.debug(f"Shape: {sudan_ref_df.shape}")
      logger.debug(f"Columns: {sudan_ref_df.columns}")
   
   dfs = pd.read_excel("data/Sudan_misc/2024-consolidated-3w-data-jan-to-dec.xlsx", sheet_name=None)
   logger.debug(f"File: 2024-consolidated-3w-data-jan-to-dec")
   for name, frame in dfs.items():
      logger.debug(f"Sheet: {name}")
      logger.debug(f"Head - {sudan_ref_df.head()}")
      logger.debug(f"Shape: {sudan_ref_df.shape}")
      logger.debug(f"Columns: {sudan_ref_df.columns}")
   
   dfs = pd.read_excel("data/Sudan_misc/all-sudan-3ws-data-combined_2014-2019.xlsx", sheet_name=None)
   logger.debug(f"File: all-sudan-3ws-data-combined_2014-2019")
   for name, frame in dfs.items():
      logger.debug(f"Sheet: {name}")
      logger.debug(f"Head - {sudan_ref_df.head()}")
      logger.debug(f"Shape: {sudan_ref_df.shape}")
      logger.debug(f"Columns: {sudan_ref_df.columns}")
   
   
   # data\Sudan_misc\DTM Sudan - Countrywide Mobility.csv - STATE OF DISPLACEMET,STATE of ORIGIN,INDIVIUALS

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   # create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)
   # create_png(admin=admin_gdf, dataset=dataset, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Tesselations over sudan and internally displaced people      
    filename = 'sudan_idp_hexmap'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
