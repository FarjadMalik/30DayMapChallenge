import folium
import geopandas as gpd

from pathlib import Path
from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def generate_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")
    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2
    logger.info(f"Center Lat Lon: {center_lat, center_lon}")
    
    # Create and Center a base map
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=10, tiles='OpenStreetMap')

    # Add desired data

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    # Focus on toponymy (place names). Experiment with font choices, label placement, 
    # typography, multiple languages, or the history and meaning behind a name. 
    # Silk route and important way points on it?
    out_filename = 'places'
    generate_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)