import folium
import geopandas as gpd
import matplotlib.pyplot as plt

from pathlib import Path
from matplotlib.patches import Patch
from branca.element import Template, MacroElement

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
   shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
   admin_gdf = gpd.read_file(shapefile_path)
   admin_gdf = admin_gdf[['COUNTRY', 'NAME_1', 'geometry']]

   # Load desired 
   dataset = None

   # Generate and save map
   output_path = f"{Path(path_dir).parent}/{filename}"
   create_html(admin=admin_gdf, dataset=dataset, output_path=output_path)
   create_png(admin=admin_gdf, dataset=dataset, output_path=output_path)

   logger.info(f"Map created – open '{filename}' to view.")


if __name__ == "__main__":
    # Pakistan suicide attacks
    # (Black Friday) Interpret the theme of Black. 
    # The map can be purely monochromatic, represent absence/darkness (e.g., light pollution), 
    # or relate to themes of consumption. 
    filename = 'black'
    generate_map(path_dir=str(get_relative_path(__file__)), filename=filename)
