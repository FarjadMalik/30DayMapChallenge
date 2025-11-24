import numpy as np
import pandas as pd
import h3pandas
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects


from pathlib import Path
from matplotlib.patches import FancyBboxPatch
from pypalettes import load_cmap
from pyfonts import load_font

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path, load_and_flatten


logger = get_logger(__name__)


def create_png(dataset, output_path):
   """
   """
   # Get bounds of the dataset
   (minx, miny, maxx, maxy) = dataset.total_bounds  # (minx, miny, maxx, maxy)
   logger.debug(f"Dataset bounds: {(minx, miny, maxx, maxy)}")

   # Define points of interest to mark on the map
   points = {
      "Khartoum": (32.86961437, 15.7999476),
      "North Dafur": (26.729736, 12.275599), 
      "West Dafur": (22.6170820563, 13.5217587279),
      "South Dafur": (24.001592, 11.968823),
      # "East Dafur": (26.844, 11.077),
   }
   
   # Load colormap and fonts
   cmap = load_cmap("Exter", cmap_type="continuous")
   lightfont = load_font(
      "https://raw.githubusercontent.com/googlefonts/dynapuff/main/fonts/ttf/DynaPuff-Regular.ttf"
   )

   mediumfont = load_font(
      "https://raw.githubusercontent.com/googlefonts/dynapuff/main/fonts/ttf/DynaPuff-Bold.ttf"
   )

   # Create percentile-based bin edges
   n_bins = 10
   percentiles = np.linspace(0, 100, n_bins + 1)
   bins = np.percentile(dataset["total_crisis_affected"], percentiles)
   logger.debug(f"bins: {bins}")

   dataset["crisis_quantiles"] = pd.cut(
      dataset["total_crisis_affected"], 
      bins=bins, 
      labels=False, 
      include_lowest=True, 
      duplicates="drop"
   )
   # Directly using qcut, without specifying bins (above), can lead to unexpected bin edges
   # dataset["crisis_quantiles"] = pd.qcut(
   #    dataset['total_crisis_affected'],
   #    q=n_bins,
   #    labels=False,
   #    duplicates="drop"
   # )

   # create fig and axis
   fig, ax = plt.subplots()
   ax.set_axis_off()

   # plot polygons with colors
   dataset.plot(
      ax=ax, 
      column="crisis_quantiles",
      edgecolor="white", # outline
      # color='', # both fill and outline
      linewidth=0.01,
      alpha=0.7,
      cmap=cmap
   )

   labels = [f"{bins[i]:.0f} - {bins[i+1]:.0f}" for i in range(len(bins) - 1)][::-1]

   rectangle_width = 0.8
   rectangle_height = 0.5
   legend_x = maxx # after the maps right edge
   legend_y_start = ((miny + maxy) / 2) + 3 # A bit above center, adjust as needed
   legend_y_step = 0.62


   for i in range(len(labels)):
      value = (i + 0.5) / len(labels)
      color = cmap(1 - value)

      ax.add_patch(
         FancyBboxPatch(
               (legend_x, legend_y_start - i * legend_y_step),
               rectangle_width,
               rectangle_height,
               boxstyle="round,pad=0.05",
               color=color,
               linewidth=0.6,
         )
      )

      min_label = int(labels[i].split('-')[0].strip())
      max_label = int(labels[i].split('-')[1].strip())
      ax.text(
         legend_x + 1,
         legend_y_start - i * legend_y_step + 0.25,
         f"{min_label:,} - {max_label:,}",
         fontsize=9,
         va="center",
         ha="left",
         font=lightfont,
      )

   for city, location in points.items():
      ax.scatter(location[0], location[1], color="white", s=12, ec="black")
      text = ax.text(
         location[0],
         location[1] + 0.18,
         s=f"{city}",
         color="white",
         font=lightfont,
         size=8,
      )
      text.set_path_effects(
         [path_effects.Stroke(linewidth=2, foreground="black"), path_effects.Normal()]
      )

   fig.text(x=0.5, y=1, s="Affected Individuals", size=25, ha="center", font=mediumfont)
   fig.text(
      x=0.5,
      y=0.96,
      s="Number of individuals affected (displaced/refugees) in Sudan (September-2025)",
      size=8,
      color="grey",
      ha="center",
      font=mediumfont,
   )

   fig.text(
      x=0.81,
      y=0.08,
      s="#30daymapchallenge 2025",
      font=mediumfont,
      ha="right",
      size=6,
   )
   fig.text(
      x=0.81,
      y=0.055,
      s="Hexagons - H3 resolution 5 (~7.4km side length)",
      font=lightfont,
      ha="right",
      size=6,
   )
   fig.text(x=0.81, y=0.03, s="Data: Humanitarian exchange", font=lightfont, ha="right", size=6)

   plt.tight_layout()
   plt.savefig(output_path, dpi=300, bbox_inches="tight")

