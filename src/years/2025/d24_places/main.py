import pandas as pd
import geopandas as gpd
import cartopy.crs as ccrs
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib import animation, colors, patches
from shapely.geometry import Polygon, MultiPolygon
from tqdm import tqdm
from PIL import Image
from pypalettes import load_cmap

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_animation_fast(world, output_path, cmap_name="Abbott", simplify_tolerance=0.1):
   """
   Fast animation: pre-render each frame as an image and assemble GIF.
   """
    
   cmap = load_cmap(cmap_name, cmap_type="continuous")
   norm = colors.Normalize(vmin=0, vmax=10)
   years = sorted(world["Year"].dropna().unique())

   # Simplify geometries for speed
   if simplify_tolerance > 0:
      world = world.copy()
      world["geometry"] = world["geometry"].simplify(simplify_tolerance)
    
   frames = []
   for year in tqdm(years, desc="Rendering frames"):
      fig, ax = plt.subplots(figsize=(14, 8), subplot_kw={'projection': ccrs.Robinson()})
      ax.set_global()
      ax.set_axis_off()
      
      # Colorbar (constant for all frames)
      sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
      sm._A = []  # required trick
      cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.6)
      cbar.set_label("Cantril Ladder Score")

      # # Use this if the fig+colorbar is outside the loop, Clear only the map data, leave colorbar,
      # ax.collections.clear()
      
      # Filter for the specific year and plot
      world_year = world[world["Year"] == year]
      world_year.plot(
         ax=ax,
         column="Cantril ladder score",
         cmap=cmap,
         norm=norm,
         edgecolor="black",
         linewidth=0.4,
         transform=ccrs.PlateCarree()
      )
      ax.set_title(f"Cantril Ladder Score – {year:.0f}", fontsize=16)
        
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
    
   # Save as GIF
   frames[0].save(
      f"{output_path}.gif",
      save_all=True,
      append_images=frames[1:],
      duration=1000,
      loop=0
   )
    
def create_animation(world, output_path, cmap_name='Abbott'):
   """
   """
   # load cmap
   cmap = load_cmap(cmap_name, cmap_type='continuous')
   
   # 0 and 10 are the min and max possible values for Cantril Ladder Score
   # norm = plt.Normalize(vmin=cl_score_min, vmax=cl_score_max)
   norm = colors.Normalize(vmin=0, vmax=10)
   years = sorted(world['Year'].dropna().unique())

   # create fig and axis
   fig, ax = plt.subplots(figsize=(14, 8), subplot_kw={'projection': ccrs.Robinson()})
   ax.set_global()
   ax.set_axis_off()
   
   # Colorbar (constant for all frames)
   sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
   sm._A = []  # required trick
   cbar = fig.colorbar(sm, ax=ax, orientation="vertical", shrink=0.6)
   cbar.set_label("Cantril Ladder Score")

   # Set title once and only update text later on
   title = ax.set_title(
        f"Cantril Ladder Score (Happiness Index) – {years[0]}",
        fontsize=16,
        pad=20
    )
   
   # Precompute geometries for all years to speed up animation ---
   geoms = []
   for year in years:
      year_df = world[world["Year"] == year]
      geoms.append(year_df)

   # First frame: draw once and reuse artist ---
   initial_frame = geoms[0]

   # Create a single reusable artist collection
   collection = initial_frame.plot(
      ax=ax,
      column="Cantril ladder score",
      cmap=cmap,
      norm=norm,
      edgecolor="black",
      linewidth=0.4,
      transform=ccrs.PlateCarree(),
      legend=False,
   )

   title = ax.set_title("", fontsize=16, pad=20)

   
   # Build a list of patches for each country instead of relying on GeoDataFrame plot collection
   country_patches = []     # list of lists → each row may map to many patches

   # Manually build patches for each country to allow efficient color updates but this is very slow
   for geom in world.geometry:
      row_patches = []

      if isinstance(geom, Polygon):
         polys = [geom]
      elif isinstance(geom, MultiPolygon):
         polys = geom.geoms
      else:
         continue

      for poly in polys:
         x, y = poly.exterior.xy
         patch = patches.Polygon(
                  xy=list(zip(x, y)),
                  closed=True,
                  linewidth=0.4,
                  edgecolor="black",
                  transform=ccrs.PlateCarree(),
                  )
         ax.add_patch(patch)
         row_patches.append(patch)

      country_patches.append(row_patches)
   
   # create a list of values for each year to speed up updates
   country_names = world["NAME"].tolist()
   yearly_values = {}

   for year in years:
      year_df = world[world["Year"] == year].set_index("NAME")["Cantril ladder score"]
      values = [year_df.get(cname, None) for cname in country_names]
      yearly_values[year] = values

   def update(i):
      year = years[i]
      values = yearly_values[year]

      # Update color of each country's patches
      for val, row_patches in zip(values, country_patches):
         if val is None:
               color = (0.9, 0.9, 0.9, 1.0)  # grey for missing
         else:
               color = cmap(norm(val))
         for p in row_patches:
               p.set_facecolor(color)

      title.set_text(f"Cantril Ladder Score (Happiness Index) – {year:.0f}")
      return []

   # Instead of plt_year function with clearing, we use the optimized update function above
   # def plt_year(year):
   #    ax.clear()

   #    # Filter data for the specific year
   #    data_year = world[world['Year'] == year]

   #    # Plot countries with colors based on Cantril Ladder Score
   #    data_year.plot(
   #       ax=ax,
   #       column='Cantril ladder score',
   #       cmap=cmap,
   #       norm=norm,
   #       edgecolor='black',
   #       linewidth=0.5,
   #       transform=ccrs.PlateCarree()
   #    )
   #    # Set title
   #    ax.set_title(f"Cantril Ladder Score (Happiness Index) - {year:.0f}", fontsize=16)

   # def update(frame):
   #    plt_year(frame)

   # Build animation 
   ani = animation.FuncAnimation(
      fig,
      update,
      frames=len(years),
      interval=1000,
      blit=False,   # blit=False because Cartopy + GeoAxes don’t support blitting
      repeat=True,
   )

   # Save the animation
   # ani.save(f"{output_path}.mp4", writer="ffmpeg", dpi=150)
   ani.save(f"{output_path}.gif", 
            writer="pillow", 
            dpi=300)

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
   # create_animation(world=world_happiness_gdf, output_path=output_path)
   create_animation_fast(world=world_happiness_gdf, output_path=f"{output_path}_fast")

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # Focus on toponymy (place names). Experiment with font choices, label placement, 
   # typography, multiple languages, or the history and meaning behind a name. 
   # Happines indice over time for the world = data/happiness-cantril-ladder/happiness-cantril-ladder.csv
   filename = 'places_happiness_over_time'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
