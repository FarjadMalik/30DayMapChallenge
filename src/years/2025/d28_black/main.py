import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from pathlib import Path
from tqdm import tqdm
from PIL import Image
from pypalettes import load_cmap
from matplotlib import animation, colors, patches
from matplotlib.lines import Line2D

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_png(world, output_path, simplify_tolerance=0.1):
   """
   """
   # logger.debug(f"CRS - {world.crs}")
   # Define color scheme
   # Take mean of deaths because large are most likely outliers, better coloring
   v_max = np.mean(world['Best estimate'])
   cmap = load_cmap("X56", cmap_type="continuous", reverse=True)
   norm = colors.Normalize(vmin=0, vmax=v_max)
   
   # Get years in dataset
   years = sorted(world["Year"].dropna().unique())
   logger.debug(f"Years in dataset: {years}")
   logger.debug(f"Years len: {len(years)}")

   # Simplify geometries for speed
   # if simplify_tolerance > 0:
   #    world = world.copy()
   #    world["geometry"] = world["geometry"].simplify(simplify_tolerance)

   frames = []
   for year in tqdm(years, desc="Rendering frames"):
      # create fig and axis
      fig, ax = plt.subplots(figsize=(10, 6), 
                             subplot_kw={'projection': ccrs.PlateCarree()})
      # fig.set_facecolor('black')

      # Add land and ocean with natural colors
      ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
      ax.add_feature(cfeature.OCEAN, facecolor='#acceff')
      ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.8)
      ax.add_feature(cfeature.BORDERS, edgecolor='gray', linewidth=0.4)

      # Set global extent
      ax.set_global()
      ax.set_axis_off()
      
      # Colorbar (constant for all frames)
      sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
      sm._A = []  # required trick
      cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", shrink=0.6)
      cbar.set_label("Number of Deaths")
      
      # Filter for the specific year and plot
      world_year = world[world["Year"] == year]
      world_year.plot(
         ax=ax,
         column="Best estimate",
         cmap=cmap,
         norm=norm,
         edgecolor="white",
         linewidth=0.4,
         zorder=10,
         transform=ccrs.PlateCarree()
      )
      # ax.set_title(f"Deaths in armed conflict – {year:.0f}", fontsize=16)

      fig.text(
         0.5, 0.95,
         f"Deaths in armed conflict around the world – Year {year:.0f}",
         horizontalalignment="center",
         fontsize=16,
         weight="bold",
         # color='white'
      )
      fig.text(
         0.5, 0.90,
         "Based on data from HDX and Uppsala Conflict Data Program (UCDP)",
         horizontalalignment="center",
         fontsize=12,
         # color='white'
      )
        
      # Capture the plot as an image, redraw to activate
      fig.canvas.draw()
      # Get RGBA buffer from the figure
      buf = fig.canvas.buffer_rgba()
      # Convert to PIL Image in RGB mode
      image = Image.frombuffer(
         'RGBA', 
         fig.canvas.get_width_height(), 
         buf, 
         'raw', 
         'RGBA', 
         0, 
         1
      ).convert('RGB')
      # Add to our frames list
      frames.append(image)
      plt.close(fig)
    
   # Save frames as a GIF
   frames[0].save(
      f"{output_path}.gif",
      save_all=True,
      append_images=frames[1:],
      duration=500,
      loop=0
   ) 
   # Save as mp4
   import imageio.v2 as imageio

   with imageio.get_writer(f"{output_path}.mp4", fps=1, format="ffmpeg") as writer:
      for frame in frames:
         writer.append_data(np.array(frame))   # frame must be a NumPy array

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Deaths in armed conflicts around the world
   conflict_deaths_csv = pd.read_csv("data/deaths-in-armed-conflicts-based-on-where-they-occurred.csv")
   # Replace country names to match shapefile
   conflict_deaths_csv['Entity'] = conflict_deaths_csv['Entity'].replace({
      'Bosnia and Herzegovina': 'Bosnia and Herz.', 
      'Marshall Islands': 'Marshall Is.', 
      'Eswatini': 'eSwatini', 
      'Antigua and Barbuda': 'Antigua and Barb.', 
      'United States': 'United States of America', 
      'Solomon Islands': 'Solomon Is.', 
      'South Sudan': 'S. Sudan', 
      'Central African Republic': 'Central African Rep.', 
      'Saint Kitts and Nevis': 'St. Kitts and Nevis', 
      'Western Sahara': 'W. Sahara', 
      'Dominican Republic': 'Dominican Rep.', 
      'East Timor': 'Timor-Leste', 
      'Democratic Republic of Congo': 'Dem. Rep. Congo', 
      'Saint Vincent and the Grenadines': 'St. Vin. and Gren.', 
      'Sao Tome and Principe': 'São Tomé and Principe', 
      "Cote d'Ivoire": "Côte d'Ivoire", 
      'Equatorial Guinea': 'Eq. Guinea'
   })

   # Load the shapefile for world admin boundaries with all countries
   world_gdf = gpd.read_file("data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
   # Keep only relevant columns
   world_gdf = world_gdf[['NAME', 'TYPE', 'ADM0_A3', 'POP_EST', 'POP_RANK', 
                          'GDP_MD', 'ECONOMY', 'INCOME_GRP', 'CONTINENT', 'SUBREGION', 'REGION_WB',
                          'geometry']]
   # world_gdf['NAME'] = world_gdf['NAME'].replace({'United States of America': 'United States'})
   # logger.debug(f"world_gdf len - {len(world_gdf)}")
   # logger.debug(f"world_gdf columns - {world_gdf.columns}")

   conflict_death_gdf = world_gdf.merge(conflict_deaths_csv, left_on='NAME', right_on='Entity', how='inner')
   logger.debug(f"conflict_death_gdf len - {len(conflict_death_gdf)}")
   logger.debug(f"conflict_death_gdf columns - {conflict_death_gdf.columns}")
   # logger.debug(f"conflict_death_gdf unique countries - {conflict_death_gdf['NAME'].nunique()}")

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(world=conflict_death_gdf, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # (Black Friday) Interpret the theme of Black. Deaths in armed conflicts around the world.
   filename = 'black_deaths_in_armed_conflicts.png'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
