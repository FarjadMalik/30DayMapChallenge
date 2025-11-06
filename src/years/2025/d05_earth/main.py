import fiona
import folium
import geopandas as gpd

from pathlib import Path
from shapely.geometry import box
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_earth_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")

    # Geodatabase path
    gdb_path = "data/PAK_misc/FL20250818PAK.gdb"
    flood_layerlist = fiona.listlayers(gdb_path)
    # logger.info(f"Layers in GDB: {flood_layerlist}")

    # Load the flood extent polygon layer
    flood_gdf = gpd.read_file(gdb_path, layer='VIIRS_20250826_20250907_FloodWaterExtent_PAK')
    # Convert date to string for tooltip display
    flood_gdf["Sensor_Date"] = flood_gdf["Sensor_Date"].astype(str)

    
    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if flood_gdf is not None and flood_gdf.crs.to_string() != "EPSG:4326":
        flood_gdf = flood_gdf.to_crs(epsg=4326)
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # TODO: join with admin boundaries to get names and areas for each admin unit
    # Add flood layer to map
    folium.GeoJson(
        flood_gdf,
        name='Flood Extents 2025',
        style_function=lambda feature: {
            'fillColor': 'blue',
            'color': 'blue',
            'weight': 1,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=['Area_ha', 'Area_m2', 'Sensor_ID', 'Sensor_Date'], 
            aliases=['Area in Hectares', 'Area in meters', 'Sensor', 'Date'],
            localize=True
            )
    ).add_to(basemap)

    # Add title — can be done via Html in map
    title_html = f"""
         <h3 align="center" style="font-size:20px"><b>Floods Pakistan 2025</b></h3>
         """
    basemap.get_root().html.add_child(folium.Element(title_html))

    # # Add Legend - Build HTML string
    # items = "".join(
    #     f"<i style='background:{colour};width:18px;height:18px;display:inline-block;margin-right:8px;'></i>{label}<br>"
    #     for label, colour in legend_dict.items()
    # )
    # html = f"""
    # <div style="position: fixed; { 'bottom: 50px;' if position.endswith('right') else '' } 
    #              { 'right: 50px;' if position.endswith('right') else 'left:50px;' } 
    #              width: 200px; height: auto; 
    #              border:2px solid grey; z-index:9999; font-size:14px;
    #              background-color:white; opacity:0.85; padding: 10px;">
    #   <b>{title}</b><br>
    #   {items}
    # </div>
    # """
    # legend = branca.element.MacroElement()
    # legend._template = branca.element.Template(html)
    # map_obj.get_root().add_child(legend)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'flood_pakistan_2025'
    create_earth_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)