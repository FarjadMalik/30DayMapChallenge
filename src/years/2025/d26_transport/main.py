import rasterio
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from pathlib import Path
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from matplotlib_scalebar.scalebar import ScaleBar
from shapely.geometry import LineString
from rasterio.plot import plotting_extent

from pypalettes import load_cmap
from pyfonts import load_font

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_png_extra(ports, lanes, invisible_lanes, distance_raster, output_path):
   """
   """
   # --- Map setup ---
   proj = ccrs.Robinson()
   fig = plt.figure(figsize=(12, 10), dpi=300)
   ax = plt.axes(projection=proj)

   # Prepare background data
   ax.add_feature(cfeature.LAND, facecolor="#f0f0f0")
   ax.add_feature(cfeature.OCEAN, facecolor="#acceff")
   ax.add_feature(cfeature.COASTLINE, edgecolor="black", linewidth=0.8)
   ax.add_feature(cfeature.BORDERS, edgecolor="gray", linewidth=0.4)
   ax.set_global()

   # Read distance-from-ports raster
   with rasterio.open(distance_raster) as src:
      # Read first (or single) band as masked array
      arr = src.read(1, masked=True)
      # Mask out land where value == 0
      # Assuming land is exactly 0 in your raster
      mask_land = (arr < 5000)  # adjust threshold as needed, 5km here
      arr_masked = np.ma.array(arr, mask=mask_land)

      # Convert meters to kilometers
      arr_km = arr_masked / 1000.0

      # Compute the plotting extent (bounds)
      ext = plotting_extent(src, src.transform)

      # Use a sequential colormap so it's not too aggressive
      cmap = load_cmap("Aluterus_scriptus", keep=[False, True, True, True, True], reverse=True)  

      # Plot raster
      im = ax.imshow(
         arr_km,
         origin="upper",
         extent=ext,
         transform=proj,  # this means that the image is interpreted in the map CRS
         cmap=cmap,
         alpha=0.4,  # semi-transparent so other layers show through
      )

      # Add colorbar
      cbar = plt.colorbar(im, ax=ax, orientation="vertical", shrink=0.5, pad=0.05)
      cbar.set_label("Distance from Ports (km)")

   # # --- Invisible lanes (AIS gap) ---
   # # Convert events to geometries (LineString) for plotting
   # # Note: these are lon/lat in events, assumed in same CRS as map
   # invisible_lines = []
   # for _, row in invisible_lanes.iterrows():
   #    start = (row["gap_start_lon"], row["gap_start_lat"])
   #    end = (row["gap_end_lon"], row["gap_end_lat"])
   #    geom = LineString([start, end])
   #    invisible_lines.append(geom)
   # gdf_invis = gpd.GeoDataFrame(invisible_lanes, geometry=invisible_lines, crs="EPSG:4326")

   # # Reproject invisible-lines to map CRS
   # gdf_invis_proj = gdf_invis.to_crs(proj.proj4_init)

   # # Plot invisible lines; color by gap hours (or by another attribute)
   # # For example: use a colormap for the duration of the gap
   # norm = plt.Normalize(vmin=gdf_invis_proj["gap_hours"].min(), vmax=gdf_invis_proj["gap_hours"].max())
   # cmap_lines = load_cmap("Bryaninops_natans", cmap_type='continuous' ,keep=[False, True, True, True, False], reverse=True)

   # for _, row in gdf_invis_proj.iterrows():
   #    ax.add_geometries(
   #       [row.geometry],
   #       crs=proj,
   #       edgecolor=cmap_lines(norm(row["gap_hours"])),
   #       facecolor="none",
   #       linewidth=1.0,
   #       alpha=0.9,
   #       zorder=4,
   #    )

   # # Add a colorbar / legend for invisible-lane hours
   # # Create a ScalarMappable for the colorbar
   # sm = plt.cm.ScalarMappable(cmap=cmap_lines, norm=norm)
   # sm.set_array([])  # only needed for the colorbar
   # cbar2 = plt.colorbar(sm, ax=ax, orientation="horizontal", fraction=0.046, pad=0.04)
   # cbar2.set_label("AIS Gap Duration (hours)")

   # Add title & legend
   ax.set_title(
      "Invisible Shipping Lanes (AIS Disabling Events) & Distance from Ports",
      fontsize=18,
      fontweight="bold",
      pad=20
   )

   # Save and close
   ax.set_axis_off()
   plt.tight_layout()
   plt.savefig(output_path, dpi=300, bbox_inches="tight")
   plt.close(fig)

