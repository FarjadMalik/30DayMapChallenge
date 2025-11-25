import geopandas as gpd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from pathlib import Path
from pypalettes import load_cmap, add_cmap
from matplotlib.lines import Line2D

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path
from src.utils.map_helpers import newworld_political_map


logger = get_logger(__name__)


def create_png(dataset, output_path):
   """
   """
   # Choose a global projection
   proj = ccrs.Mollweide() 

   # create fig and axis
   fig = plt.figure(figsize=(12, 10), dpi=800)
   # fig.set_facecolor('black')
   ax = plt.axes(projection=proj)

   # Add land and ocean with natural colors
   ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
   # ax.add_feature(cfeature.OCEAN, facecolor='#acceff')
   # ax.add_feature(cfeature.COASTLINE, edgecolor='black', linewidth=0.8)
   # ax.add_feature(cfeature.BORDERS, edgecolor='gray', linewidth=0.4)
   # Set global extent
   ax.set_global()

   political_cats = sorted(dataset['world_order'].unique().tolist())
   cmap = add_cmap(colors=['#AC1F25FF', '#272727FF', "#5F984AFF", '#004F63FF', '#96804BFF', '#828788FF'], name='political_cats_cmap')
   # '#C969A1FF', '#CE4441FF', '#EE8577FF', '#EB7926FF', '#FFBB44FF', '#859B6CFF', '#62929AFF', '#004F63FF', '#122451FF'
   cat_to_color = {cat: cmap(i / len(political_cats)) 
                   for i, cat in enumerate(political_cats)}
   
   # plot polygons with colors
   for cat in political_cats:
        subset = dataset[dataset['world_order'] == cat]
        if subset.empty:
            continue
        subset.plot(
            ax=ax,
            facecolor=cat_to_color[cat],
            edgecolor="white",
            linewidth=0.3,
            transform=ccrs.PlateCarree(),  # your world_gdf is likely in lon/lat
            zorder=2,
        )

   # Add title & legend
   legend_handles = [
      Line2D([0], [0], marker="o", color=cat_to_color[cat], linestyle="", markersize=10, label=cat)
      for cat in political_cats
   ]
   legend = ax.legend(
      handles=legend_handles,
      title="Political / Ideological Category",
      loc="upper left",
      frameon=True,
      framealpha=0.9,
   )
   
   # ax.set_title(
   #    "TITLE",
   #    fontsize=18,
   #    fontweight="bold",
   #    pad=20
   # )
   fig.text(
      0.5, 0.95,
      "Global Map of Political / Ideological Divisions",
      horizontalalignment="center",
      fontsize=16,
      weight="bold",
      # color='white'
   )
   fig.text(
      0.5, 0.90,
      "Based on custom categories: NATO, BRICS, Global South, Communists, etc.",
      horizontalalignment="center",
      fontsize=12,
      # color='white'
   )
   fig.text(
      0.02, 0.02,
      "Data source: Natural Earth admin boundaries + user-defined political categories",
      fontsize=8,
      alpha=0.7,
      # color='white'
   )
   
   ax.set_axis_off()
   plt.tight_layout()
   plt.savefig(output_path, dpi=800, bbox_inches="tight")
   plt.close(fig)

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for world admin boundaries with all countries
   world_gdf = gpd.read_file("data/ne_10m_admin_0_countries/ne_10m_admin_0_countries.shp")
   # Keep only relevant columns
   world_gdf = world_gdf[['NAME', 'TYPE', 'ADM0_A3', 'POP_EST', 'POP_RANK', 
                          'GDP_MD', 'ECONOMY', 'INCOME_GRP', 'CONTINENT', 'SUBREGION', 'REGION_WB',
                          'geometry']]
   # logger.debug(f"world_gdf len - {len(world_gdf)}")
   # logger.debug(f"world_gdf columns - {world_gdf.columns}")

   # Prepare a mapping dict: country_name → category
   # Here we invert the `category_map` above:
   country_to_cat = {}
   for cat, countries in newworld_political_map.items():
      for c in countries:
         if c not in country_to_cat:
            country_to_cat[c] = cat
   # Make a new column in your GeoDataFrame
   def assign_category(row):
      name = row["NAME"]  # or whatever your name field is
      return country_to_cat.get(name, "Undecided")

   world_gdf["world_order"] = world_gdf.apply(assign_category, axis=1)
   logger.debug(f"world_gdf world_order - {world_gdf['world_order'].value_counts()}")
   logger.debug(f"world_gdf world_order - {sorted(world_gdf['world_order'].unique())}")
   # logger.debug(f"world_gdf world_order empty - {world_gdf.loc[world_gdf['world_order'].isna(), ['NAME']]}")
   # logger.debug(f"world_gdf world_order - {world_gdf.loc[world_gdf['world_order']=='BRICS', ['NAME']]}")

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_png(dataset=world_gdf, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # New world order as you see it, BRICS, NATO, Global South, Communists, Undecided etc
   # Map lines of division—political, physical, ecological, or conceptual. Explore the meaning and impact of a dividing line, real or perceived. 
   filename = 'boundaries_new_world_order'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
