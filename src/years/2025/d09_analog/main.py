import os
import folium
import imageio
import rasterio
import numpy as np
import geopandas as gpd

from PIL import Image
from pathlib import Path
from rasterio.plot import reshape_as_image

from src.utils.logger import get_logger
from src.utils.helpers import get_relative_path


logger = get_logger(__name__)


def create_analog_map(path_dir: str, file_html: str):
    """
    Creates polygon map for Day 3 exercises
    
    """
    logger.info(f"Hello from {path_dir}")

    # list of analog maps with approximate  “time” label
    # if the maps are not georeferenced then define boundingbbox
    maps_info = [
        {
            "path": "data/PAK_misc/analog_maps/ancientindia_modified.tif",
            # "bounds": [68, 6, 97, 36],  # [min_lon, min_lat, max_lon, max_lat]
            "year": 1850
        },
        # {
        #     "path": "british_india_map_1900.png",
        #     "bounds": [68, 6, 97, 36],
        #     "year": 1900
        # },
        # {
        #     "path": "british_india_map_1940.png",
        #     "bounds": [68, 6, 97, 36],
        #     "year": 1940
        # },
    ]

    
    # Load the shapefile for pakistan admin boundaries
    shapefile_path = "data/pakistan_admin/gadm41_PAK_3.shp"
    admin_gdf = gpd.read_file(shapefile_path)

    # # Ensure the CRS is WGS84 (EPSG:4326) so it works with Folium
    if admin_gdf is not None and admin_gdf.crs.to_string() != "EPSG:4326":
        admin_gdf = admin_gdf.to_crs(epsg=4326)

    # Calculate a center for the map, e.g., the mean of the bounds
    bounds = admin_gdf.total_bounds  # [minx, miny, maxx, maxy]
    center_lat = (bounds[1] + bounds[3]) / 2
    center_lon = (bounds[0] + bounds[2]) / 2

    # Create base folium map 
    basemap = folium.Map(location=[center_lat, center_lon], zoom_start=6, tiles='OpenStreetMap')
      
    # Add each map one by one
    for map in maps_info: 
        # Load land cover land use layer 
        
        with rasterio.open(map['path']) as src:
            bounds = src.bounds
            img = src.read()
            crs = src.crs
        
        logger.info(f"Raster CRS: {crs}")
        logger.info(f"Raster bounds: {bounds}")
        logger.info(f"Raster img shape: {img.shape}")
        
        # Reshape the image for proper display (bands, rows, cols) -> (rows, cols, bands)
        img = reshape_as_image(img)
        logger.info(f"Raster reshaped shape: {img.shape}")

        # Normalize image values to 0–1 for display
        img = img.astype(float)
        img = (img - np.nanmin(img)) / (np.nanmax(img) - np.nanmin(img))

        folium.raster_layers.ImageOverlay(
            name="Ancient India Map",
            image=img,
            bounds=[[bounds[1], bounds[0]], [bounds[3], bounds[2]]],  # [[lat_min, lon_min], [lat_max, lon_max]]
            opacity=0.7,
            interactive=True,
            cross_origin=False,
            zindex=1
        ).add_to(basemap)

    # Add the administrative boundaries layer
    folium.GeoJson(
        admin_gdf,
        name='Administrative Boundaries',
        style_function=lambda feature: {
            'fillColor': 'none',
            'color': 'blue',
            'weight': 1,
            'dashArray': '5, 5'
        }
    ).add_to(basemap)

    # Allows toggling between layers interactively 
    folium.LayerControl().add_to(basemap)
    # Save the map to an HTML file
    basemap.save(f"{Path(path_dir).parent}/{file_html}.html")
    logger.info(f"Map created – open '{file_html}.html' to view.")


if __name__ == "__main__":
    # Draw one of the maps from analog folder
    # Maps were georeferenced using QGIS
    out_filename = 'analog_map'
    create_analog_map(path_dir=str(get_relative_path(__file__)), file_html=out_filename)