def create_png(ports, lanes, output_path):
   """
   """
   # Set up the map with Cartopy
   proj = ccrs.Robinson()
   proj4 = proj.proj4_init

   # create fig and axis
   fig = plt.figure(figsize=(12, 10), dpi=300)
   ax = plt.axes(projection=proj)
   # ax.set_extent([bounds[0], bounds[2], bounds[1], bounds[3]])
   ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
   ax.add_feature(cfeature.OCEAN, facecolor='#acceff')
   ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.8)
   ax.add_feature(cfeature.BORDERS, edgecolor='gray', linewidth=0.4)
   ax.set_global()

   # Adding shipping lanes
   # reproject lanes to ccrs map projection
   lanes = lanes.to_crs(proj4)
   # get colormap for lanes
   lane_cmap = load_cmap('Althoff', keep=[False, True, True, True, False], reverse=True)
   # map lane types to colors
   lane_types = lanes['Type'].unique()
   lane_to_color = dict(zip(lane_types, lane_cmap.colors[:len(lane_types)]))
   # logger.debug(f"lanes_color: {lane_to_color}")
   # plot lanes with varying colors & linewidths based on type
   lanes.plot(
      ax=ax,
      transform=proj,
      color=lanes['Type'].map(lane_to_color),
      linewidth=lanes['Type'].map(lambda x: 0.7 if x == "Minor" else (1.0 if x == "Middle" else 1.5)),
      alpha=1,
      zorder=2
   )

   # Add global ports
   # reproject ports to ccrs map projection
   ports = ports.to_crs(proj4)
   # get colormap for ports
   port_cmap = load_cmap("Badlands", keep=[False, True, True, True, True])
   # map port sizes to colors
   port_sizes = ports['prtsize'].unique()
   port_to_color = dict(zip(port_sizes, port_cmap.colors[:len(port_sizes)]))
   # logger.debug(f"port_to_color: {port_to_color}")
   # plot ports with varying colors & sizes based on size
   ports.plot(
      ax=ax,
      transform=proj,
      color=ports['prtsize'].map(port_to_color),
      marker='^',
      markersize=ports['prtsize'].map(lambda x: 10 if x == "Small" else (20 if x == "Medium" else (40 if x == "Large" else 5))),
      alpha=0.8,
      zorder=3,
      edgecolor='k',
      linewidth=0.3
   )
   
   # Add title & legend
   ax.set_title(
      "Global Ports and Shipping Lanes",
      fontsize=18,
      fontweight="bold",
      pad=20
   )

   # Add port size legend
   legend_handles = []
   for cat in port_to_color.keys():
      legend_handles.append(
         Line2D(
               [0],
               [0],
               marker="^",
               color="w",
               markerfacecolor=port_to_color[cat],
               markeredgecolor="black",
               markersize=8,
               label=cat.capitalize(),
         )
      )
   port_legend = ax.legend(handles=legend_handles, title="Port (& their Sizes)", loc="upper left")

   ax.add_artist(port_legend)

   # Second legend: for shipping lanes
   lane_handles = [
      Line2D([0], [0], 
             color=lane_to_color[ltype], 
             lw=2, 
             label=ltype.capitalize())
      for ltype in lane_types
   ]
   lanes_legend = ax.legend(
      handles=lane_handles,
      title="Shipping Lanes (& their Types)",
      loc="lower right"
   )
   # ax.add_artist(lanes_legend)
   ax.set_axis_off()
   plt.tight_layout()
   plt.savefig(output_path, dpi=300, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load ports and shipping lanes of the world
   ports_gdf = gpd.read_file("data/global_ports/GLOBAL_Ports.shp", parse_dates=False)
   shipping_lanes_gdf = gpd.read_file("data/Shipping_Lanes_v1.geojson")
   # other datasets (Global fishing network), distance from port raster
   distance_raster_path = "data/distance-from-port-v1.tiff" # meters
   # AIS disabling events (AIS data points where transponders were disabled)
   ais_events_df = pd.read_csv("data/ais_disabling_events.csv")
   
   # Filter unnecessary columns
   ports_gdf = ports_gdf[['objectid', 'portname', 'prtsize', 'country', 'geometry']]
   shipping_lanes_gdf = shipping_lanes_gdf[['Type', 'geometry']]
   ais_events_df = ais_events_df[['gap_start_lat', 'gap_start_lon', 'gap_end_lat', 'gap_end_lon', 'gap_hours']]
   
   # Clean port size data
   ports_gdf['prtsize'] = ports_gdf['prtsize'].fillna('Unknown')
   ports_gdf['prtsize'] = ports_gdf['prtsize'].replace({
      'Small': 'Small',
      'Medium': 'Medium',
      'Large': 'Large',
      'small': 'Small',
      'medium': 'Medium',
      'large': 'Large',
      'Very Small': 'Small'})
   # logger.debug(f"Port sizes:\n{ports_gdf['prtsize'].unique()}")
   # logger.debug(f"Port sizes counts:\n{ports_gdf['prtsize'].value_counts()}")

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(ports=ports_gdf, lanes=shipping_lanes_gdf, 
              output_path=output_path)
   # create_png_extra(ports=ports_gdf, lanes=shipping_lanes_gdf,
   #                  invisible_lanes=ais_events_df, distance_raster=distance_raster_path,
   #                  output_path=f"{Path(path_dir).parent}/{filename}_AIS.png")

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # (World Sustainable Transport Day) Map mobility on the seas, Global Shipping Lanes, or ports.
   filename = 'marine_transport'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
