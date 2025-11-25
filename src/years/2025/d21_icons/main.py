import folium
import numpy as np
import pandas as pd
import geopandas as gpd
import contextily as ctx
import matplotlib.pyplot as plt

from pathlib import Path
from shapely.geometry import Point
from matplotlib.patches import Patch

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_html(admin, dataset, output_path):
   """
   """
   # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
   if admin is not None and admin.crs.to_string() != "EPSG:4326":
         admin = admin.to_crs(epsg=4326)
   if admin.crs != dataset.crs:
      dataset = dataset.to_crs(admin.crs)
      
   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]
   center_lat = (bounds[1] + bounds[3]) / 2
   center_lon = (bounds[0] + bounds[2]) / 2

   # Create and Center a base map
   basemap = folium.Map(location=[center_lat, center_lon], zoom_start=7, 
                        tiles='OpenStreetMap')

   # Add the administrative boundaries layer
   folium.GeoJson(
         admin,
         name='Administrative Boundaries',
         style_function=lambda feature: {
            'fillColor': None,
            'color': 'black',
            'weight': 1,
            'opacity': 0.5
         },
         tooltip=folium.GeoJsonTooltip(
            fields=['NAME_1'], 
            aliases=['Province:']
         )
   ).add_to(basemap)

   # Add dataset
   folium.GeoJson(
       dataset,
       name='',
       style_function=lambda feature: {
           'fillColor': feature['properties']['color'],
           'color': feature['properties']['color'],
           'weight': 1,
           'fillOpacity': 0.5
       },
       tooltip=folium.GeoJsonTooltip(
           fields=[''],
           aliases=[''],
           localize=True
       )
   ).add_to(basemap)

   
      #   icon_f = folium.Icon(color="black",icon='meteor',prefix='fa')

      #   folium.Marker(
      #       location=[lat, lon],
      #       icon=icon_f,
      #       popup=folium.Popup(popup_html, max_width=300),
      #       tooltip=tooltip_f
      #   ).add_to(marker_cluster)

   # items = "".join([
   #      f'<i style="background:{name};width:12px;height:12px;display:inline-block;margin-right:5px;"></i>'
   #      f'{name}<br>'
   #      for name in dataset.amenity.unique()
   #  ])

   # legend_html = """{% macro html(this, kwargs) %}
   # <div style="position: fixed; 
   #             top: 10px; left: 50px; width: 320px; z-index:9999; 
   #             background-color: white; border:2px solid grey; border-radius:5px; 
   #             padding: 10px; font-size:14px;">
   #    <h4 style="margin-bottom:10px;"><b>Educational Institutes Per Province</b></h4>
      
   #    <b>Items:</b><br>
   #    """ + items + """
   # </div>
   # {% endmacro %}
   # """
   # legend = MacroElement()
   # legend._template = Template(legend_html)
   # basemap.get_root().add_child(legend)
   
   # # Add title
   # title_html = '''
   # <h3 align="center" style="font-size:20px; font-weight:bold; margin-top:10px">
   #    TITLE
   # </h3>
   # '''
   # basemap.get_root().html.add_child(folium.Element(title_html))

   # Allows toggling between layers interactively 
   folium.LayerControl().add_to(basemap)
   # Save and exit
   basemap.save(f"{output_path}.html")
   
def create_png(admin, dataset, output_path):
   """
   """
   # Web tiles (contextily) use web mercator (epsg:3857)
   admin = admin.to_crs(epsg=3857)
   dataset = dataset.to_crs(epsg=3857)
   logger.debug(f"admin.crs: {admin.crs}")
   logger.debug(f"dataset.crs: {dataset.crs}")

   # Prepare marker size scaling
   killed_raw = dataset['Killed Max'].astype(float)
   min_s, max_s = 20, 400
   if not killed_raw.empty:
       scaled = (killed_raw - killed_raw.min()) / (killed_raw.max() - killed_raw.min())
       sizes = scaled * (max_s - min_s) + min_s
   else:
       sizes = np.full(len(dataset), min_s)

   # Calculate a center for the map, e.g., the mean of the bounds
   bounds = admin.total_bounds  # [minx, miny, maxx, maxy]

   # create fig and axis
   _, ax = plt.subplots(figsize=(12, 10))

   # plot admin boundaries
   admin.plot(
      ax=ax,
      color='white',
      edgecolor='black',
      linewidth=1,
      alpha=0.2
   )

   # these are in degrees, to work with contextily use meters as given below
   # ax.set_xlim(center_lon - 9, center_lon + 9)
   # ax.set_ylim(center_lat - 9, center_lat + 9)
   # Set extent BEFORE basemap
   padding = 50_000  # 50 km padding
   ax.set_xlim(bounds[0] - padding, bounds[2] + padding)
   ax.set_ylim(bounds[1] - padding, bounds[3] + padding)
   # Add basemap tiles
   ctx.add_basemap(ax, source=ctx.providers.OpenStreetMap.Mapnik, crs=admin.crs.to_string())
   
   for type, group in dataset.groupby("type"):
       logger.debug(f"type - {type}: {len(group)}")
       color = 'black' if type == 'suicide' else 'red'
       marker = 'o' if type == 'suicide' else '^'
       # Use GeoPandas plot
       group.plot(
           ax=ax,
           marker=marker,
           color=color,
           markersize=sizes[group.index],
           alpha=0.7,
           edgecolor='black',  # helps visibility
           linewidth=0.5,
           zorder=5
      )
      #  ax.scatter(
      #      group.geometry.x,
      #      group.geometry.y,
      #      s=20,
      #      c='red',
      #      marker='o',
      #      alpha=0.7,
      #      linewidths=0.5,
      #      transform=None,
      #      edgecolor='white',  # this helps points stand out
      #      zorder=10  # ensure scatter is above basemap
      #   )

   # Add title & legend
   ax.set_title(
      "Suicide and Drone Attacks (Size ~ Casualities)",
      fontsize=18,
      fontweight="bold",
      pad=20
   )

   # Define your color mapping for phases (for legend use, takes care of missing phases in the dataset)
   type_color_dict = {
      'suicide': '#000000', # Level 1
      'drone': '#ff0000', # Level 1
   }
   legend_elements = []
   for type, color in type_color_dict.items():
      legend_elements.append(Patch(facecolor=color, edgecolor=color,
                                    label=f"{type}"))
   
   # Beautify, add legend and save
   ax.legend(
      handles=legend_elements,
      title="Legend Title",
      loc="upper left", # legend location
      frameon=True
   )
   ax.set_axis_off()
   plt.tight_layout()
   plt.savefig(output_path, dpi=500, bbox_inches="tight")

