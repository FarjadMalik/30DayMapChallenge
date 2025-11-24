import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.animation as animation

from pathlib import Path
from matplotlib.patches import Patch
from pypalettes import load_cmap

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_animation(world, output_path, cmap_name='Abbott'):
   """
   """
   # load cmap
   cmap = load_cmap(cmap_name, cmap_type='continuous')

   # 0 and 10 are the min and max possible values for Cantril Ladder Score
   norm = colors.Normalize(vmin=0, vmax=10)
   # norm = plt.Normalize(vmin=cl_score_min, vmax=cl_score_max)
   years = sorted(world['Year'].dropna().unique())
   logger.debug(f"Years to plot: {years}")

   # create fig and axis
   fig, ax = plt.subplots(figsize=(14, 8), subplot_kw={'projection': ccrs.Robinson()})
   ax.set_axis_off()
   ax.set_global()

   # Colorbar (constant for all frames)
   sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
   sm._A = []  # required trick
   cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.6)
   cbar.set_label("Cantril Ladder Score")

   def plt_year(year):
      ax.clear()

      # Filter data for the specific year
      data_year = world[world['Year'] == year]

      # Plot countries with colors based on Cantril Ladder Score
      data_year.plot(
         ax=ax,
         column='Cantril ladder score',
         cmap=cmap,
         norm=norm,
         edgecolor='black',
         linewidth=0.5,
         transform=ccrs.PlateCarree()
      )
      # Set title
      ax.set_title(f"Cantril Ladder Score (Happiness Index) - {year:.0f}", fontsize=16)

   def update(frame):
      plt_year(frame)

   ani = animation.FuncAnimation(
      fig,
      update,
      frames=years,
      interval=1000,
      repeat=True
   )
   
   # Save the animation
   # ani.save(f"{output_path}.mp4", writer="ffmpeg", dpi=150)
   ani.save(f"{output_path}.gif", writer="pillow", dpi=300)

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load csv file with happiness indices over time for the world
   happiness_ladder_df = pd.read_csv("data/happiness-cantril-ladder/happiness-cantril-ladder.csv")
   # Remove rows with general world and continent based data
   happiness_ladder_df = happiness_ladder_df.loc[~(happiness_ladder_df['Code'].isna())]
   happiness_ladder_df = happiness_ladder_df.loc[~(happiness_ladder_df['Entity']=='World')]
   
   
   # Replace country names with correct ones to match with geometry file
   happiness_ladder_df['Entity'] = happiness_ladder_df['Entity'].replace({
                                    'United States': 'United States of America',
                                    "Cote d'Ivoire": "Côte d'Ivoire", 
                                    })
   happiness_ladder_df['Year'] = happiness_ladder_df['Year'].astype(int)
   
   # world_gdf = gpd.read_file("data/countries.geojson")
   world_gdf = gpd.read_file("data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
   world_gdf= world_gdf[['NAME', 'ADM0_A3', 'ECONOMY', 'INCOME_GRP', 'geometry']]
      
   # Replace country names with full names to match with other file
   replacements = {
      'Dem. Rep. Congo' : 'Democratic Republic of Congo', 
      'N. Cyprus' : 'Northern Cyprus', 
      'eSwatini' : 'Eswatini', 
      'Bosnia and Herz.' : 'Bosnia and Herzegovina', 
      'Central African Rep.' : 'Central African Republic', 
      'Dominican Rep.' : 'Dominican Republic', 
      'S. Sudan' : 'South Sudan'
   }
   world_gdf['NAME'] = world_gdf['NAME'].replace(replacements)

   # Merge happiness data with world geometries
   world_happiness_gdf = world_gdf.merge(
      happiness_ladder_df,
      left_on='NAME',
      right_on='Entity',
      how='left'
   )
   
   # Clean up
   del world_gdf, happiness_ladder_df

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_animation(world=world_happiness_gdf, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Focus on toponymy (place names). Experiment with font choices, label placement, 
    # typography, multiple languages, or the history and meaning behind a name. 
    # Happines indice over time for the world = data/happiness-cantril-ladder/happiness-cantril-ladder.csv
    filename = 'places_happiness_over_time'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