def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # (Not Used) data\Sudan_misc\DTM Sudan - Countrywide Mobility.csv - STATE OF DISPLACEMET,STATE of ORIGIN,INDIVIUALS
   
   # Load the shapefile for boundaries or localities
   sudan_gdf = gpd.read_file("data/Sudan_misc/locality_polygon_mar20/Locality_Polygon_Mar20.shp")
   # Aggregate to state level, summing population and area (input file is locality level)
   sudan_gdf = sudan_gdf.dissolve(
      by='State_En',
      as_index=False,
      aggfunc={'State': 'first', 'Total_Pop': 'sum', 'Shape_Area': 'sum'}
   )
   
   # Flatten nested 'data' column, json objects have a nested structure
   sudan_idp_df = load_and_flatten("data/Sudan_misc/undp_internallydisplacedpeople.json", 
                                   meta=['title_language_en'])
   
   # sudan_idp_df = sudan_idp_df[['geomaster_name', 'source', 'date', 'individuals', 'numChildren', 'color', 'meta_title_language_en']]
   # # Extract metadata variables 
   # idp_source = sudan_idp_df['source'].unique()[0]
   # idp_color = sudan_idp_df['color'].unique()[0]
   # idp_title = sudan_idp_df['meta_title_language_en'].unique()[0]
   # idp_date = sudan_idp_df['date'].unique()[0]
   # logger.debug(f"idp_source: {idp_source}")
   # logger.debug(f"idp_color: {idp_color}")
   # logger.debug(f"idp_title: {idp_title}")
   # logger.debug(f"idp_date: {idp_date}")

   # Remove meta variables from main dataframe and rename columns
   sudan_idp_df = sudan_idp_df[['geomaster_name', 'individuals', 'numChildren']]
   sudan_idp_df = sudan_idp_df.rename(
      columns={'geomaster_name': 'State', 
               'individuals': 'idp_individuals', 
               'numChildren': 'idp_children'}
   )
   sudan_idp_df['State'] = sudan_idp_df['State'].replace({'Nile': 'River Nile'})

   sudan_ref_df = load_and_flatten("data/Sudan_misc/undp_selfrelocatedrefugees.json")

   # sudan_ref_df = sudan_ref_df[['geomaster_name', 'source', 'date', 'individuals', 'color']]   
   # # Extract metadata variables
   # selfref_source = sudan_ref_df['source'].unique()[0]
   # selfref_color = sudan_ref_df['color'].unique()[0]
   # selfref_date = sudan_ref_df['date'].unique()[0]
   # logger.debug(f"selfref_source: {selfref_source}")
   # logger.debug(f"selfref_color: {selfref_color}")
   # logger.debug(f"selfref_date: {selfref_date}")

   # Remove meta variables from main dataframe and rename columns
   sudan_ref_df = sudan_ref_df[['geomaster_name', 'individuals']]
   sudan_ref_df = sudan_ref_df.rename(
      columns={'geomaster_name': 'State', 
               'individuals': 'self_relocated_individuals'}
   )

   # Merge datasets on province/state name and filter only columns needed
   sudan_crisis_gdf = sudan_gdf.merge(sudan_idp_df, left_on='State_En', right_on='State', how='left')
   sudan_crisis_gdf = sudan_crisis_gdf.merge(sudan_ref_df, left_on='State_En', right_on='State', how='left') # , suffixes=('_idp', '_ref'))
   sudan_crisis_gdf = sudan_crisis_gdf[['State_En', 'Total_Pop', 'Shape_Area', 
                                        'idp_individuals', 'idp_children', 'self_relocated_individuals',
                                        'geometry']]
   
   # logger.debug(f"sudan_crisis_gdf Columns: {sudan_crisis_gdf.dtypes}")
   # Assign 0 to NaN values and convert to integer
   sudan_crisis_gdf['idp_individuals'] = sudan_crisis_gdf['idp_individuals'].fillna(0)
   sudan_crisis_gdf['self_relocated_individuals'] = sudan_crisis_gdf['self_relocated_individuals'].fillna(0)
   sudan_crisis_gdf['idp_individuals'] = sudan_crisis_gdf['idp_individuals'].astype(int)
   sudan_crisis_gdf['self_relocated_individuals'] = sudan_crisis_gdf['self_relocated_individuals'].astype(int)

   # Add total crisis-affected individuals column
   sudan_crisis_gdf['total_crisis_affected'] = (
      sudan_crisis_gdf['idp_individuals'] + 
      sudan_crisis_gdf['self_relocated_individuals']
   )
   
   # Create hexagonal tesselation over Sudan
   sudan_crisis_gdf = sudan_crisis_gdf.h3.polyfill_resample(resolution=5)
   logger.debug(f"sudan_crisis_gdf Shape: {sudan_crisis_gdf.shape}")
   logger.debug(f"sudan_crisis_gdf Columns: {sudan_crisis_gdf.columns}")


   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   # create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)
   create_png(dataset=sudan_crisis_gdf, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Tesselations over sudan and internally displaced people      
    filename = 'sudan_idp_hexmap'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
