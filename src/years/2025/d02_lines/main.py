import fiona
import folium
import geopandas as gpd
import pandas as pd
import numpy as np
import rasterio

from pathlib import Path
from rasterio.plot import reshape_as_image
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_lines_map(path_dir: str, file_html: str):
    """
    Creates hydro map using hydro geopackage
    
    """
    logger.info(f"Running {path_dir}")

    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_1.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create the Folium map, centered on Pakistan (admin boundaries center)
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')

    # Load rails and roads layer from geopackage
    rail_gpkg_path = "data/PAK_misc/openstreetmap/openstreetmap_rail__PAK.gpkg"
    road_gpkg_path = "data/PAK_misc/openstreetmap/openstreetmap_roads-tertiary__PAK.gpkg"

    rail_gdf = gpd.read_file(rail_gpkg_path, layer='lines')
    road_gdf= gpd.read_file(road_gpkg_path, layer='lines')

    # Filter out roads and rails of importance to limit the dataset
    rail_gdf = rail_gdf.query("railway == 'rail' and usage == 'main'").loc[:, 
                                                            ['osm_id', 'name', 'other_tags', 'geometry']]
    highwaytype_list = ['primary', 'trunk', 'motorway']
    road_gdf = road_gdf.loc[road_gdf['highway'].isin(highwaytype_list), 
                            ['osm_id', 'name', 'surface', 'maxspeed', 'lanes', 'other_tags', 'geometry']]

    rail_gdf["type"] = "rail"
    road_gdf["type"] = "road"
    # Combine rail and road dataframes with a new column indicating type
    railroad_gdf = gpd.GeoDataFrame(pd.concat([rail_gdf, road_gdf], ignore_index=True), geometry='geometry', 
                                    crs=rail_gdf.crs)
    logger.info(len(railroad_gdf))


    # Add hydro/rivers layer to map
    folium.GeoJson(
        railroad_gdf,
        name='Rail Roads',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'purple' if feature['properties']['type'] == 'rail' else 'red',
            'weight': 1,
        },
        highlight_function=lambda feature: {
            "weight": 3,
            "color": "red"
        }
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    out_filename = 'pk_railroad_map'
    create_lines_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)