def convert_df_to_gdf(dataset, lat_col, lon_col, input_crs: str='EPSG:4326'):
   """
   """
   # Drop rows with missing lat/lon
   dataset = dataset.dropna(subset=[lat_col, lon_col])

   # Create Point geometry column
   geometry = [Point(xy) for xy in zip(dataset[lon_col], dataset[lat_col])]
   dataset_gdf = gpd.GeoDataFrame(dataset, geometry=geometry, crs=input_crs)

   return dataset_gdf


def generate_map(path_dir: str, filename: str):
   """    
   """
   logger.info(f"Generating {path_dir}")
   
   # Load the shapefile for boundaries or admin units
   shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
   admin_gdf = gpd.read_file(shapefile_path)
   admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

   # Drone and Suicide attacks csvs
   fp_suicide = "data/PAK_misc/zusmani_pakistansuicideattacks/PakistanSuicideAttacks Ver 11 (30-November-2017).csv"
   fp_drone = "data/PAK_misc/zusmani_pakistandroneattacks/PakistanDroneAttacksWithTemp Ver 11 (November 30 2017).csv"
   
   # Read as pd dataset and then convert based on lat lon fields 
   suicide_df = pd.read_csv(fp_suicide, encoding='latin1')
   drone_df = pd.read_csv(fp_drone, encoding='latin1')
   logger.debug(f"Length suicide_df - {len(suicide_df)}")
   logger.debug(f"Length drone_df - {len(drone_df)}")

   # Define sensitivity conditions for a drone strike
   sensitivty_drone_conds = [
      (drone_df["Women/Children  "] == 'Y') | (drone_df["Foreigners Min"] > 0),
      (drone_df["Civilians Min"] > 0),
      (drone_df["Al-Qaeda"] > 0) | (drone_df["Taliban"] > 0),
   ]
   # Define corresponding choices
   choices = ["High", "Medium", "Low"]
   # Use np.select to make the new column
   drone_df["Sensitivity"] = np.select(sensitivty_drone_conds, choices, default="None")
   
   # Keep only necessary columns
   suicide_df = suicide_df[['S#', 'Date', 'Latitude', 'Longitude', 'Location Sensitivity', 'Killed Max', 'Injured Max']]
   drone_df = drone_df[['S#', 'Date', 'Latitude', 'Longitude', 'Sensitivity', 'Total Died Max', 'Injured Max']]
   # Rename columns to match
   suicide_df.rename(columns={
       'Location Sensitivity':'Sensitivity',
       }, inplace=True)
   drone_df.rename(columns={
       'Total Died Max':'Killed Max',
       }, inplace=True)
   
   # Fix Sensitivity values where empty or wrong case
   suicide_df["Sensitivity"] = suicide_df["Sensitivity"].fillna("None")
   suicide_df.loc[suicide_df['Sensitivity'] == 'low', "Sensitivity"] = "Low"

   # Assign type of attack
   suicide_df['type'] = 'suicide'
   drone_df['type'] = 'drone'

   # concat/merge two dataframes
   dataset = pd.concat([suicide_df, drone_df], axis=0, ignore_index=True)
   # Convert to geo dataframe, assign geometries
   dataset = convert_df_to_gdf(dataset, lat_col='Latitude',lon_col='Longitude')
   logger.debug(f"Length dataset - {len(dataset)}")
   logger.debug(f"Columns dataset - {dataset.columns}")
   logger.debug(f"Sensitivity values (dataset) - {dataset['Sensitivity'].value_counts(dropna=False)}")
   counts_by_origin = dataset.groupby(["type", "Sensitivity"]).size()
   logger.debug(f"Sensitivity type - {counts_by_origin}")

   # Clean extra data
   del suicide_df, drone_df

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   # create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)
   create_png(admin=admin_gdf, dataset=dataset, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
   # Create a map where icons, pictograms, or custom symbols are the main focus. 
   # Use them to highlight points of interest or replace traditional cartographic features. 
   # Place icons for suicide attacks and use bomb icons?
   filename = 'iconic_map'
   generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
